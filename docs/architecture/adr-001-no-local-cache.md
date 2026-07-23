# ADR-001: No Local Indicator Cache

**Status:** Accepted  
**Date:** 2026-07-23

---

## Context

The worldbank-mcp server needs to look up indicators by topic name. The World Bank
`/data360/searchv2` API provides full-text search across all indicator names and
descriptions. The question is whether to query this API live on every request, or to
pre-build and cache a local copy of the indicator catalogue.

---

## Decision

**All indicator discovery queries go live to the World Bank search API. No local
cache is built or maintained.**

---

## Reasoning

1. **Complexity vs benefit mismatch at this scale.** This project is learning-focused
   and used by a single AI agent, not a high-traffic service. The number of
   `search_indicator` calls per session is small. The latency of a live search call
   (typically <2 seconds with retry) is acceptable at this scale.

2. **Cache invalidation is non-trivial.** The World Bank dataset is updated
   periodically. A local cache requires a rebuild strategy, versioning, and
   detection of stale entries. This complexity is not justified by the current usage
   pattern.

3. **Live search is always fresh.** A query to `/searchv2` always reflects the
   current indicator catalogue. A cached catalogue can silently lag behind reality
   after a World Bank data release.

4. **The `mcp` architecture already constrains us.** The server is stateless between
   tool calls by design. Maintaining a warm in-memory cache across calls would
   require persistent state that conflicts with the process model.

---

## Consequences

- Each `search_indicator` tool call makes a live HTTP request to the World Bank API.
- The resilience layer (`infrastructure/resilience/retry_policy.py`) handles transient
  failures with exponential backoff, so occasional slow responses don't fail the call.
- Latency is bounded by the World Bank API response time (~1–2 s normally).

---

## Revisit Condition

**Revisit this decision if:** repeated identical searches from a single AI session
create a measurable latency problem, or if the World Bank API introduces rate limits
that make live-per-call infeasible. At that point, an in-process session-scoped
cache (not a persistent catalogue) is the first option to consider.
