-- Smartilee Study Abroad - Supabase Schema
-- Database Engineer: Adithya

-- 1. Enable pgvector extension for RAG
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. packages table
-- Stores country-specific study abroad packages
CREATE TABLE IF NOT EXISTS packages (
    id text PRIMARY KEY, -- e.g. 'pkg_germany_001'
    country text NOT NULL, -- 'Germany' | 'France' | 'Netherlands'
    package_name text NOT NULL,
    overview text,
    tuition_fee text,
    living_cost text,
    duration text,
    universities text[] DEFAULT '{}',
    services_included text[] DEFAULT '{}',
    services_not_included text[] DEFAULT '{}',
    visa_support text,
    scholarships text,
    intake_months text[] DEFAULT '{}',
    eligibility text,
    created_at timestamptz DEFAULT now()
);

-- 3. customers table
-- Stores student profile (Digital Twin)
CREATE TABLE IF NOT EXISTS customers (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number text UNIQUE NOT NULL,
    name text,
    language text DEFAULT 'en', -- en/hi/ml/ta etc.
    tone_preference text DEFAULT 'casual',
    preferred_country text, -- 'Germany' | 'France' | 'Netherlands'
    interested_package_id text REFERENCES packages(id),
    education_level text, -- 'Bachelors' | 'Masters' | 'MBA'
    field_of_study text, -- e.g. 'Computer Science'
    ielts_score float,
    budget_range text, -- e.g. 'Low (0-5k EUR)'
    last_active timestamptz DEFAULT now(),
    churn_score float DEFAULT 0,
    is_handoff_active boolean DEFAULT false,
    category text DEFAULT 'New', -- Champion/Loyal/At Risk/Lost/New
    business_id uuid,
    created_at timestamptz DEFAULT now()
);

-- 4. conversations table
-- Stores all chat history
CREATE TABLE IF NOT EXISTS conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid REFERENCES customers(id) ON DELETE CASCADE,
    direction text CHECK (direction IN ('inbound', 'outbound')),
    message_text text,
    intent_label text, -- enquiry/visa_question/scholarship_query/complaint/churn_risk/general
    sentiment text, -- positive/neutral/negative
    action_taken text, -- auto_reply/upsell/handoff/schedule_followup
    language text,
    package_context text, -- package discussed
    timestamp timestamptz DEFAULT now()
);

-- 5. enquiry_events table
-- Tracks enquiry activity (Replaces cart_events)
CREATE TABLE IF NOT EXISTS enquiry_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid REFERENCES customers(id) ON DELETE CASCADE,
    package_id text,
    country text,
    status text DEFAULT 'active' CHECK (status IN ('active', 'abandoned', 'converted', 'followup_sent')),
    notes text,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- 6. handoff_queue table
-- Tracks human intervention requests
CREATE TABLE IF NOT EXISTS handoff_queue (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid REFERENCES customers(id) ON DELETE CASCADE,
    reason text,
    package_discussed text,
    status text DEFAULT 'pending' CHECK (status IN ('pending', 'resolved')),
    created_at timestamptz DEFAULT now(),
    resolved_at timestamptz
);

-- 7. followups table
-- Scheduled re-engagement messages
CREATE TABLE IF NOT EXISTS followups (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id uuid REFERENCES customers(id) ON DELETE CASCADE,
    scheduled_at timestamptz,
    message_hint text,
    package_id text,
    status text DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'cancelled')),
    created_at timestamptz DEFAULT now()
);

-- 8. knowledge_base table
-- Stores RAG facts
CREATE TABLE IF NOT EXISTS knowledge_base (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    package_id text, -- NULL for general knowledge
    country text, -- 'Germany' | 'France' | 'Netherlands' | 'General'
    category text, -- 'tuition' | 'visa' | 'scholarships' | 'living' | 'universities' | 'eligibility' | 'intake' | 'faq' | 'services'
    title text UNIQUE, -- Added UNIQUE to solve the ON CONFLICT error
    content text,
    embedding vector(1536),
    created_at timestamptz DEFAULT now()
);

-- RAG SEARCH FUNCTION
-- Pass filter_country and filter_category for precision
CREATE OR REPLACE FUNCTION match_knowledge_base (
  query_embedding vector(1536),
  match_count int DEFAULT 4,
  filter_country text DEFAULT NULL,
  filter_category text DEFAULT NULL
) RETURNS TABLE (
  id uuid,
  package_id text,
  country text,
  category text,
  title text,
  content text,
  similarity float
) LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    kb.id,
    kb.package_id,
    kb.country,
    kb.category,
    kb.title,
    kb.content,
    1 - (kb.embedding <=> query_embedding) AS similarity
  FROM knowledge_base kb
  WHERE kb.embedding IS NOT NULL
    AND (filter_country IS NULL OR kb.country = filter_country)
    AND (filter_category IS NULL OR kb.category = filter_category)
  ORDER BY kb.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ROW LEVEL SECURITY (RLS)
-- Enable RLS on all tables
ALTER TABLE packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE enquiry_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE handoff_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE followups ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;

-- Security Policies
-- Based on business_id = auth.uid() for multi-tenant isolation
CREATE POLICY "Public access to packages" ON packages FOR SELECT USING (true);
CREATE POLICY "Public access to knowledge_base" ON knowledge_base FOR SELECT USING (true);

-- Customers and related tables are restricted by business_id
CREATE POLICY "Businesses can only see their own customers" ON customers
    FOR ALL USING (business_id = auth.uid());

CREATE POLICY "Businesses can only see their customers conversations" ON conversations
    FOR ALL USING (EXISTS (
        SELECT 1 FROM customers WHERE customers.id = conversations.customer_id AND customers.business_id = auth.uid()
    ));

CREATE POLICY "Businesses can only see their enquiry_events" ON enquiry_events
    FOR ALL USING (EXISTS (
        SELECT 1 FROM customers WHERE customers.id = enquiry_events.customer_id AND customers.business_id = auth.uid()
    ));

CREATE POLICY "Businesses can only see their handoff_queue" ON handoff_queue
    FOR ALL USING (EXISTS (
        SELECT 1 FROM customers WHERE customers.id = handoff_queue.customer_id AND customers.business_id = auth.uid()
    ));

CREATE POLICY "Businesses can only see their followups" ON followups
    FOR ALL USING (EXISTS (
        SELECT 1 FROM customers WHERE customers.id = followups.customer_id AND customers.business_id = auth.uid()
    ));

-- REPLICATION SETUP FOR REAL-TIME
ALTER TABLE enquiry_events REPLICA IDENTITY FULL;
ALTER TABLE handoff_queue REPLICA IDENTITY FULL;
