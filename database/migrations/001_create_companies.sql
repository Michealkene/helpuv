-- Migration: Create companies, import_batches, and email_verification_jobs tables
-- Run this on your Supabase database

-- Create enum for email verification status
DO $$ BEGIN
    CREATE TYPE email_verification_status AS ENUM ('pending', 'verified', 'invalid', 'catch_all', 'unknown');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================
-- Import Batches Table (must be created first due to FK)
-- ============================================================
CREATE TABLE IF NOT EXISTS import_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Import info
    filename VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    total_rows INTEGER DEFAULT 0,
    imported_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    skipped_rows INTEGER DEFAULT 0,

    -- Verification stats
    verified_emails INTEGER DEFAULT 0,
    invalid_emails INTEGER DEFAULT 0,
    pending_verification INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    error_details JSONB,

    -- Admin who triggered import
    imported_by UUID REFERENCES admin_users(id),

    -- Target dataset (optional)
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,

    -- Timestamps
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_import_batches_status ON import_batches(status);
CREATE INDEX IF NOT EXISTS idx_import_batches_created_at ON import_batches(created_at DESC);

-- ============================================================
-- Companies Table
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core company info
    company_name VARCHAR(500) NOT NULL,
    category VARCHAR(255),
    group_name VARCHAR(255),

    -- Contact information
    email VARCHAR(255),
    emails TEXT[],  -- Array of additional emails
    phone VARCHAR(100),
    phones TEXT[],  -- Array of additional phones

    -- Address
    street VARCHAR(500),
    locality VARCHAR(255),
    city VARCHAR(255),
    state VARCHAR(255),
    zip_code VARCHAR(50),
    country VARCHAR(100),

    -- Online presence
    website VARCHAR(500),
    linkedin_url VARCHAR(500),
    twitter_url VARCHAR(500),
    facebook_url VARCHAR(500),
    instagram_url VARCHAR(500),
    socials TEXT,

    -- Business info
    ceo_name VARCHAR(255),
    description TEXT,
    meta_title VARCHAR(500),
    employee_count INTEGER,
    founded_year INTEGER,
    rating FLOAT,
    reviews INTEGER,

    -- Media
    avatar_url VARCHAR(500),
    favicon_url VARCHAR(500),

    -- Crawl metadata
    performance_score FLOAT,
    response_time_ms INTEGER,
    crawl_status VARCHAR(50),
    crawl_error TEXT,
    sent BOOLEAN DEFAULT FALSE,

    -- Email verification status
    email_verification_status email_verification_status DEFAULT 'pending',
    email_verified_at TIMESTAMPTZ,
    email_verification_error TEXT,
    email_mx_record VARCHAR(255),
    email_smtp_response TEXT,

    -- Enrichment level (for pricing)
    has_email BOOLEAN DEFAULT FALSE,
    has_phone BOOLEAN DEFAULT FALSE,
    has_verified_email BOOLEAN DEFAULT FALSE,

    -- Import tracking
    import_batch_id UUID REFERENCES import_batches(id) ON DELETE SET NULL,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,

    -- Display control (only verified emails shown)
    is_displayable BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_company_name ON companies(company_name);
