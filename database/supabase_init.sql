-- ============================================================
-- HELPUVIO DATABASE - COMPLETE INITIALIZATION FOR SUPABASE
-- Run this script on your new Supabase database
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ENUM TYPES
-- ============================================================
DO $$ BEGIN
    CREATE TYPE email_verification_status AS ENUM ('pending', 'verified', 'invalid', 'catch_all', 'unknown');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================
-- CATEGORIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    icon VARCHAR(50),
    description TEXT,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    latitude NUMERIC,
    longitude NUMERIC,
    city VARCHAR(255),
    state VARCHAR(255),
    country VARCHAR(255),
    postal_code VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    onboarding_completed BOOLEAN DEFAULT FALSE,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMPTZ,
    email_verify_token VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================
-- REFRESH TOKENS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(500) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);

-- ============================================================
-- DATASETS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    location VARCHAR(200),
    company_count INTEGER NOT NULL DEFAULT 0,
    enrichment_level VARCHAR(50) NOT NULL DEFAULT 'phone_only',
    price_cents INTEGER NOT NULL,
    csv_file_path VARCHAR(500),
    sample_preview_json JSONB,
    is_published BOOLEAN DEFAULT FALSE,
    total_purchases INTEGER DEFAULT 0,
    total_revenue_cents BIGINT DEFAULT 0,
    last_updated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_datasets_slug ON datasets(slug);
CREATE INDEX IF NOT EXISTS idx_datasets_category ON datasets(category_id);
CREATE INDEX IF NOT EXISTS idx_datasets_published ON datasets(is_published);

-- ============================================================
-- DATASET FIELDS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS dataset_fields (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL,
    field_label VARCHAR(100),
    is_enriched BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    UNIQUE(dataset_id, field_name)
);

-- ============================================================
-- PURCHASES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
    amount_cents INTEGER NOT NULL,
    paystack_reference VARCHAR(200) UNIQUE NOT NULL,
    paystack_authorization_code VARCHAR(200),
    status VARCHAR(50) DEFAULT 'pending',
    refund_amount_cents INTEGER,
    refund_reason TEXT,
    refunded_by UUID,
    refunded_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_purchases_dataset ON purchases(dataset_id);
CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status);
CREATE INDEX IF NOT EXISTS idx_purchases_reference ON purchases(paystack_reference);

