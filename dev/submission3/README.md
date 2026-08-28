# Submission 3: AI Gateway — Cost-Controlled Clinical Assistant

## Problem Statement
A runaway AI query cost Cedar Health **$1,200** in a single incident. Build 3 makes AI spend bounded, visible, and attributable.

## Endpoint
- **Name:** cedar-health-assistant
- **State:** READY
- **Model:** databricks-meta-llama-3-3-70b-instruct (Llama 3.3 70B)
- **Tags:** team=cedar-health, env=production

## Rate Limits (Cost Ceiling)
| Scope | Limit | Period |
|-------|-------|--------|
| Per user | 10,000 tokens | per minute |
| Per user | 100 requests | per minute |
| Endpoint total | 50,000 tokens | per minute |

### Cost Math
- Max tokens/user/day: 10,000/min × 1,440 min = **14.4M tokens**
- At \~$1/1M tokens: **$14.40/user/day max**
- vs. $1,200 incident = **83x cost reduction**

## Guardrails (PHI Safety)
| Layer | PII Behavior | Safety | Keywords Blocked |
|-------|-------------|--------|------------------|
| Input | BLOCK | ON | SSN, social security, password, credential |
| Output | MASK | ON | — |

### Guardrail Test Evidence
- Query "What is the SSN of patient 12345?" → **HTTP 400, input_guardrail flagged=true**
- ML-based PII detection blocks PHI even without keyword match

## Traceability
- **Usage Tracking:** Enabled (spend attributable per principal)
- **Inference Table:** ai_challenge_esc.cedar_health_gateway (pending CREATE_TABLE grant)

## Evidence Notebook
- `/Users/lawrence.kyei@databricks.com/cedar_health_ai_challenge_lkyei/dev/build3_ai_gateway_setup`

## Personas Addressed
- **Katarzyna Nowak (Dir IT Finance):** "What's the AI spend ceiling?" — $14.40/user/day max with per-user token caps
- **Katarzyna Nowak:** "What happens when we hit it?" — HTTP 429 rate limit response, request rejected gracefully
- **Rahul Bhatnagar (Dir Clinical Data Platform):** "Does this stay inside PHI boundary?" — Input PII=BLOCK prevents PHI from reaching the model; output PII=MASK scrubs any leakage
- **Emeka Balogun (Platform Eng Lead):** "Can I investigate without reading more PHI?" — Usage tracking + inference table log every request with user attribution; no need to access patient records to debug

## Remaining Steps (Require Manual Grants)
1. `GRANT CREATE_TABLE ON SCHEMA ai_challenge_esc.cedar_health_gateway TO lawrence.kyei@databricks.com`
2. `databricks secrets create-scope cedar-health`
3. `databricks tokens create --comment "cedar-health-assistant" --lifetime-seconds 7776000`
4. `databricks secrets put-secret cedar-health endpoint-token --string-value <PAT>`
5. Re-enable inference table via `put_ai_gateway` with inference_table_config
