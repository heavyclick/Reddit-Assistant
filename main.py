from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from config.settings import settings
from config.supabase_client import get_supabase
from models.account import AccountCreate, AccountUpdate
from models.draft import DraftApprove, DraftReject
from services.reddit_monitor import reddit_monitor
from services.draft_generator import draft_generator
from services.karma_scorer import karma_scorer
from services.reddit_poster import reddit_poster
from services.performance_tracker import performance_tracker
from utils.email_client import email_client

# Initialize FastAPI app
app = FastAPI(
    title="Reddit Assistant API",
    description="AI-Assisted Reddit Engagement System for Accessibility",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = get_supabase()


# Health check
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "Reddit Assistant API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


# ============================================================================
# ACCOUNT ENDPOINTS
# ============================================================================

@app.get("/accounts")
async def list_accounts():
    """List all accounts"""
    result = db.table('accounts').select('*').execute()
    return {"accounts": result.data}


@app.get("/accounts/{account_id}")
async def get_account(account_id: str):
    """Get account by ID"""
    result = db.table('accounts').select('*').eq('id', account_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Account not found")

    return result.data[0]


@app.post("/accounts")
async def create_account(account: AccountCreate):
    """Create new account"""
    # Check account limit
    count = db.table('accounts').select('id', count='exact').execute()
    if count.count >= settings.MAX_ACCOUNTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_ACCOUNTS} accounts allowed"
        )

    # Generate user agent if not provided
    user_agent = account.user_agent or account.generate_user_agent()

    result = db.table('accounts').insert({
        'reddit_username': account.reddit_username,
        'personality_json_url': account.personality_json_url,
        'reddit_client_id': account.reddit_client_id,
        'reddit_client_secret': account.reddit_client_secret,
        'reddit_refresh_token': account.reddit_refresh_token,
        'user_agent': user_agent,
        'active': True,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }).execute()

    return {"message": "Account created", "account": result.data[0]}


@app.patch("/accounts/{account_id}")
async def update_account(account_id: str, update: AccountUpdate):
    """Update account"""
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()

    result = db.table('accounts').update(update_data).eq('id', account_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Account not found")

    return {"message": "Account updated", "account": result.data[0]}


@app.delete("/accounts/{account_id}")
async def delete_account(account_id: str):
    """Delete account"""
    db.table('accounts').delete().eq('id', account_id).execute()
    return {"message": "Account deleted"}


# ============================================================================
# OPPORTUNITY ENDPOINTS
# ============================================================================

@app.get("/opportunities")
async def list_opportunities(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """List opportunities"""
    query = db.table('opportunities').select('*')

    if account_id:
        query = query.eq('account_id', account_id)
    if status:
        query = query.eq('status', status)

    result = query.order('karma_opportunity_score', desc=True).limit(limit).execute()
    return {"opportunities": result.data}


# ============================================================================
# DRAFT ENDPOINTS
# ============================================================================

@app.get("/drafts")
async def list_drafts(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """List drafts"""
    query = db.table('drafts').select('*, opportunity:opportunities(*), account:accounts(*)')

    if account_id:
        query = query.eq('account_id', account_id)
    if status:
        query = query.eq('status', status)

    result = query.order('karma_probability_score', desc=True).limit(limit).execute()
    return {"drafts": result.data}


@app.get("/drafts/{draft_id}")
async def get_draft(draft_id: str):
    """Get draft by ID"""
    result = db.table('drafts').select(
        '*, opportunity:opportunities(*), account:accounts(*)'
    ).eq('id', draft_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Draft not found")

    return result.data[0]


@app.post("/drafts/{draft_id}/approve")
async def approve_draft(draft_id: str, approval: DraftApprove):
    """Approve a draft for posting"""
    # Update draft
    update_data = {
        'status': 'approved',
        'approved_at': datetime.now(timezone.utc).isoformat(),
        'approved_by': approval.approved_by
    }

    if approval.edited_text:
        update_data['edited_text'] = approval.edited_text
    if approval.user_notes:
        update_data['user_notes'] = approval.user_notes

    result = db.table('drafts').update(update_data).eq('id', draft_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Draft not found")

    return {"message": "Draft approved", "draft": result.data[0]}


@app.post("/drafts/{draft_id}/reject")
async def reject_draft(draft_id: str, rejection: DraftReject):
    """Reject a draft"""
    result = db.table('drafts').update({
        'status': 'rejected',
        'user_notes': rejection.reason
    }).eq('id', draft_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Draft not found")

    return {"message": "Draft rejected"}


@app.post("/drafts/{draft_id}/regenerate")
async def regenerate_draft(draft_id: str, custom_instructions: Optional[str] = None):
    """Regenerate a draft with optional custom instructions"""
    try:
        new_text = await draft_generator.regenerate_draft(
            draft_id,
            custom_instructions
        )
        return {"message": "Draft regenerated", "draft_text": new_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics/{account_id}")
async def get_analytics(account_id: str, days: int = 30):
    """Get account analytics"""
    analytics = await performance_tracker.get_account_analytics(account_id, days)
    return analytics


@app.get("/insights/{account_id}")
async def get_insights(account_id: str):
    """Get learning insights for account"""
    result = db.table('learning_insights').select('*').eq(
        'account_id', account_id
    ).order('confidence_score', desc=True).execute()

    return {"insights": result.data}


# ============================================================================
# JOB TRIGGER ENDPOINTS (for manual testing)
# ============================================================================

@app.post("/jobs/monitor")
async def trigger_monitor_job(background_tasks: BackgroundTasks):
    """Trigger Reddit monitoring job"""
    background_tasks.add_task(reddit_monitor.monitor_all_accounts)
    return {"message": "Monitoring job triggered"}


@app.post("/jobs/generate-drafts")
async def trigger_draft_generation(background_tasks: BackgroundTasks):
    """Trigger draft generation job"""
    background_tasks.add_task(draft_generator.generate_drafts_for_all_accounts)
    background_tasks.add_task(karma_scorer.score_all_pending_drafts)
    return {"message": "Draft generation job triggered"}


@app.post("/jobs/post-approved")
async def trigger_posting_job(background_tasks: BackgroundTasks):
    """Trigger posting job"""
    background_tasks.add_task(reddit_poster.post_all_approved_drafts)
    return {"message": "Posting job triggered"}


@app.post("/jobs/track-performance")
async def trigger_performance_tracking(background_tasks: BackgroundTasks):
    """Trigger performance tracking job"""
    background_tasks.add_task(performance_tracker.track_all_accounts)
    return {"message": "Performance tracking job triggered"}


# ============================================================================
# WORKFLOW ENDPOINT (for testing full workflow)
# ============================================================================

@app.post("/test-workflow/{account_id}")
async def test_workflow(account_id: str):
    """Test the full workflow for one account"""
    # Get account
    result = db.table('accounts').select('*').eq('id', account_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Account not found")

    account = result.data[0]

    # 1. Monitor
    await reddit_monitor.monitor_account(account)

    # 2. Generate drafts
    await draft_generator.generate_drafts_for_account(account, max_opportunities=3)

    # 3. Score drafts
    await karma_scorer.score_all_pending_drafts()

    return {"message": "Workflow completed", "account": account['reddit_username']}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
