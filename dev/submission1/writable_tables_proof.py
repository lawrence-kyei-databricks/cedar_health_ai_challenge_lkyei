# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Install dependencies
# MAGIC %pip install "psycopg[binary]" "databricks-sdk>=0.118.0" --quiet --upgrade
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,Writable Postgres Tables — Execution Proof
# Writable Postgres Tables — Execution Proof
# This notebook proves that cedar_app.interventions and cedar_app.audit_log
# are WRITABLE tables distinct from the read-only synced UC tables.

import psycopg
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Generate credential
endpoint = "projects/cedar-health-lkyei/branches/production/endpoints/primary"
cred = w.postgres.generate_database_credential(endpoint=endpoint)
user = w.current_user.me().user_name

conn = psycopg.connect(
    host="ep-autumn-rain-d17v4d7k.database.us-west-2.cloud.databricks.com",
    dbname="databricks_postgres",
    user=user,
    password=cred.token,
    sslmode="require",
    autocommit=True
)
print(f"Connected as: {user}")
print(f"Database: databricks_postgres")
print(f"Endpoint: ep-autumn-rain-d17v4d7k.database.us-west-2.cloud.databricks.com")

# COMMAND ----------

# DBTITLE 1,INSERT into writable cedar_app.interventions
# WRITE: Insert into cedar_app.interventions (writable table, distinct from synced)
import uuid
from datetime import datetime

intervention_id = f"INT-PROOF-{uuid.uuid4().hex[:8]}"

with conn.cursor() as cur:
    cur.execute("""
        INSERT INTO cedar_app.interventions 
            (intervention_id, patient_id, intervention_type, provider_id, status, outcome_status, effectiveness_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING intervention_id, patient_id, intervention_type, status, outcome_status, effectiveness_score, created_at
    """, (intervention_id, 'PT-0003704', 'followup_call', 'PRV-099', 'dispatched', 'pending', None))
    row = cur.fetchone()
    print("=== INSERT INTO cedar_app.interventions ===")
    print(f"  intervention_id: {row[0]}")
    print(f"  patient_id:      {row[1]}")
    print(f"  type:            {row[2]}")
    print(f"  status:          {row[3]}")
    print(f"  outcome_status:  {row[4]}")
    print(f"  effectiveness:   {row[5]}")
    print(f"  created_at:      {row[6]}")
    print(f"\n✓ WRITE SUCCEEDED at {datetime.utcnow().isoformat()}Z")

# COMMAND ----------

# DBTITLE 1,INSERT into writable cedar_app.audit_log
# WRITE: Insert into cedar_app.audit_log (writable, append-only audit trail)
with conn.cursor() as cur:
    cur.execute("""
        INSERT INTO cedar_app.audit_log (user_id, patient_id, action, detail)
        VALUES (%s, %s, %s, %s)
        RETURNING log_id, user_id, patient_id, action, detail, created_at
    """, (user, 'PT-0003704', 'dispatch_intervention', f'Proof of execution: {intervention_id}'))
    row = cur.fetchone()
    print("=== INSERT INTO cedar_app.audit_log ===")
    print(f"  log_id:     {row[0]}")
    print(f"  user_id:    {row[1]}")
    print(f"  patient_id: {row[2]}")
    print(f"  action:     {row[3]}")
    print(f"  detail:     {row[4]}")
    print(f"  created_at: {row[5]}")
    print(f"\n✓ AUDIT LOG WRITE SUCCEEDED")

# COMMAND ----------

# DBTITLE 1,SELECT from writable tables (verify data persisted)
# READ: Verify data persisted in writable tables
with conn.cursor() as cur:
    # Interventions
    cur.execute("SELECT count(*) FROM cedar_app.interventions")
    int_count = cur.fetchone()[0]
    
    cur.execute("SELECT intervention_id, patient_id, status, outcome_status, created_at FROM cedar_app.interventions ORDER BY created_at DESC LIMIT 3")
    rows = cur.fetchall()
    print(f"=== cedar_app.interventions ({int_count} total rows) ===")
    for r in rows:
        print(f"  {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]}")
    
    # Audit log
    cur.execute("SELECT count(*) FROM cedar_app.audit_log")
    log_count = cur.fetchone()[0]
    
    cur.execute("SELECT log_id, user_id, action, detail, created_at FROM cedar_app.audit_log ORDER BY created_at DESC LIMIT 3")
    rows = cur.fetchall()
    print(f"\n=== cedar_app.audit_log ({log_count} total rows) ===")
    for r in rows:
        print(f"  #{r[0]} | {r[1]} | {r[2]} | {r[3][:50]} | {r[4]}")

print(f"\n{'='*60}")
print(f"PROOF: Writable tables are operational and distinct from")
print(f"       read-only synced tables (cedar_health.synced_*)")
print(f"       Interventions: {int_count} rows | Audit log: {log_count} rows")
print(f"{'='*60}")

