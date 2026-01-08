from datetime import datetime, timedelta, timezone
from typing import List, Dict
from config.supabase_client import get_supabase
from utils.reddit_client import reddit_client_manager


class PerformanceTracker:
    """Tracks karma and performance over time"""

    def __init__(self):
        self.db = get_supabase()

    async def track_all_accounts(self):
        """Track performance for all active accounts"""
        accounts = self.db.table('accounts').select('*').eq('active', True).execute()

        print(f"Tracking performance for {len(accounts.data)} accounts...")

        for account in accounts.data:
            try:
                await self.track_account_performance(account)
            except Exception as e:
                print(f"Error tracking {account['reddit_username']}: {e}")

    async def track_account_performance(self, account: Dict):
        """Track performance for a single account"""
        print(f"Tracking u/{account['reddit_username']}...")

        # Get Reddit client
        reddit = reddit_client_manager.get_client(account)

        # Get posted content from last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

        posted_content = self.db.table('posted_content').select('*').eq(
            'account_id', account['id']
        ).gte(
            'posted_at', thirty_days_ago.isoformat()
        ).execute()

        if not posted_content.data:
            print(f"  → No content to track")
            return

        total_karma = 0
        updated_count = 0

        for content in posted_content.data:
            try:
                # Fetch current karma from Reddit
                if content.get('reddit_comment_id'):
                    comment = reddit.comment(id=content['reddit_comment_id'])
                    current_karma = comment.score
                    removed = comment.removed_by_category is not None
                else:
                    # It's a post
                    submission = reddit.submission(id=content['reddit_post_id'])
                    current_karma = submission.score
                    removed = submission.removed_by_category is not None

                # Update posted_content
                self.db.table('posted_content').update({
                    'current_karma': current_karma,
                    'removed': removed,
                    'last_karma_check': datetime.now(timezone.utc).isoformat()
                }).eq('id', content['id']).execute()

                # Record in performance_history
                hours_since_post = (
                    datetime.now(timezone.utc) -
                    datetime.fromisoformat(content['posted_at'].replace('Z', '+00:00'))
                ).total_seconds() / 3600

                self.db.table('performance_history').insert({
                    'account_id': account['id'],
                    'posted_content_id': content['id'],
                    'karma_score': current_karma,
                    'subreddit': content['subreddit'],
                    'time_since_post_hours': hours_since_post,
                    'recorded_at': datetime.now(timezone.utc).isoformat()
                }).execute()

                total_karma += current_karma
                updated_count += 1

                if removed:
                    print(f"  ⚠️  Content removed: {content['reddit_permalink']}")

            except Exception as e:
                print(f"  ✗ Error tracking content {content['id']}: {e}")

        # Update account total karma
        self.db.table('accounts').update({
            'total_karma': total_karma
        }).eq('id', account['id']).execute()

        print(f"  → Tracked {updated_count} items, total karma: {total_karma}")

        # Generate insights
        await self.generate_insights(account)

    async def generate_insights(self, account: Dict):
        """Generate learning insights from performance data"""
        # Get top performing content (karma >= 20)
        top_content = self.db.table('posted_content').select('*').eq(
            'account_id', account['id']
        ).gte(
            'current_karma', 20
        ).order(
            'current_karma', desc=True
        ).limit(20).execute()

        if not top_content.data:
            return

        # Analyze by subreddit
        subreddit_performance = {}

        for content in top_content.data:
            subreddit = content['subreddit']
            if subreddit not in subreddit_performance:
                subreddit_performance[subreddit] = {
                    'count': 0,
                    'total_karma': 0,
                    'texts': []
                }

            subreddit_performance[subreddit]['count'] += 1
            subreddit_performance[subreddit]['total_karma'] += content['current_karma']
            subreddit_performance[subreddit]['texts'].append(content['final_text'])

        # Generate insights per subreddit
        for subreddit, data in subreddit_performance.items():
            if data['count'] < 3:  # Need at least 3 samples
                continue

            avg_karma = data['total_karma'] / data['count']
            avg_length = sum(len(text.split()) for text in data['texts']) / len(data['texts'])

            # Check if insight already exists
            existing = self.db.table('learning_insights').select('id').eq(
                'account_id', account['id']
            ).eq(
                'subreddit', subreddit
            ).eq(
                'insight_type', 'successful_pattern'
            ).execute()

            insight_description = (
                f"Comments averaging {avg_length:.0f} words get {avg_karma:.0f} "
                f"karma on average in r/{subreddit}. Sample size: {data['count']} posts."
            )

            if existing.data:
                # Update existing insight
                self.db.table('learning_insights').update({
                    'pattern_description': insight_description,
                    'confidence_score': min(data['count'] / 10, 1.0),
                    'applied_count': 0
                }).eq('id', existing.data[0]['id']).execute()
            else:
                # Create new insight
                self.db.table('learning_insights').insert({
                    'account_id': account['id'],
                    'insight_type': 'successful_pattern',
                    'subreddit': subreddit,
                    'pattern_description': insight_description,
                    'evidence_post_ids': [c['id'] for c in top_content.data if c['subreddit'] == subreddit],
                    'confidence_score': min(data['count'] / 10, 1.0),
                    'learned_at': datetime.now(timezone.utc).isoformat(),
                    'applied_count': 0
                }).execute()

        print(f"  → Generated insights for {len(subreddit_performance)} subreddits")

    async def get_account_analytics(self, account_id: str, days: int = 30) -> Dict:
        """Get analytics for an account"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get posted content
        content = self.db.table('posted_content').select('*').eq(
            'account_id', account_id
        ).gte(
            'posted_at', cutoff_date.isoformat()
        ).execute()

        if not content.data:
            return {
                'total_posts': 0,
                'total_karma': 0,
                'avg_karma': 0,
                'top_subreddits': [],
                'best_posts': []
            }

        total_karma = sum(c['current_karma'] for c in content.data)
        avg_karma = total_karma / len(content.data)

        # Subreddit breakdown
        subreddit_stats = {}
        for c in content.data:
            sr = c['subreddit']
            if sr not in subreddit_stats:
                subreddit_stats[sr] = {'count': 0, 'karma': 0}
            subreddit_stats[sr]['count'] += 1
            subreddit_stats[sr]['karma'] += c['current_karma']

        top_subreddits = sorted(
            [{'subreddit': sr, **stats} for sr, stats in subreddit_stats.items()],
            key=lambda x: x['karma'],
            reverse=True
        )[:5]

        # Best posts
        best_posts = sorted(
            content.data,
            key=lambda x: x['current_karma'],
            reverse=True
        )[:5]

        return {
            'total_posts': len(content.data),
            'total_karma': total_karma,
            'avg_karma': avg_karma,
            'top_subreddits': top_subreddits,
            'best_posts': best_posts
        }


# Global instance
performance_tracker = PerformanceTracker()
