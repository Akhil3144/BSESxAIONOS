# Optional grounded AI adapter

The synthetic pilot remains fully functional without keys. `LLM_ENABLED=false` is the default. Optional OpenAI Responses integration is implemented, but **no real live connectivity has been tested** in this environment. Configured does not mean verified. Health/config expose that distinction; a successful individual run records its actual prompt/model/evidence metadata.

To opt in, an administrator must explicitly set all of LLM_ENABLED=true, LLM_DATA_APPROVAL_REF (organizational authorization/change record), LLM_MODEL (approved structured-output-capable model) and OPENAI_API_KEY in environment/secrets. The code checks presence of the approval reference; it cannot verify the organization's actual approval. Obtain approval before supplying these settings. `LLM_TIMEOUT_SECONDS` defaults to 15, bounded 1–60. No UI field stores secrets, no API key is returned, and no live-provider call is required for seeding, engine tests or demo operation.

## Closed structured plan

The provider receives deterministic benchmark fields and source-linked comparator cards only: source IDs/references, effective observation dates, normalized prices, explicit transformation/rule, engine status and limitations. No raw document body, supplier performance/risk allegation payload, uploaded instruction or unrestricted retrieval is sent. Comparator IDs are allowed citations, not external URLs. Source hashes establish technical lineage, not independent business authenticity.

The JSON schema allows only a focus enum, supplied evidence IDs, question codes and concession codes. It contains **no price, amount, supplier allegation or free-form narrative fields**. The model chooses/reorders evidence and approved strategy blocks. Local code renders the final explanation from the engine's unchanged numerical conclusion plus approved text, and validates the entire rendered object against those selections. This deliberately narrower form of model-assisted generation prevents prices/citations/allegations from acquiring model authority. It is not unrestricted conversational negotiation.

Supported cases must cite existing evidence. Unknown/duplicate IDs, extra fields, invented codes, unjustified outlier assertions or unsupported concessions during insufficient evidence are rejected. Low evidence must select evidence_gaps and defer_target. Returned prose cannot be modified after rendering. Existing deterministic template validation remains supported.

The adapter calls only `https://api.openai.com/v1/responses`, uses strict JSON-schema `text.format`, `store:false`, a bounded output token count and response size, no redirects, no environment proxy inheritance, one bounded request and no automatic retries. It checks HTTP errors, completion status, explicit refusal and exactly one structured output. On any failure/rejection the agent persists the numerical result and deterministic explanation fallback without retaining provider exception messages or secrets.

`store:false` is an API request setting, **not** a claim of zero retention, confidential-data approval, provider entitlement or BSES security certification. Live use still requires approved account/data policies, hosting and source-use rights.

## Evidence and tests

`backend/tests/test_live_ai.py` uses httpx MockTransport to exercise the actual request builder, parser, schema validation, rendering and fallback. Tests cover allowed output, unfamiliar evidence/numerical fields/supplier allegations, injected raw instructions, refusal, truncation, absent output, HTTP 401/429/500, timeout and no-transmission configuration gates. These are contract tests, not live connectivity evidence. A successful authorized real call and SME usefulness review remain pending.

Protocol reference checked against [official OpenAI Structured Outputs documentation](https://developers.openai.com/api/docs/guides/structured-outputs). No model is selected automatically; use an organization-approved model with matching capabilities. No automatic supplier communication, procurement award or source-system write is available to this adapter.