CREATE INDEX IF NOT EXISTS idx_company_category ON companies(category);
CREATE INDEX IF NOT EXISTS idx_company_country ON companies(country);
CREATE INDEX IF NOT EXISTS idx_company_state ON companies(state);
CREATE INDEX IF NOT EXISTS idx_company_group ON companies(group_name);
CREATE INDEX IF NOT EXISTS idx_company_email ON companies(email);
CREATE INDEX IF NOT EXISTS idx_company_phone ON companies(phone);
CREATE INDEX IF NOT EXISTS idx_company_displayable ON companies(is_displayable);
CREATE INDEX IF NOT EXISTS idx_company_verification_status ON companies(email_verification_status);
CREATE INDEX IF NOT EXISTS idx_company_has_email_phone ON companies(has_email, has_phone);
CREATE INDEX IF NOT EXISTS idx_company_batch ON companies(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_company_dataset ON companies(dataset_id);
CREATE INDEX IF NOT EXISTS idx_company_displayable_category ON companies(is_displayable, category);
CREATE INDEX IF NOT EXISTS idx_company_displayable_country ON companies(is_displayable, country);

-- ============================================================
-- Email Verification Jobs Table
-- ============================================================
CREATE TABLE IF NOT EXISTS email_verification_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Target
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,

    -- Job status
    status VARCHAR(50) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,

    -- Results
    result VARCHAR(50),
    error_message TEXT,
    mx_record VARCHAR(255),
    smtp_response TEXT,

    -- Worker tracking
    worker_id VARCHAR(100),
    locked_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_job_status ON email_verification_jobs(status);
CREATE INDEX IF NOT EXISTS idx_job_company ON email_verification_jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_job_status_created ON email_verification_jobs(status, created_at);

-- ============================================================
-- Trigger to update updated_at timestamp
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_companies_updated_at ON companies;
CREATE TRIGGER update_companies_updated_at
    BEFORE UPDATE ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Function to update company displayable status
-- ============================================================
CREATE OR REPLACE FUNCTION update_company_displayable()
RETURNS TRIGGER AS $$
BEGIN
    -- Company is displayable if:
    -- 1. Has phone only (no email), OR
    -- 2. Has verified email
    IF NEW.has_phone AND NOT NEW.has_email THEN
        NEW.is_displayable := TRUE;
    ELSIF NEW.has_email AND NEW.email_verification_status = 'verified' THEN
        NEW.is_displayable := TRUE;
        NEW.has_verified_email := TRUE;
    ELSE
        NEW.is_displayable := FALSE;
        NEW.has_verified_email := FALSE;
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_company_displayable ON companies;
CREATE TRIGGER trigger_company_displayable
    BEFORE INSERT OR UPDATE OF has_email, has_phone, email_verification_status ON companies
    FOR EACH ROW
    EXECUTE FUNCTION update_company_displayable();

-- ============================================================
-- Useful Views
-- ============================================================

-- View: Displayable companies (for public API)
CREATE OR REPLACE VIEW v_displayable_companies AS
SELECT
    id,
    company_name,
    category,
    group_name,
    CASE WHEN has_verified_email THEN email ELSE NULL END as email,
    CASE WHEN has_verified_email THEN emails ELSE '{}' END as emails,
    phone,
    phones,
    street,
    locality,
    city,
    state,
    zip_code,
    country,
    website,
    linkedin_url,
    twitter_url,
    facebook_url,
    instagram_url,
    ceo_name,
    description,
    employee_count,
    founded_year,
    rating,
    reviews,
    has_verified_email as has_email,
    has_phone,
    created_at
FROM companies
WHERE is_displayable = TRUE;

-- View: Company statistics by category
CREATE OR REPLACE VIEW v_company_stats_by_category AS
SELECT
    category,
    COUNT(*) as total_companies,
    COUNT(*) FILTER (WHERE is_displayable) as displayable_companies,
    COUNT(*) FILTER (WHERE has_verified_email) as with_verified_email,
    COUNT(*) FILTER (WHERE has_phone) as with_phone,
    COUNT(*) FILTER (WHERE has_verified_email AND has_phone) as with_email_and_phone
FROM companies
WHERE category IS NOT NULL
GROUP BY category
ORDER BY total_companies DESC;

-- View: Company statistics by country
CREATE OR REPLACE VIEW v_company_stats_by_country AS
SELECT
    country,
    COUNT(*) as total_companies,
    COUNT(*) FILTER (WHERE is_displayable) as displayable_companies,
    COUNT(*) FILTER (WHERE has_verified_email) as with_verified_email,
    COUNT(*) FILTER (WHERE has_phone) as with_phone
FROM companies
WHERE country IS NOT NULL
GROUP BY country
ORDER BY total_companies DESC;

-- View: Verification queue status
CREATE OR REPLACE VIEW v_verification_queue AS
SELECT
    status,
    COUNT(*) as job_count,
    MIN(created_at) as oldest_job,
    MAX(created_at) as newest_job
FROM email_verification_jobs
GROUP BY status;

-- ============================================================
-- Grant permissions (for Supabase)
-- ============================================================
GRANT ALL ON companies TO postgres;
GRANT ALL ON import_batches TO postgres;
GRANT ALL ON email_verification_jobs TO postgres;
GRANT SELECT ON v_displayable_companies TO postgres;
GRANT SELECT ON v_company_stats_by_category TO postgres;
GRANT SELECT ON v_company_stats_by_country TO postgres;
GRANT SELECT ON v_verification_queue TO postgres;

-- Done!
SELECT 'Migration completed successfully!' as status;
