-- Reddit Assistant Database Schema for Supabase
-- Run this SQL in your Supabase SQL editor to create all tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ACCOUNTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reddit_username TEXT UNIQUE NOT NULL,
    personality_json_url TEXT NOT NULL,
    reddit_client_id TEXT NOT NULL,
    reddit_client_secret TEXT NOT NULL,
    reddit_refresh_token TEXT NOT NULL,
    user_agent TEXT NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    last_monitored_at TIMESTAMP WITH TIME ZONE,
    total_karma INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_accounts_active ON accounts(active);
CREATE INDEX idx_accounts_username ON accounts(reddit_username);

-- ============================================================================
-- OPPORTUNITIES TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE NOT NULL,
    reddit_post_id TEXT NOT NULL,
    reddit_permalink TEXT NOT NULL,
    subreddit TEXT NOT NULL,
    post_title TEXT,
    post_body TEXT,
    post_author TEXT,
    post_created_utc TIMESTAMP WITH TIME ZONE,
    post_score INTEGER DEFAULT 0,
    post_num_comments INTEGER DEFAULT 0,
    post_age_hours REAL DEFAULT 0.0,
    engagement_velocity REAL DEFAULT 0.0,
    karma_opportunity_score REAL DEFAULT 0.0,
    priority_match BOOLEAN DEFAULT FALSE,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'new' CHECK (status IN ('new', 'drafting', 'drafted', 'expired', 'posted')),
    UNIQUE(account_id, reddit_post_id)
);

CREATE INDEX idx_opportunities_account_status ON opportunities(account_id, status);
CREATE INDEX idx_opportunities_score ON opportunities(karma_opportunity_score DESC);
CREATE INDEX idx_opportunities_subreddit ON opportunities(subreddit);
CREATE INDEX idx_opportunities_discovered ON opportunities(discovered_at DESC);

-- ============================================================================
-- DRAFTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS drafts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE NOT NULL,
    opportunity_id UUID REFERENCES opportunities(id) ON DELETE CASCADE NOT NULL,
    draft_text TEXT NOT NULL,
    draft_type TEXT DEFAULT 'comment' CHECK (draft_type IN ('comment', 'reply', 'post')),
    variant_number INTEGER DEFAULT 1,
    karma_probability_score REAL,
    personality_alignment_score REAL,
    reasoning TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'edited', 'posted', 'failed')),
    edited_text TEXT,
    user_notes TEXT,
    approved_at TIMESTAMP WITH TIME ZONE,
    approved_by TEXT,
    posted_at TIMESTAMP WITH TIME ZONE,
    notification_sent_at TIMESTAMP WITH TIME ZONE,
    auto_approved BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_drafts_account_status ON drafts(account_id, status);
CREATE INDEX idx_drafts_score ON drafts(karma_probability_score DESC);
CREATE INDEX idx_drafts_generated ON drafts(generated_at DESC);
CREATE INDEX idx_drafts_notification_sent ON drafts(notification_sent_at);

-- ============================================================================
-- POSTED_CONTENT TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS posted_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE NOT NULL,
    draft_id UUID REFERENCES drafts(id),
    opportunity_id UUID REFERENCES opportunities(id),
    reddit_comment_id TEXT UNIQUE,
    reddit_post_id TEXT UNIQUE,
    reddit_permalink TEXT,
    final_text TEXT NOT NULL,
    subreddit TEXT NOT NULL,
    parent_post_id TEXT,
    posted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    current_karma INTEGER DEFAULT 0,
    last_karma_check TIMESTAMP WITH TIME ZONE,
    removed BOOLEAN DEFAULT FALSE,
    removal_reason TEXT
);

CREATE INDEX idx_posted_content_account ON posted_content(account_id);
CREATE INDEX idx_posted_content_subreddit ON posted_content(subreddit);
CREATE INDEX idx_posted_content_karma ON posted_content(current_karma DESC);
CREATE INDEX idx_posted_content_posted ON posted_content(posted_at DESC);

-- ============================================================================
-- PERFORMANCE_HISTORY TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS performance_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE NOT NULL,
    posted_content_id UUID REFERENCES posted_content(id) ON DELETE CASCADE NOT NULL,
    karma_score INTEGER NOT NULL,
    engagement_rate REAL,
    subreddit TEXT NOT NULL,
    time_since_post_hours REAL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_performance_account_time ON performance_history(account_id, recorded_at DESC);
CREATE INDEX idx_performance_subreddit ON performance_history(subreddit);

-- ============================================================================
-- LEARNING_INSIGHTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS learning_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE NOT NULL,
    insight_type TEXT NOT NULL,
    subreddit TEXT,
    pattern_description TEXT NOT NULL,
    evidence_post_ids TEXT[],
    confidence_score REAL DEFAULT 0.0,
    learned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied_count INTEGER DEFAULT 0
);

CREATE INDEX idx_learning_account ON learning_insights(account_id);
CREATE INDEX idx_learning_subreddit ON learning_insights(subreddit);
CREATE INDEX idx_learning_confidence ON learning_insights(confidence_score DESC);

-- ============================================================================
-- RATE_LIMITS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE NOT NULL,
    limit_type TEXT NOT NULL,
    limit_window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_count INTEGER DEFAULT 0,
    max_allowed INTEGER NOT NULL,
    UNIQUE(account_id, limit_type, limit_window_start)
);

CREATE INDEX idx_rate_limits_account ON rate_limits(account_id, limit_type);

-- ============================================================================
-- AUDIT_LOG TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    details JSONB,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_log_account_time ON audit_log(account_id, created_at DESC);
CREATE INDEX idx_audit_log_action ON audit_log(action);

-- ============================================================================
-- ROW-LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE posted_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Service role can do everything
CREATE POLICY "Service role has full access to accounts"
    ON accounts FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to opportunities"
    ON opportunities FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to drafts"
    ON drafts FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to posted_content"
    ON posted_content FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to performance_history"
    ON performance_history FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to learning_insights"
    ON learning_insights FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to rate_limits"
    ON rate_limits FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to audit_log"
    ON audit_log FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for accounts table
CREATE TRIGGER update_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA (OPTIONAL)
-- ============================================================================

-- You can add seed data here if needed
