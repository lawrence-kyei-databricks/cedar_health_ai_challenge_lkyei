# Submission 1: Lakebase — Operational Postgres Layer

## Project
- **Name:** cedar-health-lkyei
- **PostgreSQL:** 17
- **Endpoint:** ep-autumn-rain-d17v4d7k.database.us-west-2.cloud.databricks.com

## Branches
| Branch | State | Purpose |
|--------|-------|---------|
| production | READY | Live operational data |
| dev | READY | Safe iteration (copy-on-write, no expiry) |

## Schema: `cedar_app` (Operational Tables)
| Table | Purpose |
|-------|---------|
| interventions | Track dispatched interventions (PK: intervention_id) |
| audit_log | Full audit trail of coordinator actions (PK: log_id SERIAL) |
| coordinator_sessions | Session state for worklist filtering (PK: session_id) |
| clinical_search | Hybrid search with pgvector embeddings + full-text (PK: patient_id) |

## Reverse ETL (Synced Tables)
| Source (Delta) | Destination (Postgres) | Rows |
|----------------|----------------------|------|
| ai_challenge_esc.cedar_health.gold_open_atrisk | cedar_health.synced_open_atrisk | 290 |
| ai_challenge_esc.cedar_health.gold_intervention_recommendations | cedar_health.synced_intervention_recs | 290 |

## Hybrid Search
- **pgvector:** v0.8.0 installed
- **Vector Index:** HNSW (cosine similarity) on `summary_embedding` column (1536 dims)
- **Full-Text Index:** GIN on `search_vector` (tsvector generated from clinical_summary)

## Evidence Notebook
- `/Users/lawrence.kyei@databricks.com/cedar_health_ai_challenge_lkyei/dev/build1_lakebase_setup`

## Personas Addressed
- **Rahul Bhatnagar (Dir Clinical Data Platform):** End-to-end PHI boundary — data stays in Lakebase Postgres with OAuth auth, no credentials in code
- **Emeka Balogun (Platform Eng Lead):** Audit log captures every action with user_id + timestamp; dev branch for safe investigation without touching production
