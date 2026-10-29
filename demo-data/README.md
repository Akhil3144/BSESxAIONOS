# DEMO / SYNTHETIC only

`synthetic-procurement.csv`: forty deterministic fictional cable observations, generated with seed 20261029, one material family, four fictional suppliers, quantity/date/price/specification/commercial variations. It can be uploaded through the actual Data ingestion screen into an empty demo database. Existing IDs are detected as duplicates.

`backend/app/seed.py` is the reproducible generator. Administration → Initialize synthetic demonstration passes its rows through the actual import validation function, freezes a snapshot and calculates five draft cases using the real engine. Ten separate synthetic holdout awards are inserted into an isolated table; these are deliberately absent from the reference CSV. Synthetic source identifiers are internally generated provenance, not authenticated business documents. Technical/market equivalence and all commercial examples are demonstration assumptions requiring SME review.

Do not use these values as BSES procurement history, actual supplier information or proof of savings. Browser QA adds clearly marked synthetic records/cases to the local pilot and is not part of this deterministic seed inventory.
