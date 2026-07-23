# World Bank MCP Project — Full Architecture Document

## 1. What We Are Building

We are building an MCP (Model Context Protocol) server called **worldbank-mcp**. Its job is to let an AI assistant (like Claude, or any LLM connected through a compatible client) answer questions about world development data — things like GDP growth, life expectancy, population, poverty rates, literacy rates — for any country, over any time range, by pulling live data from the World Bank's Data360 API.

The AI itself does not "know" this data. It doesn't have it memorised, and it shouldn't guess. Instead, when a user asks a question like *"What was Nigeria's GDP growth from 1990 to 2012?"*, the AI recognises it needs external data, calls a tool that we've built, that tool goes and fetches the real numbers from the World Bank, cleans them up, and hands them back to the AI so it can answer accurately.

The point of this project is not just "connect to an API." It's to learn how to build a properly structured, reliable, cost-efficient bridge between a messy real-world API and an AI model — handling ambiguity, errors, and formatting along the way.

---

## 2. The Core Problem We're Solving

The World Bank's Data360 API is not simple. It has three separate concerns tangled together:

1. **Discovery** — finding which "indicator code" corresponds to a topic a human would type in plain language (e.g., "GDP" could match several different indicator codes).
2. **Retrieval** — once you know the exact code, fetching the actual yearly data for a specific country.
3. **Noise** — the raw response from the API is bloated with repeated, irrelevant fields that don't need to reach the AI.

If we don't solve these three problems deliberately, the project either breaks (wrong data returned), becomes unreliable (inconsistent answers to the same question), or becomes expensive (wasting tokens and money passing around unnecessary data every single time a question is asked).

---

## 3. High-Level Roles in the System

There are three distinct "actors" in this system, and it's important to keep their responsibilities separate:

**The User** — the person asking a question in plain language, e.g. "show me Kenya's population growth from 2000 to 2015."

**The Client** — the application that holds the actual conversation. It has the connection to the AI model (the LLM), it manages the back-and-forth conversation, and it knows how to talk to one or more MCP servers to get information the AI needs. The client is the "chat app." It does not itself contain any World Bank–specific logic.

**The MCP Server (worldbank-mcp)** — this is what we are focused on building right now. It does not chat with anyone. It does not run an LLM. Its entire job is: expose a small set of well-defined "tools" that the client can call, and when called, go fetch and clean World Bank data, then return a clean result.

Keeping these three roles separate is the foundation of the whole design. The MCP server should be usable by *any* MCP-compatible client — Claude Desktop, a custom chatbot, anything — without needing to change a single line of the server's code.

---

## 4. Deployment Model — Standalone Process

**worldbank-mcp is a standalone MCP server process.** It is not bolted onto, embedded in, or merged with any other service (including SupportOS AI).

It communicates via the MCP protocol over stdio transport (the standard mode for connecting to clients like Claude Desktop). It does not expose HTTP routes, does not use FastAPI, does not require middleware or JWT auth, and does not share a process with anything else.

The reason for this is not just convenience — it's correctness for the use case:

- MCP servers speak a specific protocol over stdio or SSE transport. This is a different communication model from an HTTP request/response cycle. Bridging the two adds real complexity for no benefit here.
- Keeping it standalone preserves the core design goal: any MCP-compatible client can connect to it independently, without needing to know or care that any other service exists.
- It avoids entangling two unrelated projects' dependencies, deployment lifecycles, and test suites.

The fact that this project uses the same four-layer architecture (core / domain / application / infrastructure / presentation) as SupportOS AI is simply because that's a good pattern — not because the two are technically joined.

---

## 5. Technology Choices

These decisions are settled and should not be relitigated without a concrete reason:

