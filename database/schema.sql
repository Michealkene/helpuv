-- ============================================================
-- HELPUVIO B2B LEAD DATA MARKETPLACE - DATABASE SCHEMA
-- ============================================================
-- This schema adds marketplace tables to your existing database
-- Run this AFTER your existing tables are in place
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ENUMS (Add these if they don't exist)
-- ============================================================

DO $$ BEGIN
    CREATE TYPE dataset_enrichment_level AS ENUM ('phone_only', 'email_and_phone');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE purchase_status AS ENUM ('pending', 'paid', 'failed', 'refunded');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================
-- DATASETS TABLE (Core product for Helpuvio)
-- ============================================================
CREATE TABLE IF NOT EXISTS datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    
    -- Classification (links to your existing categories table)
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    location VARCHAR(200), -- "Lagos, Nigeria", "Global", "USA"
    
    -- Metadata
    company_count INTEGER NOT NULL DEFAULT 0,
    
    -- CRITICAL: This determines pricing
    -- 'phone_only' = Companies with phone numbers only (cheaper)
    -- 'email_and_phone' = Companies with email AND phone (premium)
    enrichment_level VARCHAR(50) NOT NULL DEFAULT 'phone_only',
    
    -- Pricing in cents (kobo for Nigeria)
    price_cents INTEGER NOT NULL,
    
    -- File storage (S3/R2 URL)
    csv_file_path VARCHAR(500),
    
    -- Sample preview (first 5 rows with redacted emails/phones)
    sample_preview_json JSONB,
    
    -- Publishing status
    is_published BOOLEAN DEFAULT FALSE,
    
    -- Stats
    total_purchases INTEGER DEFAULT 0,
    total_revenue_cents BIGINT DEFAULT 0,
    
    -- Timestamps
    last_updated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_datasets_slug ON datasets(slug);
CREATE INDEX IF NOT EXISTS idx_datasets_category ON datasets(category_id);
CREATE INDEX IF NOT EXISTS idx_datasets_published ON datasets(is_published);
CREATE INDEX IF NOT EXISTS idx_datasets_enrichment ON datasets(enrichment_level);
CREATE INDEX IF NOT EXISTS idx_datasets_price ON datasets(price_cents);

-- ============================================================
-- DATASET FIELDS (What's included in each dataset)
-- ============================================================
CREATE TABLE IF NOT EXISTS dataset_fields (
    id SERIAL PRIMARY KEY,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE CASCADE,
    field_name VARCHAR(100) NOT NULL, -- "company_email", "contact_phone"
    field_label VARCHAR(100), -- "Company Email", "Contact Phone"
    is_enriched BOOLEAN DEFAULT FALSE, -- TRUE if only in premium tier
    display_order INTEGER DEFAULT 0,
    
    UNIQUE(dataset_id, field_name)
);

CREATE INDEX IF NOT EXISTS idx_dataset_fields_dataset ON dataset_fields(dataset_id);

-- ============================================================
-- PURCHASES TABLE (Revenue tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
    
    -- Payment details
    amount_cents INTEGER NOT NULL,
    paystack_reference VARCHAR(200) UNIQUE NOT NULL,
    paystack_authorization_code VARCHAR(200),
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Refund tracking
    refund_amount_cents INTEGER,
    refund_reason TEXT,
    refunded_by UUID,
    refunded_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_purchases_dataset ON purchases(dataset_id);
CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status);
CREATE INDEX IF NOT EXISTS idx_purchases_paystack_ref ON purchases(paystack_reference);

-- ============================================================
-- DOWNLOAD LOGS (Audit trail + abuse prevention)
-- ============================================================
CREATE TABLE IF NOT EXISTS download_logs (
    id SERIAL PRIMARY KEY,
    purchase_id UUID REFERENCES purchases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    dataset_id INTEGER REFERENCES datasets(id) ON DELETE SET NULL,
    
    -- Request metadata for abuse detection
    ip_address INET NOT NULL,
    user_agent TEXT,
    country_code VARCHAR(5),
    
    downloaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_download_logs_purchase ON download_logs(purchase_id);
CREATE INDEX IF NOT EXISTS idx_download_logs_user ON download_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_download_logs_ip ON download_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_download_logs_date ON download_logs(downloaded_at DESC);

-- ============================================================
-- ADMIN USERS (Separate from regular users)
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================
-- ADMIN AUDIT LOGS (Compliance tracking)
-- ============================================================
CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id UUID REFERENCES admin_users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin ON admin_audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created ON admin_audit_logs(created_at DESC);

-- ============================================================
-- DAILY METRICS (Analytics)
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_metrics (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    signups INTEGER DEFAULT 0,
    purchases INTEGER DEFAULT 0,
    revenue_cents BIGINT DEFAULT 0,
    downloads INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(date DESC);

-- ============================================================
-- TRIGGERS: Auto-update timestamps
-- ============================================================

-- Update updated_at on datasets
CREATE OR REPLACE FUNCTION update_dataset_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_datasets_updated_at ON datasets;
CREATE TRIGGER trigger_datasets_updated_at
    BEFORE UPDATE ON datasets
    FOR EACH ROW EXECUTE FUNCTION update_dataset_updated_at();

-- Update dataset stats on purchase
CREATE OR REPLACE FUNCTION update_dataset_purchase_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'paid' AND (OLD.status IS NULL OR OLD.status != 'paid') THEN
        UPDATE datasets 
        SET 
            total_purchases = total_purchases + 1,
            total_revenue_cents = total_revenue_cents + NEW.amount_cents
        WHERE id = NEW.dataset_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_dataset_purchase_stats ON purchases;
CREATE TRIGGER trigger_dataset_purchase_stats
    AFTER INSERT OR UPDATE ON purchases
    FOR EACH ROW EXECUTE FUNCTION update_dataset_purchase_stats();

-- ============================================================
-- VIEWS: Useful queries
-- ============================================================

-- View: Companies with phone only (for phone_only datasets)
CREATE OR REPLACE VIEW v_companies_phone_only AS
SELECT 
    c.id,
    c.name,
    c.domain,
    c.website,
    c.description,
    c.employee_count,
    c.founded_year,
    p.phone,
    cl.city,
    cl.state,
    cl.country
FROM companies c
INNER JOIN phones p ON p.company_id = c.id AND p.is_valid = true
LEFT JOIN company_locations cl ON cl.company_id = c.id AND cl.is_headquarters = true
WHERE c.is_active = true
  AND NOT EXISTS (
    SELECT 1 FROM emails e 
    WHERE e.company_id = c.id AND e.verified = true
  );

-- View: Companies with email AND phone (for email_and_phone datasets)
CREATE OR REPLACE VIEW v_companies_email_and_phone AS
SELECT 
    c.id,
    c.name,
    c.domain,
    c.website,
    c.description,
    c.employee_count,
    c.founded_year,
    e.email,
    p.phone,
    cl.city,
    cl.state,
    cl.country
FROM companies c
INNER JOIN emails e ON e.company_id = c.id AND e.verified = true
INNER JOIN phones p ON p.company_id = c.id AND p.is_valid = true
LEFT JOIN company_locations cl ON cl.company_id = c.id AND cl.is_headquarters = true
WHERE c.is_active = true;

-- ============================================================
-- SAMPLE DATA: Default admin user
-- ============================================================
-- Password: admin123 (change this immediately in production!)
INSERT INTO admin_users (email, password_hash, name, role)
VALUES (
    'admin@helpuvio.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lWfGD.P8B9wW',
    'Admin',
    'superadmin'
) ON CONFLICT (email) DO NOTHING;

-- ============================================================
-- SAMPLE DATASETS (You'll update these with real data)
-- ============================================================
INSERT INTO datasets (name, slug, description, location, company_count, enrichment_level, price_cents, is_published)
VALUES 
    ('Nigerian Tech Companies - Phone Only', 'nigerian-tech-phone', 'Technology companies in Nigeria with verified phone numbers', 'Nigeria', 0, 'phone_only', 1999, false),
    ('Nigerian Tech Companies - Premium', 'nigerian-tech-premium', 'Technology companies in Nigeria with verified emails AND phone numbers', 'Nigeria', 0, 'email_and_phone', 4999, false),
    ('Lagos Startups - Phone Only', 'lagos-startups-phone', 'Startup companies in Lagos with verified phone numbers', 'Lagos, Nigeria', 0, 'phone_only', 2999, false),
    ('Lagos Startups - Premium', 'lagos-startups-premium', 'Startup companies in Lagos with verified emails AND phone numbers', 'Lagos, Nigeria', 0, 'email_and_phone', 5999, false)
ON CONFLICT (slug) DO NOTHING;

-- ============================================================
-- HELPFUL QUERIES FOR DATASET GENERATION
-- ============================================================

-- Count companies by enrichment level
-- SELECT 
--     CASE 
--         WHEN EXISTS (SELECT 1 FROM emails WHERE company_id = c.id AND verified = true)
--              AND EXISTS (SELECT 1 FROM phones WHERE company_id = c.id AND is_valid = true)
--         THEN 'email_and_phone'
--         WHEN EXISTS (SELECT 1 FROM phones WHERE company_id = c.id AND is_valid = true)
--         THEN 'phone_only'
--         ELSE 'no_contact'
--     END as enrichment_level,
--     COUNT(*) as company_count
-- FROM companies c
-- WHERE c.is_active = true
-- GROUP BY 1;

-- ============================================================
-- END OF SCHEMA
-- ============================================================
