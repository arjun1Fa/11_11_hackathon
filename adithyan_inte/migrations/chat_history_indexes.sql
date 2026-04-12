-- ══════════════════════════════════════════════════════════════════════════════
-- Smartilee — Supabase SQL Migration
-- Run this in: Supabase Dashboard → SQL Editor → New Query → Run
-- ══════════════════════════════════════════════════════════════════════════════

-- 1. Ensure 'conversations' table has 'created_at' column with auto-timestamp
ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- 2. Ensure 'conversations' has a direction column ('inbound' or 'outbound')
ALTER TABLE conversations
  ADD COLUMN IF NOT EXISTS direction TEXT DEFAULT 'inbound';

-- 3. Index for fast lookups by phone number (chat history page loads fast)
CREATE INDEX IF NOT EXISTS idx_conversations_phone
  ON conversations (phone_number);

-- 4. Index for fast ordering by time per user
CREATE INDEX IF NOT EXISTS idx_conversations_phone_time
  ON conversations (phone_number, created_at DESC);

-- 5. Index for inbox view (latest message per user)
CREATE INDEX IF NOT EXISTS idx_conversations_created_at
  ON conversations (created_at DESC);

-- 6. Add 'risk_level' column to customers (low, medium, high)
ALTER TABLE customers
  ADD COLUMN IF NOT EXISTS risk_level TEXT DEFAULT 'low';

-- 7. Index for customers channel filter
CREATE INDEX IF NOT EXISTS idx_customers_channel
  ON customers (channel);

-- 8. Index for customers risk filter
CREATE INDEX IF NOT EXISTS idx_customers_risk
  ON customers (risk_level);

-- ── Verify everything looks right ────────────────────────────────────────────
SELECT
  column_name,
  data_type,
  column_default,
  is_nullable
FROM information_schema.columns
WHERE table_name = 'conversations'
ORDER BY ordinal_position;
