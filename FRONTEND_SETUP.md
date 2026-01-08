# FRONTEND SETUP GUIDE

The frontend is a **Next.js 14** application with TypeScript and Tailwind CSS.

## Structure Created

```
frontend/
├── package.json           ✅ Created
├── next.config.js         ✅ Created
├── tailwind.config.ts     ✅ Created
├── tsconfig.json          ✅ Created
├── postcss.config.js      ✅ Created
├── .env.local.example     ✅ Created
├── lib/
│   ├── supabase.ts        ✅ API client
│   └── api.ts             ✅ Backend API client
└── app/
    ├── globals.css        ✅ Tailwind styles
    ├── layout.tsx         ✅ Root layout with nav
    └── page.tsx           ✅ Dashboard page
```

## Installation

```bash
cd frontend
npm install
```

## Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Run Development Server

```bash
npm run dev
```

Open http://localhost:3000

## Remaining Pages to Create

### 1. Accounts List Page

**File:** `frontend/app/accounts/page.tsx`

```typescript
'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { getAccounts } from '@/lib/api'

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<any[]>([])

  useEffect(() => {
    getAccounts().then(res => setAccounts(res.data.accounts || []))
  }, [])

  return (
    <div>
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <h1 className="text-2xl font-bold">Reddit Accounts</h1>
        <Link href="/accounts/new" className="btn-primary">
          Add Account
        </Link>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {accounts.map((account) => (
            <li key={account.id}>
              <Link href={`/accounts/${account.id}`} className="block hover:bg-gray-50 px-4 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-reddit-orange">
                      u/{account.reddit_username}
                    </p>
                    <p className="text-sm text-gray-500">
                      {account.total_karma} karma
                    </p>
                  </div>
                  <div>
                    <span className={`px-2 py-1 text-xs rounded ${account.active ? 'bg-green-100 text-green-800' : 'bg-gray-100'}`}>
                      {account.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
```

### 2. Account Detail Page

**File:** `frontend/app/accounts/[id]/page.tsx`

```typescript
'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { getAccount, getAnalytics } from '@/lib/api'
import { supabase } from '@/lib/supabase'

export default function AccountDetailPage() {
  const params = useParams()
  const [account, setAccount] = useState<any>(null)
  const [analytics, setAnalytics] = useState<any>(null)
  const [postedContent, setPostedContent] = useState<any[]>([])

  useEffect(() => {
    loadData()
  }, [params.id])

  const loadData = async () => {
    const [accountRes, analyticsRes] = await Promise.all([
      getAccount(params.id as string),
      getAnalytics(params.id as string)
    ])

    setAccount(accountRes.data)
    setAnalytics(analyticsRes.data)

    // Load posted content from Supabase
    const { data } = await supabase
      .from('posted_content')
      .select('*')
      .eq('account_id', params.id)
      .order('posted_at', { ascending: false })
      .limit(20)

    setPostedContent(data || [])
  }

  if (!account) return <div>Loading...</div>

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">u/{account.reddit_username}</h1>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-500">Total Karma</p>
          <p className="text-2xl font-bold">{account.total_karma}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-500">Total Posts</p>
          <p className="text-2xl font-bold">{analytics?.total_posts || 0}</p>
        </div>
        <div className="bg-white p-4 rounded shadow">
          <p className="text-sm text-gray-500">Avg Karma</p>
          <p className="text-2xl font-bold">{analytics?.avg_karma?.toFixed(1) || 0}</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium mb-4">Recent Comments</h3>
          <div className="space-y-4">
            {postedContent.map((content) => (
              <div key={content.id} className="border-l-4 border-reddit-orange pl-4">
                <p className="text-xs text-gray-500">
                  r/{content.subreddit} • {new Date(content.posted_at).toLocaleDateString()} • {content.current_karma} karma
                </p>
                <p className="text-sm mt-1">{content.final_text.substring(0, 200)}...</p>
                <a href={content.reddit_permalink} target="_blank" className="text-xs text-reddit-blue hover:underline">
                  View on Reddit →
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
```

### 3. Add Account Page

**File:** `frontend/app/accounts/new/page.tsx`