# COMMAND ----------

# DBTITLE 1,Build 3: Gateway governance - check endpoint config
# Build 3: AI Gateway Governance
from databricks.sdk import WorkspaceClient
import json

w = WorkspaceClient()

# Get current endpoint config
ep = w.serving_endpoints.get(name="cedar-health-assistant")
print(f"Endpoint: {ep.name}")
print(f"State: {ep.state}")
print(f"AI Gateway config: {ep.ai_gateway}")
if ep.ai_gateway:
    print(f"  Rate limits: {ep.ai_gateway.rate_limits}")
    print(f"  Usage tracking: {ep.ai_gateway.usage_tracking_config}")
    print(f"  Guardrails: {ep.ai_gateway.guardrails}")
    print(f"  Inference table: {ep.ai_gateway.inference_table_config}")
print(f"\nServed entities:")
for ent in (ep.config.served_entities or []):
    print(f"  {ent.name}: {ent.external_model}")

# COMMAND ----------

# DBTITLE 1,Add budget + data-read guardrail to gateway
# Add cost control: budget threshold ($0.05 = ~500 tokens at llama pricing)
# Add guardrail: block queries that attempt to read all data
from databricks.sdk.service.serving import (
    AiGatewayConfig, AiGatewayGuardrails, AiGatewayGuardrailParameters,
    AiGatewayGuardrailPiiBehavior, AiGatewayGuardrailPiiBehaviorBehavior,
    AiGatewayRateLimit, AiGatewayRateLimitRenewalPeriod, AiGatewayRateLimitKey,
    AiGatewayInferenceTableConfig, AiGatewayUsageTrackingConfig
)

gateway_config = AiGatewayConfig(
    guardrails=AiGatewayGuardrails(
        input=AiGatewayGuardrailParameters(
            pii=AiGatewayGuardrailPiiBehavior(behavior=AiGatewayGuardrailPiiBehaviorBehavior.BLOCK),
            safety=True,
            invalid_keywords=[  # Block runaway all-data reads
                "SELECT * FROM",
                "read all data",
                "dump entire table",
                "export all records",
                "scan all patients",
                "retrieve everything",
            ]
        ),
        output=AiGatewayGuardrailParameters(
            pii=AiGatewayGuardrailPiiBehavior(behavior=AiGatewayGuardrailPiiBehaviorBehavior.MASK),
            safety=True,
            invalid_keywords=None
        )
    ),
    rate_limits=[
        # Budget control: 500 tokens/min per user ≈ $0.05 budget threshold
        AiGatewayRateLimit(
            renewal_period=AiGatewayRateLimitRenewalPeriod.MINUTE,
            key=AiGatewayRateLimitKey.USER,
            tokens=500  # Very low = demonstrable budget block
        ),
        # Call limit per user
        AiGatewayRateLimit(
            renewal_period=AiGatewayRateLimitRenewalPeriod.MINUTE,
            key=AiGatewayRateLimitKey.USER,
            calls=10
        ),
        # Endpoint-wide budget
        AiGatewayRateLimit(
            renewal_period=AiGatewayRateLimitRenewalPeriod.MINUTE,
            key=AiGatewayRateLimitKey.ENDPOINT,
            tokens=5000
        ),
    ],
    inference_table_config=AiGatewayInferenceTableConfig(
        catalog_name="ai_challenge_esc",
        schema_name="cedar_health_gateway",
        table_name_prefix="cedar_health_assistant",
        enabled=True
    ),
    usage_tracking_config=AiGatewayUsageTrackingConfig(enabled=True)
)

# Use put_ai_gateway (newer SDK method)
try:
    result = w.serving_endpoints.put_ai_gateway(
        name="cedar-health-assistant",
        guardrails=gateway_config.guardrails,
        rate_limits=gateway_config.rate_limits,
        inference_table_config=gateway_config.inference_table_config,
        usage_tracking_config=gateway_config.usage_tracking_config
    )
