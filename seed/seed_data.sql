-- =============================================================================
-- COMPLETE SEED DATA: Agentic Analytics Chatbot Database
-- =============================================================================
-- Tables: teams (10), projects (30), quarterly_revenue (72), monthly_revenue (216),
--         monthly_metrics (95), deliverables (87), budget_breakdown (78),
--         resource_allocation (159), incidents (50)
-- Total rows: ~797 rows
-- All DETERMINISTIC (no random() function) — production-ready
-- =============================================================================

-- Drop tables if they exist (clean slate)
DROP TABLE IF EXISTS incidents CASCADE;
DROP TABLE IF EXISTS resource_allocation CASCADE;
DROP TABLE IF EXISTS deliverables CASCADE;
DROP TABLE IF EXISTS monthly_metrics CASCADE;
DROP TABLE IF EXISTS budget_breakdown CASCADE;
DROP TABLE IF EXISTS monthly_revenue CASCADE;
DROP TABLE IF EXISTS quarterly_revenue CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS teams CASCADE;

-- =============================================================================
-- SECTION 1: TEAMS (10 rows)
-- =============================================================================

CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    headcount INTEGER NOT NULL,
    location VARCHAR(50) NOT NULL,
    created_date DATE NOT NULL DEFAULT CURRENT_DATE
);

INSERT INTO teams (name, department, headcount, location, created_date) VALUES
('Platform Core', 'Engineering', 12, 'San Francisco', '2023-01-15'),
('Mobile Squad', 'Engineering', 8, 'San Francisco', '2023-02-01'),
('Data Pipeline', 'Engineering', 10, 'Austin', '2023-03-10'),
('Cloud Infra', 'Engineering', 15, 'Seattle', '2023-01-20'),
('Frontend UX', 'Engineering', 7, 'San Francisco', '2023-04-05'),
('Product Strategy', 'Product', 6, 'New York', '2023-05-15'),
('Growth Analytics', 'Analytics', 5, 'Austin', '2023-06-01'),
('DevOps SRE', 'Operations', 9, 'Seattle', '2023-02-20'),
('QA Automation', 'Quality', 6, 'Austin', '2023-03-25'),
('Security Ops', 'Security', 4, 'Seattle', '2023-07-10');

-- =============================================================================
-- SECTION 2: PROJECTS (30 rows)
-- =============================================================================
-- Fix 1: No explicit id column — SERIAL will auto-generate
-- Fix 3: Project 30 has status='on_track' and actual_spend=0
-- Ensure projects 28, 29 are not_started with $0 spend and NULL end_date

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('on_track', 'at_risk', 'blocked', 'completed', 'not_started')),
    priority VARCHAR(10) NOT NULL CHECK (priority IN ('high', 'medium', 'low')),
    budget NUMERIC(12,2) NOT NULL,
    actual_spend NUMERIC(12,2) NOT NULL DEFAULT 0,
    start_date DATE NOT NULL,
    end_date DATE,
    owner_team_id INTEGER REFERENCES teams(id),
    description TEXT
);

INSERT INTO projects (name, status, priority, budget, actual_spend, start_date, end_date, owner_team_id, description) VALUES
('API Gateway Redesign', 'on_track', 'high', 350000.00, 210000.00, '2025-01-10', '2025-06-30', 1, 'Migrate to event-driven architecture'),
('Mobile App v3.0', 'at_risk', 'high', 680000.00, 520000.00, '2025-02-01', '2025-08-31', 2, 'Major mobile app redesign with new features'),
('Data Lake Migration', 'on_track', 'high', 920000.00, 445000.00, '2025-01-01', '2025-12-31', 3, 'Migrate on-prem data warehouse to cloud data lake'),
('Kubernetes Migration', 'on_track', 'high', 1200000.00, 380000.00, '2025-03-01', '2025-10-31', 4, 'Migrate all services to Kubernetes'),
('Design System 2.0', 'completed', 'medium', 180000.00, 175000.00, '2024-09-01', '2025-03-31', 5, 'Rebuild component library with accessibility focus'),
('Customer 360 Dashboard', 'at_risk', 'high', 280000.00, 410000.00, '2025-04-01', '2025-11-30', 6, 'Unified customer view across all touchpoints'),
('Real-Time Analytics Pipeline', 'on_track', 'high', 720000.00, 290000.00, '2025-05-01', '2026-02-28', 7, 'Stream processing for real-time business metrics'),
('CI/CD Pipeline Overhaul', 'completed', 'medium', 210000.00, 195000.00, '2024-11-01', '2025-04-30', 8, 'Modernize build and deployment pipelines'),
('Automated Regression Suite', 'on_track', 'medium', 160000.00, 95000.00, '2025-06-01', '2025-12-31', 9, 'End-to-end test automation framework'),
('Zero Trust Security', 'blocked', 'high', 480000.00, 120000.00, '2025-03-15', '2025-12-31', 10, 'Implement zero trust network architecture'),
('ML Feature Store', 'on_track', 'medium', 340000.00, 180000.00, '2025-04-15', '2026-01-31', 3, 'Centralized feature store for ML models'),
('API Rate Limiting v2', 'completed', 'low', 85000.00, 82000.00, '2025-01-01', '2025-05-31', 1, 'Enhanced rate limiting with per-customer quotas'),
('React Native Migration', 'at_risk', 'medium', 520000.00, 480000.00, '2025-02-15', '2025-09-30', 2, 'Migrate iOS app from Swift to React Native'),
('Data Governance Framework', 'not_started', 'medium', 290000.00, 0.00, '2025-09-01', '2026-03-31', 3, 'Implement data classification and access controls'),
('Edge Computing POC', 'on_track', 'low', 150000.00, 65000.00, '2025-07-01', '2025-12-31', 4, 'Proof of concept for edge deployment'),
('Chatbot Integration', 'on_track', 'medium', 280000.00, 140000.00, '2025-05-15', '2026-01-15', 5, 'AI chatbot for customer support'),
('Observability Platform', 'at_risk', 'high', 610000.00, 580000.00, '2025-01-15', '2025-08-31', 8, 'Unified logging, metrics, and tracing'),
('Payment Gateway v2', 'blocked', 'high', 750000.00, 210000.00, '2025-06-01', '2026-04-30', 1, 'PCI-compliant payment processing upgrade'),
('Search Re-architecture', 'on_track', 'medium', 430000.00, 220000.00, '2025-04-01', '2025-12-31', 3, 'Elasticsearch to OpenSearch migration'),
('SSO Integration', 'completed', 'high', 190000.00, 185000.00, '2025-02-01', '2025-06-30', 10, 'Enterprise SSO across all internal tools'),
('Performance Optimization', 'on_track', 'medium', 175000.00, 110000.00, '2025-07-15', '2025-12-31', 1, 'Reduce p99 latency by 40% across core APIs'),
('Compliance Audit Tool', 'not_started', 'high', 360000.00, 0.00, '2025-10-01', '2026-06-30', 9, 'Automated compliance checking and reporting'),
('Microservices Decomposition', 'at_risk', 'high', 890000.00, 720000.00, '2024-10-01', '2025-09-30', 4, 'Break monolith into domain services'),
('Internal Developer Portal', 'on_track', 'low', 220000.00, 105000.00, '2025-06-15', '2026-01-31', 8, 'Self-service portal for internal tooling'),
('AI Code Review', 'on_track', 'medium', 195000.00, 60000.00, '2025-08-01', '2026-02-28', 9, 'AI-assisted code review integration'),
('Infrastructure as Code', 'on_track', 'high', 520000.00, 380000.00, '2025-03-20', '2025-11-15', 4, 'Terraform and CloudFormation standardization'),
('Legacy System Modernization', 'at_risk', 'high', 650000.00, 480000.00, '2024-12-01', '2025-10-31', 2, 'Refactor legacy monolithic applications'),
('Cloud Migration Wave 1', 'not_started', 'high', 850000.00, 0.00, '2025-10-15', NULL, 4, 'Move on-premises infrastructure to cloud'),
('API Versioning Strategy', 'not_started', 'medium', 120000.00, 0.00, '2025-11-01', NULL, 1, 'Implement backward-compatible API versioning'),
('Disaster Recovery Plan', 'on_track', 'high', 380000.00, 0.00, '2025-01-15', '2025-12-31', 8, 'Multi-region failover and recovery procedures');

-- =============================================================================
-- SECTION 3: QUARTERLY_REVENUE (72 rows)
-- =============================================================================

CREATE TABLE quarterly_revenue (
    id SERIAL PRIMARY KEY,
    quarter VARCHAR(7) NOT NULL,
    region VARCHAR(20) NOT NULL,
    product_line VARCHAR(50) NOT NULL,
    revenue NUMERIC(12,2) NOT NULL,
    target NUMERIC(12,2) NOT NULL,
    deals_closed INTEGER NOT NULL,
    new_customers INTEGER NOT NULL,
    churn_rate NUMERIC(4,2) NOT NULL
);

