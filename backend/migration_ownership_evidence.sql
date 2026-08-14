-- migration_ownership_evidence.sql
-- Run this once against your Postgres DB to add the tables needed for
-- YouTube-sourced ownership evidence + human-in-the-loop review.
-- NOTE: artists/songs/artist_profiles use UUID primary keys in this project,
-- so all foreign keys referencing them are UUID too.

-- Evidence pulled from YouTube (or future sources) backing an ownership claim
CREATE TABLE IF NOT EXISTS ownership_evidence (
    id SERIAL PRIMARY KEY,
    matched_artist_id UUID REFERENCES artists(id),      -- nullable until resolved
    matched_artist_name VARCHAR(255) NOT NULL,          -- kept even if artist_id lookup fails, for review UI
    source_type VARCHAR(50) NOT NULL DEFAULT 'youtube',
    source_url TEXT NOT NULL,
    video_title TEXT,
    channel_id VARCHAR(255),
    channel_confidence VARCHAR(20) NOT NULL,            -- 'high' | 'medium' | 'low' (channel trust tier)
    evidence_type VARCHAR(30) NOT NULL,                 -- 'structured_credit' | 'mention_only'
    match_type VARCHAR(20) NOT NULL,                    -- 'exact' | 'partial' | 'mention_only'
    role VARCHAR(30),                                   -- 'lyrics' | 'music' | 'singer' | 'writer' | 'unknown'
    raw_credit_text TEXT,                                -- the actual matched line, for the review UI to show
    stage_name_tag VARCHAR(255),                         -- e.g. "Bharjari", if present
    status VARCHAR(30) NOT NULL DEFAULT 'pending_review', -- 'auto_confirmed' | 'pending_review' | 'confirmed' | 'rejected'
    reviewed_at TIMESTAMP,
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ownership_evidence_status ON ownership_evidence(status);
CREATE INDEX IF NOT EXISTS idx_ownership_evidence_artist ON ownership_evidence(matched_artist_id);

-- Deterministic ownership-conflict flags (kept separate from probabilistic fraud_scores)
CREATE TABLE IF NOT EXISTS ownership_conflicts (
    id SERIAL PRIMARY KEY,
    song_id UUID REFERENCES songs(id),
    claiming_profile_id UUID REFERENCES artist_profiles(id),
    true_owner_artist_id UUID REFERENCES artists(id),
    true_owner_claimed BOOLEAN NOT NULL,
    conflict_type VARCHAR(50) NOT NULL,   -- 'unclaimed_ownership_conflict' | 'impersonation_conflict'
    evidence_id INTEGER REFERENCES ownership_evidence(id),
    flagged_at TIMESTAMP DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE
);
