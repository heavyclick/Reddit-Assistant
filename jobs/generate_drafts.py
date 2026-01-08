#!/usr/bin/env python3
"""
Cron job: Generate drafts and send approval emails
Schedule: Every 45 minutes
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.draft_generator import draft_generator
from services.karma_scorer import karma_scorer
from utils.slack_client import slack_client
from config.supabase_client import get_supabase
from datetime import datetime, timezone


async def main():
    print("=" * 60)
    print("DRAFT GENERATION JOB STARTED")
    print("=" * 60)

    db = get_supabase()

    try:
        # 1. Generate drafts for all accounts
        await draft_generator.generate_drafts_for_all_accounts(max_opportunities_per_account=5)

        # 2. Score all pending drafts
        print("\nScoring drafts...")
        await karma_scorer.score_all_pending_drafts()

        # 3. Send Slack notifications and set auto-approve timestamp
        print("\nSending Slack notifications...")
        accounts = db.table('accounts').select('*').eq('active', True).execute()

        for account in accounts.data:
            # Get pending drafts for this account
            drafts = db.table('drafts').select(
                '*, opportunity:opportunities(*)'
            ).eq(
                'account_id', account['id']
            ).eq(
                'status', 'pending'
            ).order(
                'karma_probability_score', desc=True
            ).limit(10).execute()

            if drafts.data:
                # Set notification sent timestamp for auto-approve logic
                for draft in drafts.data:
                    db.table('drafts').update({
                        'notification_sent_at': datetime.now(timezone.utc).isoformat()
                    }).eq('id', draft['id']).execute()

                # Send Slack notification
                await slack_client.send_draft_notification(account, drafts.data)

        print("\n✓ Draft generation job completed successfully")

    except Exception as e:
        print(f"\n✗ Draft generation job failed: {e}")
        raise

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