INSERT INTO quarterly_revenue (quarter, region, product_line, revenue, target, deals_closed, new_customers, churn_rate) VALUES
-- 2024-Q3 (baseline)
('2024-Q3', 'North America', 'Enterprise Platform',  3600000.00, 3500000.00, 22, 10, 2.80),
('2024-Q3', 'North America', 'SMB Suite',            1550000.00, 1700000.00, 120, 42, 5.20),
('2024-Q3', 'North America', 'API Services',          780000.00,  800000.00, 55, 18, 3.90),
('2024-Q3', 'Europe',        'Enterprise Platform',  2400000.00, 2600000.00, 14,  6, 2.50),
('2024-Q3', 'Europe',        'SMB Suite',            1000000.00, 1100000.00, 82, 28, 5.80),
('2024-Q3', 'Europe',        'API Services',          550000.00,  600000.00, 35, 12, 4.30),
('2024-Q3', 'Asia Pacific',  'Enterprise Platform',  1200000.00, 1500000.00,  8,  4, 2.10),
('2024-Q3', 'Asia Pacific',  'SMB Suite',             650000.00,  750000.00, 50, 22, 6.80),
('2024-Q3', 'Asia Pacific',  'API Services',          350000.00,  420000.00, 25, 0, 4.70),
('2024-Q3', 'Latin America', 'Enterprise Platform',   520000.00,  580000.00,  3,  2, 3.00),
('2024-Q3', 'Latin America', 'SMB Suite',             310000.00,  340000.00, 28, 14, 6.50),
('2024-Q3', 'Latin America', 'API Services',          150000.00,  170000.00, 12,  6, 5.10),
-- 2024-Q4 (seasonal boost ~15% over Q3)
('2024-Q4', 'North America', 'Enterprise Platform',  4000000.00, 3800000.00, 26, 11, 2.40),
('2024-Q4', 'North America', 'SMB Suite',            1750000.00, 1900000.00, 135, 48, 4.80),
('2024-Q4', 'North America', 'API Services',          870000.00,  850000.00, 62, 21, 3.50),
('2024-Q4', 'Europe',        'Enterprise Platform',  2650000.00, 2800000.00, 16,  7, 2.10),
('2024-Q4', 'Europe',        'SMB Suite',            1100000.00, 1200000.00, 90, 32, 5.40),
('2024-Q4', 'Europe',        'API Services',          620000.00,  650000.00, 39, 14, 4.00),
('2024-Q4', 'Asia Pacific',  'Enterprise Platform',  1400000.00, 1650000.00,  9,  5, 1.80),
('2024-Q4', 'Asia Pacific',  'SMB Suite',             730000.00,  820000.00, 56, 25, 6.40),
('2024-Q4', 'Asia Pacific',  'API Services',          400000.00,  470000.00, 28, 10, 4.40),
('2024-Q4', 'Latin America', 'Enterprise Platform',   590000.00,  640000.00,  4,  2, 2.70),
('2024-Q4', 'Latin America', 'SMB Suite',             350000.00,  370000.00, 32, 16, 6.10),
('2024-Q4', 'Latin America', 'API Services',          170000.00,  185000.00, 14,  7, 4.80),
-- 2025-Q1
('2025-Q1', 'North America', 'Enterprise Platform',  4200000.00, 4000000.00, 28, 12, 2.10),
('2025-Q1', 'North America', 'SMB Suite',            1850000.00, 2000000.00, 145, 52, 4.50),
('2025-Q1', 'North America', 'API Services',          920000.00,  900000.00, 67, 23, 3.20),
('2025-Q1', 'Europe',        'Enterprise Platform',  2800000.00, 3000000.00, 18,  8, 1.80),
('2025-Q1', 'Europe',        'SMB Suite',            1200000.00, 1300000.00, 98, 35, 5.10),
('2025-Q1', 'Europe',        'API Services',          650000.00,  700000.00, 42, 15, 3.80),
('2025-Q1', 'Asia Pacific',  'Enterprise Platform',  1500000.00, 1800000.00, 10,  5, 1.50),
('2025-Q1', 'Asia Pacific',  'SMB Suite',             780000.00,  900000.00, 62, 28, 6.20),
('2025-Q1', 'Asia Pacific',  'API Services',          420000.00,  500000.00, 30, 12, 4.10),
('2025-Q1', 'Latin America', 'Enterprise Platform',   650000.00,  700000.00,  5,  3, 2.30),
('2025-Q1', 'Latin America', 'SMB Suite',             380000.00,  400000.00, 35, 18, 5.80),
('2025-Q1', 'Latin America', 'API Services',          180000.00,  200000.00, 15,  8, 4.50),
('2025-Q2', 'North America', 'Enterprise Platform',  4500000.00, 4200000.00, 32, 14, 1.90),
('2025-Q2', 'North America', 'SMB Suite',            2100000.00, 2100000.00, 160, 58, 4.20),
('2025-Q2', 'North America', 'API Services',         1050000.00, 1000000.00, 75, 28, 2.90),
('2025-Q2', 'Europe',        'Enterprise Platform',  3100000.00, 3100000.00, 22, 10, 1.60),
('2025-Q2', 'Europe',        'SMB Suite',            1350000.00, 1400000.00, 108, 40, 4.80),
('2025-Q2', 'Europe',        'API Services',          720000.00,  750000.00, 48, 18, 3.50),
('2025-Q2', 'Asia Pacific',  'Enterprise Platform',  1800000.00, 1900000.00, 14,  7, 1.30),
('2025-Q2', 'Asia Pacific',  'SMB Suite',             920000.00,  950000.00, 72, 32, 5.80),
('2025-Q2', 'Asia Pacific',  'API Services',          510000.00,  550000.00, 36, 15, 3.70),
('2025-Q2', 'Latin America', 'Enterprise Platform',   720000.00,  750000.00,  7,  4, 2.10),
('2025-Q2', 'Latin America', 'SMB Suite',             430000.00,  450000.00, 40, 20, 5.50),
('2025-Q2', 'Latin America', 'API Services',          210000.00,  220000.00, 18, 10, 4.20),
('2025-Q3', 'North America', 'Enterprise Platform',  4800000.00, 4500000.00, 35, 16, 1.70),
('2025-Q3', 'North America', 'SMB Suite',            2300000.00, 2200000.00, 175, 65, 3.90),
('2025-Q3', 'North America', 'API Services',         1180000.00, 1100000.00, 82, 32, 2.70),
('2025-Q3', 'Europe',        'Enterprise Platform',  3400000.00, 3200000.00, 25, 12, 1.50),
('2025-Q3', 'Europe',        'SMB Suite',            1500000.00, 1500000.00, 115, 45, 4.50),
('2025-Q3', 'Europe',        'API Services',          800000.00,  800000.00, 52, 20, 3.30),
('2025-Q3', 'Asia Pacific',  'Enterprise Platform',  2100000.00, 2000000.00, 18,  9, 1.20),
('2025-Q3', 'Asia Pacific',  'SMB Suite',            1080000.00, 1000000.00, 80, 36, 5.40),
('2025-Q3', 'Asia Pacific',  'API Services',          600000.00,  600000.00, 42, 18, 3.40),
('2025-Q3', 'Latin America', 'Enterprise Platform',   820000.00,  800000.00,  9,  5, 1.90),
('2025-Q3', 'Latin America', 'SMB Suite',             490000.00,  500000.00, 45, 22, 5.20),
('2025-Q3', 'Latin America', 'API Services',          250000.00,  250000.00, 22, 12, 3.90),
('2025-Q4', 'North America', 'Enterprise Platform',  5200000.00, 4800000.00, 40, 18, 1.50),
('2025-Q4', 'North America', 'SMB Suite',            2500000.00, 2400000.00, 190, 72, 3.60),
('2025-Q4', 'North America', 'API Services',         1320000.00, 1200000.00, 90, 35, 2.50),
('2025-Q4', 'Europe',        'Enterprise Platform',  3700000.00, 3500000.00, 28, 14, 1.40),
('2025-Q4', 'Europe',        'SMB Suite',            1680000.00, 1600000.00, 125, 50, 4.20),
('2025-Q4', 'Europe',        'API Services',          880000.00,  850000.00, 58, 22, 3.10),
('2025-Q4', 'Asia Pacific',  'Enterprise Platform',  2400000.00, 2200000.00, 22, 11, 1.10),
('2025-Q4', 'Asia Pacific',  'SMB Suite',            1250000.00, 1100000.00, 90, 42, 5.00),
('2025-Q4', 'Asia Pacific',  'API Services',          700000.00,  650000.00, 48, 20, 3.10),
('2025-Q4', 'Latin America', 'Enterprise Platform',   950000.00,  850000.00, 12,  6, 1.70),
('2025-Q4', 'Latin America', 'SMB Suite',             560000.00,  550000.00, 52, 25, 4.80),
('2025-Q4', 'Latin America', 'API Services',          290000.00,  280000.00, 25, 14, 3.60);

-- =============================================================================
-- SECTION 4: MONTHLY_REVENUE (216 rows)
-- =============================================================================

CREATE TABLE monthly_revenue (
    id SERIAL PRIMARY KEY,
    month DATE NOT NULL,
    region VARCHAR(20) NOT NULL,
    product_line VARCHAR(50) NOT NULL,
    revenue NUMERIC(12,2) NOT NULL,
    deals_closed INTEGER NOT NULL,
    pipeline_value NUMERIC(12,2) NOT NULL
);