-- ============================================================
-- DOWNLOAD LOGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS download_logs (
    id SERIAL PRIMARY KEY,
    purchase_id UUID REFERENCES purchases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
    ip_address INET NOT NULL,
    user_agent TEXT,
    country_code VARCHAR(5),
    downloaded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ADMIN USERS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- ============================================================
-- ADMIN AUDIT LOGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id UUID REFERENCES admin_users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- DAILY METRICS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_metrics (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    signups INTEGER DEFAULT 0,
    purchases INTEGER DEFAULT 0,
    revenue_cents BIGINT DEFAULT 0,
    downloads INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- IMPORT BATCHES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS import_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    total_rows INTEGER DEFAULT 0,
    imported_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    skipped_rows INTEGER DEFAULT 0,
    verified_emails INTEGER DEFAULT 0,
    invalid_emails INTEGER DEFAULT 0,
    pending_verification INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    error_details JSONB,
    imported_by UUID REFERENCES admin_users(id),
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_import_batches_status ON import_batches(status);
CREATE INDEX IF NOT EXISTS idx_import_batches_created_at ON import_batches(created_at DESC);

-- ============================================================
-- COMPANIES TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core company info
    company_name VARCHAR(500) NOT NULL,
    category VARCHAR(255),
    group_name VARCHAR(255),

    -- Contact information
    email VARCHAR(255),
    emails TEXT[] DEFAULT '{}',
    phone VARCHAR(100),
    phones TEXT[] DEFAULT '{}',

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

    -- Email verification
    email_verification_status email_verification_status DEFAULT 'pending',
    email_verified_at TIMESTAMPTZ,
    email_verification_error TEXT,
    email_mx_record VARCHAR(255),
    email_smtp_response TEXT,

    -- Enrichment flags (for pricing)
    has_email BOOLEAN DEFAULT FALSE,
    has_phone BOOLEAN DEFAULT FALSE,
    has_verified_email BOOLEAN DEFAULT FALSE,

    -- Import tracking
    import_batch_id UUID REFERENCES import_batches(id) ON DELETE SET NULL,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,

    -- Display control
    is_displayable BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Company indexes
CREATE INDEX IF NOT EXISTS idx_company_name ON companies(company_name);
CREATE INDEX IF NOT EXISTS idx_company_category ON companies(category);
CREATE INDEX IF NOT EXISTS idx_company_country ON companies(country);
CREATE INDEX IF NOT EXISTS idx_company_state ON companies(state);
CREATE INDEX IF NOT EXISTS idx_company_group ON companies(group_name);
CREATE INDEX IF NOT EXISTS idx_company_email ON companies(email);
CREATE INDEX IF NOT EXISTS idx_company_phone ON companies(phone);
CREATE INDEX IF NOT EXISTS idx_company_displayable ON companies(is_displayable);
CREATE INDEX IF NOT EXISTS idx_company_verification ON companies(email_verification_status);
CREATE INDEX IF NOT EXISTS idx_company_has_email_phone ON companies(has_email, has_phone);
CREATE INDEX IF NOT EXISTS idx_company_batch ON companies(import_batch_id);
CREATE INDEX IF NOT EXISTS idx_company_dataset ON companies(dataset_id);
CREATE INDEX IF NOT EXISTS idx_company_displayable_category ON companies(is_displayable, category);
CREATE INDEX IF NOT EXISTS idx_company_displayable_country ON companies(is_displayable, country);

-- ============================================================
-- EMAIL VERIFICATION JOBS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS email_verification_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    result VARCHAR(50),
    error_message TEXT,
    mx_record VARCHAR(255),
    smtp_response TEXT,
    worker_id VARCHAR(100),
    locked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_job_status ON email_verification_jobs(status);
CREATE INDEX IF NOT EXISTS idx_job_company ON email_verification_jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_job_status_created ON email_verification_jobs(status, created_at);

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Update timestamp trigger
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

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_datasets_updated_at ON datasets;
CREATE TRIGGER update_datasets_updated_at
    BEFORE UPDATE ON datasets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Company displayable status trigger
CREATE OR REPLACE FUNCTION update_company_displayable()
RETURNS TRIGGER AS $$
BEGIN
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
-- VIEWS
-- ============================================================

-- Displayable companies view
CREATE OR REPLACE VIEW v_displayable_companies AS
SELECT
    id, company_name, category, group_name,
    CASE WHEN has_verified_email THEN email ELSE NULL END as email,
    CASE WHEN has_verified_email THEN emails ELSE '{}' END as emails,
    phone, phones, street, locality, city, state, zip_code, country,
    website, linkedin_url, twitter_url, facebook_url, instagram_url,
    ceo_name, description, employee_count, founded_year, rating, reviews,
    has_verified_email as has_email, has_phone, created_at
FROM companies
WHERE is_displayable = TRUE;

-- Stats by category
CREATE OR REPLACE VIEW v_company_stats_by_category AS
SELECT
    category,
    COUNT(*) as total_companies,
    COUNT(*) FILTER (WHERE is_displayable) as displayable,
    COUNT(*) FILTER (WHERE has_verified_email) as with_email,
    COUNT(*) FILTER (WHERE has_phone) as with_phone,
    COUNT(*) FILTER (WHERE has_verified_email AND has_phone) as premium
FROM companies WHERE category IS NOT NULL
GROUP BY category ORDER BY total_companies DESC;

-- Stats by country
CREATE OR REPLACE VIEW v_company_stats_by_country AS
SELECT
    country,
    COUNT(*) as total_companies,
    COUNT(*) FILTER (WHERE is_displayable) as displayable,
    COUNT(*) FILTER (WHERE has_verified_email) as with_email,
    COUNT(*) FILTER (WHERE has_phone) as with_phone
FROM companies WHERE country IS NOT NULL
GROUP BY country ORDER BY total_companies DESC;

-- Stats by group
CREATE OR REPLACE VIEW v_company_stats_by_group AS
SELECT
    group_name,
    COUNT(*) as total_companies,
    COUNT(*) FILTER (WHERE is_displayable) as displayable,
    COUNT(*) FILTER (WHERE has_verified_email) as with_email,
    COUNT(*) FILTER (WHERE has_phone) as with_phone
FROM companies WHERE group_name IS NOT NULL
GROUP BY group_name ORDER BY total_companies DESC;

-- ============================================================
-- DEFAULT DATA
-- ============================================================

-- Default admin (password: admin123)
INSERT INTO admin_users (email, password_hash, name, role)
VALUES (
    'admin@helpuvio.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lWfGD.P8B9wW',
    'Admin',
    'superadmin'
) ON CONFLICT (email) DO NOTHING;

-- Default categories
INSERT INTO categories (name, slug, description, display_order) VALUES
    ('Technology', 'technology', 'Tech companies and startups', 1),
    ('Finance', 'finance', 'Banks, fintech, and financial services', 2),
    ('Healthcare', 'healthcare', 'Hospitals, clinics, and health services', 3),
    ('Real Estate', 'real-estate', 'Property developers and agents', 4),
    ('E-commerce', 'ecommerce', 'Online stores and marketplaces', 5),
    ('Manufacturing', 'manufacturing', 'Factories and producers', 6),
    ('Services', 'services', 'Professional and business services', 7),
    ('Education', 'education', 'Schools, training, and e-learning', 8),
    ('Retail', 'retail', 'Retail stores and shops', 9),
    ('Food & Beverage', 'food-beverage', 'Restaurants, cafes, and food services', 10),
    ('Transportation', 'transportation', 'Logistics and transport companies', 11),
    ('Construction', 'construction', 'Construction and building companies', 12)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================
-- DONE!
-- ============================================================
SELECT 'Database initialized successfully!' as status;
