# Reddit Assistant - AI-Powered Accessibility Tool

**A multi-account Reddit engagement system designed for disabled users who face cognitive, physical, or time constraints that limit their ability to participate in Reddit communities.**

---

## What This Is

This is **NOT** a bot that secretly impersonates humans.

This **IS** an accessibility tool that:
- Monitors Reddit for opportunities to engage
- Drafts thoughtful, personality-aligned comments using AI
- Scores drafts by karma probability
- **Requires human approval before posting**
- Learns from performance to improve over time

Think of it like an advanced "autocomplete" or "writing assistant" specifically designed for Reddit, preserving your authentic voice while minimizing the physical and cognitive burden of participation.

---

## Features

### Core Functionality
- **Multi-Account Support** (up to 6 accounts)
- **JSON Personality Profiles** - Each account has a detailed personality that drives authentic engagement
- **Reddit Monitoring** - Tracks selected subreddits for high-opportunity posts
- **AI Draft Generation** - Uses Google Gemini or OpenAI to create personality-aligned comments
- **Karma Probability Scoring** - Ranks drafts by likelihood of upvotes
- **Human-in-the-Loop Approval** - Dashboard + email notifications for draft review
- **Automated Posting** - Posts approved drafts with rate limiting
- **Performance Tracking** - Monitors karma over time and generates insights
- **Learning Engine** - Adapts strategy based on what works

### Compliance & Safety
- Mandatory human approval for every post
- Rate limiting (configurable per account)
- Subreddit rule respect
- Transparent audit logging
- No vote manipulation
- Accessibility-first design

---

## Architecture

