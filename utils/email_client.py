import resend
from typing import List, Dict, Optional
from config.settings import settings


class EmailClient:
    """Email notification client using Resend"""

    _api_initialized = False

    def __init__(self):
        # Initialize API key on first instantiation (lazy)
        if not EmailClient._api_initialized:
            resend.api_key = getattr(settings, 'RESEND_API_KEY', None)
            EmailClient._api_initialized = True

        self.from_email = "Reddit Assistant <noreply@yourdomain.com>"
        self.to_email = getattr(settings, 'NOTIFICATION_EMAIL', None)
        self.dashboard_url = settings.DASHBOARD_URL

    async def send_draft_approval_email(self, account: Dict, drafts: List[Dict]):
        """Send email with pending drafts for approval"""

        if not drafts:
            return

        # Build HTML for each draft
        draft_html = ""
        for draft in drafts:
            opp = draft.get('opportunity', {})

            draft_html += f"""
            <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; background: white;">
                <div style="margin-bottom: 12px;">
                    <strong style="color: #2563eb;">r/{opp.get('subreddit', 'unknown')}</strong>
                    <span style="color: #6b7280; font-size: 14px; margin-left: 8px;">
                        Karma Probability: {draft.get('karma_probability_score', 0):.0f}/100
                    </span>
                </div>

                <div style="background: #f9fafb; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
                    <p style="font-weight: 600; margin: 0 0 8px 0;">{opp.get('post_title', 'No title')}</p>
                    <p style="font-size: 14px; color: #4b5563; margin: 0 0 8px 0;">
                        {(opp.get('post_body', '') or '')[:200]}{'...' if len(opp.get('post_body', '') or '') > 200 else ''}
                    </p>
                    <a href="{opp.get('reddit_permalink', '#')}"
                       style="color: #3b82f6; font-size: 14px; text-decoration: none;">
                        View on Reddit →
                    </a>
                </div>

                <div style="background: white; border: 1px solid #d1d5db; padding: 12px; border-radius: 4px; margin-bottom: 12px;">
                    <strong style="color: #374151;">Proposed Comment:</strong>
                    <p style="margin: 8px 0 0 0; line-height: 1.6; white-space: pre-wrap;">{draft.get('draft_text', '')}</p>
                </div>

                <div style="display: flex; gap: 12px;">
                    <a href="{self.dashboard_url}/approve/{draft.get('id', '')}"
                       style="background: #10b981; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: 500;">
                        ✓ Approve
                    </a>
                    <a href="{self.dashboard_url}/reject/{draft.get('id', '')}"
                       style="background: #ef4444; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: 500;">
                        ✗ Reject
                    </a>
                    <a href="{self.dashboard_url}/edit/{draft.get('id', '')}"
                       style="background: #6b7280; color: white; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-weight: 500;">
                        ✏️ Edit
                    </a>
                </div>
            </div>
            """

        # Send email
        try:
            resend.Emails.send({
                "from": self.from_email,
                "to": self.to_email,
                "subject": f"🎯 {len(drafts)} Reddit draft{'s' if len(drafts) > 1 else ''} ready for approval (u/{account.get('reddit_username', 'unknown')})",
                "html": f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f9fafb;">
                    <div style="background: white; border-radius: 8px; padding: 24px; margin-bottom: 16px;">
                        <h1 style="color: #1f2937; margin: 0 0 8px 0; font-size: 24px;">Reddit Draft Approval</h1>
                        <p style="color: #6b7280; margin: 0;">
                            You have <strong style="color: #1f2937;">{len(drafts)} new draft{'s' if len(drafts) > 1 else ''}</strong> ready for review for account <strong style="color: #2563eb;">u/{account.get('reddit_username', 'unknown')}</strong>.
                        </p>
                    </div>

                    {draft_html}

                    <div style="background: white; border-radius: 8px; padding: 16px; text-align: center;">
                        <p style="margin: 0; color: #6b7280; font-size: 14px;">
                            You can also review all drafts in the dashboard:
                        </p>
                        <a href="{self.dashboard_url}"
                           style="display: inline-block; margin-top: 12px; background: #2563eb; color: white; padding: 10px 20px; border-radius: 4px; text-decoration: none; font-weight: 500;">
                            Open Dashboard
                        </a>
                    </div>

                    <div style="margin-top: 24px; text-align: center; color: #9ca3af; font-size: 12px;">
                        <p>Reddit Assistant - Accessibility-First Engagement Tool</p>
                    </div>
                </body>
                </html>
                """
            })
            print(f"✓ Sent approval email for {len(drafts)} drafts")

        except Exception as e:
            print(f"✗ Failed to send email: {e}")

    async def send_post_confirmation(self, account: Dict, posted_content: Dict):
        """Send confirmation email after posting"""
        try:
            resend.Emails.send({
                "from": self.from_email,
                "to": self.to_email,
                "subject": f"✓ Comment posted successfully (u/{account.get('reddit_username', 'unknown')})",
                "html": f"""
                <!DOCTYPE html>
                <html>
                <body style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Comment Posted Successfully</h2>
                    <p>Your comment has been posted to <strong>r/{posted_content.get('subreddit', 'unknown')}</strong>.</p>

                    <div style="background: #f9fafb; padding: 16px; border-radius: 4px; margin: 16px 0;">
                        <p style="margin: 0; white-space: pre-wrap;">{posted_content.get('final_text', '')}</p>
                    </div>

                    <a href="{posted_content.get('reddit_permalink', '#')}"
                       style="background: #2563eb; color: white; padding: 10px 20px; border-radius: 4px; text-decoration: none; display: inline-block;">
                        View on Reddit
                    </a>
                </body>
                </html>
                """
            })

        except Exception as e:
            print(f"✗ Failed to send confirmation email: {e}")


# Lazy-load global instance
_email_client_instance: Optional['EmailClient'] = None


def get_email_client() -> 'EmailClient':
    """Get EmailClient instance (lazy-loaded)"""
    global _email_client_instance
    if _email_client_instance is None:
        _email_client_instance = EmailClient()
    return _email_client_instance
