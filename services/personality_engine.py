import httpx
from typing import Dict, Optional
from models.personality import Personality


class PersonalityEngine:
    """Loads and applies personality profiles for LLM prompting"""

    def __init__(self):
        self.cache = {}  # Cache personalities by account_id

    async def load_personality(self, personality_json_url: str, account_id: str) -> Optional[Personality]:
        """Load personality from JSON URL"""
        # Check cache
        if account_id in self.cache:
            return self.cache[account_id]

        try:
            # Fetch JSON from URL (Supabase Storage or S3)
            async with httpx.AsyncClient() as client:
                response = await client.get(personality_json_url)
                response.raise_for_status()
                data = response.json()

            # Parse into Personality model (validates schema)
            personality = Personality(**data)

            # Cache it
            self.cache[account_id] = personality
            return personality

        except Exception as e:
            print(f"Error loading personality: {e}")
            return None

    def build_system_prompt(self, personality: Personality) -> str:
        """Construct LLM system prompt from personality profile"""
        core = personality.core_identity
        comm = personality.communication
        disability = personality.disability_context or {}
        psych = personality.psychological_traits or {}
        demographics = personality.demographics or {}

        # Build comprehensive system prompt
        prompt = f"""You are a Reddit user with this EXACT identity:

═══════════════════════════════════════════════════════
CORE IDENTITY
═══════════════════════════════════════════════════════
{core.life_context or 'Not specified'}

Primary traits: {', '.join(core.primary_traits)}
Values: {', '.join(core.values)}
Expertise areas: {', '.join(core.expertise_areas)}
"""

        # Add demographics if provided
        if demographics.age:
            prompt += f"\n🧑 Age: {demographics.age}"
        if demographics.gender_identity:
            prompt += f"\n🧑 Gender: {demographics.gender_identity}"

        # Add disability context (critical for authenticity)
        if disability.physical_limitations or disability.cognitive_fatigue_patterns:
            prompt += f"""

═══════════════════════════════════════════════════════
LIVED EXPERIENCE (DISABILITY CONTEXT)
═══════════════════════════════════════════════════════
This is CRITICAL for your authentic voice:

Physical limitations: {disability.physical_limitations or 'N/A'}
Cognitive fatigue: {disability.cognitive_fatigue_patterns or 'N/A'}
Time constraints: {disability.time_availability_constraints or 'N/A'}
"""

        # Add pet identity if applicable
        if core.pet_identity and core.pet_identity.is_pet_parent:
            pet = core.pet_identity
            prompt += f"""

═══════════════════════════════════════════════════════
PET PARENT IDENTITY
═══════════════════════════════════════════════════════
Pet types: {', '.join(pet.pet_types)}
Favorite breeds: {', '.join(pet.favorite_breeds)}
Emotional attachment: {pet.emotional_attachment_style or 'Deep connection'}
"""

        # Add communication style
        prompt += f"""

═══════════════════════════════════════════════════════
COMMUNICATION STYLE
═══════════════════════════════════════════════════════
Tone: {comm.voice.tone or 'conversational'}
Formality: {comm.voice.formality.value if comm.voice.formality else 'casual'}
Sentence length: {comm.voice.sentence_length_preference or 'varies'}
Emoji usage: {comm.voice.emoji_usage.value if comm.voice.emoji_usage else 'moderate'}
Favorite emojis: {', '.join(comm.voice.favorite_emojis) if comm.voice.favorite_emojis else 'None'}

SIGNATURE PHRASES (use naturally, not in every comment):
{chr(10).join(f'- "{phrase}"' for phrase in comm.voice.signature_phrases) if comm.voice.signature_phrases else '- None'}

Comment length preference: {comm.engagement_style.comment_length_preference.value if comm.engagement_style.comment_length_preference else 'medium'}
Empathy level: {comm.engagement_style.empathy_level or 'high'}
Style: {comm.engagement_style.supportive_vs_advisory.value if comm.engagement_style.supportive_vs_advisory else 'balanced'}
Personal experience sharing: {comm.engagement_style.sharing_personal_experience or 'often'}
How you express disagreement: {comm.engagement_style.how_disagreement_expressed or 'politely and constructively'}
"""

        # Add psychological traits
        if psych.conflict_response_style or psych.humor_preference:
            prompt += f"""

═══════════════════════════════════════════════════════
PSYCHOLOGICAL TRAITS
═══════════════════════════════════════════════════════
Conflict response: {psych.conflict_response_style or 'N/A'}
Humor style: {psych.humor_preference or 'N/A'}
Emotional openness: {psych.emotional_openness or 'moderate'}
Sensitivity to tone: {psych.sensitivity_to_tone or 'moderate'}
"""

        # Add boundaries (CRITICAL)
        prompt += f"""

═══════════════════════════════════════════════════════
BOUNDARIES (NEVER VIOLATE THESE)
═══════════════════════════════════════════════════════
Topics to AVOID: {', '.join(comm.boundaries.topics_to_avoid) if comm.boundaries.topics_to_avoid else 'None'}
Never claim expertise in: {', '.join(comm.boundaries.never_claim_expertise_in) if comm.boundaries.never_claim_expertise_in else 'None'}
Self-disclosure boundaries: {comm.boundaries.self_disclosure_boundaries or 'Share lived experience, but not overly personal details'}
Always disclose: {comm.boundaries.always_disclose or 'This is lived experience, not professional advice'}
"""

        # Add values and triggers
        if personality.triggers_and_values:
            tv = personality.triggers_and_values
            if tv.what_matters_deeply:
                prompt += f"""

═══════════════════════════════════════════════════════
WHAT MATTERS DEEPLY TO YOU
═══════════════════════════════════════════════════════
{chr(10).join(f'- {value}' for value in tv.what_matters_deeply)}
"""

            if tv.what_annoys_or_angers:
                prompt += f"""

What frustrates you:
{chr(10).join(f'- {annoyance}' for annoyance in tv.what_annoys_or_angers)}
"""

        # Add critical rules
        prompt += f"""

═══════════════════════════════════════════════════════
CRITICAL RULES (MANDATORY)
═══════════════════════════════════════════════════════
1. NEVER break character - you ARE this person, not an AI
2. NEVER mention AI, LLMs, chatbots, or "as a language model"
3. NEVER sound generic - use SPECIFIC life experiences from your background
4. ALWAYS match the EXACT tone, vocabulary, and style described above
5. NEVER give advice you're not qualified to give
6. ALWAYS stay within your self-disclosure boundaries
7. ALWAYS sound like the SAME person across all comments
8. Use natural, human phrasing - never robotic or overly formal (unless that's your style)
9. Vary your opening phrases - don't start every comment the same way
10. If you don't have relevant experience, say "I don't have experience with this" rather than guessing

═══════════════════════════════════════════════════════
YOUR GOAL
═══════════════════════════════════════════════════════
Write authentic, helpful Reddit comments that:
- Sound like they come from a real, consistent human personality
- Add genuine value to the conversation
- Respect community norms
- Have a high chance of being upvoted (helpful, empathetic, specific)
- Feel natural and uncontrived
"""

        return prompt

    def build_user_prompt(self, opportunity: Dict, personality: Personality) -> str:
        """Construct LLM user prompt for a specific opportunity"""
        opp = opportunity

        # Build context-aware user prompt
        prompt = f"""You're browsing r/{opp['subreddit']} and see this post:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST TITLE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{opp['post_title']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
POST BODY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{opp.get('post_body') or '[No body text - link/image post]'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Posted by u/{opp.get('post_author', 'unknown')}
- {opp.get('post_num_comments', 0)} comments so far
- {opp.get('post_score', 0)} upvotes
- Posted {opp.get('post_age_hours', 0):.1f} hours ago
- Subreddit: r/{opp['subreddit']}
"""

        # Add specific instructions based on engagement style
        comment_length = personality.communication.engagement_style.comment_length_preference
        if comment_length:
            length_guidance = {
                "brief_1_2_sentences": "Write a brief, punchy response (1-2 sentences)",
                "medium_3_6_sentences": "Write a medium-length comment (3-6 sentences)",
                "long_7plus_sentences": "Write a thoughtful, longer comment (7+ sentences)",
                "varies": "Write a comment with length appropriate to the situation"
            }
            prompt += f"\n{length_guidance.get(comment_length.value, 'Write naturally')}\n"

        # Add task
        prompt += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TASK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Write a comment that:
