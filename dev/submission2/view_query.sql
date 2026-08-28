-- Live Care Coordinator Worklist View
-- Reads from synced UC table (read-only) + writable interventions table
-- Triggered on: daily scheduled scan (08:00 UTC) OR real-time risk threshold breach
-- Ranks patients by risk and surfaces action priority

SELECT
    p.patient_id,
    p.patient_display_name,
    p.primary_condition,
    p.readmission_risk_score,
    p.risk_band,
    p.readmission_exposure_usd,
    p.days_since_discharge,
    p.open_gap_count,
    p.has_open_followup,
    COALESCE(i.pending_interventions, 0) AS pending_interventions,
    CASE
        WHEN p.readmission_risk_score >= 0.9 AND p.open_gap_count >= 2
            THEN 'URGENT: intervene now'
        WHEN p.readmission_risk_score >= 0.8
            THEN 'HIGH: review today'
        WHEN p.readmission_risk_score >= 0.6
            THEN 'MODERATE: schedule this week'
        ELSE 'LOW: monitor'
    END AS action_priority
FROM cedar_health.synced_open_atrisk p
LEFT JOIN (
    SELECT patient_id, COUNT(*) AS pending_interventions
    FROM cedar_app.interventions
    WHERE outcome_status = 'pending'
    GROUP BY patient_id
) i ON p.patient_id = i.patient_id
ORDER BY p.readmission_risk_score DESC, p.open_gap_count DESC
LIMIT 15;
