-- ─── Run this in Supabase → SQL Editor ───

-- 1. Create visits table
CREATE TABLE IF NOT EXISTS visits (
  id          BIGSERIAL PRIMARY KEY,
  timestamp   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ip          TEXT NOT NULL,
  user_agent  TEXT
);

-- 2. Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_visits_ip        ON visits(ip);
CREATE INDEX IF NOT EXISTS idx_visits_timestamp ON visits(timestamp DESC);

-- 3. Enable RLS (Supabase recommends this)
ALTER TABLE visits ENABLE ROW LEVEL SECURITY;

-- 4. service_role key bypasses RLS automatically — no policy needed for your backend.
--    This policy blocks ALL anon/public access (nobody can read your visitor data from the browser)
CREATE POLICY "deny_all_public" ON visits
  FOR ALL
  TO anon, authenticated
  USING (false)
  WITH CHECK (false);

-- ─── Migrate existing visitor_data.json data (run after table is created) ───
-- Paste each visit as an INSERT — example format:
-- INSERT INTO visits (timestamp, ip, user_agent) VALUES ('2026-02-02T17:22:38', '175.139.100.69', 'Mozilla/5.0...');
-- Or just start fresh — your call.
