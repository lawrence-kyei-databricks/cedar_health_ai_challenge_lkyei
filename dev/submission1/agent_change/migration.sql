-- Co-authored-by: Genie Code (Databricks Assistant)
-- Author: Genie Code Agent via cedar_health_ai_challenge_lkyei workspace
-- Date: 2026-08-28
-- Branch: projects/cedar-health-lkyei/branches/dev
-- Purpose: Add intervention outcome tracking for effectiveness measurement

-- Migration: Add outcome tracking to interventions table
-- Executed on dev branch first, validated, then promoted to production

ALTER TABLE cedar_app.interventions
    ADD COLUMN IF NOT EXISTS outcome_status TEXT DEFAULT 'pending'
        CHECK (outcome_status IN ('pending', 'completed', 'cancelled', 'escalated')),
    ADD COLUMN IF NOT EXISTS outcome_date TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS effectiveness_score NUMERIC(3,2)
        CHECK (effectiveness_score BETWEEN 0.0 AND 1.0);

-- Performance index for outcome queries
CREATE INDEX IF NOT EXISTS idx_interventions_outcome
    ON cedar_app.interventions(outcome_status, outcome_date);

-- Validation query (run on dev branch)
INSERT INTO cedar_app.interventions
    (intervention_id, patient_id, intervention_type, provider_id, status, outcome_status, effectiveness_score)
VALUES
    ('INT-VALIDATE-001', 'PT-0002966', 'followup_call', 'PRV-001', 'dispatched', 'completed', 0.85)
RETURNING intervention_id, outcome_status, effectiveness_score;

-- Promotion: same DDL applied to production branch after dev validation succeeded
