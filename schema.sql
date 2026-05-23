-- ChittyScore 6D Trust Scoring Schema
-- Target: ChittyOS-Core Neon project (restless-grass-40598426)
-- Namespaced under `chittyscore` Postgres schema to avoid collision with
-- ChittyTrust's `public.trust_scores` (DRL / TY-VY-RY model) in the same DB.
--
-- Apply with:
--   psql "$DATABASE_URL" -f schema.sql
-- Or via Neon MCP: validated on branch br-late-hat-aey8hnjq (2026-05-23).

CREATE SCHEMA IF NOT EXISTS chittyscore;

-- Trust scoring results — one row per /api/trust/calculate (history-preserving)
CREATE TABLE IF NOT EXISTS chittyscore.results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_id UUID NOT NULL REFERENCES public.identities(id) ON DELETE CASCADE,

    -- 6 dimension scores (0-100)
    source_dimension   NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (source_dimension   BETWEEN 0 AND 100),
    temporal_dimension NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (temporal_dimension BETWEEN 0 AND 100),
    channel_dimension  NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (channel_dimension  BETWEEN 0 AND 100),
    outcome_dimension  NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (outcome_dimension  BETWEEN 0 AND 100),
    network_dimension  NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (network_dimension  BETWEEN 0 AND 100),
    justice_dimension  NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (justice_dimension  BETWEEN 0 AND 100),

    -- 4 output scores (0-100)
    people_score  NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (people_score  BETWEEN 0 AND 100),
    legal_score   NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (legal_score   BETWEEN 0 AND 100),
    state_score   NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (state_score   BETWEEN 0 AND 100),
    chitty_score  NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (chitty_score  BETWEEN 0 AND 100),

    composite_score NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (composite_score BETWEEN 0 AND 100),
    trust_level     VARCHAR(20)  NOT NULL DEFAULT 'L0_ANONYMOUS',
    confidence      NUMERIC(5,2) NOT NULL DEFAULT 0 CHECK (confidence BETWEEN 0 AND 100),

    insights            JSONB NOT NULL DEFAULT '[]'::jsonb,
    calculation_details JSONB NOT NULL DEFAULT '{}'::jsonb,

    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trust events — input signals consumed by the engine
CREATE TABLE IF NOT EXISTS chittyscore.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_id UUID NOT NULL REFERENCES public.identities(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_timestamp TIMESTAMPTZ NOT NULL,
    channel VARCHAR(50),
    outcome VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (outcome IN ('positive','negative','neutral','pending')),
    impact_score NUMERIC(4,2) NOT NULL DEFAULT 1.0
        CHECK (impact_score BETWEEN 0 AND 10),
    tags TEXT[] NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chittyscore_results_identity
    ON chittyscore.results(identity_id);
CREATE INDEX IF NOT EXISTS idx_chittyscore_results_identity_calc
    ON chittyscore.results(identity_id, calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chittyscore_results_chitty
    ON chittyscore.results(chitty_score DESC);
CREATE INDEX IF NOT EXISTS idx_chittyscore_results_trust_level
    ON chittyscore.results(trust_level);

CREATE INDEX IF NOT EXISTS idx_chittyscore_events_identity
    ON chittyscore.events(identity_id);
CREATE INDEX IF NOT EXISTS idx_chittyscore_events_type
    ON chittyscore.events(event_type);
CREATE INDEX IF NOT EXISTS idx_chittyscore_events_timestamp
    ON chittyscore.events(event_timestamp DESC);
