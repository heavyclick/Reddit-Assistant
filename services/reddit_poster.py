import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from config.supabase_client import get_supabase
from config.settings import settings
from utils.reddit_client import reddit_client_manager
from utils.rate_limiter import rate_limiter
from utils.slack_client import slack_client


class RedditPoster:
    """Posts approved drafts to Reddit"""

    def __init__(self):
        self.db = get_supabase()

    async def post_all_approved_drafts(self):
        """Post all approved drafts with rate limiting"""
        # First, handle auto-approvals
        await self.auto_approve_expired_drafts()

        # Get all active accounts
        accounts = self.db.table('accounts').select('*').eq('active', True).execute()

        print(f"Processing approved drafts for {len(accounts.data)} accounts...")

        for account in accounts.data:
            try:
                await self.post_approved_drafts_for_account(account)
            except Exception as e:
                print(f"Error posting for {account['reddit_username']}: {e}")

    async def auto_approve_expired_drafts(self):
        """Auto-approve drafts that have been pending for more than AUTO_APPROVE_TIMEOUT_MINUTES"""
        timeout_minutes = settings.AUTO_APPROVE_TIMEOUT_MINUTES
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)

        # Find pending drafts with notification sent more than timeout_minutes ago
        pending_drafts = self.db.table('drafts').select('*').eq(
            'status', 'pending'
        ).not_.is_(
            'notification_sent_at', 'null'
        ).lte(
            'notification_sent_at', cutoff_time.isoformat()
        ).execute()

        if pending_drafts.data:
            print(f"Auto-approving {len(pending_drafts.data)} drafts (timeout: {timeout_minutes} min)...")

            for draft in pending_drafts.data:
                self.db.table('drafts').update({
                    'status': 'approved',
                    'approved_at': datetime.now(timezone.utc).isoformat(),
                    'approved_by': 'auto_approve_system',
                    'auto_approved': True
                }).eq('id', draft['id']).execute()

                print(f"  ✓ Auto-approved draft {draft['id'][:8]}")

    async def post_approved_drafts_for_account(self, account: Dict):
        """Post approved drafts for a single account"""
        # Check rate limit
        can_post = rate_limiter.check_rate_limit(
            account_id=account['id'],
            limit_type='daily_comments',
            max_allowed=settings.MAX_COMMENTS_PER_DAY_DEFAULT,
            window_hours=24
        )

        if not can_post:
            print(f"  ⏸️  Rate limit reached for u/{account['reddit_username']}, skipping")
            return

        # Get approved drafts
        drafts = self.db.table('drafts').select(
            '*, opportunity:opportunities(*)'
        ).eq(
            'account_id', account['id']
        ).eq(
            'status', 'approved'
        ).order(
            'karma_probability_score', desc=True
        ).limit(5).execute()

        if not drafts.data:
            return

        print(f"Posting for u/{account['reddit_username']}: {len(drafts.data)} drafts")

        # Get Reddit client
        reddit = reddit_client_manager.get_client(account)

        posts_made = 0

        for draft in drafts.data:
            try:
                # Double-check rate limit before each post
                can_post = rate_limiter.check_rate_limit(
                    account_id=account['id'],
                    limit_type='daily_comments',
                    max_allowed=settings.MAX_COMMENTS_PER_DAY_DEFAULT,
                    window_hours=24
                )

                if not can_post:
                    print(f"  ⏸️  Rate limit reached, stopping")
                    break

                # Post to Reddit
                result = await self.post_draft(draft, account, reddit)

                if result:
                    posts_made += 1

                    # Wait between posts to avoid spam detection
                    await asyncio.sleep(90)  # 1.5 minute delay

            except Exception as e:
                print(f"  ✗ Error posting draft {draft['id']}: {e}")
                # Mark draft as failed
                self.db.table('drafts').update({
                    'status': 'failed',
                    'user_notes': f"Post failed: {str(e)}"
                }).eq('id', draft['id']).execute()

        print(f"  → Posted {posts_made} comments for u/{account['reddit_username']}")

    async def post_draft(
        self,
        draft: Dict,
        account: Dict,
        reddit
    ) -> bool:
        """Post a single draft to Reddit"""
        opportunity = draft['opportunity']

        try:
            # Get the submission
            submission = reddit.submission(id=opportunity['reddit_post_id'])

            # Use edited text if available, otherwise original
            final_text = draft['edited_text'] or draft['draft_text']

            # Post comment
            comment = submission.reply(final_text)

            # Record in database
            posted_content = self.db.table('posted_content').insert({
                'account_id': account['id'],
                'draft_id': draft['id'],
                'opportunity_id': opportunity['id'],
                'reddit_comment_id': comment.id,
                'reddit_permalink': f"https://reddit.com{comment.permalink}",
                'final_text': final_text,
                'subreddit': opportunity['subreddit'],
                'parent_post_id': opportunity['reddit_post_id'],
                'posted_at': datetime.now(timezone.utc).isoformat(),
                'current_karma': 1  # Reddit starts at 1
            }).execute()

            # Update draft status
            self.db.table('drafts').update({
                'status': 'posted',
                'posted_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', draft['id']).execute()

            # Increment rate limit
            rate_limiter.increment_rate_limit(
                account_id=account['id'],
                limit_type='daily_comments',
                max_allowed=settings.MAX_COMMENTS_PER_DAY_DEFAULT,
                window_hours=24
            )

            # Log audit trail
            self.db.table('audit_log').insert({
                'account_id': account['id'],
                'action': 'comment_posted',
                'details': {
                    'draft_id': draft['id'],
                    'reddit_comment_id': comment.id,
                    'subreddit': opportunity['subreddit'],
                    'permalink': f"https://reddit.com{comment.permalink}"
                }
            }).execute()

            print(f"  ✓ Posted comment to r/{opportunity['subreddit']}: https://reddit.com{comment.permalink}")

            # Send confirmation via Slack
            try:
                await slack_client.send_post_confirmation(
                    account,
                    posted_content.data[0]
                )
            except:
                pass  # Don't fail post if email fails

            return True

        except Exception as e:
            print(f"  ✗ Failed to post: {e}")

            # Log failure
            self.db.table('audit_log').insert({
                'account_id': account['id'],
                'action': 'post_failed',
                'details': {
                    'draft_id': draft['id'],
                    'error': str(e),
                    'subreddit': opportunity['subreddit']
                }
            }).execute()

            raise


# Lazy-load global instance
_reddit_poster_instance = None

def get_reddit_poster() -> 'RedditPoster':
    """Get RedditPoster instance (lazy-loaded)"""
    global _reddit_poster_instance
    if _reddit_poster_instance is None:
        _reddit_poster_instance = RedditPoster()
    return _reddit_poster_instance