INSERT INTO monthly_revenue (month, region, product_line, revenue, deals_closed, pipeline_value) VALUES
-- 2024-07
('2024-07-01', 'North America', 'Enterprise Platform', 1180000.00, 7, 1800000.00),
('2024-07-01', 'North America', 'SMB Suite', 500000.00, 39, 720000.00),
('2024-07-01', 'North America', 'API Services', 250000.00, 18, 380000.00),
('2024-07-01', 'Europe', 'Enterprise Platform', 780000.00, 5, 1050000.00),
('2024-07-01', 'Europe', 'SMB Suite', 330000.00, 27, 450000.00),
('2024-07-01', 'Europe', 'API Services', 180000.00, 11, 240000.00),
('2024-07-01', 'Asia Pacific', 'Enterprise Platform', 400000.00, 3, 650000.00),
('2024-07-01', 'Asia Pacific', 'SMB Suite', 210000.00, 17, 300000.00),
('2024-07-01', 'Asia Pacific', 'API Services', 115000.00, 8, 160000.00),
('2024-07-01', 'Latin America', 'Enterprise Platform', 170000.00, 1, 240000.00),
('2024-07-01', 'Latin America', 'SMB Suite', 100000.00, 9, 130000.00),
('2024-07-01', 'Latin America', 'API Services', 48000.00, 4, 65000.00),
-- 2024-08
('2024-08-01', 'North America', 'Enterprise Platform', 1200000.00, 7, 1850000.00),
('2024-08-01', 'North America', 'SMB Suite', 510000.00, 40, 740000.00),
('2024-08-01', 'North America', 'API Services', 255000.00, 18, 390000.00),
('2024-08-01', 'Europe', 'Enterprise Platform', 790000.00, 5, 1080000.00),
('2024-08-01', 'Europe', 'SMB Suite', 335000.00, 28, 460000.00),
('2024-08-01', 'Europe', 'API Services', 182000.00, 12, 250000.00),
('2024-08-01', 'Asia Pacific', 'Enterprise Platform', 410000.00, 3, 670000.00),
('2024-08-01', 'Asia Pacific', 'SMB Suite', 215000.00, 17, 310000.00),
('2024-08-01', 'Asia Pacific', 'API Services', 118000.00, 8, 165000.00),
('2024-08-01', 'Latin America', 'Enterprise Platform', 175000.00, 1, 250000.00),
('2024-08-01', 'Latin America', 'SMB Suite', 102000.00, 9, 135000.00),
('2024-08-01', 'Latin America', 'API Services', 50000.00, 4, 68000.00),
-- 2024-09
('2024-09-01', 'North America', 'Enterprise Platform', 1220000.00, 8, 1900000.00),
('2024-09-01', 'North America', 'SMB Suite', 520000.00, 41, 760000.00),
('2024-09-01', 'North America', 'API Services', 260000.00, 19, 400000.00),
('2024-09-01', 'Europe', 'Enterprise Platform', 800000.00, 5, 1100000.00),
('2024-09-01', 'Europe', 'SMB Suite', 340000.00, 28, 470000.00),
('2024-09-01', 'Europe', 'API Services', 185000.00, 12, 255000.00),
('2024-09-01', 'Asia Pacific', 'Enterprise Platform', 420000.00, 3, 690000.00),
('2024-09-01', 'Asia Pacific', 'SMB Suite', 218000.00, 17, 315000.00),
('2024-09-01', 'Asia Pacific', 'API Services', 120000.00, 9, 170000.00),
('2024-09-01', 'Latin America', 'Enterprise Platform', 178000.00, 1, 255000.00),
('2024-09-01', 'Latin America', 'SMB Suite', 105000.00, 10, 140000.00),
('2024-09-01', 'Latin America', 'API Services', 52000.00, 4, 70000.00),
-- 2024-10
('2024-10-01', 'North America', 'Enterprise Platform', 1260000.00, 9, 1980000.00),
('2024-10-01', 'North America', 'SMB Suite', 540000.00, 42, 790000.00),
('2024-10-01', 'North America', 'API Services', 270000.00, 20, 420000.00),
('2024-10-01', 'Europe', 'Enterprise Platform', 830000.00, 5, 1150000.00),
('2024-10-01', 'Europe', 'SMB Suite', 355000.00, 29, 490000.00),
('2024-10-01', 'Europe', 'API Services', 190000.00, 13, 265000.00),
('2024-10-01', 'Asia Pacific', 'Enterprise Platform', 440000.00, 3, 720000.00),
('2024-10-01', 'Asia Pacific', 'SMB Suite', 225000.00, 18, 330000.00),
('2024-10-01', 'Asia Pacific', 'API Services', 125000.00, 9, 180000.00),
('2024-10-01', 'Latin America', 'Enterprise Platform', 185000.00, 1, 270000.00),
('2024-10-01', 'Latin America', 'SMB Suite', 110000.00, 10, 150000.00),
('2024-10-01', 'Latin America', 'API Services', 55000.00, 5, 74000.00),
-- 2024-11 (pre-holiday spike)
('2024-11-01', 'North America', 'Enterprise Platform', 1320000.00, 9, 2050000.00),
('2024-11-01', 'North America', 'SMB Suite', 565000.00, 44, 830000.00),
('2024-11-01', 'North America', 'API Services', 282000.00, 21, 440000.00),
('2024-11-01', 'Europe', 'Enterprise Platform', 860000.00, 6, 1200000.00),
('2024-11-01', 'Europe', 'SMB Suite', 370000.00, 31, 510000.00),
('2024-11-01', 'Europe', 'API Services', 200000.00, 14, 275000.00),
('2024-11-01', 'Asia Pacific', 'Enterprise Platform', 460000.00, 3, 750000.00),
('2024-11-01', 'Asia Pacific', 'SMB Suite', 235000.00, 19, 345000.00),
('2024-11-01', 'Asia Pacific', 'API Services', 128000.00, 10, 185000.00),
('2024-11-01', 'Latin America', 'Enterprise Platform', 195000.00, 2, 285000.00),
('2024-11-01', 'Latin America', 'SMB Suite', 115000.00, 11, 155000.00),
('2024-11-01', 'Latin America', 'API Services', 57000.00, 5, 78000.00),
-- 2024-12 (peak holiday)
('2024-12-01', 'North America', 'Enterprise Platform', 1380000.00, 10, 2080000.00),
('2024-12-01', 'North America', 'SMB Suite', 590000.00, 46, 860000.00),
('2024-12-01', 'North America', 'API Services', 295000.00, 22, 460000.00),
('2024-12-01', 'Europe', 'Enterprise Platform', 890000.00, 6, 1220000.00),
('2024-12-01', 'Europe', 'SMB Suite', 385000.00, 32, 530000.00),
('2024-12-01', 'Europe', 'API Services', 208000.00, 14, 285000.00),
('2024-12-01', 'Asia Pacific', 'Enterprise Platform', 475000.00, 4, 770000.00),
('2024-12-01', 'Asia Pacific', 'SMB Suite', 242000.00, 20, 355000.00),
('2024-12-01', 'Asia Pacific', 'API Services', 132000.00, 10, 190000.00),
('2024-12-01', 'Latin America', 'Enterprise Platform', 205000.00, 2, 295000.00),
('2024-12-01', 'Latin America', 'SMB Suite', 118000.00, 11, 160000.00),
('2024-12-01', 'Latin America', 'API Services', 59000.00, 5, 80000.00),
-- 2025-01
('2025-01-01', 'North America', 'Enterprise Platform', 1350000.00, 9, 2100000.00),
('2025-01-01', 'North America', 'SMB Suite', 580000.00, 45, 850000.00),
('2025-01-01', 'North America', 'API Services', 290000.00, 22, 450000.00),
('2025-01-01', 'Europe', 'Enterprise Platform', 880000.00, 6, 1200000.00),
('2025-01-01', 'Europe', 'SMB Suite', 380000.00, 32, 520000.00),
('2025-01-01', 'Europe', 'API Services', 210000.00, 14, 280000.00),
('2025-01-01', 'Asia Pacific', 'Enterprise Platform', 480000.00, 3, 800000.00),
('2025-01-01', 'Asia Pacific', 'SMB Suite', 240000.00, 20, 350000.00),
('2025-01-01', 'Asia Pacific', 'API Services', 130000.00, 10, 180000.00),
('2025-01-01', 'Latin America', 'Enterprise Platform', 210000.00, 2, 300000.00),
('2025-01-01', 'Latin America', 'SMB Suite', 120000.00, 11, 160000.00),
('2025-01-01', 'Latin America', 'API Services', 60000.00, 5, 80000.00),
('2025-02-01', 'North America', 'Enterprise Platform', 1420000.00, 10, 2250000.00),
('2025-02-01', 'North America', 'SMB Suite', 610000.00, 48, 920000.00),
('2025-02-01', 'North America', 'API Services', 310000.00, 23, 480000.00),
('2025-02-01', 'Europe', 'Enterprise Platform', 920000.00, 7, 1300000.00),
('2025-02-01', 'Europe', 'SMB Suite', 410000.00, 35, 580000.00),
('2025-02-01', 'Europe', 'API Services', 230000.00, 15, 310000.00),
('2025-02-01', 'Asia Pacific', 'Enterprise Platform', 510000.00, 4, 850000.00),
('2025-02-01', 'Asia Pacific', 'SMB Suite', 260000.00, 22, 390000.00),
('2025-02-01', 'Asia Pacific', 'API Services', 150000.00, 11, 210000.00),
('2025-02-01', 'Latin America', 'Enterprise Platform', 230000.00, 2, 330000.00),
('2025-02-01', 'Latin America', 'SMB Suite', 130000.00, 13, 180000.00),
('2025-02-01', 'Latin America', 'API Services', 70000.00, 6, 95000.00),
('2025-03-01', 'North America', 'Enterprise Platform', 1430000.00, 9, 2100000.00),
('2025-03-01', 'North America', 'SMB Suite', 660000.00, 52, 980000.00),
('2025-03-01', 'North America', 'API Services', 320000.00, 22, 450000.00),
('2025-03-01', 'Europe', 'Enterprise Platform', 1000000.00, 5, 1500000.00),
('2025-03-01', 'Europe', 'SMB Suite', 410000.00, 31, 550000.00),
('2025-03-01', 'Europe', 'API Services', 210000.00, 13, 280000.00),
('2025-03-01', 'Asia Pacific', 'Enterprise Platform', 510000.00, 3, 750000.00),
('2025-03-01', 'Asia Pacific', 'SMB Suite', 260000.00, 20, 360000.00),
('2025-03-01', 'Asia Pacific', 'API Services', 140000.00, 10, 190000.00),
('2025-03-01', 'Latin America', 'Enterprise Platform', 210000.00, 2, 280000.00),
('2025-03-01', 'Latin America', 'SMB Suite', 130000.00, 12, 160000.00),
('2025-03-01', 'Latin America', 'API Services', 70000.00, 5, 85000.00),
('2025-04-01', 'North America', 'Enterprise Platform', 1480000.00, 11, 2300000.00),
('2025-04-01', 'North America', 'SMB Suite', 700000.00, 54, 1050000.00),
('2025-04-01', 'North America', 'API Services', 350000.00, 25, 500000.00),
('2025-04-01', 'Europe', 'Enterprise Platform', 1050000.00, 8, 1600000.00),
('2025-04-01', 'Europe', 'SMB Suite', 460000.00, 37, 620000.00),
('2025-04-01', 'Europe', 'API Services', 240000.00, 16, 320000.00),
('2025-04-01', 'Asia Pacific', 'Enterprise Platform', 600000.00, 5, 900000.00),
('2025-04-01', 'Asia Pacific', 'SMB Suite', 310000.00, 24, 440000.00),
('2025-04-01', 'Asia Pacific', 'API Services', 170000.00, 12, 240000.00),
('2025-04-01', 'Latin America', 'Enterprise Platform', 240000.00, 2, 350000.00),
('2025-04-01', 'Latin America', 'SMB Suite', 150000.00, 14, 200000.00),
('2025-04-01', 'Latin America', 'API Services', 70000.00, 6, 95000.00),
('2025-05-01', 'North America', 'Enterprise Platform', 1500000.00, 11, 2400000.00),
('2025-05-01', 'North America', 'SMB Suite', 730000.00, 56, 1100000.00),
('2025-05-01', 'North America', 'API Services', 360000.00, 26, 530000.00),
('2025-05-01', 'Europe', 'Enterprise Platform', 1050000.00, 7, 1550000.00),
('2025-05-01', 'Europe', 'SMB Suite', 460000.00, 36, 600000.00),
('2025-05-01', 'Europe', 'API Services', 240000.00, 16, 310000.00),
('2025-05-01', 'Asia Pacific', 'Enterprise Platform', 600000.00, 5, 880000.00),
('2025-05-01', 'Asia Pacific', 'SMB Suite', 310000.00, 24, 430000.00),
('2025-05-01', 'Asia Pacific', 'API Services', 170000.00, 12, 230000.00),
('2025-05-01', 'Latin America', 'Enterprise Platform', 240000.00, 2, 340000.00),
('2025-05-01', 'Latin America', 'SMB Suite', 150000.00, 14, 190000.00),
('2025-05-01', 'Latin America', 'API Services', 70000.00, 6, 90000.00),
('2025-06-01', 'North America', 'Enterprise Platform', 1520000.00, 11, 2350000.00),
('2025-06-01', 'North America', 'SMB Suite', 750000.00, 58, 1150000.00),
('2025-06-01', 'North America', 'API Services', 380000.00, 27, 560000.00),
('2025-06-01', 'Europe', 'Enterprise Platform', 1100000.00, 8, 1650000.00),
('2025-06-01', 'Europe', 'SMB Suite', 480000.00, 38, 650000.00),
('2025-06-01', 'Europe', 'API Services', 250000.00, 17, 340000.00),
('2025-06-01', 'Asia Pacific', 'Enterprise Platform', 620000.00, 5, 920000.00),
('2025-06-01', 'Asia Pacific', 'SMB Suite', 320000.00, 25, 460000.00),
('2025-06-01', 'Asia Pacific', 'API Services', 180000.00, 13, 260000.00),
('2025-06-01', 'Latin America', 'Enterprise Platform', 250000.00, 3, 370000.00),
('2025-06-01', 'Latin America', 'SMB Suite', 160000.00, 15, 210000.00),
('2025-06-01', 'Latin America', 'API Services', 80000.00, 7, 105000.00),
('2025-07-01', 'North America', 'Enterprise Platform', 1600000.00, 12, 2500000.00),
('2025-07-01', 'North America', 'SMB Suite', 800000.00, 60, 1250000.00),
('2025-07-01', 'North America', 'API Services', 400000.00, 28, 600000.00),
('2025-07-01', 'Europe', 'Enterprise Platform', 1150000.00, 9, 1750000.00),
('2025-07-01', 'Europe', 'SMB Suite', 500000.00, 39, 700000.00),
('2025-07-01', 'Europe', 'API Services', 270000.00, 18, 370000.00),
('2025-07-01', 'Asia Pacific', 'Enterprise Platform', 650000.00, 6, 980000.00),
('2025-07-01', 'Asia Pacific', 'SMB Suite', 340000.00, 26, 500000.00),
('2025-07-01', 'Asia Pacific', 'API Services', 190000.00, 14, 280000.00),
('2025-07-01', 'Latin America', 'Enterprise Platform', 270000.00, 3, 400000.00),
('2025-07-01', 'Latin America', 'SMB Suite', 170000.00, 16, 240000.00),
('2025-07-01', 'Latin America', 'API Services', 85000.00, 7, 120000.00),
('2025-08-01', 'North America', 'Enterprise Platform', 1600000.00, 12, 2450000.00),
('2025-08-01', 'North America', 'SMB Suite', 760000.00, 58, 1200000.00),
('2025-08-01', 'North America', 'API Services', 390000.00, 27, 580000.00),
('2025-08-01', 'Europe', 'Enterprise Platform', 1130000.00, 8, 1700000.00),
('2025-08-01', 'Europe', 'SMB Suite', 490000.00, 38, 670000.00),
('2025-08-01', 'Europe', 'API Services', 265000.00, 17, 360000.00),
('2025-08-01', 'Asia Pacific', 'Enterprise Platform', 630000.00, 5, 950000.00),
('2025-08-01', 'Asia Pacific', 'SMB Suite', 330000.00, 25, 480000.00),
('2025-08-01', 'Asia Pacific', 'API Services', 185000.00, 13, 270000.00),
('2025-08-01', 'Latin America', 'Enterprise Platform', 260000.00, 3, 380000.00),
('2025-08-01', 'Latin America', 'SMB Suite', 160000.00, 15, 220000.00),
('2025-08-01', 'Latin America', 'API Services', 80000.00, 7, 110000.00),
('2025-09-01', 'North America', 'Enterprise Platform', 1650000.00, 12, 2600000.00),
('2025-09-01', 'North America', 'SMB Suite', 790000.00, 60, 1300000.00),
('2025-09-01', 'North America', 'API Services', 410000.00, 29, 620000.00),
('2025-09-01', 'Europe', 'Enterprise Platform', 1180000.00, 9, 1800000.00),
('2025-09-01', 'Europe', 'SMB Suite', 520000.00, 40, 720000.00),
('2025-09-01', 'Europe', 'API Services', 280000.00, 18, 390000.00),
('2025-09-01', 'Asia Pacific', 'Enterprise Platform', 670000.00, 6, 1020000.00),
('2025-09-01', 'Asia Pacific', 'SMB Suite', 350000.00, 27, 520000.00),
('2025-09-01', 'Asia Pacific', 'API Services', 200000.00, 14, 300000.00),
('2025-09-01', 'Latin America', 'Enterprise Platform', 280000.00, 3, 420000.00),
('2025-09-01', 'Latin America', 'SMB Suite', 180000.00, 16, 260000.00),
('2025-09-01', 'Latin America', 'API Services', 90000.00, 8, 130000.00),
('2025-10-01', 'North America', 'Enterprise Platform', 1700000.00, 13, 2700000.00),
('2025-10-01', 'North America', 'SMB Suite', 820000.00, 63, 1400000.00),
('2025-10-01', 'North America', 'API Services', 430000.00, 30, 650000.00),
('2025-10-01', 'Europe', 'Enterprise Platform', 1220000.00, 10, 1900000.00),
('2025-10-01', 'Europe', 'SMB Suite', 550000.00, 42, 770000.00),
('2025-10-01', 'Europe', 'API Services', 295000.00, 19, 420000.00),
('2025-10-01', 'Asia Pacific', 'Enterprise Platform', 710000.00, 7, 1100000.00),
('2025-10-01', 'Asia Pacific', 'SMB Suite', 370000.00, 29, 570000.00),
('2025-10-01', 'Asia Pacific', 'API Services', 215000.00, 15, 330000.00),
('2025-10-01', 'Latin America', 'Enterprise Platform', 300000.00, 3, 450000.00),
('2025-10-01', 'Latin America', 'SMB Suite', 190000.00, 17, 280000.00),
('2025-10-01', 'Latin America', 'API Services', 95000.00, 8, 140000.00),
('2025-11-01', 'North America', 'Enterprise Platform', 1750000.00, 14, 2800000.00),
('2025-11-01', 'North America', 'SMB Suite', 850000.00, 65, 1450000.00),
('2025-11-01', 'North America', 'API Services', 450000.00, 31, 680000.00),
('2025-11-01', 'Europe', 'Enterprise Platform', 1250000.00, 10, 1950000.00),
('2025-11-01', 'Europe', 'SMB Suite', 570000.00, 43, 800000.00),
('2025-11-01', 'Europe', 'API Services', 310000.00, 20, 450000.00),
('2025-11-01', 'Asia Pacific', 'Enterprise Platform', 740000.00, 7, 1150000.00),
('2025-11-01', 'Asia Pacific', 'SMB Suite', 390000.00, 30, 600000.00),
('2025-11-01', 'Asia Pacific', 'API Services', 230000.00, 16, 360000.00),
('2025-11-01', 'Latin America', 'Enterprise Platform', 320000.00, 4, 480000.00),
('2025-11-01', 'Latin America', 'SMB Suite', 200000.00, 18, 300000.00),
('2025-11-01', 'Latin America', 'API Services', 100000.00, 8, 150000.00),
('2025-12-01', 'North America', 'Enterprise Platform', 1800000.00, 15, 2500000.00),
('2025-12-01', 'North America', 'SMB Suite', 900000.00, 70, 1250000.00),
('2025-12-01', 'North America', 'API Services', 480000.00, 32, 600000.00),
('2025-12-01', 'Europe', 'Enterprise Platform', 1300000.00, 11, 1800000.00),
('2025-12-01', 'Europe', 'SMB Suite', 600000.00, 45, 750000.00),
('2025-12-01', 'Europe', 'API Services', 330000.00, 21, 420000.00),
('2025-12-01', 'Asia Pacific', 'Enterprise Platform', 800000.00, 8, 1050000.00),
('2025-12-01', 'Asia Pacific', 'SMB Suite', 420000.00, 32, 550000.00),
('2025-12-01', 'Asia Pacific', 'API Services', 250000.00, 17, 330000.00),
('2025-12-01', 'Latin America', 'Enterprise Platform', 350000.00, 4, 450000.00),
('2025-12-01', 'Latin America', 'SMB Suite', 220000.00, 20, 280000.00),
('2025-12-01', 'Latin America', 'API Services', 110000.00, 9, 140000.00);

