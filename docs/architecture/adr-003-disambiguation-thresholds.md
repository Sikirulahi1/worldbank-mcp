# ADR-003: Disambiguation Thresholds — Three-Outcome Rule

**Status:** Accepted  
**Date:** 2026-07-23

---

## Context

After ranking and deduplication, `domain/indicator/disambiguation.py` must decide
which of three outcomes to return:

- **Outcome A (auto_resolve):** A single candidate with sufficient confidence. Return
  it directly without asking the user.
- **Outcome B (ask_user):** Multiple genuinely different concepts, or a single result
  that isn't confident enough to auto-resolve. Ask the user to choose or confirm.
- **Outcome C (not_found):** Zero results, or all results rejected as irrelevant.

The thresholds that separate these outcomes must be concrete, not vague. This ADR
records the working thresholds and the evidence behind them.

---

## Evidence from Real API Exploration

Real `@search.score` values observed from the World Bank `/data360/searchv2` API:

| Query | Top result name | Score |
|---|---|---|
| "GDP" | GDP growth (annual %) — WB_ESG | 21.649889 |
| "GDP" | GDP growth (annual %) — WB_GS  | 21.649889 |
| "GDP" | GDP growth (annual %) — WB_CLEAR | 20.819328 |
| "GDP" | GDP per person employed (const PPP $) | 20.595543 |

Observation: Same-concept duplicates score identically or within ~1 point of each
other. Different-concept results have scores that diverge more quickly.

The `@search.score` field is the relevance signal. It is not normalised (does not
have a fixed maximum) but is consistent within a single response.

---

## Decision — Working Thresholds

### Outcome C: Not Found
- **Condition:** Zero candidates remain after ranking and deduplication.
- **Also triggers when:** all candidates have `@search.score < 10.0`.
  (A score that low means the API found something, but it's almost certainly
  not what the user asked for.)
- **Returns:** `NotFound(reason="...")`

### Outcome A: Auto-Resolve
- **Condition:** After deduplication, exactly one candidate remains
  **and** its score is `>= WEAK_MATCH_SCORE_THRESHOLD` (15.0).
- **Returns:** the resolved `IndicatorCandidate` directly.

### Outcome B: Ask User
All remaining cases:
- Multiple candidates after deduplication (different concepts, not just different
  databases of the same concept).
- Single candidate with score `< WEAK_MATCH_SCORE_THRESHOLD` (15.0) — the score is
  low enough that auto-resolving would likely give the user the wrong indicator.
- **Returns:** `ClarificationNeeded(candidates=[...], context="...")`

---

## Where these live in code

- `src/core/constants.py` — `WEAK_MATCH_SCORE_THRESHOLD = 15.0`
- `src/domain/indicator/disambiguation.py` — implements the three-outcome logic
  using the constants above.

---

## Consequences

- A threshold of 15.0 has not yet been tested against the full range of query types.
  It is a calibration starting point, not a permanently settled value.
- Scores below 10.0 being treated as not-found is a conservative safety net. If real
  usage shows that valid queries regularly score 10–14, the threshold should be
  lowered.

---

## Revisit Condition

**Revisit this decision after:** the first 20–30 real tool calls have been observed.
If auto-resolve is firing for queries where the result was clearly wrong, raise
`WEAK_MATCH_SCORE_THRESHOLD`. If the AI is asked to clarify too often for clearly
unambiguous queries, lower it. This ADR must be updated when thresholds change.
