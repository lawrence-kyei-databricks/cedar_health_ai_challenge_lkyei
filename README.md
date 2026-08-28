# Cedar Health AI Challenge

**Team:** Lawrence Kyei | **Platform:** Databricks (Lakebase + Apps + AI Gateway)  
**Repo Branch:** `main`

## The Problem

Cedar Health — a regional provider network (~12 hospitals, ~$1.5B revenue) — loses **~$45M annually** to avoidable 30-day readmissions. At a 15% readmission rate across ~20,000 discharges, each percentage-point reduction is worth **~$3M**.

## The Solution

A production-ready Care Coordinator application that surfaces at-risk patients, recommends evidence-based interventions, and provides an AI clinical assistant — all within a cost-controlled, PHI-safe architecture.

**Live App:** [cedar-health-coordinator](https://cedar-health-coordinator-7474654066080903.aws.databricksapps.com)

---

## Architecture

```
+-----------------------+       +---------------------------+       +--------------------+
|   Unity Catalog       |       |   Lakebase Postgres       |       |   AI Gateway       |
|   (Delta Gold Layer)  | ----> |   (Operational Layer)     |       |   (LLM Access)     |
|                       | Sync  |                           |       |                    |
|  gold_open_atrisk     |       |  synced_open_atrisk       |       |  cedar-health-     |
|  gold_intervention_   |       |  synced_intervention_recs |       |  assistant         |
|  recommendations      |       |  interventions (writes)   |       |                    |
|                       |       |  audit_log (compliance)   |       |  Llama 3.3 70B     |
+-----------------------+       +---------------------------+       +--------------------+
         |                                   |                                |
         |                                   v                                |
         |                       +---------------------------+                |
         |                       |   Databricks App          |                |
         +---------------------> |   (Streamlit)             | <--------------+
                                 |                           |
                                 |  - Patient Risk Queue     |
                                 |  - Intervention Recs      |
                                 |  - Dispatch + Audit       |
                                 |  - AI Clinical Chat       |
                                 +---------------------------+
```

---

## Three Builds

| # | Build | Key Deliverable | Submission |
|---|-------|----------------|------------|
| 1 | **Lakebase** | Operational Postgres with reverse ETL, pgvector hybrid search, audit schema | [submission1/](dev/submission1/README.md) |
| 2 | **Databricks App** | Streamlit Care Coordinator with 4 panels, live dispatch, AI chat | [submission2/](dev/submission2/README.md) |
| 3 | **AI Gateway** | Cost-capped, guardrailed clinical LLM endpoint with usage tracking | [submission3/](dev/submission3/README.md) |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Patients at risk (active queue) | 290 |
| Avg risk score | 0.72 |
| Total financial exposure | ~$4.4M |
| AI cost ceiling (per user/day) | $14.40 |
| Cost reduction vs. prior incident | 83x |
| PHI guardrail | Input BLOCK + Output MASK |
| Rate limits | 10K tokens/min/user, 50K tokens/min/endpoint |

---

## Persona Alignment

| Persona | Role | Addressed By |
|---------|------|-------------|
| Adaeze Okafor | VP Population Health | App dispatch tracking answers "who got intervention this week?" |
| Katarzyna Nowak | Dir IT Finance | AI Gateway rate limits = bounded, predictable AI spend |
| Rahul Bhatnagar | Dir Clinical Data Platform | End-to-end PHI boundary — OAuth auth, no creds in code, PII guardrails |
| Emeka Balogun | Platform Eng Lead | Audit log + dev branch + usage tracking = investigate without reading PHI |

---

## Technology Stack

- **Data Layer:** Unity Catalog (Delta Lake gold tables, metric views)
- **Operational DB:** Lakebase Postgres 17 (pgvector 0.8, HNSW + GIN indexes)
- **Application:** Databricks Apps (Streamlit, OAuth-secured)
- **AI:** AI Gateway (Llama 3.3 70B, guardrails, inference table)
- **Analytics:** AI/BI Dashboard + Genie Space

---

## Evidence Notebooks

- [`dev/build1_lakebase_setup.py`](dev/build1_lakebase_setup.py) — Lakebase provisioning, schema creation, reverse ETL
- [`dev/build3_ai_gateway_setup.py`](dev/build3_ai_gateway_setup.py) — AI Gateway configuration, guardrail testing

---

## Running the App

The app is deployed and running at the URL above. It authenticates via Databricks OAuth (workspace SSO) and connects to Lakebase using dynamic credential generation — no secrets in code.

## Repository Structure

```
cedar_health_ai_challenge_lkyei/
|-- README.md                          <- This file
|-- dev/
    |-- build1_lakebase_setup.py       <- Lakebase evidence notebook
    |-- build3_ai_gateway_setup.py     <- AI Gateway evidence notebook
    |-- submission1/README.md          <- Lakebase submission
    |-- submission2/README.md          <- App submission
    |-- submission3/README.md          <- AI Gateway submission
```