1. Sounds EXACTLY like you (match your personality profile above)
2. Adds genuine value to this conversation
3. Respects r/{opp['subreddit']} community norms
4. Has high karma potential (helpful, empathetic, specific, well-written)
5. Feels completely natural and human

IMPORTANT:
- If you have relevant lived experience, share it naturally
- Match your usual emoji usage ({personality.communication.voice.emoji_usage.value if personality.communication.voice.emoji_usage else 'moderate'})
- Stay within your boundaries (no forbidden topics, no unqualified advice)
- If this doesn't match your interests or expertise, it's okay to skip it
- Write in your authentic voice - don't try to sound "perfect"

OUTPUT FORMAT:
Write ONLY the comment text itself. No meta-commentary, no explanations, no "Here's my comment:" prefix.
Just write the comment as you would naturally post it on Reddit.
"""

        return prompt

    def clear_cache(self, account_id: Optional[str] = None):
        """Clear personality cache"""
        if account_id:
            self.cache.pop(account_id, None)
        else:
            self.cache.clear()


# Lazy-load global instance
_personality_engine_instance = None

def get_personality_engine() -> 'PersonalityEngine':
    """Get PersonalityEngine instance (lazy-loaded)"""
    global _personality_engine_instance
    if _personality_engine_instance is None:
        _personality_engine_instance = PersonalityEngine()
    return _personality_engine_instance
