-- Business Question: Which critical-risk patients have highest exposure with open gaps?
-- Run against: cedar_health.synced_open_atrisk (Lakebase Postgres, production branch)

SELECT 
    patient_id,
    patient_display_name,
    primary_condition,
    readmission_risk_score,
    readmission_exposure_usd,
    days_since_discharge,
    open_gap_count,
    has_open_followup
FROM cedar_health.synced_open_atrisk
WHERE risk_band = 'critical'
  AND open_gap_count >= 2
ORDER BY readmission_exposure_usd DESC, readmission_risk_score DESC
LIMIT 10;
