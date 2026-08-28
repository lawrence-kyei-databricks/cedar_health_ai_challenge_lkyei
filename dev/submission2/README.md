# Submission 2: Databricks App — Care Coordinator Panel

## App
- **Name:** cedar-health-coordinator
- **URL:** https://cedar-health-coordinator-7474654066080903.aws.databricksapps.com
- **Status:** RUNNING (deployed 2026-08-27T20:19:07Z)
- **Compute:** MEDIUM, ACTIVE
- **Framework:** Streamlit

## Features (4 Panels)

### 1. Patient Risk Queue
- 290 at-risk patients sorted by readmission_risk_score DESC
- Columns: patient name, condition, risk band, risk score (progress bar), exposure ($), days since discharge, open gaps
- Filters: primary condition (HF/COPD/AMI/PNA), risk band (critical/elevated)
- KPI row: total at-risk, avg risk score, total exposure, avg days since DC

### 2. Intervention Recommendations
- Per-patient ranked interventions from synced_intervention_recs
- Shows: intervention type, provider, predicted risk reduction, net value ($), ranking

### 3. Dispatch Action
- Button writes to Lakebase `cedar_app.interventions` + `cedar_app.audit_log`
- Creates unique intervention_id, records user, action, timestamp
- Full audit trail for compliance

### 4. AI Clinical Assistant
- Chat widget connected to `cedar-health-assistant` AI Gateway endpoint
- System prompt for evidence-based readmission prevention
- Rate-limited + PHI-safe via gateway guardrails

## Data Sources
- **Lakebase:** ep-autumn-rain-d17v4d7k.database.us-west-2.cloud.databricks.com
- **Synced Tables:** cedar_health.synced_open_atrisk, cedar_health.synced_intervention_recs
- **Operational:** cedar_app.interventions, cedar_app.audit_log
- **AI Gateway:** cedar-health-assistant endpoint

## Source Files
- `/Users/lawrence.kyei@databricks.com/cedar-health-coordinator/app.py`
- `/Users/lawrence.kyei@databricks.com/cedar-health-coordinator/app.yaml`

## Personas Addressed
- **Adaeze Okafor (VP Pop Health):** "Which patients got intervention this week they otherwise wouldn't have?" — dispatch tracking in audit_log answers this directly
- **Emeka Balogun (Platform Eng Lead):** "Can I investigate without reading more PHI than I should?" — App uses OAuth scoped credentials; audit_log tracks who viewed what

## Genie Space
- **Name:** Cedar Health — Care Coordinator Assistant
- **ID:** 01f1a24a4e02181d9be01e57a2fe5d7f
- **Tables:** mv_patient_risk, gold_open_atrisk, gold_intervention_recommendations, gold_intervention_outcomes, silver_encounters

## AI/BI Dashboard
- **Name:** Cedar Health — Readmission Risk & Intervention Performance
- **ID:** 01f1a249a17b166cb7f660ebf1cf5e4d
