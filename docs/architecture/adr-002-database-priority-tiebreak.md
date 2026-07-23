# ADR-002: Database Priority Tie-Break for Duplicate Indicators

**Status:** Accepted  
**Date:** 2026-07-23

---

## Context

The World Bank `/data360/searchv2` API returns indicators from multiple databases.
The same real-world concept often appears under several database IDs with identical
or near-identical names. For example, searching "GDP growth" returns:

```
WB_ESG_NY_GDP_MKTP_KD_ZG  "GDP growth (annual %)"   score: 21.649889
WB_GS_NY_GDP_MKTP_KD_ZG   "GDP growth (annual %)"   score: 21.649889
WB_CLEAR_NY_GDP_MKTP_KD_ZG "GDP growth (annual %)"  score: 20.819328
```

These are three representations of the same indicator from three different databases.
After deduplication collapses them into one canonical entry, a single database must
be selected to fetch actual data from. The question is: which one?

---

## Decision

**A fixed priority order determines which database wins when multiple entries
represent the same concept.** The priority list is stored in `core/constants.py`
as `DATABASE_PRIORITY`.

**Priority order (highest to lowest):**

```
WB_WDI      — World Development Indicators (the primary, most cited database)
WB_WDI_GEP  — WDI Global Economic Prospects (WDI extension, high quality)
WB_ESG      — ESG database (themed subset, but data comes from WDI methodology)
WB_GS       — Global Statistics
WB_CLEAR    — CLEAR database
<others>    — Alphabetically, for any database not in the list above
```

---

## Reasoning

1. **WB_WDI is the canonical World Bank database.** It is the most frequently cited,
   most consistently updated, and most broadly covered. When in doubt, prefer it.

2. **Alphabetical fallback is deterministic.** For any database not in the explicit
   list, alphabetical order prevents non-deterministic behaviour.

3. **A fixed list is simpler than scoring.** We could compute which database has
   more years of data or better coverage for a given country. That's complex and
   requires extra API calls. A fixed priority list is fast, predictable, and auditable.

---

## Where this lives in code

`src/core/constants.py` — the `DATABASE_PRIORITY` list.

`src/domain/indicator/deduplication.py` — the deduplication logic reads
`DATABASE_PRIORITY` to select the winning database_id when collapsing duplicates.

---

## Consequences

- If WB_WDI has a coverage gap for a specific indicator/country combination, but
  WB_ESG has it, the server will report the gap as a coverage warning rather than
  transparently falling back to WB_ESG. This is a deliberate trade-off: a predictable
  result with a warning is better than a silent fallback to a different database.
- The priority list is adjustable by editing `core/constants.py`. No other code needs
  to change.

---

## Revisit Condition

**Revisit this decision if:** real usage consistently shows that a higher-priority
database has systematically worse coverage than a lower-priority one for common
queries. At that point, a per-indicator coverage check may be worth the extra call.
