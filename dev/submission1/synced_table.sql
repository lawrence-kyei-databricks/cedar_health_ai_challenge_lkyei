-- Connectivity check
SELECT version();
-- Result: PostgreSQL 17.11 (32e7196) on x86_64-pc-linux-gnu

-- Instance: cedar-health-lkyei
-- Endpoint: ep-autumn-rain-d17v4d7k.database.us-west-2.cloud.databricks.com
-- Database: databricks_postgres

-- Query against synced Unity Catalog table (cedar_health.synced_open_atrisk)
-- Source: ai_challenge_esc.cedar_health.gold_open_atrisk (CDF-enabled Delta)
-- Sync: Continuous via DLT pipeline 3af61b6b-0691-41a7-835a-f9f79c01f014
SELECT 
    patient_id,
    patient_display_name,
    primary_condition,
    readmission_risk_score,
    risk_band,
    readmission_exposure_usd,
    days_since_discharge,
    open_gap_count
FROM cedar_health.synced_open_atrisk
ORDER BY readmission_risk_score DESC
LIMIT 10;