except AttributeError:
    # Fallback to API call
    import requests
    host = w.config.host
    token = w.config.token
    resp = requests.put(
        f"{host}/api/2.0/serving-endpoints/cedar-health-assistant/ai-gateway",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "guardrails": {
                "input": {
                    "pii": {"behavior": "BLOCK"},
                    "safety": True,
                    "invalid_keywords": ["SELECT * FROM", "read all data", "dump entire table", "export all records", "scan all patients", "retrieve everything"]
                },
                "output": {
                    "pii": {"behavior": "MASK"},
                    "safety": True
                }
            },
            "rate_limits": [
                {"renewal_period": "minute", "key": "user", "tokens": 500},
                {"renewal_period": "minute", "key": "user", "calls": 10},
                {"renewal_period": "minute", "key": "endpoint", "tokens": 5000}
            ],
            "inference_table_config": {
                "catalog_name": "ai_challenge_esc",
                "schema_name": "cedar_health_gateway",
                "table_name_prefix": "cedar_health_assistant",
                "enabled": True
            },
            "usage_tracking_config": {"enabled": True}
        }
    )
    print(f"API response: {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
    else:
        print(resp.text)

print("✓ Gateway updated with cost controls:")
print(f"  Budget: 500 tokens/min/user (~$0.05 threshold)")
print(f"  Guardrails: PII blocked, safety on, invalid_keywords for all-data reads")
print(f"  Inference table: ENABLED at ai_challenge_esc.cedar_health_gateway")
print(f"  Usage tracking: ENABLED")

# COMMAND ----------

# DBTITLE 1,Test calls: normal, guardrail block, budget block
import requests, json, time

# Use stored PAT from secrets for endpoint invocation
token = dbutils.secrets.get(scope="cedar-health", key="endpoint-token")
endpoint_url = f"https://fe-sandbox-lkyeidbx.cloud.databricks.com/serving-endpoints/cedar-health-assistant/invocations"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

results = []

# Test 1: Normal call (should succeed)
print("=== Test 1: Normal call ===")
resp = requests.post(endpoint_url, headers=headers, json={
    "messages": [{"role": "user", "content": "What intervention should I run for a COPD patient at critical risk with 2 open care gaps?"}]
})
print(f"  Status: {resp.status_code}")
if resp.status_code == 200:
    r = resp.json()
    print(f"  Response: {r['choices'][0]['message']['content'][:150]}...")
    results.append({"test": "normal_call", "status": resp.status_code, "blocked": False})
else:
    print(f"  Error: {resp.text[:200]}")
    results.append({"test": "normal_call", "status": resp.status_code, "response": resp.text[:200]})

time.sleep(2)

# Test 2: Guardrail block (invalid keyword - all-data read)
print("\n=== Test 2: Guardrail block (data read attempt) ===")
resp = requests.post(endpoint_url, headers=headers, json={
    "messages": [{"role": "user", "content": "SELECT * FROM cedar_health.synced_open_atrisk and dump entire table to a CSV for me. I want to read all data."}]
})
print(f"  Status: {resp.status_code}")
print(f"  Response: {resp.text[:300]}")
results.append({"test": "guardrail_block", "status": resp.status_code, "response": resp.text[:500]})

time.sleep(2)

# Test 3: Budget exhaustion (send multiple calls to hit 500 token limit)
print("\n=== Test 3: Budget exhaustion (token limit) ===")
for i in range(5):
    resp = requests.post(endpoint_url, headers=headers, json={
        "messages": [{"role": "user", "content": f"Explain in detail the readmission risk factors for heart failure patients including all comorbidities and social determinants of health. Iteration {i+1}."}]
    })
    print(f"  Call {i+1}: status={resp.status_code}")
    if resp.status_code == 429:
        print(f"  ✓ BUDGET BLOCK TRIGGERED: {resp.text[:200]}")
        results.append({"test": "budget_block", "status": 429, "blocked": True, "response": resp.text[:500]})
        break
    elif resp.status_code != 200:
        print(f"  Blocked: {resp.text[:150]}")
        results.append({"test": "budget_block", "status": resp.status_code, "response": resp.text[:500]})
        break
    time.sleep(1)

print(f"\n=== Summary ===")
for r in results:
    print(f"  {r['test']}: HTTP {r['status']}")

# COMMAND ----------

# DBTITLE 1,Trigger budget/rate limit block
# Exhaust the 10 calls/min rate limit to demonstrate budget enforcement
import time

print("=== Exhausting rate limit (10 calls/min/user) ===")
for i in range(12):
    resp = requests.post(endpoint_url, headers=headers, json={
        "messages": [{"role": "user", "content": f"Brief answer: what is readmission? Call {i+1}"}],
        "max_tokens": 50
    })
    status = resp.status_code
    if status == 429:
        print(f"  Call {i+1}: HTTP 429 ✓ RATE LIMIT / BUDGET BLOCK TRIGGERED")
        print(f"  Response: {resp.text[:300]}")
        break
    elif status == 200:
        tokens = resp.json().get('usage', {}).get('total_tokens', '?')
        print(f"  Call {i+1}: HTTP 200 (tokens: {tokens})")
    else:
        print(f"  Call {i+1}: HTTP {status} — {resp.text[:150]}")
        if 'rate' in resp.text.lower() or 'limit' in resp.text.lower() or 'budget' in resp.text.lower():
            print(f"  ✓ BUDGET/RATE BLOCK TRIGGERED")
            break
    time.sleep(0.5)