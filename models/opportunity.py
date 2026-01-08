from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class Opportunity(BaseModel):
    """Reddit post/thread opportunity model"""
    id: UUID
    account_id: UUID
    reddit_post_id: str
    reddit_permalink: str
    subreddit: str
    post_title: Optional[str] = None
    post_body: Optional[str] = None
    post_author: Optional[str] = None
    post_created_utc: Optional[datetime] = None
    post_score: int = 0
    post_num_comments: int = 0
    post_age_hours: float = 0.0
    engagement_velocity: float = 0.0  # score per hour
    karma_opportunity_score: float = 0.0  # 0-100
    priority_match: bool = False  # matches user's priority triggers
    discovered_at: datetime
    status: str = "new"  # new, drafting, drafted, expired, posted

    class Config:
        from_attributes = True


class OpportunityCreate(BaseModel):
    """Create opportunity request"""
    account_id: UUID
    reddit_post_id: str
    reddit_permalink: str
    subreddit: str
    post_title: Optional[str] = None
    post_body: Optional[str] = None
    post_author: Optional[str] = None
    post_created_utc: Optional[datetime] = None
    post_score: int = 0
    post_num_comments: int = 0
    post_age_hours: float = 0.0
    engagement_velocity: float = 0.0
    karma_opportunity_score: float = 0.0
    priority_match: bool = False
