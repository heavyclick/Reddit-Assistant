from slack_sdk.webhook import WebhookClient
from typing import List, Dict
from config.settings import settings


class SlackClient:
    """Slack notification client using webhooks"""

    def __init__(self):
        self.webhook_url = settings.SLACK_WEBHOOK_URL
        self.channel = settings.SLACK_CHANNEL
        self.dashboard_url = settings.DASHBOARD_URL
        self.client = WebhookClient(self.webhook_url)

    async def send_draft_notification(self, account: Dict, drafts: List[Dict]):
        """Send Slack notification with pending drafts for approval"""

        if not drafts:
            return

        # Build blocks for each draft
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎯 {len(drafts)} Reddit Draft{'s' if len(drafts) > 1 else ''} Ready for Approval",
                    "emoji": True
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Account: *u/{account.get('reddit_username', 'unknown')}* | ⏱️ Auto-approves in {settings.AUTO_APPROVE_TIMEOUT_MINUTES} minute{'s' if settings.AUTO_APPROVE_TIMEOUT_MINUTES > 1 else ''}"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]

        # Add each draft
        for i, draft in enumerate(drafts[:5], 1):  # Limit to 5 to avoid message size limits
            opp = draft.get('opportunity', {})
            karma_score = draft.get('karma_probability_score', 0)

            # Draft section
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{i}. r/{opp.get('subreddit', 'unknown')}* | Karma Score: {karma_score:.0f}/100\n_{opp.get('post_title', 'No title')[:100]}_"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{draft.get('draft_text', '')[:300]}{'...' if len(draft.get('draft_text', '')) > 300 else ''}```"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✓ Approve",
                                "emoji": True
                            },
                            "style": "primary",
                            "url": f"{self.dashboard_url}/approve/{draft.get('id', '')}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✏️ Edit",
                                "emoji": True
                            },
                            "url": f"{self.dashboard_url}/edit/{draft.get('id', '')}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✗ Reject",
                                "emoji": True
                            },
                            "style": "danger",
                            "url": f"{self.dashboard_url}/reject/{draft.get('id', '')}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔗 View Post",
                                "emoji": True
                            },
                            "url": opp.get('reddit_permalink', '#')
                        }
                    ]
                },
                {
                    "type": "divider"
                }
            ])

        # Add footer with dashboard link
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"<{self.dashboard_url}|Open Dashboard> | If no action taken in {settings.AUTO_APPROVE_TIMEOUT_MINUTES} minute(s), drafts will auto-approve"
                }
            ]
        })

        # Send message
        try:
            response = self.client.send(
                text=f"🎯 {len(drafts)} Reddit draft(s) ready for u/{account.get('reddit_username')}",
                blocks=blocks
            )

            if response.status_code == 200:
                print(f"✓ Sent Slack notification for {len(drafts)} drafts")
            else:
                print(f"✗ Slack notification failed: {response.status_code}")

        except Exception as e:
            print(f"✗ Failed to send Slack notification: {e}")

    async def send_post_confirmation(self, account: Dict, posted_content: Dict):
        """Send confirmation notification after posting"""
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Comment Posted Successfully",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*u/{account.get('reddit_username')}* posted to *r/{posted_content.get('subreddit', 'unknown')}*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{posted_content.get('final_text', '')[:400]}{'...' if len(posted_content.get('final_text', '')) > 400 else ''}```"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View on Reddit",
                                "emoji": True
                            },
                            "url": posted_content.get('reddit_permalink', '#')
                        }
                    ]
                }
            ]

            self.client.send(
                text=f"✅ Comment posted by u/{account.get('reddit_username')}",
                blocks=blocks
            )

        except Exception as e:
            print(f"✗ Failed to send confirmation: {e}")

    async def send_error_notification(self, message: str, details: Dict = None):
        """Send error notification"""
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⚠️ Reddit Assistant Error",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{message}*"
                    }
                }
            ]

            if details:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{str(details)[:500]}```"
                    }
                })

            self.client.send(
                text=f"⚠️ Error: {message}",
                blocks=blocks
            )

        except Exception as e:
            print(f"✗ Failed to send error notification: {e}")


# Lazy-load global instance
_slack_client_instance = None

def get_slack_client() -> 'SlackClient':
    """Get SlackClient instance (lazy-loaded)"""
    global _slack_client_instance
    if _slack_client_instance is None:
        _slack_client_instance = SlackClient()
    return _slack_client_instance