```typescript
'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createAccount } from '@/lib/api'

export default function NewAccountPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    reddit_username: '',
    personality_json_url: '',
    reddit_client_id: '',
    reddit_client_secret: '',
    reddit_refresh_token: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createAccount(formData)
      router.push('/accounts')
    } catch (error) {
      alert('Error creating account')
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Add Reddit Account</h1>

      <form onSubmit={handleSubmit} className="bg-white shadow rounded-lg p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Reddit Username</label>
          <input
            type="text"
            value={formData.reddit_username}
            onChange={(e) => setFormData({...formData, reddit_username: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-reddit-orange focus:ring-reddit-orange"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Personality JSON URL</label>
          <input
            type="url"
            value={formData.personality_json_url}
            onChange={(e) => setFormData({...formData, personality_json_url: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            placeholder="https://your-storage.com/personality.json"
            required
          />
          <p className="mt-1 text-xs text-gray-500">Upload to Supabase Storage or S3 first</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Reddit Client ID</label>
          <input
            type="text"
            value={formData.reddit_client_id}
            onChange={(e) => setFormData({...formData, reddit_client_id: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Reddit Client Secret</label>
          <input
            type="password"
            value={formData.reddit_client_secret}
            onChange={(e) => setFormData({...formData, reddit_client_secret: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Reddit Refresh Token</label>
          <input
            type="password"
            value={formData.reddit_refresh_token}
            onChange={(e) => setFormData({...formData, reddit_refresh_token: e.target.value})}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm"
            required
          />
        </div>

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => router.back()}
            className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-reddit-orange text-white rounded-md text-sm font-medium hover:bg-reddit-orange/90"
          >
            Add Account
          </button>
        </div>
      </form>
    </div>
  )
}
```

### 4. Draft Approval Page

**File:** `frontend/app/drafts/page.tsx`

```typescript
'use client'
import { useEffect, useState } from 'react'
import { getDrafts, approveDraft, rejectDraft } from '@/lib/api'

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<any[]>([])

  useEffect(() => {
    loadDrafts()
  }, [])

  const loadDrafts = async () => {
    const res = await getDrafts({ status: 'pending' })
    setDrafts(res.data.drafts || [])
  }

  const handleApprove = async (draftId: string) => {
    await approveDraft(draftId, { draft_id: draftId, approved_by: 'web_user' })
    loadDrafts()
  }

  const handleReject = async (draftId: string) => {
    await rejectDraft(draftId, { draft_id: draftId })
    loadDrafts()
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Pending Drafts</h1>

      {drafts.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-500">No pending drafts</p>
        </div>
      ) : (
        <div className="space-y-4">
          {drafts.map((draft) => (
            <div key={draft.id} className="bg-white shadow rounded-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    u/{draft.account?.reddit_username}
                  </p>
                  <p className="text-sm text-gray-500">
                    r/{draft.opportunity?.subreddit} • Karma Score: {draft.karma_probability_score?.toFixed(0)}/100
                  </p>
                </div>
              </div>

              {/* Original Post */}
              <div className="bg-gray-50 p-4 rounded mb-4">
                <p className="text-sm font-semibold mb-2">{draft.opportunity?.post_title}</p>
                <p className="text-xs text-gray-600">{draft.opportunity?.post_body?.substring(0, 200)}...</p>
                <a href={draft.opportunity?.reddit_permalink} target="_blank" className="text-xs text-reddit-blue hover:underline">
                  View on Reddit →
                </a>
              </div>

              {/* Draft */}
              <div className="bg-white border border-gray-200 p-4 rounded mb-4">
                <p className="text-sm whitespace-pre-wrap">{draft.draft_text}</p>
              </div>

              {/* Actions */}
              <div className="flex space-x-3">
                <button
                  onClick={() => handleApprove(draft.id)}
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700"
                >
                  ✓ Approve & Post
                </button>
                <button
                  onClick={() => handleReject(draft.id)}
                  className="flex-1 bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700"
                >
                  ✗ Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

## Build for Production

```bash
npm run build
npm start
```

## Deploy to Vercel

```bash
npm install -g vercel
vercel
```

Or connect your GitHub repo to Vercel dashboard.

## Next Steps

1. Install dependencies: `npm install`
2. Copy `.env.local.example` to `.env.local` and fill in values
3. Run dev server: `npm run dev`
4. Create the remaining pages above
5. Customize styling as needed

The frontend will connect to your FastAPI backend at `http://localhost:8000` and Supabase for real-time updates.
