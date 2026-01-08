import time
from datetime import datetime, timezone
from typing import List
from uuid import UUID
import praw
from config.supabase_client import get_supabase
from utils.reddit_client import reddit_client_manager
from models.personality import Personality
import json
import httpx


class RedditMonitor:
    """Monitors Reddit for karma opportunities"""

    def __init__(self):
        self.db = get_supabase()

    async def monitor_all_accounts(self):
        """Monitor subreddits for all active accounts"""
        # Get all active accounts
        result = self.db.table('accounts').select('*').eq('active', True).execute()
        accounts = result.data

        print(f"Monitoring {len(accounts)} active accounts...")

        for account in accounts:
            try:
                await self.monitor_account(account)
            except Exception as e:
                print(f"Error monitoring account {account['reddit_username']}: {e}")

    async def monitor_account(self, account: dict):
        """Monitor subreddits for a single account"""
        print(f"Monitoring account: u/{account['reddit_username']}")

        # Load personality to get subreddits
        personality = await self.load_personality(account['personality_json_url'])

        if not personality:
            print(f"  ✗ Could not load personality for {account['reddit_username']}")
            return

        # Get subreddits to monitor
        subreddits = personality.subreddits.primary + personality.subreddits.secondary

        # Get Reddit client
        reddit = reddit_client_manager.get_client(account)

        opportunities_found = 0

        for subreddit_name in subreddits:
            try:
                # Clean subreddit name (remove r/ if present)
                subreddit_name = subreddit_name.replace('r/', '')

                subreddit = reddit.subreddit(subreddit_name)

                # Get new posts (last 12 hours, limit 50)
                for submission in subreddit.new(limit=50):
                    # Check age
                    post_age_hours = (time.time() - submission.created_utc) / 3600
                    if post_age_hours > 12:
                        continue

                    # Skip if already tracked
                    existing = self.db.table('opportunities').select('id').eq(
                        'account_id', account['id']
                    ).eq(
                        'reddit_post_id', submission.id
                    ).execute()

                    if existing.data:
                        continue

                    # Calculate opportunity score
                    opportunity_score = self.calculate_opportunity_score(
                        submission,
                        post_age_hours,
                        personality
                    )

                    # Only save if score > 30 (filter low quality)
                    if opportunity_score < 30:
                        continue

                    # Check priority match
                    priority_match = self.check_priority_match(submission, personality)

                    # Create opportunity
                    self.db.table('opportunities').insert({
                        'account_id': account['id'],
                        'reddit_post_id': submission.id,
                        'reddit_permalink': f"https://reddit.com{submission.permalink}",
                        'subreddit': subreddit_name,
                        'post_title': submission.title,
                        'post_body': submission.selftext[:2000] if submission.selftext else None,
                        'post_author': str(submission.author) if submission.author else '[deleted]',
                        'post_created_utc': datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).isoformat(),
                        'post_score': submission.score,
                        'post_num_comments': submission.num_comments,
                        'post_age_hours': post_age_hours,
                        'engagement_velocity': submission.score / max(post_age_hours, 0.1),
                        'karma_opportunity_score': opportunity_score,
                        'priority_match': priority_match,
                        'status': 'new'
                    }).execute()

                    opportunities_found += 1
                    print(f"  ✓ Found opportunity in r/{subreddit_name}: {submission.title[:60]}... (score: {opportunity_score:.0f})")

            except Exception as e:
                print(f"  ✗ Error monitoring r/{subreddit_name}: {e}")

        # Update last_monitored_at
        self.db.table('accounts').update({
            'last_monitored_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', account['id']).execute()

        print(f"  → Found {opportunities_found} new opportunities for u/{account['reddit_username']}")

    def calculate_opportunity_score(
        self,
        submission: praw.models.Submission,
        post_age_hours: float,
        personality: Personality
    ) -> float:
        """Calculate karma opportunity score (0-100)"""
        score = 0.0

        # 1. Age factor (newer = better)
        if post_age_hours < 1:
            score += 30
        elif post_age_hours < 3:
            score += 25
        elif post_age_hours < 6:
            score += 15
        elif post_age_hours < 12:
            score += 10

        # 2. Engagement velocity (upvotes per hour)
        velocity = submission.score / max(post_age_hours, 0.1)
        if velocity > 100:
            score += 25
        elif velocity > 50:
            score += 20
        elif velocity > 20:
            score += 15
        elif velocity > 10:
            score += 10
        elif velocity > 5:
            score += 5

        # 3. Comment sparsity (fewer comments = more opportunity)
        if submission.num_comments < 5:
            score += 20
        elif submission.num_comments < 15:
            score += 15
        elif submission.num_comments < 30:
            score += 10
        elif submission.num_comments < 50:
            score += 5

        # 4. Post quality (has body text, not just title)
        if submission.selftext and len(submission.selftext) > 100:
            score += 10

        # 5. Not locked or archived
        if not submission.locked and not submission.archived:
            score += 5

        return min(score, 100)

    def check_priority_match(
        self,
        submission: praw.models.Submission,
        personality: Personality
    ) -> bool:
        """Check if post matches user's priority triggers"""
        if not personality.strategy.priority_triggers:
            return False

        post_text = f"{submission.title} {submission.selftext}".lower()

        for trigger in personality.strategy.priority_triggers:
            if trigger.lower() in post_text:
                return True

        return False

    async def load_personality(self, personality_json_url: str) -> Personality:
        """Load personality from JSON URL"""
        try:
            # Fetch JSON from URL
            async with httpx.AsyncClient() as client:
                response = await client.get(personality_json_url)
                response.raise_for_status()
                data = response.json()

            # Parse into Personality model
            personality = Personality(**data)
            return personality

        except Exception as e:
            print(f"Error loading personality from {personality_json_url}: {e}")
            return None


# Lazy-load global instance
_reddit_monitor_instance = None

def get_reddit_monitor() -> RedditMonitor:
    """Get RedditMonitor instance (lazy-loaded)"""
    global _reddit_monitor_instance
    if _reddit_monitor_instance is None:
        _reddit_monitor_instance = RedditMonitor()
    return _reddit_monitor_instance
