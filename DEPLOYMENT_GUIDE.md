# DEPLOYMENT GUIDE - Reddit Assistant

You need **2 separate deployments**:
1. **Backend** (Python FastAPI) → Railway
2. **Frontend** (Next.js) → Vercel (recommended) or Railway

---

## BACKEND DEPLOYMENT (Railway)

### Step 1: Create Backend Railway Project

1. Go to: https://railway.app/new
2. Click **"Deploy from GitHub repo"**
3. Select: `heavyclick/Reddit-Assistant`
4. Railway will try to deploy everything - **we need to fix this**

### Step 2: Configure Root Directory for Backend

Railway needs to know to deploy only the backend, not the frontend.

**Option A: Using Railway Dashboard**

1. In Railway project settings → **"Settings"** tab
2. Scroll to **"Root Directory"**
3. Leave it as `/` (root)
4. In **"Build Command"**, set: `pip install -r requirements.txt`
5. In **"Start Command"**, set: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Option B: Create railway.toml** (Better)

I'll create this file for you.

### Step 3: Add Environment Variables

In Railway dashboard → **"Variables"** tab, add:

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_ANON_KEY=your_anon_key

# LLM
GOOGLE_API_KEY=AIzaSy...
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.0-flash-exp
LLM_TEMPERATURE=0.9
LLM_MAX_TOKENS=500

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#reddit-assistant

# Dashboard
DASHBOARD_URL=https://your-frontend-url.vercel.app

# System
ENVIRONMENT=production
MAX_ACCOUNTS=6
DEFAULT_TIMEZONE=America/New_York
LOG_LEVEL=INFO
AUTO_APPROVE_TIMEOUT_MINUTES=1

# Rate Limiting
MAX_COMMENTS_PER_DAY_DEFAULT=5
MAX_POSTS_PER_WEEK_DEFAULT=2
MIN_HOURS_BETWEEN_COMMENTS=2
REDDIT_API_REQUESTS_PER_MINUTE=60

# Cron Schedules
MONITOR_CRON_SCHEDULE=*/30 * * * *
DRAFT_CRON_SCHEDULE=*/45 * * * *
POST_CRON_SCHEDULE=*/15 * * * *
TRACK_CRON_SCHEDULE=0 */6 * * *
```

### Step 4: Setup Cron Jobs (IMPORTANT)

Railway doesn't support cron jobs in `railway.json` anymore. You need to use **Railway's Cron Triggers**.

**Option 1: Use Railway Cron Service (Recommended)**

1. In Railway dashboard, add a **new service** to your project
2. Name it: `cron-jobs`
3. Deploy from same GitHub repo
4. Set Root Directory: `/`
5. Build Command: `pip install -r requirements.txt`
6. Start Command: (leave empty, we'll trigger via webhooks)

**Option 2: Use External Cron (easier)**

Use **cron-job.org** or **EasyCron** to hit your Railway endpoints every X minutes:

- `POST https://your-backend.railway.app/jobs/monitor` (every 30 min)
- `POST https://your-backend.railway.app/jobs/generate-drafts` (every 45 min)
- `POST https://your-backend.railway.app/jobs/post-approved` (every 15 min)
- `POST https://your-backend.railway.app/jobs/track-performance` (every 6 hours)

### Step 5: Deploy

Click **"Deploy"** in Railway. The backend should now work.

---

## FRONTEND DEPLOYMENT (Vercel - Recommended)

### Why Vercel?
- Free tier
- Automatic Next.js optimization
- Easy GitHub integration
- No configuration needed

### Step 1: Deploy to Vercel

1. Go to: https://vercel.com/new
2. Import your GitHub repo: `heavyclick/Reddit-Assistant`
3. Vercel will auto-detect Next.js

### Step 2: Configure Root Directory

Since frontend is in a subdirectory:

1. **Root Directory**: Set to `frontend`
2. **Framework Preset**: Next.js (auto-detected)
3. **Build Command**: `npm run build` (auto-filled)
4. **Output Directory**: `.next` (auto-filled)

### Step 3: Add Environment Variables

