from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class Account(BaseModel):
    """Reddit account model"""
    id: UUID
    reddit_username: str
    personality_json_url: str
    reddit_client_id: str
    reddit_client_secret: str
    reddit_refresh_token: str
    user_agent: str
    active: bool = True
    last_monitored_at: Optional[datetime] = None
    total_karma: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccountCreate(BaseModel):
    """Create account request"""
    reddit_username: str
    personality_json_url: str
    reddit_client_id: str
    reddit_client_secret: str
    reddit_refresh_token: str
    user_agent: Optional[str] = None

    def generate_user_agent(self) -> str:
        """Generate default user agent"""
        return f"RedditAssistant:1.0 (by /u/{self.reddit_username})"


class AccountUpdate(BaseModel):
    """Update account request"""
    personality_json_url: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_refresh_token: Optional[str] = None
    user_agent: Optional[str] = None
    active: Optional[bool] = None
