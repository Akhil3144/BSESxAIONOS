# Evidence lineage

Source upload → import_batch ID, original bytes, SHA256, validation errors → unique source_record/source ID and canonical original fields → frozen snapshot ID and SHA256 → case and preserved quote → benchmark_run ID, exact rule, included/excluded records, transformation strings and result SHA256 → evidence view → exact review action/run → report snapshot, byte-identical PDF archive and PDF SHA256.

Evidence Cards are the independently inspectable benchmark run representation. They contain original included values, source references, supplier context for calculated runs, exclusion reasons, method, limitations, case/snapshot/run IDs, timestamps, rule and reviewer history. No fake public citations are generated. Protected retained-file downloads allow reviewers to inspect source evidence. A recorded source_ref is an identifier supplied by the uploader; its existence is validated but business authenticity is not independently attested. Hashing proves integrity relative to retained bytes, not external authentication.

Initial seeded run context can be resolved from the supplier table; subsequent actual runs persist context. Default narrative is a deterministic template. Optional validated plans record prompt/model/evidence-hash metadata; live connectivity remains unverified. The SHA256 result hash is recalculated from its serialized payload. The engine fingerprint omits timing for reproducibility.

Audit entries are chained with SHA256(previous hash + actor + event + canonical payload + timestamp). Audit read validates the chain. A privileged database administrator can rewrite an unanchored chain; deletion of an unanchored tail cannot be detected independently. This is an application-level tamper-evident mechanism, not immutable external audit storage.