-- =============================================================================
-- SECTION 5: MONTHLY_METRICS (110 rows)
-- =============================================================================

CREATE TABLE monthly_metrics (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    month DATE NOT NULL,
    planned_value NUMERIC(10,2) NOT NULL,
    earned_value NUMERIC(10,2) NOT NULL,
    actual_cost NUMERIC(10,2) NOT NULL,
    story_points_planned INTEGER NOT NULL DEFAULT 0,
    story_points_completed INTEGER NOT NULL DEFAULT 0,
    defects_found INTEGER NOT NULL DEFAULT 0,
    defects_resolved INTEGER NOT NULL DEFAULT 0
);

INSERT INTO monthly_metrics (project_id, month, planned_value, earned_value, actual_cost, story_points_planned, story_points_completed, defects_found, defects_resolved) VALUES
-- PROJECT 1: on_track, $450K budget over 12 months
(1, '2025-01-01', 35000.00, 34000.00, 34500.00, 20, 19, 3, 3),
(1, '2025-02-01', 36000.00, 35500.00, 35800.00, 22, 21, 4, 4),
(1, '2025-03-01', 37000.00, 36500.00, 37100.00, 24, 23, 5, 5),
(1, '2025-04-01', 38000.00, 37500.00, 38200.00, 25, 24, 4, 4),
(1, '2025-05-01', 39000.00, 38500.00, 39100.00, 26, 25, 6, 6),
(1, '2025-06-01', 39500.00, 39000.00, 39400.00, 27, 26, 5, 5),
(1, '2025-07-01', 40000.00, 39500.00, 40100.00, 28, 27, 7, 7),
(1, '2025-08-01', 40500.00, 40000.00, 40300.00, 29, 28, 6, 6),
(1, '2025-09-01', 41000.00, 41000.00, 41200.00, 30, 29, 8, 8),
(1, '2025-10-01', 41500.00, 41500.00, 41600.00, 31, 30, 7, 7),
(1, '2025-11-01', 42000.00, 42000.00, 42100.00, 32, 31, 9, 9),
(1, '2025-12-01', 43500.00, 43500.00, 43500.00, 33, 33, 8, 8),
-- PROJECT 2: at_risk, $680K budget, fell behind from month 5
(2, '2025-01-01', 52000.00, 51000.00, 51500.00, 25, 24, 5, 5),
(2, '2025-02-01', 54000.00, 53500.00, 53800.00, 27, 26, 6, 6),
(2, '2025-03-01', 56000.00, 55500.00, 55900.00, 28, 27, 7, 7),
(2, '2025-04-01', 58000.00, 57000.00, 57500.00, 29, 28, 8, 7),
(2, '2025-05-01', 60000.00, 57000.00, 61000.00, 30, 25, 9, 6),
(2, '2025-06-01', 62000.00, 56000.00, 64000.00, 31, 22, 10, 5),
(2, '2025-07-01', 63000.00, 54000.00, 66000.00, 32, 20, 11, 4),
(2, '2025-08-01', 64000.00, 52000.00, 68000.00, 33, 18, 12, 3),
(2, '2025-09-01', 65000.00, 51000.00, 70000.00, 34, 17, 11, 2),
(2, '2025-10-01', 66000.00, 50000.00, 72000.00, 35, 16, 10, 2),
(2, '2025-11-01', 67000.00, 50000.00, 74000.00, 35, 16, 9, 2),
(2, '2025-12-01', 68000.00, 50000.00, 76000.00, 35, 16, 8, 2),
-- PROJECT 3: on_track, $920K budget, large project, consistent performance
(3, '2025-01-01', 70000.00, 69000.00, 69500.00, 28, 27, 8, 8),
(3, '2025-02-01', 72000.00, 71000.00, 71500.00, 30, 29, 9, 9),
(3, '2025-03-01', 74000.00, 73000.00, 73500.00, 32, 31, 10, 10),
(3, '2025-04-01', 76000.00, 75000.00, 75500.00, 33, 32, 11, 11),
(3, '2025-05-01', 78000.00, 77000.00, 77500.00, 34, 33, 10, 10),
(3, '2025-06-01', 79000.00, 78000.00, 78500.00, 35, 34, 11, 11),
(3, '2025-07-01', 80000.00, 79000.00, 79500.00, 36, 35, 12, 12),
(3, '2025-08-01', 81000.00, 80000.00, 80500.00, 37, 36, 11, 11),
(3, '2025-09-01', 82000.00, 81000.00, 81500.00, 38, 37, 12, 12),
(3, '2025-10-01', 83000.00, 82000.00, 82500.00, 39, 38, 13, 13),
(3, '2025-11-01', 84000.00, 83000.00, 83500.00, 40, 39, 12, 12),
(3, '2025-12-01', 85000.00, 84000.00, 84500.00, 41, 40, 11, 11),
-- PROJECT 4: on_track high budget, ramp-up pattern (assume $1,200K budget)
(4, '2025-01-01', 20000.00, 18000.00, 19000.00, 8, 7, 2, 2),
(4, '2025-02-01', 30000.00, 27000.00, 28500.00, 12, 10, 3, 3),
(4, '2025-03-01', 40000.00, 36000.00, 38000.00, 15, 13, 4, 4),
(4, '2025-04-01', 80000.00, 78000.00, 79000.00, 28, 27, 8, 8),
(4, '2025-05-01', 90000.00, 88000.00, 89000.00, 32, 31, 9, 9),
(4, '2025-06-01', 100000.00, 99000.00, 100000.00, 35, 34, 10, 10),
(4, '2025-07-01', 110000.00, 109000.00, 110000.00, 38, 37, 11, 11),
(4, '2025-08-01', 120000.00, 118000.00, 119000.00, 40, 39, 12, 12),
(4, '2025-09-01', 130000.00, 128000.00, 129000.00, 42, 41, 13, 13),
(4, '2025-10-01', 140000.00, 139000.00, 140000.00, 44, 43, 14, 14),
(4, '2025-11-01', 150000.00, 148000.00, 149000.00, 45, 44, 12, 12),
(4, '2025-12-01', 160000.00, 159000.00, 160000.00, 46, 45, 11, 11),
-- PROJECT 5: completed, $180K budget, early completion
(5, '2025-01-01', 18000.00, 17500.00, 17600.00, 15, 14, 2, 2),
(5, '2025-02-01', 19000.00, 19000.00, 19000.00, 16, 16, 3, 3),
(5, '2025-03-01', 20000.00, 20000.00, 20000.00, 17, 17, 2, 2),
(5, '2025-04-01', 21000.00, 21000.00, 21000.00, 18, 18, 3, 3),
(5, '2025-05-01', 22000.00, 22000.00, 22000.00, 19, 19, 2, 2),
(5, '2025-06-01', 23000.00, 23000.00, 23000.00, 20, 20, 4, 4),
(5, '2025-07-01', 28000.00, 28000.00, 28000.00, 21, 21, 3, 3),
(5, '2025-08-01', 29000.00, 29000.00, 28900.00, 20, 20, 1, 1),
-- PROJECT 6: at_risk over budget, significant overspending
(6, '2025-01-01', 20000.00, 18000.00, 25000.00, 12, 10, 6, 5),
(6, '2025-02-01', 21000.00, 19000.00, 27000.00, 13, 11, 7, 5),
(6, '2025-03-01', 22000.00, 20000.00, 29000.00, 14, 12, 8, 5),
(6, '2025-04-01', 23000.00, 20000.00, 31000.00, 15, 12, 9, 4),
(6, '2025-05-01', 24000.00, 21000.00, 33000.00, 16, 13, 10, 3),
(6, '2025-06-01', 25000.00, 21000.00, 35000.00, 17, 13, 11, 3),
(6, '2025-07-01', 26000.00, 22000.00, 37000.00, 18, 14, 10, 2),
(6, '2025-08-01', 27000.00, 22000.00, 39000.00, 19, 14, 9, 2),
(6, '2025-09-01', 28000.00, 23000.00, 41000.00, 20, 15, 8, 2),
(6, '2025-10-01', 29000.00, 23000.00, 43000.00, 21, 15, 7, 2),
(6, '2025-11-01', 30000.00, 24000.00, 45000.00, 22, 16, 6, 2),
(6, '2025-12-01', 31000.00, 24000.00, 47000.00, 23, 16, 5, 2),
-- PROJECT 10: blocked, $480K budget, stalled from month 4 onwards
(10, '2025-01-01', 38000.00, 36000.00, 37000.00, 20, 19, 4, 4),
(10, '2025-02-01', 39000.00, 38000.00, 38500.00, 22, 21, 5, 5),
(10, '2025-03-01', 40000.00, 40000.00, 40000.00, 24, 23, 6, 6),
(10, '2025-04-01', 41000.00, 40000.00, 42000.00, 25, 23, 8, 2),
(10, '2025-05-01', 42000.00, 40000.00, 44000.00, 26, 23, 7, 1),
(10, '2025-06-01', 43000.00, 40000.00, 45000.00, 27, 23, 6, 1),
(10, '2025-07-01', 44000.00, 40000.00, 46000.00, 28, 23, 7, 1),
(10, '2025-08-01', 45000.00, 40000.00, 47000.00, 29, 23, 8, 0),
(10, '2025-09-01', 46000.00, 40000.00, 48000.00, 30, 23, 9, 0),
(10, '2025-10-01', 47000.00, 40000.00, 49000.00, 31, 23, 10, 0),
(10, '2025-11-01', 48000.00, 40000.00, 50000.00, 32, 23, 9, 0),
(10, '2025-12-01', 49000.00, 40000.00, 51000.00, 33, 23, 8, 0),
-- PROJECT 23: at_risk legacy project, 15 months (Oct 2024 - Dec 2025)
(23, '2024-10-01', 55000.00, 54000.00, 54500.00, 26, 25, 7, 7),
(23, '2024-11-01', 56000.00, 55500.00, 56000.00, 27, 26, 8, 8),
(23, '2024-12-01', 58000.00, 57500.00, 58000.00, 28, 27, 9, 9),
(23, '2025-01-01', 60000.00, 59000.00, 60000.00, 29, 28, 8, 8),
(23, '2025-02-01', 61000.00, 59500.00, 62000.00, 30, 28, 9, 7),
(23, '2025-03-01', 62000.00, 59500.00, 64000.00, 31, 28, 10, 6),
(23, '2025-04-01', 63000.00, 58500.00, 66000.00, 32, 26, 11, 5),
(23, '2025-05-01', 64000.00, 57000.00, 68000.00, 33, 25, 12, 4),
(23, '2025-06-01', 65000.00, 55000.00, 70000.00, 34, 23, 12, 3),
(23, '2025-07-01', 66000.00, 53000.00, 72000.00, 35, 21, 11, 3),
(23, '2025-08-01', 67000.00, 51000.00, 74000.00, 36, 20, 10, 2),
(23, '2025-09-01', 68000.00, 50000.00, 76000.00, 37, 19, 9, 2),
(23, '2025-10-01', 69000.00, 49000.00, 78000.00, 38, 18, 8, 2),
(23, '2025-11-01', 70000.00, 49000.00, 80000.00, 39, 18, 7, 1),
(23, '2025-12-01', 71000.00, 49000.00, 82000.00, 40, 18, 6, 1);

