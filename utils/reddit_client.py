import praw
from typing import Optional
from models.account import Account


class RedditClientManager:
    """Manages Reddit API clients for multiple accounts"""

    def __init__(self):
        self.clients = {}  # Cache clients by account_id

    def get_client(self, account: Account) -> praw.Reddit:
        """Get or create Reddit client for account"""
        if account.id in self.clients:
            return self.clients[account.id]

        client = praw.Reddit(
            client_id=account.reddit_client_id,
            client_secret=account.reddit_client_secret,
            refresh_token=account.reddit_refresh_token,
            user_agent=account.user_agent
        )

        # Cache the client
        self.clients[account.id] = client
        return client

    def clear_cache(self, account_id: Optional[str] = None):
        """Clear cached clients"""
        if account_id:
            self.clients.pop(account_id, None)
        else:
            self.clients.clear()


# Lazy-load global instance
_reddit_client_manager_instance = None

def get_reddit_client_manager() -> 'RedditClientManager':
    """Get RedditClientManager instance (lazy-loaded)"""
    global _reddit_client_manager_instance
    if _reddit_client_manager_instance is None:
        _reddit_client_manager_instance = RedditClientManager()
    return _reddit_client_manager_instance
