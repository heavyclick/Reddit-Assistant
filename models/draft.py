from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class Draft(BaseModel):
    """Generated comment/post draft model"""
    id: UUID
    account_id: UUID
    opportunity_id: UUID
    draft_text: str
    draft_type: str = "comment"  # comment, reply, post
    variant_number: int = 1
    karma_probability_score: Optional[float] = None
    personality_alignment_score: Optional[float] = None
    reasoning: Optional[str] = None
    generated_at: datetime
    status: str = "pending"  # pending, approved, rejected, edited, posted, failed
    edited_text: Optional[str] = None
    user_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    posted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DraftCreate(BaseModel):
    """Create draft request"""
    account_id: UUID
    opportunity_id: UUID
    draft_text: str
    draft_type: str = "comment"
    variant_number: int = 1
    karma_probability_score: Optional[float] = None
    personality_alignment_score: Optional[float] = None
    reasoning: Optional[str] = None


class DraftApprove(BaseModel):
    """Approve draft request"""
    draft_id: UUID
    edited_text: Optional[str] = None
    user_notes: Optional[str] = None
    approved_by: str


class DraftReject(BaseModel):
    """Reject draft request"""
    draft_id: UUID
    reason: Optional[str] = None