-- =============================================================================
-- SECTION 6: DELIVERABLES (65 rows)
-- =============================================================================

CREATE TABLE deliverables (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('on_track', 'at_risk', 'blocked', 'completed', 'not_started')),
    completion_pct INTEGER NOT NULL CHECK (completion_pct >= 0 AND completion_pct <= 100),
    due_date DATE NOT NULL,
    assigned_team_id INTEGER REFERENCES teams(id),
    category VARCHAR(50) NOT NULL
);

INSERT INTO deliverables (project_id, name, status, completion_pct, due_date, assigned_team_id, category) VALUES
-- PROJECT 1 (5 deliverables: 2 completed, 2 on_track, 1 at_risk)
(1, 'P1 System Architecture Design', 'completed', 100, '2025-02-15', 1, 'Design'),
(1, 'P1 API Endpoint Development Phase 1', 'on_track', 75, '2025-04-30', 2, 'Development'),
(1, 'P1 Integration Testing Suite', 'on_track', 65, '2025-05-15', 3, 'Testing'),
(1, 'P1 Database Schema Optimization', 'completed', 100, '2025-03-01', 4, 'Infrastructure'),
(1, 'P1 Performance Monitoring Setup', 'at_risk', 40, '2025-06-30', 5, 'Operations'),
-- PROJECT 2 (6 deliverables: 1 completed, 2 on_track, 3 at_risk)
(2, 'P2 Initial Requirements Review', 'completed', 100, '2025-01-20', 1, 'Documentation'),
(2, 'P2 UI/UX Design Mockups', 'on_track', 70, '2025-04-30', 2, 'Design'),
(2, 'P2 Backend Service Architecture', 'at_risk', 50, '2025-05-31', 3, 'Development'),
(2, 'P2 Automated Test Framework', 'at_risk', 30, '2025-06-15', 4, 'Testing'),
(2, 'P2 Compliance Documentation', 'at_risk', 25, '2025-07-31', NULL, 'Compliance'),
(2, 'P2 Release Candidate Build', 'on_track', 55, '2025-08-31', 5, 'Release'),
-- PROJECT 3 (6 deliverables: 3 completed, 2 on_track, 1 at_risk)
(3, 'P3 User Research & Analysis', 'completed', 100, '2025-01-15', 1, 'Design'),
(3, 'P3 Data Migration Scripts', 'completed', 100, '2025-02-28', 2, 'Infrastructure'),
(3, 'P3 Core Platform Development', 'on_track', 80, '2025-06-30', 3, 'Development'),
(3, 'P3 Security Audit & Remediation', 'completed', 100, '2025-03-31', 4, 'Compliance'),
(3, 'P3 Staging Deployment Pipeline', 'on_track', 85, '2025-07-15', 5, 'Release'),
(3, 'P3 User Acceptance Testing', 'at_risk', 60, '2025-08-31', 6, 'Testing'),
-- PROJECT 4 (5 deliverables: 2 completed, 2 on_track, 1 not_started)
(4, 'P4 Infrastructure Provisioning', 'completed', 100, '2025-03-15', 7, 'Infrastructure'),
(4, 'P4 API Gateway Setup', 'on_track', 90, '2025-04-30', 8, 'Infrastructure'),
(4, 'P4 Microservices Architecture', 'completed', 100, '2025-05-15', 9, 'Development'),
(4, 'P4 Load Testing & Optimization', 'on_track', 70, '2025-06-30', 10, 'Testing'),
(4, 'P4 Production Runbook Documentation', 'not_started', 0, '2025-09-30', NULL, 'Documentation'),
-- PROJECT 5 (4 deliverables: ALL completed)
(5, 'P5 Requirements Specification', 'completed', 100, '2024-12-01', 1, 'Documentation'),
(5, 'P5 Frontend Development', 'completed', 100, '2025-01-15', 2, 'Development'),
(5, 'P5 Backend Services', 'completed', 100, '2025-02-28', 3, 'Development'),
(5, 'P5 QA & Release', 'completed', 100, '2025-04-15', 4, 'Release'),
-- PROJECT 6 (5 deliverables: 1 completed, 1 on_track, 3 at_risk)
(6, 'P6 Design Phase', 'completed', 100, '2025-02-01', 1, 'Design'),
(6, 'P6 Core Module Development', 'at_risk', 45, '2025-05-31', 2, 'Development'),
(6, 'P6 Integration Layer', 'at_risk', 35, '2025-06-30', 3, 'Development'),
(6, 'P6 System Testing', 'at_risk', 20, '2025-07-31', 4, 'Testing'),
(6, 'P6 Production Deployment', 'on_track', 50, '2025-09-30', 5, 'Release'),
-- PROJECT 7 (5 deliverables: 2 completed, 2 on_track, 1 not_started)
(7, 'P7 Business Process Analysis', 'completed', 100, '2025-01-10', 1, 'Documentation'),
(7, 'P7 System Design Document', 'completed', 100, '2025-02-20', 2, 'Design'),
(7, 'P7 Feature Development Batch 1', 'on_track', 75, '2025-05-15', 3, 'Development'),
(7, 'P7 Integration Testing', 'on_track', 60, '2025-06-30', 4, 'Testing'),
(7, 'P7 Training Materials', 'not_started', 0, '2025-08-31', 5, 'Documentation'),
-- PROJECT 9 (5 deliverables: 1 completed, 2 on_track, 2 at_risk)
(9, 'P9 Requirements Gathering', 'completed', 100, '2025-01-30', 1, 'Documentation'),
(9, 'P9 UI Design & Prototyping', 'on_track', 80, '2025-03-31', 2, 'Design'),
(9, 'P9 Backend API Development', 'at_risk', 55, '2025-05-31', 3, 'Development'),
(9, 'P9 Database Design', 'at_risk', 65, '2025-04-30', 4, 'Infrastructure'),
(9, 'P9 Regression Testing', 'on_track', 40, '2025-07-31', 5, 'Testing'),
-- PROJECT 10 (5 deliverables: ALL blocked)
(10, 'P10 Stakeholder Sign-off', 'blocked', 25, '2025-03-31', 1, 'Documentation'),
(10, 'P10 Technical Architecture', 'blocked', 30, '2025-04-30', 2, 'Design'),
(10, 'P10 Development Phase 1', 'blocked', 15, '2025-06-30', 3, 'Development'),
(10, 'P10 Quality Assurance', 'blocked', 10, '2025-07-31', 4, 'Testing'),
(10, 'P10 Deployment Preparation', 'blocked', 0, '2025-09-30', 5, 'Release'),
-- PROJECT 11 (4 deliverables: 1 completed, 2 on_track, 1 not_started)
(11, 'P11 Competitive Analysis', 'completed', 100, '2025-02-14', 1, 'Documentation'),
(11, 'P11 Product Design', 'on_track', 95, '2025-04-30', 2, 'Design'),
(11, 'P11 Development & QA', 'on_track', 50, '2025-07-31', 3, 'Development'),
(11, 'P11 Launch Planning', 'not_started', 0, '2025-08-31', 4, 'Release'),
-- PROJECT 15 (5 deliverables: 2 completed, 2 on_track, 1 at_risk)
(15, 'P15 Strategy & Planning', 'completed', 100, '2025-01-31', 1, 'Documentation'),
(15, 'P15 Platform Architecture', 'completed', 100, '2025-02-28', 2, 'Infrastructure'),
(15, 'P15 Core Development', 'on_track', 70, '2025-06-30', 3, 'Development'),
(15, 'P15 Performance Testing', 'on_track', 85, '2025-07-15', 4, 'Testing'),
(15, 'P15 Deployment & Ops', 'at_risk', 30, '2025-08-31', 5, 'Operations'),
-- PROJECT 16 (5 deliverables: 2 completed, 2 on_track, 1 at_risk)
(16, 'P16 Security Assessment', 'completed', 100, '2025-02-28', 1, 'Compliance'),
(16, 'P16 Frontend Components', 'on_track', 99, '2025-05-31', 2, 'Development'),
(16, 'P16 Backend Services', 'completed', 100, '2025-04-15', 3, 'Development'),
(16, 'P16 Integration Testing', 'on_track', 75, '2025-06-30', 4, 'Testing'),
(16, 'P16 Documentation', 'at_risk', 50, '2025-08-31', 5, 'Documentation'),
-- PROJECT 17 (4 deliverables: 1 completed, 2 on_track, 1 blocked)
(17, 'P17 Scope & Charter', 'completed', 100, '2025-01-15', 1, 'Documentation'),
(17, 'P17 Design Phase', 'on_track', 85, '2025-04-30', 2, 'Design'),
(17, 'P17 Development', 'blocked', 20, '2025-07-31', 3, 'Development'),
(17, 'P17 Delivery Preparation', 'on_track', 40, '2025-08-31', 4, 'Release'),
-- PROJECT 18 (5 deliverables: 2 completed, 2 on_track, 1 at_risk)
(18, 'P18 Research & Discovery', 'completed', 100, '2025-02-01', 1, 'Documentation'),
(18, 'P18 Technical Specifications', 'completed', 100, '2025-02-28', 2, 'Design'),
(18, 'P18 Build & Development', 'on_track', 60, '2025-07-31', 3, 'Development'),
(18, 'P18 UAT & Sign-off', 'on_track', 35, '2025-08-31', 4, 'Testing'),
(18, 'P18 Go-Live Activities', 'at_risk', 15, '2025-09-30', 5, 'Release'),
-- PROJECT 19 (4 deliverables: 1 completed, 2 on_track, 1 not_started)
(19, 'P19 Vision & Approach', 'completed', 100, '2025-01-31', 1, 'Documentation'),
(19, 'P19 Architecture & Design', 'on_track', 80, '2025-04-30', 2, 'Infrastructure'),
(19, 'P19 Implementation', 'on_track', 55, '2025-08-31', 3, 'Development'),
(19, 'P19 Handoff & Support', 'not_started', 0, '2025-10-31', 4, 'Operations'),
-- PROJECT 23 (6 deliverables: 2 completed, 2 on_track, 2 at_risk)
(23, 'P23 Legacy System Assessment', 'completed', 100, '2024-11-30', 1, 'Documentation'),
(23, 'P23 Migration Planning', 'completed', 100, '2025-01-31', 2, 'Design'),
(23, 'P23 Data Migration', 'on_track', 90, '2025-05-31', 3, 'Infrastructure'),
(23, 'P23 Application Upgrades', 'at_risk', 45, '2025-07-31', 4, 'Development'),
(23, 'P23 Testing & Validation', 'on_track', 70, '2025-08-31', 5, 'Testing'),
(23, 'P23 Cutover & Support', 'at_risk', 25, '2025-10-31', 6, 'Operations'),
-- PROJECT 24 (4 deliverables: 1 completed, 2 on_track, 1 not_started)
(24, 'P24 Project Charter', 'completed', 100, '2025-01-15', 1, 'Documentation'),
(24, 'P24 Solution Design', 'on_track', 78, '2025-04-30', 2, 'Design'),
(24, 'P24 Development & Build', 'on_track', 45, '2025-08-31', 3, 'Development'),
(24, 'P24 Testing & Verification', 'not_started', 0, '2025-09-30', 4, 'Testing'),
-- PROJECT 25 (4 deliverables: 2 completed, 1 on_track, 1 blocked)
(25, 'P25 Requirements Definition', 'completed', 100, '2025-01-31', 1, 'Documentation'),
(25, 'P25 Design & Prototyping', 'completed', 100, '2025-03-15', 2, 'Design'),
(25, 'P25 Development Sprint Series', 'on_track', 65, '2025-08-31', 3, 'Development'),
(25, 'P25 Infrastructure & Deployment', 'blocked', 10, '2025-09-30', 4, 'Infrastructure');

