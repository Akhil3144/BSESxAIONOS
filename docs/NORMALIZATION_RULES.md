# Normalization rules

Registered demo rule: metres ↔ kilometres. A price per source unit is transformed as `original_price / metres_in_source_unit * metres_in_quote_unit`. Factors: m=1, km=1000. Quantity eligibility is compared in metres. Original rows and calculation strings remain in the benchmark result.

Different specification, currency, tax, location, delivery or payment terms cause exclusion. There is no inferred inflation, index, freight, timing, commercial, FX or specification surcharge. Timing is a strict observation/availability cutoff with optional configurable age ceiling, not an index adjustment. Quantity ratio and supplier-count bounds are fully materialized in each new result; duplicate evidence is excluded and IQR outliers are retained/flagged. Unsupported units fail ingestion. Invalid/nonfinite prices and quantities are rejected. No should-cost model exists.

This is a safe one-family baseline, not a general normalization registry. Approved evidence-backed adjustment references, effective-date lookup, configurable factors and category-specific profiles remain productization work. The registered conversion factors are technical SI conversions; any commercial rule still needs SME approval.
