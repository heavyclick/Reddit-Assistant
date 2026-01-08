from datetime import datetime, timedelta
from typing import Optional
from config.supabase_client import get_supabase


class RateLimiter:
    """Rate limiting for Reddit API and posting"""

    def __init__(self):
        self.db = get_supabase()

    def check_rate_limit(
        self,
        account_id: str,
        limit_type: str,
        max_allowed: int,
        window_hours: int = 24
    ) -> bool:
        """Check if account is within rate limit"""
        window_start = datetime.now() - timedelta(hours=window_hours)

        # Query current rate limit
        result = self.db.table('rate_limits').select('*').eq(
            'account_id', account_id
        ).eq(
            'limit_type', limit_type
        ).gte(
            'limit_window_start', window_start.isoformat()
        ).execute()

        if not result.data:
            # No limit entry, create one
            self.db.table('rate_limits').insert({
                'account_id': account_id,
                'limit_type': limit_type,
                'limit_window_start': datetime.now().isoformat(),
                'current_count': 0,
                'max_allowed': max_allowed
            }).execute()
            return True

        rate_limit = result.data[0]
        return rate_limit['current_count'] < rate_limit['max_allowed']

    def increment_rate_limit(
        self,
        account_id: str,
        limit_type: str,
        max_allowed: int,
        window_hours: int = 24
    ):
        """Increment rate limit counter"""
        window_start = datetime.now() - timedelta(hours=window_hours)

        # Try to find existing limit
        result = self.db.table('rate_limits').select('*').eq(
            'account_id', account_id
        ).eq(
            'limit_type', limit_type
        ).gte(
            'limit_window_start', window_start.isoformat()
        ).execute()

        if result.data:
            # Increment existing
            rate_limit = result.data[0]
            self.db.table('rate_limits').update({
                'current_count': rate_limit['current_count'] + 1
            }).eq('id', rate_limit['id']).execute()
        else:
            # Create new
            self.db.table('rate_limits').insert({
                'account_id': account_id,
                'limit_type': limit_type,
                'limit_window_start': datetime.now().isoformat(),
                'current_count': 1,
                'max_allowed': max_allowed
            }).execute()

    def reset_rate_limit(self, account_id: str, limit_type: str):
        """Reset rate limit for account"""
        self.db.table('rate_limits').delete().eq(
            'account_id', account_id
        ).eq(
            'limit_type', limit_type
        ).execute()


# Lazy-load global instance
_rate_limiter_instance = None

def get_rate_limiter() -> 'RateLimiter':
    """Get RateLimiter instance (lazy-loaded)"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
    return _rate_limiter_instance