-- =============================================================================
-- SECTION 7: BUDGET BREAKDOWN (90 rows)
-- =============================================================================

CREATE TABLE budget_breakdown (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    phase VARCHAR(30) NOT NULL,
    allocated_budget NUMERIC(12,2) NOT NULL,
    spent_budget NUMERIC(12,2) NOT NULL DEFAULT 0
);

INSERT INTO budget_breakdown (project_id, phase, allocated_budget, spent_budget) VALUES
-- PROJECT 1 ($450K budget)
(1, 'Planning', 15000.00, 15000.00),
(1, 'Design', 45000.00, 45000.00),
(1, 'Development', 200000.00, 190000.00),
(1, 'Testing', 80000.00, 75000.00),
(1, 'Deployment', 40000.00, 30000.00),
(1, 'Maintenance', 30000.00, 15000.00),
(1, 'Contingency', 30000.00, 10000.00),
(1, 'Training', 10000.00, 5000.00),
-- PROJECT 2 ($680K budget)
(2, 'Planning', 25000.00, 25000.00),
(2, 'Design', 70000.00, 70000.00),
(2, 'Development', 300000.00, 250000.00),
(2, 'Testing', 120000.00, 100000.00),
(2, 'Deployment', 60000.00, 40000.00),
(2, 'Contingency', 50000.00, 25000.00),
(2, 'Support', 55000.00, 20000.00),
-- PROJECT 3 ($920K budget)
(3, 'Planning', 30000.00, 30000.00),
(3, 'Design', 100000.00, 100000.00),
(3, 'Development', 420000.00, 410000.00),
(3, 'Testing', 180000.00, 170000.00),
(3, 'Deployment', 80000.00, 60000.00),
(3, 'Maintenance', 50000.00, 25000.00),
(3, 'Contingency', 50000.00, 20000.00),
(3, 'Training', 20000.00, 10000.00),
-- PROJECT 4 ($1,200K budget)
(4, 'Planning', 40000.00, 40000.00),
(4, 'Design', 120000.00, 120000.00),
(4, 'Development', 600000.00, 500000.00),
(4, 'Testing', 200000.00, 150000.00),
(4, 'Deployment', 120000.00, 80000.00),
(4, 'Infrastructure', 90000.00, 60000.00),
(4, 'Contingency', 90000.00, 30000.00),
(4, 'Support', 40000.00, 10000.00),
-- PROJECT 5 ($180K budget - completed)
(5, 'Planning', 8000.00, 8000.00),
(5, 'Design', 20000.00, 20000.00),
(5, 'Development', 90000.00, 90000.00),
(5, 'Testing', 30000.00, 30000.00),
(5, 'Deployment', 15000.00, 15000.00),
(5, 'Support', 10000.00, 8000.00),
(5, 'Training', 5000.00, 5000.00),
(5, 'Contingency', 2000.00, 2000.00),
-- PROJECT 6 ($280K budget)
(6, 'Planning', 10000.00, 10000.00),
(6, 'Design', 35000.00, 35000.00),
(6, 'Development', 130000.00, 130000.00),
(6, 'Testing', 50000.00, 35000.00),
(6, 'Deployment', 25000.00, 15000.00),
(6, 'Contingency', 20000.00, 10000.00),
(6, 'Licensing', 8000.00, 8000.00),
(6, 'Support', 2000.00, 0.00),
-- PROJECT 10 ($480K budget - blocked)
(10, 'Planning', 20000.00, 20000.00),
(10, 'Design', 60000.00, 50000.00),
(10, 'Development', 250000.00, 100000.00),
(10, 'Testing', 80000.00, 20000.00),
(10, 'Deployment', 40000.00, 5000.00),
(10, 'Contingency', 25000.00, 10000.00),
(10, 'Support', 5000.00, 0.00),
-- PROJECT 23 ($890K budget - legacy)
(23, 'Planning', 25000.00, 25000.00),
(23, 'Design', 80000.00, 80000.00),
(23, 'Development', 400000.00, 320000.00),
(23, 'Testing', 150000.00, 120000.00),
(23, 'Deployment', 100000.00, 60000.00),
(23, 'Maintenance', 70000.00, 40000.00),
(23, 'Contingency', 55000.00, 30000.00),
(23, 'Support', 10000.00, 5000.00),
-- PROJECT 15 ($560K budget - large)
(15, 'Planning', 18000.00, 18000.00),
(15, 'Design', 65000.00, 65000.00),
(15, 'Development', 280000.00, 240000.00),
(15, 'Testing', 100000.00, 80000.00),
(15, 'Deployment', 60000.00, 40000.00),
(15, 'Infrastructure', 15000.00, 10000.00),
(15, 'Contingency', 15000.00, 8000.00),
(15, 'Training', 7000.00, 3000.00),
-- PROJECT 25 ($340K budget)
(25, 'Planning', 12000.00, 12000.00),
(25, 'Design', 45000.00, 45000.00),
(25, 'Development', 160000.00, 110000.00),
(25, 'Testing', 60000.00, 40000.00),
(25, 'Deployment', 35000.00, 15000.00),
(25, 'Infrastructure', 20000.00, 10000.00),
(25, 'Contingency', 5000.00, 2000.00),
(25, 'Support', 3000.00, 0.00);