| Concern | Choice | Reason |
|---|---|---|
| MCP SDK | `mcp` (the official Python SDK, maintained under the Model Context Protocol project) | It is the reference implementation. Claude Desktop and other mainstream clients are built to expect it. No need for a third-party wrapper at this project's scale. |
| HTTP client | `httpx` (async) | Supports both sync and async. Since MCP servers benefit from async — so a slow World Bank response doesn't block other tool calls — this is the correct default over `requests`. |
| Excel export | `openpyxl`, via `pandas` | `pandas` makes the table-merge step in `domain/report/table_merge.py` considerably simpler to write and test (merging multiple series into a single year-keyed table). `openpyxl` is used as the engine. `pandas` is worth including as a dependency even if it isn't used elsewhere. |
| CSV / JSON export | Python built-ins (`csv`, `json` modules) | No extra dependency needed. |
| Testing | `pytest` | Standard; no need to revisit. |
| Pipeline result type | Discriminated union of dataclasses in `core/result.py` | Three named outcome shapes (`DataResult`, `ClarificationNeeded`, `NotFound`) make pipeline outputs explicitly typed and testable with `isinstance`. Genuine infrastructure failures stay as named exceptions — not a fourth result type — so expected outcomes and unexpected breakage are never conflated. |

---

## 6. `core/result.py` — Pipeline Outcome Design

Every application pipeline in `application/` returns exactly one of three named outcome types, defined as dataclasses in `core/result.py`. The design uses a **discriminated union of dataclasses** — each class represents exactly one possible outcome, and callers check the type with `isinstance` (or a `match` statement in Python 3.10+).

### The three outcome types

**`DataResult`** — the successful case. Fields:
- `series`: the clean `IndicatorSeries` (or merged table for exports).
- `coverage_warnings`: a list of strings describing any gaps or out-of-range years. This is part of the success result, not a separate error — a coverage gap is a fact worth surfacing, not a failure.

**`ClarificationNeeded`** — the "ask the user" case. Fields:
- `candidates`: the shortlist of `IndicatorCandidate` objects (name + code) the AI has something concrete to present to the user.
- `context`: a short human-readable string explaining what was ambiguous (e.g., "'poverty' matched multiple distinct indicators").

**`NotFound`** — zero results. Fields:
- `reason`: a short human-readable string (e.g., "No indicator matched 'xyzzy'" or "No data available for this country/indicator combination").

### What stays as exceptions

Genuine infrastructure failures — network timeout exhausted, malformed API response, unsupported file format — stay as named exceptions from `core/exceptions.py`. They are raised up through the pipeline and caught at `presentation/mcp/tool_handlers.py`, which is the single place responsible for translating any uncaught exception into a clean MCP error response.

This keeps the result type meaningful: it answers "what did the pipeline learn?", not "did something break?". A pipeline that completes normally always returns one of the three outcome types above. A pipeline that breaks unexpectedly raises an exception. The two mechanisms are kept distinct.

---

## 7. The Tools Our MCP Server Exposes

A "tool" in MCP terms is simply a function the AI is allowed to call, with a clearly defined set of inputs and outputs. We are building four tools:

### Tool 1: Search Indicator
**Purpose:** Take a vague human topic (like "GDP" or "female literacy") and find the matching official indicator code(s) in the World Bank's system.

**How it works:** It sends a live search request to the World Bank's search endpoint, gets back a list of possible matches, ranks them by relevance, collapses same-concept duplicates across different databases, and strips away all the irrelevant technical noise in the response before returning just the useful part: the indicator's name and its code.

**Output:** A short list of candidate indicators (name + code), not the full unfiltered response.

### Tool 2: Get Indicator Data
**Purpose:** Given an exact, already-known indicator code, fetch the real numeric data for a specific country and time range.

**How it works:** It sends a live request to the World Bank's data endpoint using the exact code, country, and year range. The raw response is a list of yearly records, each stuffed with many repeated technical fields. This tool cleans that response so that only the information that actually matters is kept — the years, the values, and any details that genuinely differ from year to year — while anything that is identical across every record gets pulled out once and mentioned separately, instead of being repeated over and over.