In Vercel dashboard → **"Settings"** → **"Environment Variables"**:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### Step 4: Deploy

Click **"Deploy"**. Your frontend will be live at `https://your-project.vercel.app`

### Step 5: Update Backend

Go back to Railway and update `DASHBOARD_URL`:
```bash
DASHBOARD_URL=https://your-project.vercel.app
```

---

## ALTERNATIVE: Frontend on Railway (Not Recommended)

If you insist on using Railway for frontend:

### Create Separate Frontend Project

1. Create a **new Railway project**
2. Deploy from same GitHub repo
3. Set **Root Directory**: `frontend`
4. **Build Command**: `npm install && npm run build`
5. **Start Command**: `npm start`
6. Add environment variables (same as Vercel above)

---

## TROUBLESHOOTING

### Error: "pip install failed"

**Problem**: Railway is trying to install Python deps from root, but also seeing frontend.

**Solution**: Use `railway.toml` (I'll create below) or set Root Directory properly.

### Error: "Module not found"

**Problem**: Python can't find modules.

**Solution**: Make sure Railway is in the root directory (`/`), not in a subdirectory.

### Error: "Port binding failed"

**Problem**: FastAPI not listening on correct port.

**Solution**: Start command must use `$PORT` env variable:
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Cron Jobs Not Running

**Problem**: Railway removed support for `railway.json` cron config.

**Solution**:
- Use external cron service (cron-job.org) to hit your endpoints
- OR manually trigger via API endpoints
- OR use Railway's scheduled tasks (if available in your plan)

---

## TESTING DEPLOYMENT

### Test Backend

```bash
# Health check
curl https://your-backend.railway.app/

# List accounts
curl https://your-backend.railway.app/accounts

# Trigger job manually
curl -X POST https://your-backend.railway.app/jobs/monitor
```

### Test Frontend

Visit: `https://your-frontend.vercel.app`

Should see dashboard with:
- Account overview
- Add account button
- Stats cards

---

## COST ESTIMATE

| Service | Usage | Cost |
|---------|-------|------|
| Railway (Backend) | Hobby plan | $5/month + usage (~$10 total) |
| Vercel (Frontend) | Hobby plan | Free |
| Supabase | Free tier | Free |
| Gemini API | ~10k requests/month | $10-20/month |
| Slack | Webhooks | Free |
| **Total** | | **~$20-30/month** |

---

## FINAL CHECKLIST

### Backend (Railway)
- [ ] Environment variables added
- [ ] Root directory set to `/`
- [ ] Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Deployment successful
- [ ] API accessible at `https://your-backend.railway.app/docs`

### Frontend (Vercel)
- [ ] Root directory set to `frontend`
- [ ] Environment variables added
- [ ] `NEXT_PUBLIC_API_URL` points to Railway backend
- [ ] Deployment successful
- [ ] Dashboard accessible

### Database (Supabase)
- [ ] SQL schema executed (`database/schema.sql`)
- [ ] All 8 tables created
- [ ] Storage bucket `personalities` created

### Slack
- [ ] Incoming webhook created
- [ ] Webhook URL added to Railway env vars
- [ ] Test notification sent successfully

### Cron Jobs
- [ ] External cron service configured (cron-job.org)
- [ ] OR manual job triggering working
- [ ] Jobs running on schedule

---

## NEXT STEPS AFTER DEPLOYMENT

1. **Add your first account** via dashboard at `https://your-frontend.vercel.app/accounts/new`
2. **Upload personality JSON** to Supabase Storage
3. **Trigger monitoring** manually: `POST /jobs/monitor`
4. **Wait for drafts** to be generated
5. **Check Slack** for approval notifications
6. **Test auto-approve** by waiting 1 minute

---

## SUPPORT

If deployment fails:
1. Check Railway logs: Dashboard → Deployments → View Logs
2. Check Vercel logs: Dashboard → Deployments → View Function Logs
3. Verify environment variables are set correctly
4. Test API endpoints manually with curl/Postman

**Common Issues:**
- Missing environment variables
- Wrong root directory
- Port not set correctly
- Frontend can't reach backend (CORS issue)