-- =============================================================================
-- SECTION 8: RESOURCE ALLOCATION (120 rows)
-- =============================================================================

CREATE TABLE resource_allocation (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    project_id INTEGER NOT NULL REFERENCES projects(id),
    month DATE NOT NULL,
    allocated_hours NUMERIC(6,1) NOT NULL,
    actual_hours NUMERIC(6,1) NOT NULL,
    utilization_pct NUMERIC(5,2) GENERATED ALWAYS AS (
        CASE WHEN allocated_hours > 0 THEN ROUND((actual_hours / allocated_hours) * 100, 2) ELSE 0 END
    ) STORED
);

INSERT INTO resource_allocation (team_id, project_id, month, allocated_hours, actual_hours)
VALUES
-- October 2024
(1, 5, '2024-10-01', 160, 168),
(1, 8, '2024-10-01', 80, 84),
(2, 3, '2024-10-01', 160, 128),
(2, 12, '2024-10-01', 80, 64),
(3, 7, '2024-10-01', 160, 160),
(4, 2, '2024-10-01', 240, 228),
(4, 15, '2024-10-01', 120, 114),
(5, 1, '2024-10-01', 160, 144),
(6, 18, '2024-10-01', 120, 120),
(7, 9, '2024-10-01', 160, 96),
(8, 11, '2024-10-01', 160, 128),
(9, 20, '2024-10-01', 140, 140),
(10, 4, '2024-10-01', 160, 144),
-- November 2024
(1, 5, '2024-11-01', 160, 171),
(1, 8, '2024-11-01', 80, 85),
(2, 3, '2024-11-01', 160, 140),
(2, 12, '2024-11-01', 80, 70),
(3, 7, '2024-11-01', 160, 158),
(3, 14, '2024-11-01', 80, 80),
(4, 2, '2024-11-01', 240, 240),
(4, 15, '2024-11-01', 120, 120),
(5, 1, '2024-11-01', 160, 144),
(6, 18, '2024-11-01', 120, 108),
(7, 9, '2024-11-01', 160, 99),
(8, 11, '2024-11-01', 160, 208),
(9, 20, '2024-11-01', 140, 126),
(10, 4, '2024-11-01', 160, 160),
-- December 2024
(1, 5, '2024-12-01', 160, 166),
(1, 8, '2024-12-01', 80, 82),
(2, 3, '2024-12-01', 160, 150),
(2, 12, '2024-12-01', 80, 75),
(3, 7, '2024-12-01', 160, 160),
(4, 2, '2024-12-01', 240, 216),
(5, 1, '2024-12-01', 160, 152),
(6, 18, '2024-12-01', 120, 120),
(7, 9, '2024-12-01', 160, 96),
(8, 11, '2024-12-01', 160, 144),
(9, 20, '2024-12-01', 140, 140),
(10, 4, '2024-12-01', 160, 140),
-- January 2025
(1, 5, '2025-01-01', 160, 169),
(1, 8, '2025-01-01', 80, 84),
(2, 3, '2025-01-01', 160, 156),
(2, 12, '2025-01-01', 80, 78),
(3, 7, '2025-01-01', 160, 162),
(3, 14, '2025-01-01', 80, 76),
(4, 2, '2025-01-01', 240, 234),
(4, 15, '2025-01-01', 120, 117),
(5, 1, '2025-01-01', 160, 160),
(6, 18, '2025-01-01', 120, 114),
(7, 9, '2025-01-01', 160, 98),
(8, 11, '2025-01-01', 160, 130),
(9, 20, '2025-01-01', 140, 140),
(10, 4, '2025-01-01', 160, 148),
-- February 2025
(1, 5, '2025-02-01', 160, 168),
(1, 8, '2025-02-01', 80, 86),
(2, 3, '2025-02-01', 160, 168),
(2, 12, '2025-02-01', 80, 84),
(3, 7, '2025-02-01', 160, 160),
(4, 2, '2025-02-01', 240, 228),
(5, 1, '2025-02-01', 160, 144),
(6, 18, '2025-02-01', 120, 120),
(7, 9, '2025-02-01', 160, 98),
(8, 11, '2025-02-01', 160, 224),
(9, 20, '2025-02-01', 140, 140),
(10, 4, '2025-02-01', 160, 148),
-- March 2025
(1, 5, '2025-03-01', 160, 170),
(1, 8, '2025-03-01', 80, 83),
(2, 3, '2025-03-01', 160, 144),
(2, 12, '2025-03-01', 80, 72),
(3, 7, '2025-03-01', 160, 158),
(3, 14, '2025-03-01', 80, 80),
(4, 2, '2025-03-01', 240, 240),
(4, 15, '2025-03-01', 120, 120),
(5, 1, '2025-03-01', 160, 160),
(6, 18, '2025-03-01', 120, 108),
(7, 9, '2025-03-01', 160, 96),
(8, 11, '2025-03-01', 160, 128),
(9, 20, '2025-03-01', 140, 140),
(10, 4, '2025-03-01', 160, 144),
-- April 2025
(1, 5, '2025-04-01', 160, 167),
(1, 8, '2025-04-01', 80, 84),
(2, 3, '2025-04-01', 160, 166),
(2, 12, '2025-04-01', 80, 82),
(3, 7, '2025-04-01', 160, 160),
(4, 2, '2025-04-01', 240, 228),
(4, 15, '2025-04-01', 120, 114),
(5, 1, '2025-04-01', 160, 152),
(6, 18, '2025-04-01', 120, 120),
(7, 9, '2025-04-01', 160, 98),
(8, 11, '2025-04-01', 160, 208),
(9, 20, '2025-04-01', 140, 140),
(10, 4, '2025-04-01', 160, 148),
-- May 2025
(1, 5, '2025-05-01', 160, 169),
(1, 8, '2025-05-01', 80, 85),
(2, 3, '2025-05-01', 160, 184),
(2, 12, '2025-05-01', 80, 92),
(3, 7, '2025-05-01', 160, 162),
(3, 14, '2025-05-01', 80, 78),
(4, 2, '2025-05-01', 240, 240),
(4, 15, '2025-05-01', 120, 120),
(5, 1, '2025-05-01', 160, 160),
(6, 18, '2025-05-01', 120, 114),
(7, 9, '2025-05-01', 160, 97),
(8, 11, '2025-05-01', 160, 144),
(9, 20, '2025-05-01', 140, 140),
(10, 4, '2025-05-01', 160, 160),
-- June 2025
(1, 5, '2025-06-01', 160, 168),
(1, 8, '2025-06-01', 80, 84),
(2, 3, '2025-06-01', 160, 176),
(2, 12, '2025-06-01', 80, 88),
(3, 7, '2025-06-01', 160, 160),
(3, 14, '2025-06-01', 80, 80),
(4, 2, '2025-06-01', 240, 234),
(4, 15, '2025-06-01', 120, 117),
(5, 1, '2025-06-01', 160, 144),
(6, 18, '2025-06-01', 120, 120),
(7, 9, '2025-06-01', 160, 96),
(8, 11, '2025-06-01', 160, 224),
(9, 20, '2025-06-01', 140, 140),
(10, 4, '2025-06-01', 160, 148),
-- July 2025
(1, 5, '2025-07-01', 160, 170),
(1, 8, '2025-07-01', 80, 86),
(2, 3, '2025-07-01', 160, 160),
(2, 12, '2025-07-01', 80, 80),
(3, 7, '2025-07-01', 160, 158),
(4, 2, '2025-07-01', 240, 228),
(5, 1, '2025-07-01', 160, 160),
(6, 18, '2025-07-01', 120, 108),
(7, 9, '2025-07-01', 160, 98),
(8, 11, '2025-07-01', 160, 128),
(9, 20, '2025-07-01', 140, 140),
(10, 4, '2025-07-01', 160, 144),
-- August 2025
(1, 5, '2025-08-01', 160, 169),
(1, 8, '2025-08-01', 80, 83),
(2, 3, '2025-08-01', 160, 152),
(2, 12, '2025-08-01', 80, 76),
(3, 7, '2025-08-01', 160, 160),
(3, 14, '2025-08-01', 80, 80),
(4, 2, '2025-08-01', 240, 240),
(4, 15, '2025-08-01', 120, 120),
(5, 1, '2025-08-01', 160, 144),
(6, 18, '2025-08-01', 120, 114),
(7, 9, '2025-08-01', 160, 0),
(8, 11, '2025-08-01', 160, 208),
(9, 20, '2025-08-01', 140, 140),
(10, 4, '2025-08-01', 160, 148),
-- September 2025
(1, 5, '2025-09-01', 160, 168),
(1, 8, '2025-09-01', 80, 84),
(2, 3, '2025-09-01', 160, 170),
(2, 12, '2025-09-01', 80, 86),
(3, 7, '2025-09-01', 160, 160),
(4, 2, '2025-09-01', 240, 228),
(4, 15, '2025-09-01', 120, 114),
(5, 1, '2025-09-01', 160, 160),
(6, 18, '2025-09-01', 120, 120),
(7, 9, '2025-09-01', 160, 0),
(8, 11, '2025-09-01', 160, 144),
(9, 20, '2025-09-01', 140, 140),
(10, 4, '2025-09-01', 160, 150);