```
┌─────────────────────────────────────────┐
│     Supabase (PostgreSQL + Storage)     │
│  - Accounts, opportunities, drafts      │
│  - Performance history, insights        │
│  - Personality JSON storage             │
└─────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────┐
│    Railway (Python FastAPI Backend)     │
│  - REST API endpoints                   │
│  - Cron jobs (monitor, draft, post)     │
│  - Services (monitor, generator, etc.)  │
└─────────────────────────────────────────┘
                    ↕
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Reddit API   │  │ Gemini/GPT   │  │ Resend Email │
│ (PRAW)       │  │ (LLM)        │  │ (Approvals)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Quick Start

### Prerequisites

1. **Supabase Account** (free tier works)
2. **Railway Account** (for deployment)
3. **Google Cloud Account** (for Gemini API) OR **OpenAI Account**
4. **Resend Account** (for email notifications, free tier works)
5. **Reddit Account(s)** with API credentials

### Step 1: Setup Supabase

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Go to SQL Editor and run `database/schema.sql` to create tables
3. Go to Settings → API to get your:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `SUPABASE_ANON_KEY`
4. Create a storage bucket named `personalities` (public read access)

### Step 2: Get Reddit API Credentials

For each Reddit account:

1. Go to https://www.reddit.com/prefs/apps
2. Click "create app" or "create another app"
3. Select "script" as the type
4. Fill in name and redirect URI (use `http://localhost:8000`)
5. Save the `client_id` and `client_secret`
6. Use [this guide](https://github.com/reddit-archive/reddit/wiki/OAuth2) to get a `refresh_token`

Alternatively, use PRAW to get refresh token:
```python
import praw

reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    redirect_uri="http://localhost:8000",
    user_agent="reddit_assistant_setup"
)

print(reddit.auth.url(scopes=["identity", "submit", "read"], state="...", duration="permanent"))
# Visit the URL, authorize, get the code
# Then:
refresh_token = reddit.auth.authorize(code)
print(refresh_token)
```

### Step 3: Create Personality JSON

1. Copy `examples/personality_example.json`
2. Customize it with your actual personality, disability context, interests, etc.
3. Fill in Reddit credentials at the bottom
4. Upload to Supabase Storage bucket `personalities` OR host on AWS S3
5. Get the public URL

### Step 4: Setup Environment Variables

1. Copy `.env.example` to `.env`
2. Fill in all values:

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_ANON_KEY=your_anon_key

# LLM (Gemini recommended for cost)
GOOGLE_API_KEY=AIzaSy...

# Email
RESEND_API_KEY=re_...
NOTIFICATION_EMAIL=your-email@example.com

# Dashboard URL
DASHBOARD_URL=http://localhost:3000  # Update when deployed
```

### Step 5: Install Dependencies

```bash
cd reddit-assistant
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 6: Add Your Account to Database

Run locally first to test:

```bash
uvicorn main:app --reload
```

Then use the API to create an account:

```bash
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "reddit_username": "your_username",
    "personality_json_url": "https://your-supabase-url/storage/v1/object/public/personalities/your_personality.json",
    "reddit_client_id": "YOUR_CLIENT_ID",
    "reddit_client_secret": "YOUR_CLIENT_SECRET",
    "reddit_refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### Step 7: Test the Workflow

```bash
# Test monitoring
curl -X POST http://localhost:8000/jobs/monitor

# Test draft generation
curl -X POST http://localhost:8000/jobs/generate-drafts

# Check drafts
curl http://localhost:8000/drafts?status=pending
```

### Step 8: Deploy to Railway

1. Install Railway CLI:
```bash
npm install -g @railway/cli
railway login
```

2. Initialize and deploy:
```bash
railway init
railway up
```

3. Set environment variables in Railway dashboard
4. Railway will automatically run cron jobs per `railway.json`

---

## Usage

### Workflow

1. **Monitor** (every 30 min) - System scans subreddits for opportunities
2. **Generate Drafts** (every 45 min) - AI creates comments, scores them, sends email
3. **Human Approval** - You review drafts in dashboard or email, approve/edit/reject
4. **Post** (every 15 min) - System posts approved drafts with rate limiting
5. **Track Performance** (every 6 hours) - Updates karma scores, generates insights

### Dashboard (Optional)

The system provides a REST API. You can build a frontend dashboard using:
- React + Supabase real-time subscriptions
- Or use the email interface exclusively

Example endpoints:
- `GET /accounts` - List all accounts
- `GET /drafts?status=pending` - View pending drafts
- `POST /drafts/{id}/approve` - Approve a draft
- `POST /drafts/{id}/reject` - Reject a draft
- `GET /analytics/{account_id}` - View performance

### Email-Based Approval

If you don't want to build a dashboard, the system sends emails with:
- Draft text
- Original post context
- Karma probability score
- Approve/Edit/Reject buttons

---

## Configuration

### Personality JSON

The personality JSON is the heart of the system. It controls:
- Voice and tone
- Topics of interest
- Boundaries and ethics
- Posting strategy
- Urgency level

See `examples/personality_example.json` for a complete template.

**Key sections:**
- `disability_context` - Critical for authentic voice
- `core_identity` - Who you are
- `communication` - How you write
- `boundaries` - What to never do
- `strategy` - Posting limits and priorities

### Rate Limits

Default limits (configurable per account in personality JSON):
- **5 comments per day**
- **2 posts per week**
- **2 hours minimum between comments**

The system enforces these automatically.

### Subreddit Selection

Choose subreddits where:
1. You have genuine interest and lived experience
2. Your contribution would add value
3. The community appreciates authentic engagement
4. Your karma goal can be realistically achieved

**Start with 2-3 subreddits**, expand later.

---

## API Reference

### Accounts

- `GET /accounts` - List all accounts
- `GET /accounts/{id}` - Get account details
- `POST /accounts` - Create new account
- `PATCH /accounts/{id}` - Update account
- `DELETE /accounts/{id}` - Delete account

### Opportunities

- `GET /opportunities?account_id=...&status=...` - List opportunities

### Drafts

- `GET /drafts?account_id=...&status=...` - List drafts
- `GET /drafts/{id}` - Get draft details
- `POST /drafts/{id}/approve` - Approve draft
- `POST /drafts/{id}/reject` - Reject draft
- `POST /drafts/{id}/regenerate` - Regenerate with custom instructions

### Analytics

- `GET /analytics/{account_id}?days=30` - Get performance analytics
- `GET /insights/{account_id}` - Get learning insights

### Jobs (Manual Triggers)

- `POST /jobs/monitor` - Trigger Reddit monitoring
- `POST /jobs/generate-drafts` - Trigger draft generation
- `POST /jobs/post-approved` - Trigger posting
- `POST /jobs/track-performance` - Trigger performance tracking

---

## Ethical Considerations

### Reddit Terms of Service Compliance

This tool is designed to comply with Reddit's ToS:

✅ **Human-in-the-loop required** - Every post must be explicitly approved
✅ **No vote manipulation** - System creates quality content, doesn't game votes
✅ **Rate limited** - Respects Reddit API limits and reasonable posting frequency
✅ **Authentic** - Content reflects real personality and lived experience
✅ **Transparent** - You can honestly say "I use assistive writing tools"
✅ **No spam** - Quality over quantity, targeted engagement only

### If a Moderator Asks

Recommended response:

> "I use an assistive writing tool due to my disability [chronic illness, limited mobility, etc.]. It helps me draft comments, but I review and approve every single one before posting. The tool uses my actual personality and lived experiences - I'm not pretending to be someone else. It's similar to using speech-to-text or grammar checkers, but more sophisticated. Every comment genuinely reflects my thoughts and values. Happy to discuss this further if you have concerns."

### What This System Does NOT Do

❌ Post without human approval
❌ Manipulate votes
❌ Create fake personas
❌ Engage in coordinated inauthentic behavior
❌ Spam or mass-post
❌ Circumvent bans or restrictions
❌ Impersonate other users

---

## Troubleshooting

### "Authentication failed" error

- Check Reddit API credentials
- Verify refresh token is valid
- Ensure scopes include: `identity`, `submit`, `read`

### "Personality JSON not found"

- Verify URL is publicly accessible
- Check Supabase Storage bucket permissions (public read)
- Test URL in browser directly

### No drafts being generated

- Check that opportunities are being found (`GET /opportunities`)
- Verify LLM API key is valid (Gemini or OpenAI)
- Check logs for errors

### Drafts not being posted

- Verify they're approved (`status=approved`)
- Check rate limits haven't been exceeded
- Ensure Reddit account credentials are valid

### Low karma on posted comments

- Review personality alignment - does it match your authentic voice?
- Check timing - are you engaging too late after post creation?
- Analyze learning insights (`GET /insights/{account_id}`)
- Adjust strategy in personality JSON

---

## Cost Estimate

| Service | Usage (1 account, 5 comments/day) | Monthly Cost |
|---------|-----------------------------------|--------------|
| Supabase | Free tier | $0 |
| Railway | Hobby plan + usage | $10-15 |
| Google Gemini API | ~3000 requests/month | $10-20 |
| Resend | 3000 emails/month | $0 (free tier) |
| **Total** | | **~$20-35/month** |

For 6 accounts: ~$40-60/month

---

## Advanced Configuration

### Using OpenAI Instead of Gemini

In `.env`:
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-...
```

### Custom Dashboard

Build a frontend using:
- React + Supabase JavaScript client
- Supabase real-time subscriptions for live updates
- Deploy to Vercel/Netlify

Example:
```javascript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Subscribe to draft changes
supabase
  .channel('drafts')
  .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'drafts' },
    payload => console.log('New draft:', payload))
  .subscribe()
```

### Adjusting Cron Schedules

Edit `railway.json`:
```json
"cron": [
  {
    "name": "monitor-reddit",
    "schedule": "*/15 * * * *",  // Every 15 minutes instead of 30
    "command": "python jobs/monitor_reddit.py"
  }
]
```

---

## Project Structure

```
reddit-assistant/
├── main.py                    # FastAPI app
├── requirements.txt
├── Procfile                   # Railway deployment
├── railway.json               # Cron job config
├── .env.example
├── config/
│   ├── settings.py           # Environment config
│   └── supabase_client.py    # DB connection
├── models/
│   ├── account.py            # Pydantic models
│   ├── personality.py
│   ├── opportunity.py
│   └── draft.py
├── services/
│   ├── reddit_monitor.py     # Core services
│   ├── personality_engine.py
│   ├── draft_generator.py
│   ├── karma_scorer.py
│   ├── reddit_poster.py
│   └── performance_tracker.py
├── utils/
│   ├── reddit_client.py      # API wrappers
│   ├── llm_client.py
│   ├── email_client.py
│   └── rate_limiter.py
├── jobs/
│   ├── monitor_reddit.py     # Cron job scripts
│   ├── generate_drafts.py
│   ├── post_approved.py
│   └── track_performance.py
├── database/
│   └── schema.sql            # Supabase schema
├── examples/
│   └── personality_example.json
└── schemas/
    └── personality_schema.json
```

---

## Contributing

This project is designed for accessibility. If you have suggestions for improvements, especially from the disability community, please open an issue or PR.

---

## License

MIT License - Use responsibly and ethically.

---

## Support

For issues, questions, or feature requests, open a GitHub issue.

**Remember:** This tool is designed to make Reddit accessible to people with disabilities. Use it to genuinely participate in communities you care about, not to game the system. Quality and authenticity always over quantity.
