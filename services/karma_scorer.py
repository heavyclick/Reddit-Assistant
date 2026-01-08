import time
from typing import Dict
from config.supabase_client import get_supabase


class KarmaScorer:
    """Scores drafts for karma probability"""

    def __init__(self):
        self.db = get_supabase()

    async def score_all_pending_drafts(self):
        """Score all pending drafts that don't have karma scores"""
        drafts = self.db.table('drafts').select(
            '*, opportunity:opportunities(*), account:accounts(*)'
        ).eq('status', 'pending').is_('karma_probability_score', 'null').execute()

        if not drafts.data:
            print("No drafts to score")
            return

        print(f"Scoring {len(drafts.data)} drafts...")

        for draft in drafts.data:
            try:
                score = await self.score_draft(draft)
                print(f"  ✓ Draft {draft['id'][:8]}: {score:.0f}/100")
            except Exception as e:
                print(f"  ✗ Error scoring draft {draft['id']}: {e}")

    async def score_draft(self, draft: Dict) -> float:
        """Score a single draft for karma probability (0-100)"""
        opportunity = draft['opportunity']
        account = draft['account']

        score = 0.0

        # 1. Length factor (optimal length varies, but extremely short/long is bad)
        word_count = len(draft['draft_text'].split())

        if 30 <= word_count <= 150:  # Sweet spot
            score += 20
        elif 15 <= word_count <= 250:  # Acceptable
            score += 15
        elif 5 <= word_count <= 300:  # Okay
            score += 10
        else:  # Too short or too long
            score += 5

        # 2. Timing factor (is this opportunity still fresh?)
        hours_since_discovery = (
            time.time() - self.parse_timestamp(opportunity['discovered_at'])
        ) / 3600

        if hours_since_discovery < 2:
            score += 25
        elif hours_since_discovery < 4:
            score += 20
        elif hours_since_discovery < 8:
            score += 15
        elif hours_since_discovery < 12:
            score += 10
        else:
            score += 5

        # 3. Opportunity quality score
        opp_score = opportunity.get('karma_opportunity_score', 50)
        score += (opp_score / 100) * 20  # Weight: 20% of total

        # 4. Historical performance in this subreddit
        history_score = await self.get_historical_performance(
            account['id'],
            opportunity['subreddit']
        )
        score += history_score * 0.15  # Weight: 15%

        # 5. Engagement quality heuristics
        engagement_score = self.score_engagement_quality(draft['draft_text'])
        score += engagement_score * 0.20  # Weight: 20%

        # Update draft with score
        final_score = min(score, 100)
        self.db.table('drafts').update({
            'karma_probability_score': final_score
        }).eq('id', draft['id']).execute()

        return final_score

    async def get_historical_performance(
        self,
        account_id: str,
        subreddit: str
    ) -> float:
        """Get historical performance score for account in subreddit (0-100)"""
        # Get posted content in this subreddit
        result = self.db.table('posted_content').select(
            'current_karma'
        ).eq(
            'account_id', account_id
        ).eq(
            'subreddit', subreddit
        ).execute()

        if not result.data or len(result.data) == 0:
            return 50  # Neutral if no history

        # Calculate average karma
        total_karma = sum(c['current_karma'] for c in result.data)
        avg_karma = total_karma / len(result.data)

        # Convert to 0-100 score
        if avg_karma >= 50:
            return 100
        elif avg_karma >= 20:
            return 80
        elif avg_karma >= 10:
            return 60
        elif avg_karma >= 5:
            return 40
        elif avg_karma >= 2:
            return 30
        else:
            return 20

    def score_engagement_quality(self, text: str) -> float:
        """Heuristic scoring for engagement potential (0-100)"""
        score = 0.0
        text_lower = text.lower()

        # Positive indicators

        # Has questions (encourages replies)
        if '?' in text:
            score += 15

        # Has empathy markers
        empathy_words = [
            'sorry', 'understand', 'feel', 'difficult', 'challenging',
            'strength', 'support', 'here for you', 'relate', 'struggle'
        ]
        empathy_count = sum(1 for word in empathy_words if word in text_lower)
        score += min(empathy_count * 5, 20)

        # Has specific examples (not generic)
        specificity_markers = [
            'when i', 'my ', 'last ', 'similar situation', 'i had',
            'i tried', 'in my experience', 'i found', 'worked for me'
        ]
        specificity_count = sum(1 for marker in specificity_markers if marker in text_lower)
        score += min(specificity_count * 8, 25)

        # Has actionable advice
        advice_markers = [
            'try', 'recommend', 'suggest', 'help', 'might', 'could',
            'consider', 'check out'
        ]
        advice_count = sum(1 for marker in advice_markers if marker in text_lower)
        score += min(advice_count * 5, 15)

        # Negative indicators

        # Too sales-y or promotional
        spam_markers = [
            'link in bio', 'dm me', 'click here', 'buy now',
            'check out my', 'subscribe', 'follow me'
        ]
        if any(marker in text_lower for marker in spam_markers):
            score -= 30

        # Too generic
        generic_phrases = [
            'as an ai', 'i am a language model', 'i cannot', 'i do not have'
        ]
        if any(phrase in text_lower for phrase in generic_phrases):
            score -= 50  # Major penalty - this should never happen

        # All caps (shouting)
        if text.isupper() and len(text) > 10:
            score -= 20

        return max(min(score, 100), 0)

    def parse_timestamp(self, timestamp_str: str) -> float:
        """Parse ISO timestamp to Unix timestamp"""
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.timestamp()
        except:
            return time.time()


# Lazy-load global instance
_karma_scorer_instance = None

def get_karma_scorer() -> 'KarmaScorer':
    """Get KarmaScorer instance (lazy-loaded)"""
    global _karma_scorer_instance
    if _karma_scorer_instance is None:
        _karma_scorer_instance = KarmaScorer()
    return _karma_scorer_instance