-- =============================================================================
-- SECTION 9: INCIDENTS (50 rows)
-- =============================================================================

CREATE TABLE incidents (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    title VARCHAR(200) NOT NULL,
    severity VARCHAR(10) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    status VARCHAR(15) NOT NULL CHECK (status IN ('open', 'investigating', 'resolved', 'closed')),
    created_date DATE NOT NULL,
    resolved_date DATE,
    resolution_hours NUMERIC(6,1),
    assigned_team_id INTEGER REFERENCES teams(id)
);

INSERT INTO incidents (project_id, title, severity, status, created_date, resolved_date, resolution_hours, assigned_team_id)
VALUES
-- CRITICAL INCIDENTS (6 total)
(2, 'Payment processing service timeout errors affecting checkout', 'critical', 'open', '2025-07-01', NULL, NULL, 1),
(5, 'Database connection pool exhaustion during peak load', 'critical', 'resolved', '2024-11-10', '2024-11-10', 8.0, 4),
(3, 'Authentication token expiration causing widespread logout', 'critical', 'resolved', '2025-01-15', '2025-01-15', 4.5, 2),
(8, 'API rate limiter misconfiguration blocking legitimate requests', 'critical', 'resolved', '2025-02-20', '2025-02-20', 2.5, 6),
(12, 'Cache invalidation failure causing stale data propagation', 'critical', 'resolved', '2025-03-08', '2025-03-08', 6.0, 3),
(15, 'Message queue deadlock preventing order processing', 'critical', 'resolved', '2025-05-12', '2025-05-12', 3.0, 4),
-- HIGH SEVERITY INCIDENTS (10 total)
(7, 'Search indexing lag exceeding 30 minutes', 'high', 'investigating', '2025-06-15', NULL, NULL, 7),
(18, 'Email notification delivery delay (batch processing)', 'high', 'investigating', '2025-06-20', NULL, NULL, 5),
(1, 'Analytics dashboard response time degradation', 'high', 'resolved', '2024-11-15', '2024-11-16', 18.0, 8),
(9, 'File upload service intermittent 500 errors', 'high', 'resolved', '2024-12-05', '2024-12-06', 24.0, 9),
(14, 'Database query timeout on user profile page', 'high', 'resolved', '2025-01-22', '2025-01-23', 28.0, 3),
(11, 'Webhook signature validation failures', 'high', 'resolved', '2025-02-10', '2025-02-11', 20.0, 6),
(4, 'SSL certificate renewal automation failed', 'high', 'resolved', '2025-04-01', '2025-04-02', 32.0, 4),
(20, 'GraphQL query complexity attack causing resource exhaustion', 'high', 'resolved', '2025-05-25', '2025-05-26', 16.0, 2),
(6, 'Scheduled job execution failure in async worker', 'high', 'resolved', '2025-06-10', '2025-06-11', 22.0, 8),
(13, 'Data export functionality producing corrupt CSV files', 'high', 'resolved', '2025-08-05', '2025-08-06', 26.0, 5),
-- MEDIUM SEVERITY INCIDENTS (18 total)
(10, 'Mobile app version compatibility warning misleading users', 'medium', 'resolved', '2024-11-20', '2024-11-22', 48.0, 2),
(16, 'Report generation timeout for large datasets (>100k rows)', 'medium', 'resolved', '2024-12-08', '2024-12-10', 52.0, 7),
(19, 'Typo in error message displayed to users', 'medium', 'resolved', '2025-01-05', '2025-01-06', 24.0, 9),
(3, 'Pagination offset calculation error in API', 'medium', 'resolved', '2025-01-28', '2025-01-30', 44.0, 2),
(5, 'Duplicate entry detection missing edge case', 'medium', 'resolved', '2025-02-14', '2025-02-16', 40.0, 1),
(8, 'Theme toggle preference not persisting across sessions', 'medium', 'resolved', '2025-03-01', '2025-03-03', 56.0, 2),
(21, 'Inconsistent date formatting across UI components', 'medium', 'resolved', '2025-03-15', '2025-03-17', 36.0, 9),
(4, 'Missing input validation on form field', 'medium', 'resolved', '2025-04-10', '2025-04-12', 48.0, 6),
(11, 'Slow regex pattern in user search functionality', 'medium', 'resolved', '2025-04-22', '2025-04-24', 50.0, 3),
(7, 'Sidebar menu not expanding on mobile devices', 'medium', 'resolved', '2025-05-05', '2025-05-07', 32.0, 2),
(17, 'Export feature using deprecated API endpoint', 'medium', 'resolved', '2025-06-15', '2025-06-17', 46.0, 4),
(9, 'Batch email sending rate limit being hit', 'medium', 'resolved', '2025-06-15', '2025-06-17', 42.0, 8),
(2, 'Floating point precision issue in financial calculations', 'medium', 'resolved', '2025-06-15', '2025-06-18', 58.0, 6),
(12, 'Memory leak in background service thread', 'medium', 'resolved', '2025-06-15', '2025-06-19', 62.0, 10),
(14, 'Incorrect timezone conversion in scheduled reports', 'medium', 'resolved', '2025-07-02', '2025-07-04', 54.0, 7),
(6, 'Missing NULL check in data transformation pipeline', 'medium', 'resolved', '2025-07-15', '2025-07-17', 38.0, 3),
(18, 'Sort order inconsistency in dropdown options', 'medium', 'resolved', '2025-08-10', '2025-08-12', 44.0, 5),
(25, 'Image optimization not working for PNG files', 'medium', 'resolved', '2025-09-01', '2025-09-02', 0.5, 1),
-- LOW SEVERITY INCIDENTS (16 total)
(27, 'Typo in footer copyright year', 'low', 'open', '2025-06-15', NULL, NULL, NULL),
(24, 'Whitespace inconsistency in CSS output', 'low', 'closed', '2024-11-25', '2024-11-26', 8.0, 9),
(26, 'Unused import statement in test file', 'low', 'closed', '2024-12-12', '2024-12-14', 42.0, 6),
(5, 'Documentation link pointing to outdated page', 'low', 'closed', '2025-01-10', '2025-01-11', 16.0, NULL),
(22, 'Button hover state color slightly off on Safari', 'low', 'closed', '2025-01-30', '2025-02-05', 72.0, 8),
(10, 'Console warning about deprecated lifecycle method', 'low', 'closed', '2025-02-18', '2025-02-19', 12.0, 2),
(15, 'Tooltip text overlapping on narrow screens', 'low', 'closed', '2025-03-12', '2025-03-13', 10.0, 7),
(20, 'Minor grammar error in help documentation', 'low', 'closed', '2025-03-25', '2025-03-27', 18.0, NULL),
(30, 'Duplicate class name in CSS stylesheet', 'low', 'closed', '2025-04-05', '2025-04-08', 56.0, 4),
(8, 'Missing alt text on decorative image element', 'low', 'closed', '2025-04-20', '2025-04-21', 6.0, 9),
(13, 'Inconsistent indentation in JSON config file', 'low', 'closed', '2025-05-10', '2025-05-11', 14.0, 3),
(19, 'Old company logo still used in one email template', 'low', 'closed', '2025-05-30', '2025-05-31', 4.0, 5),
(23, 'Browser console shows deprecation warning', 'low', 'closed', '2025-06-08', '2025-06-09', 22.0, 2),
(28, 'Incorrect field label capitalization', 'low', 'closed', '2025-07-20', '2025-07-21', 8.0, 6),
(29, 'Temporary test data visible in production logs', 'low', 'closed', '2025-08-15', '2025-08-16', 10.0, 10),
(27, 'Unused variable in batch processing script', 'low', 'closed', '2025-09-10', '2025-09-11', 20.0, 3);

-- =============================================================================
-- SECTION 10: INDEXES
-- =============================================================================

CREATE INDEX idx_monthly_metrics_project_id ON monthly_metrics(project_id);
CREATE INDEX idx_monthly_metrics_month ON monthly_metrics(month);
CREATE INDEX idx_monthly_revenue_month ON monthly_revenue(month);
CREATE INDEX idx_monthly_revenue_region ON monthly_revenue(region);
CREATE INDEX idx_monthly_revenue_product_line ON monthly_revenue(product_line);
CREATE INDEX idx_deliverables_project_id ON deliverables(project_id);
CREATE INDEX idx_deliverables_status ON deliverables(status);
CREATE INDEX idx_deliverables_category ON deliverables(category);
CREATE INDEX idx_resource_allocation_team_id ON resource_allocation(team_id);
CREATE INDEX idx_resource_allocation_project_id ON resource_allocation(project_id);
CREATE INDEX idx_resource_allocation_month ON resource_allocation(month);
CREATE INDEX idx_resource_allocation_team_month ON resource_allocation(team_id, month);
CREATE INDEX idx_incidents_project_id ON incidents(project_id);
CREATE INDEX idx_incidents_severity ON incidents(severity);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_created_date ON incidents(created_date);
CREATE INDEX idx_incidents_severity_created ON incidents(severity, created_date);
CREATE INDEX idx_incidents_assigned_team_id ON incidents(assigned_team_id);
CREATE INDEX idx_quarterly_revenue_quarter ON quarterly_revenue(quarter);
CREATE INDEX idx_quarterly_revenue_region ON quarterly_revenue(region);
CREATE INDEX idx_quarterly_revenue_product_line ON quarterly_revenue(product_line);
CREATE INDEX idx_budget_breakdown_project_id ON budget_breakdown(project_id);
CREATE INDEX idx_budget_breakdown_phase ON budget_breakdown(phase);

-- =============================================================================
-- SECTION 11: VERIFICATION QUERY
-- =============================================================================
-- Purpose: Verify data integrity and row counts across all tables
-- Usage: Uncomment and run to validate seed data completion
-- Expected output: Total of all table counts should match documented values

/*
SELECT
    'teams' AS table_name, COUNT(*) AS row_count FROM teams
UNION ALL
SELECT 'projects', COUNT(*) FROM projects
UNION ALL
SELECT 'monthly_metrics', COUNT(*) FROM monthly_metrics
UNION ALL
SELECT 'monthly_revenue', COUNT(*) FROM monthly_revenue
UNION ALL
SELECT 'deliverables', COUNT(*) FROM deliverables
UNION ALL
SELECT 'resource_allocation', COUNT(*) FROM resource_allocation
UNION ALL
SELECT 'incidents', COUNT(*) FROM incidents
UNION ALL
SELECT 'quarterly_revenue', COUNT(*) FROM quarterly_revenue
UNION ALL
SELECT 'budget_breakdown', COUNT(*) FROM budget_breakdown
ORDER BY table_name;

-- Expected results:
-- budget_breakdown        | 78
-- deliverables            | 87
-- incidents               | 50
-- monthly_metrics         | 95
-- monthly_revenue         | 216
-- projects                | 30
-- quarterly_revenue       | 72
-- resource_allocation     | 159
-- teams                   | 10
-- Total: 797 rows
*/