**Output:** A clean, compact set of "year: value" pairs, plus basic context (what the indicator is, what units it's measured in, and any coverage gaps explicitly flagged).

### Tool 3: Get Country Indicator (the "convenience" tool)
**Purpose:** Combine the search step and the data-fetch step into one single action, for the common case where there's no real ambiguity about what the user means.

**How it works:** Internally, it performs the same steps as Tool 1 and Tool 2 back-to-back, without requiring the AI to make two separate decisions in the middle. The disambiguation rule (Section 8 below) determines whether it proceeds automatically or stops to ask the user. This tool produces exactly one of three outcomes: final clean data, a shortlist for the user to choose from, or a clear "nothing found" message.

**Output:** Either the final clean data (the common case), or a short list of choices for the user to pick from (the ambiguous case), or an explicit not-found message.

### Tool 4: Export Report
**Purpose:** Let a user request multiple indicators at once, for one country and one time range, and get the result back as an actual downloadable file (CSV, Excel, or JSON).

**How it works:** It repeats the process from Tool 3 for each requested indicator (looping through search-and-fetch for "GDP," then "life expectancy," then whatever else was asked for), merges all the resulting series into one combined table (rows = years, columns = indicators), and writes that table out to a file in the requested format.

**Output:** A short confirmation message and a path to the finished file. The raw row-by-row data never needs to be shown to the AI directly for this tool — only a summary of what was produced.

---

## 7. Why We Strip and Clean the Data (Not Just Pass It Through)

The raw response from the World Bank's data endpoint includes around 19 separate fields for every single year of data — most of which never change from row to row within one query (things like which database it came from, the frequency of measurement, unrelated classification codes). If we pass this raw response straight through to the AI without cleaning it, we waste a large amount of space and cost on information that adds no value, for every single question a user asks.

The solution is a generic cleaning process that works for any indicator, not just the ones we've tested:

For each field in the response, we check whether its value is the same across every row of that particular result. If it is the same everywhere, it gets pulled out once as shared context (e.g., "this is measured as an annual percentage"). If it actually changes from row to row (which is normally just the year and the value, but occasionally other things too, depending on the indicator), it gets kept as part of the real data table.

This means the cleaning logic — implemented in `domain/shaping/field_analysis.py` and `domain/shaping/series_builder.py` — doesn't need to know in advance which specific indicator is being asked about. It adapts automatically to whatever shape of data comes back.

**Special case — single-row responses:** If the response contains only one row, every field will look "constant" by definition. The logic must not wrongly treat a single-row response as having no meaningful data. Year and value fields must always be classified as varying/meaningful regardless of row count.

---

## 8. The Disambiguation Rule (Concrete Thresholds)

Some topics a user asks about will map cleanly to exactly one indicator. Others will be genuinely ambiguous. The disambiguation rule in `domain/indicator/disambiguation.py` classifies every search result into exactly one of three outcomes:

### Outcome A — Auto-resolve (proceed without asking)
Triggered when:
- There is exactly one result **and** it is a clearly confident match (not a weak/low-relevance hit).
- There are multiple results **but** they are the same underlying concept filed under different internal databases (the "GDP growth appears in WB_WDI, WB_ESG, and WB_GS" case). These are collapsed by `domain/indicator/deduplication.py` using the fixed database-priority tie-break rule (see ADR-002), and the surviving single result is then treated as unambiguous.

### Outcome B — Ask the user (return a shortlist)
Triggered when:
- There is exactly one result but it is a **weak/low-confidence match** — meaning the system isn't sure this result is even a good answer for the topic at all, not just that it's competing against other options. In this case, the single result is returned as a suggestion and the user is asked to confirm, rather than silently trusting a shaky answer.
- There are multiple results **and** they represent genuinely different concepts (different indicator names, not just different database sources for the same concept). The "poverty" example: poverty headcount ratio, poverty gap, and multidimensional poverty index are truly different measurements — the user must choose.

### Outcome C — Not found (report clearly)
Triggered when:
- The search returned zero results for the given topic.

These thresholds should be treated as the starting point. They are adjustable once real searches reveal whether the boundary between "weak single match" and "confident single match" needs to be tuned. The guiding principle is: **never silently guess when there is genuine uncertainty; only bother the user when the uncertainty is real.**

---

## 9. Human-in-the-Loop Disambiguation (The Flow)

When the disambiguation rule produces Outcome B, the flow works like this:

1. The search step finds candidates and the disambiguation rule returns "ask the user."
2. Rather than picking one automatically, the tool returns the shortlist back to the AI.
3. The AI presents these options to the user in plain language and asks which one they meant.
4. The user picks one.
5. The AI then calls the data-fetching tool again, this time using the exact code the user selected — no more guessing involved.
6. If the user needs more than one indicator (say, GDP and life expectancy), this same disambiguation process happens separately for each one, one at a time, only when needed.

If the disambiguation rule produces Outcome A (including the deduplication-collapsed case), the system proceeds straight to fetching the data without asking the user anything.

This approach makes the final answer trustworthy: whenever there was real uncertainty, a human explicitly made the choice.

---

## 10. The Full Request Lifecycle (Step-by-Step Example)

Here is exactly what happens, from start to finish, when a user asks a question:

**User asks:** "Give me Nigeria's GDP growth and life expectancy from 1990 to 2012 as an Excel file."

1. The AI understands this requires fetching data and producing a file, so it calls the Export Report tool with the country, the year range, the list of topics requested, and the desired file format.
2. Inside the MCP server, for the first topic ("GDP growth"), the system searches for matching indicators via `infrastructure/worldbank_client/search_client.py`.
3. The raw candidates are ranked by `domain/indicator/ranking.py`, then same-concept duplicates collapsed by `domain/indicator/deduplication.py`, then evaluated by `domain/indicator/disambiguation.py`.
4. If there's a clear single best match (Outcome A), it proceeds automatically. If there are multiple genuinely different matches (Outcome B), it pauses and returns the shortlist; once the user picks one, it continues.
5. Once the exact indicator is confirmed, `infrastructure/worldbank_client/data_client.py` fetches the real yearly data for Nigeria between 1990 and 2012.
6. `domain/shaping/field_analysis.py` and `domain/shaping/series_builder.py` clean the response. `domain/shaping/coverage.py` checks for any gaps or out-of-range years and flags them explicitly.
7. The same process (steps 2–6) repeats for the second topic ("life expectancy").
8. Once both data series are ready, `domain/report/table_merge.py` merges them into a single table, organised by year.
9. `infrastructure/file_export/excel_writer.py` writes the table to an `.xlsx` file.
10. The MCP server returns a short message back to the AI: essentially, "Here is a file with GDP growth and life expectancy for Nigeria, 1990–2012," along with the file path.
11. The AI shares this result with the user in natural language, along with the file.

Notice that at no point does the AI need to see or process the full raw data table itself — it just orchestrates the process and reports the outcome.

---

## 11. Edge Cases and How Each One Is Handled

**No indicator found for the topic requested.** The system returns Outcome C from the disambiguation rule — a clear "nothing found" message — rather than crashing or returning an empty result.

**Ambiguous topic with genuinely different meanings.** Outcome B from the disambiguation rule — the shortlist is returned to the AI for the user to choose from.

**Duplicate-looking results across different internal databases.** Deduplication collapses these to a single representative result using the fixed database-priority rule (see ADR-002), then auto-resolves via Outcome A. The user is never bothered with a distinction they don't care about.

**Weak single match.** Outcome B — the single result is returned as a suggestion and the user is asked to confirm, rather than it being silently trusted.

**Ambiguous country names.** Handled by `domain/country/resolution.py` against the static reference list in `domain/country/reference_data.py`. "Congo" returns an explicit ask-which-one response; a name that matches nothing returns a clear not-found.

**Missing data for specific years.** Shown explicitly as unavailable by `domain/shaping/coverage.py` — not silently skipped or filled in with guesses.

**Indicator exists but no data at all for the requested country.** A valid outcome reported clearly — "no data recorded for this country/indicator combination" — not an error.

**Requested time range falls outside what's actually available.** `domain/shaping/coverage.py` identifies this and clearly states the real available range, rather than quietly returning partial results. The real available range is retrieved from the World Bank's metadata endpoint via `infrastructure/worldbank_client/metadata_client.py`, which confirmed during API exploration that the `time_periods.start` / `time_periods.end` fields live in the `/metadata` response, not embedded in `searchv2` output.

**Very large result sets / pagination.** `infrastructure/worldbank_client/data_client.py` handles the pagination loop so that all pages of results are fetched transparently, even when a single API response doesn't contain the full result set.

**Temporary failures or rate limiting.** `infrastructure/resilience/retry_policy.py` retries a small number of times with backoff. `infrastructure/resilience/rate_limit_handler.py` handles 429 responses specifically. Only genuinely temporary failures trigger a retry — a permanent failure (invalid indicator code) fails cleanly after a bounded number of attempts, not indefinitely.

**Unexpected or malformed responses.** `infrastructure/worldbank_client/response_parser.py` validates the response shape before handing it to the domain. If the response doesn't look like expected data, a clear, honest error is returned rather than a confusing crash.

---

## 12. Layer Architecture and File Structure

The project is organised into four layers. The dependency rule is strict: each layer may only depend on layers listed below it — never upward.

```
presentation/mcp/        ← outermost: MCP tool definitions, registration, server startup
application/             ← orchestration: pipelines that compose domain + ports
domain/                  ← pure logic: no I/O, no network, no side effects
infrastructure/          ← external connections: HTTP client, file writers, resilience
core/                    ← cross-cutting: config, constants, exceptions, result types
```

The `application/ports/` directory contains the abstract interfaces (`search_port.py`, `data_port.py`, `file_writer_port.py`) that the application layer depends on. The `infrastructure/` layer provides the concrete implementations. This inversion of dependency means:

- Application pipelines can be tested completely using fake/stub ports — no real HTTP calls needed.
- If the World Bank ever changes their API, only `infrastructure/worldbank_client/` needs to change. Nothing in `domain/` or `application/` is affected.
- A second data source could be added later as a new infrastructure adapter, without touching anything that already works.

**`infrastructure/worldbank_client/metadata_client.py` — confirmed necessary, narrow scope.** Real API responses confirmed that the indicator year-coverage information (`time_periods.start` / `time_periods.end`) lives in the `/metadata` response and is not embedded in `searchv2` output. This client is therefore genuinely needed — but its scope is limited to that single query. It should not grow into a general-purpose metadata wrapper. It fetches year coverage for a given indicator code, and nothing else.

**`presentation/mcp/server.py` and `run.py` — stdio only, no HTTP server.** `run.py`'s entire job is to construct the MCP server instance (with all four tools registered via `server.py`) and hand control to the `mcp` SDK's stdio server loop. There is no web framework, no port binding, and no `uvicorn` anywhere in this file. This must be kept explicit to avoid habits carrying over from FastAPI-shaped codebases.

The proposed directory structure for the full project is documented separately in `docs/additions/proposed_structure.md`.

---

## 13. Architecture Decision Records

Three decisions from this document are recorded as standalone ADRs in `docs/architecture/`:

- **ADR-001** (`adr-001-no-local-cache.md`): No locally cached indicator catalogue. All discovery goes live to the World Bank's search API. The project is learning-focused and small-scale; the complexity of cache-building and invalidation is not justified at this stage. **Revisit if:** repeated identical searches create a measurable latency or cost problem in practice.
- **ADR-002** (`adr-002-database-priority-tiebreak.md`): When the same indicator concept appears under multiple World Bank database IDs, a fixed priority order is used to select the canonical one (e.g., WB_WDI preferred over WB_ESG, WB_GS, WB_CLEAR). This rule is stored in `core/constants.py`.
- **ADR-003** (`adr-003-disambiguation-thresholds.md`): The concrete thresholds for the three-outcome disambiguation rule described in Section 9 above.

Two further design decisions are documented inline in this document rather than as separate ADRs, because they are architectural constraints rather than one-off choices:

- **`core/result.py` discriminated union design** — described in full in Section 6. Decision: three named dataclass outcomes; infrastructure failures stay as exceptions. This keeps result types meaningful and exception handling distinct.
- **`metadata_client.py` narrow scope** — described in Section 13's layer notes. Decision: the client is confirmed necessary (coverage data lives in `/metadata`), scope is permanently limited to year-coverage lookups only.

---

## 14. The Client's Role, Kept Simple

The MCP server we're building is not a chatbot, and it doesn't have its own "ask a question" interface. It's a set of tools that any properly connected AI assistant application can use. Testing and using this project means connecting it to an existing MCP-compatible AI chat application (such as Claude Desktop) that already knows how to have conversations and call tools — so that we can focus entirely on making sure the World Bank data-fetching logic itself is correct, clean, reliable, and well-organised, without needing to also build a chat interface.

---

## 15. Summary of the Goal

By the end of this project, we will have a small, focused, well-organised standalone MCP server that can take a plain-language question about world development data for any country and any time range, resolve any ambiguity about exactly which data is meant (asking the user when it's genuinely unclear, and proceeding automatically when it isn't), fetch the real numbers live from the World Bank, clean and shape the response so it's efficient and easy to use, and — when asked — package multiple pieces of data together into a downloadable file. Every part of this is designed to be predictable, cost-efficient, and honest about its limitations, rather than guessing or hiding uncertainty from the user.