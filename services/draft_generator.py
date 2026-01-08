from datetime import datetime, timezone
from typing import List, Dict
from config.supabase_client import get_supabase
from services.personality_engine import get_personality_engine
from utils.llm_client import get_llm_client


class DraftGenerator:
    """Generates Reddit comment drafts using LLM"""

    def __init__(self):
        self.db = get_supabase()

    async def generate_drafts_for_all_accounts(self, max_opportunities_per_account: int = 5):
        """Generate drafts for top opportunities across all active accounts"""
        # Get all active accounts
        result = self.db.table('accounts').select('*').eq('active', True).execute()
        accounts = result.data

        print(f"Generating drafts for {len(accounts)} active accounts...")

        for account in accounts:
            try:
                await self.generate_drafts_for_account(
                    account,
                    max_opportunities=max_opportunities_per_account
                )
            except Exception as e:
                print(f"Error generating drafts for {account['reddit_username']}: {e}")

    async def generate_drafts_for_account(
        self,
        account: dict,
        max_opportunities: int = 5,
        num_variants: int = 2
    ):
        """Generate drafts for top opportunities for a single account"""
        print(f"Generating drafts for u/{account['reddit_username']}...")

        # Load personality
        personality = await get_personality_engine().load_personality(
            account['personality_json_url'],
            account['id']
        )

        if not personality:
            print(f"  ✗ Could not load personality")
            return

        # Get top opportunities (not yet drafted)
        opportunities = self.db.table('opportunities').select('*').eq(
            'account_id', account['id']
        ).eq(
            'status', 'new'
        ).order(
            'karma_opportunity_score', desc=True
        ).limit(max_opportunities).execute()

        if not opportunities.data:
            print(f"  → No new opportunities to draft")
            return

        drafts_created = 0

        for opp in opportunities.data:
            try:
                # Mark as drafting
                self.db.table('opportunities').update({
                    'status': 'drafting'
                }).eq('id', opp['id']).execute()

                # Generate variants
                variants = await self.generate_variants(
                    opportunity=opp,
                    personality=personality,
                    num_variants=num_variants
                )

                # Save drafts
                for i, draft_text in enumerate(variants):
                    self.db.table('drafts').insert({
                        'account_id': account['id'],
                        'opportunity_id': opp['id'],
                        'draft_text': draft_text,
                        'draft_type': 'comment',
                        'variant_number': i + 1,
                        'generated_at': datetime.now(timezone.utc).isoformat(),
                        'status': 'pending'
                    }).execute()

                    drafts_created += 1

                # Mark opportunity as drafted
                self.db.table('opportunities').update({
                    'status': 'drafted'
                }).eq('id', opp['id']).execute()

                print(f"  ✓ Generated {num_variants} drafts for: {opp['post_title'][:60]}...")

            except Exception as e:
                print(f"  ✗ Error generating draft for opportunity {opp['id']}: {e}")
                # Reset status
                self.db.table('opportunities').update({
                    'status': 'new'
                }).eq('id', opp['id']).execute()

        print(f"  → Created {drafts_created} drafts total")

    async def generate_variants(
        self,
        opportunity: Dict,
        personality,
        num_variants: int = 2
    ) -> List[str]:
        """Generate multiple draft variants for an opportunity"""
        # Build prompts
        system_prompt = get_personality_engine().build_system_prompt(personality)
        user_prompt = get_personality_engine().build_user_prompt(opportunity, personality)

        variants = []

        for i in range(num_variants):
            try:
                # Add variant instruction
                if i == 0:
                    variant_instruction = "\n\n[Generate your most natural, authentic response]"
                elif i == 1:
                    variant_instruction = "\n\n[Generate an alternative version - slightly different angle or emphasis, but same authentic voice]"
                else:
                    variant_instruction = f"\n\n[Generate variant #{i+1} - another authentic take]"

                # Generate draft
                draft_text = await get_llm_client().generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt + variant_instruction,
                    temperature=0.9,  # Higher temperature for variety
                    max_tokens=500
                )

                # Clean up draft
                draft_text = draft_text.strip()

                # Remove any meta-commentary if present
                if draft_text.startswith("Here's"):
                    lines = draft_text.split('\n')
                    draft_text = '\n'.join(lines[1:]).strip()

                variants.append(draft_text)

            except Exception as e:
                print(f"    ✗ Error generating variant {i+1}: {e}")
                # Add fallback
                variants.append(f"[Error generating draft: {str(e)}]")

        return variants

    async def regenerate_draft(
        self,
        draft_id: str,
        custom_instructions: str = None
    ) -> str:
        """Regenerate a single draft with optional custom instructions"""
        # Get draft and related data
        draft_result = self.db.table('drafts').select(
            '*, opportunity:opportunities(*), account:accounts(*)'
        ).eq('id', draft_id).execute()

        if not draft_result.data:
            raise ValueError(f"Draft {draft_id} not found")

        draft = draft_result.data[0]
        account = draft['account']
        opportunity = draft['opportunity']

        # Load personality
        personality = await get_personality_engine().load_personality(
            account['personality_json_url'],
            account['id']
        )

        # Build prompts
        system_prompt = get_personality_engine().build_system_prompt(personality)
        user_prompt = get_personality_engine().build_user_prompt(opportunity, personality)

        # Add custom instructions if provided
        if custom_instructions:
            user_prompt += f"\n\nADDITIONAL INSTRUCTIONS: {custom_instructions}"

        # Generate new draft
        new_draft_text = await get_llm_client().generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.9,
            max_tokens=500
        )

        new_draft_text = new_draft_text.strip()

        # Update draft
        self.db.table('drafts').update({
            'draft_text': new_draft_text,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'user_notes': custom_instructions
        }).eq('id', draft_id).execute()

        return new_draft_text


# Lazy-load global instance
_draft_generator_instance = None

def get_draft_generator() -> 'DraftGenerator':
    """Get DraftGenerator instance (lazy-loaded)"""
    global _draft_generator_instance
    if _draft_generator_instance is None:
        _draft_generator_instance = DraftGenerator()
    return _draft_generator_instance
