# QUICK DEPLOY GUIDE

## 🚀 Deploy in 15 Minutes

### STEP 1: Deploy Backend to Railway (5 min)

1. **Go to**: https://railway.app/new
2. **Click**: "Deploy from GitHub repo"
3. **Select**: `heavyclick/Reddit-Assistant`
4. **Wait** for auto-detection
5. **Railway should now use** `railway.toml` config automatically
6. **Add Environment Variables**: Click "Variables" tab and add:
   ```bash
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_SERVICE_KEY=your_key
   SUPABASE_ANON_KEY=your_key
   GOOGLE_API_KEY=your_key
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   SLACK_CHANNEL=#reddit-assistant
   DASHBOARD_URL=https://will-add-after-frontend.vercel.app
   ENVIRONMENT=production
   MAX_ACCOUNTS=6
   AUTO_APPROVE_TIMEOUT_MINUTES=1
   ```
7. **Click**: "Deploy"
8. **Copy Backend URL**: e.g., `https://reddit-assistant-production.up.railway.app`

---

### STEP 2: Deploy Frontend to Vercel (5 min)

1. **Go to**: https://vercel.com/new
2. **Import**: `heavyclick/Reddit-Assistant` from GitHub
3. **Configure**:
   - **Root Directory**: `frontend` ← IMPORTANT!
   - **Framework**: Next.js (auto-detected)
4. **Add Environment Variables**:
   ```bash
   NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
   NEXT_PUBLIC_API_URL=https://reddit-assistant-production.up.railway.app
   ```
5. **Click**: "Deploy"
6. **Copy Frontend URL**: e.g., `https://reddit-assistant.vercel.app`

---

### STEP 3: Update Backend with Frontend URL (1 min)

1. **Go back to Railway**
2. **Variables** tab
3. **Update** `DASHBOARD_URL` to your Vercel URL
4. Railway will auto-redeploy

---

### STEP 4: Setup Database (3 min)

1. **Go to**: https://supabase.com/dashboard
2. **Open your project** → SQL Editor
3. **Copy/paste** the contents of `database/schema.sql`
4. **Click**: "Run"
5. **Create storage bucket**: Storage → "New Bucket" → Name: `personalities` → Public

---

### STEP 5: Setup Slack Webhook (2 min)

1. **Go to**: https://api.slack.com/messaging/webhooks
2. **Create** an Incoming Webhook
3. **Select** a channel (or create `#reddit-assistant`)
4. **Copy** webhook URL
5. **Add to Railway** environment variables (already did in Step 1)
6. **Test**: Send a test notification

---

### STEP 6: Setup Cron Jobs (External) (5 min)

Since Railway doesn't support built-in crons anymore, use **cron-job.org**:

1. **Go to**: https://cron-job.org/en/
2. **Create account** (free)
3. **Add 4 cron jobs**:

**Job 1: Monitor Reddit**
- URL: `https://your-backend.railway.app/jobs/monitor`
- Method: POST
- Schedule: Every 30 minutes (`*/30 * * * *`)

**Job 2: Generate Drafts**
- URL: `https://your-backend.railway.app/jobs/generate-drafts`
- Method: POST
- Schedule: Every 45 minutes (`*/45 * * * *`)

**Job 3: Post Approved**
- URL: `https://your-backend.railway.app/jobs/post-approved`
- Method: POST
- Schedule: Every 15 minutes (`*/15 * * * *`)

**Job 4: Track Performance**
- URL: `https://your-backend.railway.app/jobs/track-performance`
- Method: POST
- Schedule: Every 6 hours (`0 */6 * * *`)

---

## ✅ VERIFICATION

### Test Backend
```bash
# Health check
curl https://your-backend.railway.app/

# Expected: {"status":"healthy",...}
```

### Test Frontend
- Visit: `https://your-frontend.vercel.app`
- Should see: Dashboard with "Add Account" button

### Test Slack
- Trigger: `POST https://your-backend.railway.app/jobs/generate-drafts`
- Check Slack for notification

---

## 🎯 YOU'RE DONE!

Now you can:
1. **Add accounts** via `https://your-frontend.vercel.app/accounts/new`
2. **Upload personality JSON** to Supabase Storage
3. **Get Reddit credentials** (see README.md)
4. **Start receiving Slack notifications** for drafts
5. **Comments auto-post** after 1 minute if not responded to

---

## 🆘 TROUBLESHOOTING

### Backend won't deploy on Railway
- Check logs: Railway Dashboard → Deployments → View Logs
- Verify `railway.toml` exists in root
- Verify `.railwayignore` exists and excludes `frontend/`
- Make sure all environment variables are set

### Frontend won't deploy on Vercel
- Root Directory must be set to `frontend`
- Check build logs for errors
- Verify `package.json` exists in `frontend/` folder

### Frontend can't connect to backend
- Check CORS settings (should allow your Vercel domain)
- Verify `NEXT_PUBLIC_API_URL` is correct
- Test backend URL directly with curl

### Cron jobs not running
- Check cron-job.org dashboard for execution logs
- Verify URLs are correct (include `/jobs/` in path)
- Test endpoints manually with curl first

---

## 📊 EXPECTED COSTS

- Railway Backend: $5-15/month
- Vercel Frontend: FREE
- Supabase: FREE (up to 500MB)
- Gemini API: $10-20/month
- Cron-job.org: FREE
- **Total: $15-35/month**
