from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class Formality(str, Enum):
    VERY_CASUAL = "very_casual"
    CASUAL = "casual"
    CASUAL_MEDIUM = "casual_medium"
    FORMAL = "formal"
    VERY_FORMAL = "very_formal"


class EmojiUsage(str, Enum):
    NEVER = "never"
    RARE = "rare"
    MODERATE = "moderate"
    FREQUENT = "frequent"
    VERY_FREQUENT = "very_frequent"


class CommentLength(str, Enum):
    BRIEF = "brief_1_2_sentences"
    MEDIUM = "medium_3_6_sentences"
    LONG = "long_7plus_sentences"
    VARIES = "varies"


class SupportiveVsAdvisory(str, Enum):
    MOSTLY_SUPPORTIVE = "mostly_supportive"
    BALANCED = "balanced"
    MOSTLY_ADVISORY = "mostly_advisory"


class Demographics(BaseModel):
    age: Optional[int] = None
    gender_identity: Optional[str] = None
    location: Optional[str] = None


class UrgentNeeds(BaseModel):
    karma_goal: Optional[int] = None
    time_sensitivity: Optional[str] = None  # LOW, MEDIUM, HIGH, CRITICAL
    emotional_stakes: Optional[str] = None
    reason: Optional[str] = None


class DisabilityContext(BaseModel):
    physical_limitations: Optional[str] = None
    cognitive_fatigue_patterns: Optional[str] = None
    time_availability_constraints: Optional[str] = None
    urgent_needs: Optional[UrgentNeeds] = None


class PetIdentity(BaseModel):
    is_pet_parent: bool = False
    pet_types: List[str] = []
    favorite_breeds: List[str] = []
    emotional_attachment_style: Optional[str] = None


class CoreIdentity(BaseModel):
    primary_traits: List[str]
    life_context: Optional[str] = None
    values: List[str] = []
    pet_identity: Optional[PetIdentity] = None
    expertise_areas: List[str] = []


class PsychologicalTraits(BaseModel):
    introversion_extroversion: Optional[str] = None
    conflict_response_style: Optional[str] = None
    sensitivity_to_tone: Optional[str] = None
    humor_preference: Optional[str] = None
    emotional_openness: Optional[str] = None


class Voice(BaseModel):
    tone: Optional[str] = None
    formality: Optional[Formality] = None
    sentence_length_preference: Optional[str] = None
    emoji_usage: Optional[EmojiUsage] = None
    favorite_emojis: List[str] = []
    signature_phrases: List[str] = []


class EngagementStyle(BaseModel):
    comment_length_preference: Optional[CommentLength] = None
    empathy_level: Optional[str] = None
    supportive_vs_advisory: Optional[SupportiveVsAdvisory] = None
    sharing_personal_experience: Optional[str] = None
    asking_followup_questions: Optional[str] = None
    how_disagreement_expressed: Optional[str] = None


class Boundaries(BaseModel):
    topics_to_avoid: List[str] = []
    never_claim_expertise_in: List[str] = []
    self_disclosure_boundaries: Optional[str] = None
    always_disclose: Optional[str] = None


class Communication(BaseModel):
    voice: Voice
    engagement_style: EngagementStyle
    boundaries: Boundaries


class Subreddits(BaseModel):
    primary: List[str]
    secondary: List[str] = []
    engagement_frequency: Dict[str, str] = {}


class PostingLimits(BaseModel):
    max_comments_per_day: int = 5
    max_posts_per_week: int = 2
    min_hours_between_comments: float = 2.0


class KarmaStrategy(BaseModel):
    target_subreddit_karma: Dict[str, int] = {}
    preferred_karma_threshold: int = 10


class Strategy(BaseModel):
    posting_limits: PostingLimits
    optimal_times: List[str] = []
    priority_triggers: List[str] = []
    karma_strategy: Optional[KarmaStrategy] = None


class TriggersAndValues(BaseModel):
    what_matters_deeply: List[str] = []
    what_annoys_or_angers: List[str] = []
    what_feels_safe_and_understood: List[str] = []


class LearningPreferences(BaseModel):
    learn_from_upvoted_comments: bool = True
    learn_from_downvoted_comments: bool = True
    adjust_tone_based_on_feedback: bool = True
    cross_account_learning: bool = False


class RedditCredentials(BaseModel):
    client_id: str
    client_secret: str
    refresh_token: str
    user_agent: Optional[str] = None


class Personality(BaseModel):
    """Complete personality profile for a Reddit account"""
    account_id: str
    reddit_username: str
    demographics: Optional[Demographics] = None
    disability_context: Optional[DisabilityContext] = None
    core_identity: CoreIdentity
    psychological_traits: Optional[PsychologicalTraits] = None
    communication: Communication
    interests: List[str] = []
    triggers_and_values: Optional[TriggersAndValues] = None
    subreddits: Subreddits
    strategy: Strategy
    learning_preferences: Optional[LearningPreferences] = None
    reddit_credentials: RedditCredentials

    class Config:
        use_enum_values = True
