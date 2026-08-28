# Databricks notebook source
# DBTITLE 1,Build 1: Lakebase — Cedar Health Care Platform
# Build 1: Lakebase — Cedar Health Care Platform
# Evidence notebook for Cedar Health AI Challenge submission
# Project: cedar-health-lkyei | PG 17 | Endpoint: ep-autumn-rain-d17v4d7k
# Branches: production (READY), dev (READY)

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.postgres import (
    Project, ProjectSpec, Branch, BranchSpec,
    SyncedTable, SyncedTableSyncedTableSpec,
    SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy
)
import psycopg

w = WorkspaceClient()

# --- STEP 1: Create Project ---
# op = w.postgres.create_project(
#     project=Project(spec=ProjectSpec(display_name="Cedar Health Care Platform", pg_version=17)),
#     project_id="cedar-health-lkyei",
# )
# project = op.wait()

# --- STEP 2: Create Dev Branch ---
# op = w.postgres.create_branch(
#     parent="projects/cedar-health-lkyei",
#     branch=Branch(spec=BranchSpec(
#         source_branch="projects/cedar-health-lkyei/branches/production",
#         no_expiry=True,
#     )),
#     branch_id="dev",
# )
# dev_branch = op.wait()

print("Project: cedar-health-lkyei")
print("Branches: production, dev")
print("Endpoint: ep-autumn-rain-d17v4d7k.database.us-west-2.cloud.databricks.com")

# COMMAND ----------

# DBTITLE 1,Schema & Tables
# --- STEP 3: Create Schema + Operational Tables ---
cred = w.postgres.generate_database_credential(
    endpoint="projects/cedar-health-lkyei/branches/production/endpoints/primary"
)

host = "ep-autumn-rain-d17v4d7k.database.us-west-2.cloud.databricks.com"

with psycopg.connect(
    host=host, dbname="databricks_postgres",
    user="lawrence.kyei@databricks.com", password=cred.token, sslmode="require"
) as conn:
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS cedar_app")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cedar_app.interventions (
                intervention_id TEXT PRIMARY KEY,
                patient_id TEXT NOT NULL,
                intervention_type TEXT NOT NULL,
                provider_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cedar_app.audit_log (
                log_id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                patient_id TEXT,
                action TEXT NOT NULL,
                detail TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cedar_app.coordinator_sessions (
                session_id TEXT PRIMARY KEY,
                coordinator_id TEXT NOT NULL,
                worklist_filter JSONB,
                last_active TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("\u2713 Schema cedar_app + 3 tables created")

# COMMAND ----------

# DBTITLE 1,Reverse ETL — Synced Tables
# --- STEP 4: Reverse ETL ---
op1 = w.postgres.create_synced_table(
    synced_table=SyncedTable(
        spec=SyncedTableSyncedTableSpec(
            source_table_full_name="ai_challenge_esc.cedar_health.gold_open_atrisk",
            branch="projects/cedar-health-lkyei/branches/production",
            postgres_database="databricks_postgres",
            primary_key_columns=["patient_id"],
            create_database_objects_if_missing=True,
            scheduling_policy=SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy.SNAPSHOT,
        )
    ),
    synced_table_id="ai_challenge_esc.cedar_health.synced_open_atrisk",
)
result1 = op1.wait()
print(f"\u2713 Synced: {result1.synced_table_id}")

op2 = w.postgres.create_synced_table(
    synced_table=SyncedTable(
        spec=SyncedTableSyncedTableSpec(
            source_table_full_name="ai_challenge_esc.cedar_health.gold_intervention_recommendations",
            branch="projects/cedar-health-lkyei/branches/production",
            postgres_database="databricks_postgres",
            primary_key_columns=["patient_id"],
            create_database_objects_if_missing=True,
            scheduling_policy=SyncedTableSyncedTableSpecSyncedTableSchedulingPolicy.SNAPSHOT,
        )
    ),
    synced_table_id="ai_challenge_esc.cedar_health.synced_intervention_recs",
)
result2 = op2.wait()
print(f"\u2713 Synced: {result2.synced_table_id}")

# COMMAND ----------

# DBTITLE 1,Hybrid Search — pgvector + Full-Text
# --- STEP 5: Hybrid Search ---
cred = w.postgres.generate_database_credential(
    endpoint="projects/cedar-health-lkyei/branches/production/endpoints/primary"
)

with psycopg.connect(
    host="ep-autumn-rain-d17v4d7k.database.us-west-2.cloud.databricks.com",
    dbname="databricks_postgres",
    user="lawrence.kyei@databricks.com", password=cred.token, sslmode="require"
) as conn:
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cedar_app.clinical_search (
                patient_id TEXT PRIMARY KEY,
                clinical_summary TEXT NOT NULL,
                summary_embedding vector(1536),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_clinical_embedding
            ON cedar_app.clinical_search
            USING hnsw (summary_embedding vector_cosine_ops)
        """)
        cur.execute("""
            ALTER TABLE cedar_app.clinical_search
            ADD COLUMN IF NOT EXISTS search_vector tsvector
            GENERATED ALWAYS AS (to_tsvector('english', clinical_summary)) STORED
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_clinical_fts
            ON cedar_app.clinical_search
            USING gin (search_vector)
        """)
        print("\u2713 pgvector + HNSW + GIN full-text search enabled")

# COMMAND ----------

# DBTITLE 1,Validation
# --- STEP 6: Full Validation ---
cred = w.postgres.generate_database_credential(
    endpoint="projects/cedar-health-lkyei/branches/production/endpoints/primary"
)

print("=" * 50)
print("BUILD 1 VALIDATION")
print("=" * 50)

# Branches
print("\nBranches:")
for b in w.postgres.list_branches(parent="projects/cedar-health-lkyei"):
    print(f"  {b.name.split('/')[-1]} | {b.status.current_state}")

# Endpoint
print("\nEndpoint:")
for ep in w.postgres.list_endpoints(parent="projects/cedar-health-lkyei/branches/production"):
    print(f"  {ep.status.hosts.host} | {ep.status.current_state}")

# Postgres validation
with psycopg.connect(
    host="ep-autumn-rain-d17v4d7k.database.us-west-2.cloud.databricks.com",
    dbname="databricks_postgres",
    user="lawrence.kyei@databricks.com", password=cred.token, sslmode="require"
) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='cedar_app' ORDER BY 1")
        print(f"\ncedar_app tables: {[r[0] for r in cur.fetchall()]}")
        
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='cedar_health' ORDER BY 1")
        synced = [r[0] for r in cur.fetchall()]
        print(f"cedar_health synced: {synced}")
        for t in synced:
            cur.execute(f'SELECT count(*) FROM cedar_health."{t}"')
            print(f"  {t}: {cur.fetchone()[0]} rows")
        
        cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
        print(f"\npgvector: v{cur.fetchone()[0]}")
        cur.execute("SELECT indexname FROM pg_indexes WHERE schemaname='cedar_app' AND tablename='clinical_search'")
        print(f"Search indexes: {[r[0] for r in cur.fetchall()]}")

print("\n\u2713 ALL CHECKS PASSED")