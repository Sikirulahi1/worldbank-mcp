# World Bank MCP Project — Step-by-Step Build Plan

This plan takes the architecture we already agreed on and turns it into a clear sequence of stages, from nothing to a fully working worldbank-mcp server. Each step says what to do, why it matters, what "done" looks like, and which edge cases must be handled at that specific step (not later).

**Settled decisions that this plan assumes:**
- **Runtime:** Standalone MCP server process using the official `mcp` Python SDK. Not embedded in SupportOS AI or any FastAPI service.
- **HTTP client:** `httpx` (async).
- **Excel writer:** `openpyxl` via `pandas` (pandas makes the table-merge step in Phase 1 considerably easier).
- **CSV/JSON:** Python built-ins (`csv`, `json`), no extra dependency.
- **No local indicator cache** — all discovery goes live to the World Bank API (see ADR-001).
- **Database priority tie-break rule** — when duplicates collapse, always prefer in this order: WB_WDI > WB_WDI_GEP > WB_ESG > WB_GS > WB_CLEAR > others alphabetically (see ADR-002). This list lives in `core/constants.py`.
- **Disambiguation thresholds** — three concrete outcomes from `domain/indicator/disambiguation.py` (see ADR-003 and Section 8 of the architecture document). These are the working thresholds to test against; they are adjustable once real search results reveal where they feel wrong.

---

## Phase 0: Preparation — Before Writing Any Logic

### Step 0.1: Set up the project skeleton
Create the full directory structure exactly as laid out in `docs/additions/proposed_structure.md`. This includes:
- `src/core/`, `src/domain/`, `src/application/`, `src/infrastructure/`, `src/presentation/`
- `tests/unit/`, `tests/integration/`, `tests/e2e/`, `tests/fixtures/sample_responses/`
- `docs/architecture/`

Nothing needs real code yet — just placeholder files (`__init__.py` where needed, empty `.py` stubs) and the three ADR files in `docs/architecture/` with their decisions written in plain prose. This matters because it forces you to think about where things belong before you're under pressure to "just make it work."

**Also set up at this step:**
- `requirements.txt` with pinned versions for: `mcp`, `httpx`, `pandas`, `openpyxl`, `pytest`, `pytest-asyncio`.
- `.env.example` with any config the server will need (World Bank base URL, timeout, max retries — see `core/config.py`).
- `run.py` as the entrypoint that starts the MCP server — **this file must contain no HTTP server startup code of any kind.** Its only job is constructing the MCP server instance and starting the `mcp` SDK's stdio loop.
- `core/result.py` with the three pipeline outcome dataclasses: `DataResult` (with `series` and `coverage_warnings` fields), `ClarificationNeeded` (with `candidates` and `context` fields), and `NotFound` (with a `reason` field). Write these now, before any pipeline code, so every step in Phase 1 and Phase 3 has something concrete to return. The design is a discriminated union of dataclasses — callers check outcomes with `isinstance`. **Do not add a `Failure` type:** infrastructure failures stay as named exceptions from `core/exceptions.py` and are caught at the presentation layer, not wrapped as a result.

**Done when:** the folder structure exists and matches `proposed_structure.md`, `core/result.py` is importable with all three outcome types defined, the three ADRs are written, requirements are pinned, and no pipeline logic has been written yet.

### Step 0.2: Manually explore the World Bank API by hand first
Before writing a single line of the server, manually test the search endpoint (`/searchv2`), the data endpoint (`/data360/data`), and the metadata endpoint, directly via curl or a browser tool, for a handful of different topics — not just GDP.

Try:
- A very common, unambiguous topic (e.g., "population").
- A topic that returns genuine same-concept duplicates across databases (e.g., "GDP growth").
- A topic that is genuinely ambiguous — different concepts with different names (e.g., "poverty").
- A topic that returns nothing or very little (something obscure).
- Deliberately sending an invalid indicator code and an invalid country code, to observe the error response shape.

**Save the raw JSON responses** as test fixture files in `tests/fixtures/sample_responses/`. These are your permanent test fixtures — Phase 1 uses them to test domain logic without any network calls. Aim to have at minimum:
- `search_gdp_clean.json` — a single unambiguous result
- `search_gdp_duplicates.json` — same concept across multiple databases
- `search_poverty_ambiguous.json` — genuinely different concepts
- `search_nonsense_empty.json` — zero results
- `data_nigeria_gdp_1990_2012.json` — a clean data fetch with multiple years
- `data_zero_records.json` — a valid indicator/country combination with no data
- `data_error_response.json` — an error response from a bad request

**Also note during this exploration:**
- What the pagination parameters look like and at what result-set size the API starts paginating.
- What "relevance score" or similar field the searchv2 endpoint returns, if any — this directly informs the weak-match threshold in ADR-003.
- **What field provides the real available year range for an indicator — confirmed: this is the `time_periods.start` / `time_periods.end` field in the `/metadata` endpoint response, not embedded in `searchv2` output.** Save an example metadata response for the indicator you tested so Step 2.5 has a real fixture to work against. Note the exact endpoint path and request shape required to retrieve it.
- The scope of `metadata_client.py` is therefore settled now: it fetches year coverage for a given indicator code from `/metadata` only. It does not implement any other metadata or disaggregation queries. Write this scoping decision into your exploration notes explicitly so the client stays minimal.

**Done when:** all fixture files above exist as real saved JSON responses, you have a saved metadata response fixture, and you have written notes covering the pagination shape, the relevance score field name, the confirmed `/metadata` year-range field path, and the `metadata_client.py` scope constraint.

### Step 0.3: Write the three ADRs
Using your exploration from Step 0.2, fill in the three ADR documents with their concrete decisions:

- **ADR-001** (`adr-001-no-local-cache.md`): Decision (live API calls, no cache), reasoning, and the explicit "revisit if" condition (repeated identical searches create a measurable latency or cost problem).
- **ADR-002** (`adr-002-database-priority-tiebreak.md`): The database priority list (WB_WDI first, etc.), where it lives in code (`core/constants.py`), and the reasoning.
- **ADR-003** (`adr-003-disambiguation-thresholds.md`): The three-outcome rule (auto-resolve, ask-user, not-found), the concrete conditions for each, the definition of "weak match" based on what the real search response looks like, and the "adjustable once we see real data" note.

**Done when:** all three ADRs are written, concrete, and not vague placeholders. Anyone reading them can implement the rules directly from the text.

---

## Phase 1: The Pure Logic Layer (Domain)

This phase deliberately has zero network calls. Everything here is tested using only the fixture files saved in Step 0.2.

### Step 1.1: Country code resolution (`domain/country/`)
Build `domain/country/reference_data.py` (the static country list — ISO codes, names, and common aliases), `domain/country/entities.py` (the `Country` dataclass), and `domain/country/resolution.py` (the resolution logic).

The resolution function takes a plain-language country mention and returns one of: a single matched `Country`, a list of candidates (ambiguous — e.g., "Congo"), or a not-found result.

**Edge cases to handle here:**
- Partial or misspelled names (fuzzy match or alias lookup).
- Alternate names for the same country (e.g., "Ivory Coast" / "Côte d'Ivoire").
- A name that matches nothing at all.

**Done when:** `tests/unit/domain/country/test_resolution.py` passes for a clean match, an ambiguous match, a misspelled match, and a no-match case, using only the static reference data — no network.

### Step 1.2: Indicator entities (`domain/indicator/entities.py`)
Define the data classes that the rest of the domain and application layers use: `IndicatorCandidate`, `IndicatorSeries`, `Observation`. These are pure data — no methods that touch anything external.

**Done when:** the dataclasses are importable and their fields match what the fixture files from Step 0.2 would produce after parsing.

### Step 1.3: Indicator deduplication (`domain/indicator/deduplication.py`)
Using your `search_gdp_duplicates.json` fixture, write the logic that collapses same-concept results across different databases down to the one with the highest priority in the `DATABASE_PRIORITY` constant from `core/constants.py`.

The function signature is: given a list of `IndicatorCandidate`, return a deduplicated list.

**Edge cases to handle here:**
- A group of duplicates where the highest-priority database isn't in the result (fall through to the next in priority).
- A single-item list (deduplication is a no-op — must not error or lose the item).
- A list where all items are genuinely different concepts (no duplicates — all items survive unchanged).

**Done when:** `tests/unit/domain/indicator/test_deduplication.py` passes for all three cases above.

### Step 1.4: Indicator ranking (`domain/indicator/ranking.py`)
Write the logic that scores and sorts a raw list of `IndicatorCandidate` by relevance. Use whatever relevance signal the searchv2 endpoint provides (noted in Step 0.2). The output is a sorted list, most relevant first.

**Done when:** `tests/unit/domain/indicator/test_ranking.py` passes using fixture data, and the sort order is stable (same input always produces the same output).

### Step 1.5: Indicator disambiguation (`domain/indicator/disambiguation.py`)
Using the ranked, deduplicated list from Steps 1.3 and 1.4 as input, implement the three-outcome rule from ADR-003:
- **Outcome A (auto_resolve):** single confident match, or duplicates already collapsed to one.
- **Outcome B (ask_user):** single weak/low-confidence match, or multiple genuinely different concepts.
- **Outcome C (not_found):** zero results.

Return type must be one of the three dataclasses from `core/result.py`:
- Outcome A → return the resolved `IndicatorCandidate` directly (the caller in Phase 3 will pass it to `get_indicator_data`).
- Outcome B → return `ClarificationNeeded(candidates=[...], context="'poverty' matched multiple distinct indicators")`.
- Outcome C → return `NotFound(reason="No indicator matched 'xyzzy'")`.

**Edge cases to handle here:**
- Zero candidates → `NotFound`.
- One candidate, strong match → resolved candidate (auto-resolve).
- One candidate, weak match → `ClarificationNeeded` with a single-item shortlist and a "please confirm" context message.
- Multiple candidates, all same concept (already deduplicated) → shouldn't occur at this stage, but handle gracefully as auto-resolve.
- Multiple candidates, different concepts → `ClarificationNeeded`.

**Done when:** `tests/unit/domain/indicator/test_disambiguation.py` passes for each case using your real fixture files. Each outcome must be asserted by type — `assert isinstance(result, ClarificationNeeded)` — and the relevant fields (`candidates`, `reason`) inspected to confirm correctness.

### Step 1.6: Indicator validation (`domain/indicator/validation.py`)
Write the pure validation rules: is this indicator code syntactically well-formed, is this year range plausible (start ≤ end, both reasonable years), is this country code a valid ISO code.

**Done when:** `tests/unit/domain/indicator/test_validation.py` covers valid and invalid inputs for each rule.

### Step 1.7: Response shaping (`domain/shaping/`)
Using your `data_nigeria_gdp_1990_2012.json` and `data_zero_records.json` fixtures:

**`field_analysis.py`:** Given a list of raw observation rows, classify each field as either "constant" (same value across all rows) or "varying" (changes from row to row). Return two collections: constant fields with their shared value, and varying field names.

**Special case (single-row response):** When there's only one row, every field looks "constant" by definition. Year and value fields must always be classified as "varying" regardless of row count. Do not wrongly treat a single-row response as having no meaningful data.

**`series_builder.py`:** Given the varying fields from `field_analysis.py`, construct the clean `{year: value}` structure, plus the shared context metadata from the constant fields.

**`coverage.py`:** Given the requested year range and the actual years present in the data, identify: years within range that have `null`/missing values (gaps), and whether the requested range extends beyond the indicator's real available range. Produce explicit annotations rather than silently omitting data.

**Done when:** `tests/unit/domain/shaping/` passes for a normal multi-year response, a single-row response (edge case), a zero-record response, and a range that partly exceeds available data.

### Step 1.8: Report table merge (`domain/report/table_merge.py`)
Write the logic that takes multiple `IndicatorSeries` objects and merges them into a single year-keyed table (a dict or pandas DataFrame — pandas is recommended here). Rows are years, columns are indicator names/codes.

**Edge cases to handle here:**
- Indicators that don't share the same set of years (fill with `None`/`NaN` for missing years).
- A single indicator (table with one data column — valid, not an error).
- All indicators having no data (produce an explicitly empty table, not crash).

**Done when:** `tests/unit/domain/report/test_table_merge.py` passes for a clean multi-indicator merge, a mismatched-years merge, and an all-empty case.

---

## Phase 2: The External Connection Layer (Infrastructure)

Now, and only now, do we connect to the real World Bank servers.

### Step 2.1: Shared HTTP client setup (`infrastructure/worldbank_client/http.py`)
Set up the shared `httpx.AsyncClient` instance — base URL, headers, timeout settings from `core/config.py`. This is the one place that knows how to construct the client; everything else imports from here.

**Done when:** the client is importable and configurable via env vars.

### Step 2.2: Response parser (`infrastructure/worldbank_client/response_parser.py`)
Write the code that translates raw World Bank JSON into domain entities (`IndicatorCandidate`, `Observation`). This is the single point that knows the shape of their JSON — if their schema changes, only this file needs to change.

Include explicit shape validation: if the response doesn't look like expected data (missing required keys, unexpected types), raise a clearly named exception from `core/exceptions.py` rather than letting a `KeyError` propagate from deep inside the app.

**Done when:** parsing is testable from the Step 0.2 fixture files, and a malformed fixture produces a clear, named error — not a Python built-in exception.

### Step 2.3: Search client (`infrastructure/worldbank_client/search_client.py`)
Implement the `SearchPort` interface from `application/ports/search_port.py` — makes a live request to the World Bank's search endpoint and returns raw parsed candidates.

**Error cases to handle distinctly:**
- Request timeout.
- Server temporarily unreachable (connection error).
- Server returns a non-200 status.
- Server returns a 200 but with a malformed body (delegate to `response_parser.py`).

Each of these should produce a distinct named exception, not one generic "something went wrong" error.

**Done when:** a live search for "GDP" returns a non-empty list of candidates. Each of the four failure cases above has been deliberately triggered (e.g., using a wrong base URL to simulate unreachability) and produces the right exception without crashing the process.

### Step 2.4: Data client (`infrastructure/worldbank_client/data_client.py`)
Implement the `DataPort` interface — makes a live request to the `/data360/data` endpoint, handles pagination transparently (fetching all pages until exhausted), and returns the full list of raw observations.

**Error cases to handle distinctly:**
- Same four network-level failures as Step 2.3.
- A valid request that returns zero records (not an error — return empty list).
- A year range that is partly outside the indicator's coverage (return whatever is available, let `coverage.py` in the domain layer flag the gap).

**Done when:** a live data request for a known indicator/country/year-range returns results. A zero-data case has been deliberately tested and returns an empty list without error. Pagination has been thought through even if it can't be easily triggered in testing.

### Step 2.5: Metadata client (`infrastructure/worldbank_client/metadata_client.py`)
Fetch the real available year range for a given indicator code from the World Bank's `/metadata` endpoint.

**Scope is permanently limited to this one query.** The `/metadata` endpoint returns more than just year coverage, but this client must not grow into a general-purpose metadata wrapper. The only method it needs to expose is something like `async def get_coverage(indicator_code: str) -> tuple[int, int]` (returning `start_year`, `end_year`). Anything beyond that belongs in a separate, explicitly justified client.

**Confirmed from API exploration (Step 0.2):** year coverage lives in `time_periods.start` / `time_periods.end` within the `/metadata` response, not in `searchv2` output. Use the saved metadata fixture from Step 0.2 to drive the parser.

**Error cases to handle distinctly:**
- Same four network-level failures as Step 2.3.
- A metadata response where `time_periods` is missing or malformed — raise a named `MetadataParseError`, not a bare `KeyError`.

**Done when:** you can retrieve the real available year range for a known indicator from the live API, and the result matches what you observed manually in Step 0.2. A malformed metadata response raises `MetadataParseError` cleanly.

### Step 2.6: Resilience wrappers (`infrastructure/resilience/`)
Wrap the clients from Steps 2.3–2.5 with retry logic:

**`retry_policy.py`:** Retry on: timeout, connection error, and 5xx server errors. **Do not retry** on: 4xx client errors (invalid code, invalid country — these will never succeed no matter how many times you retry). Use exponential backoff. Max retries configurable via `core/config.py`.

**`rate_limit_handler.py`:** Handle 429 responses specifically — respect the `Retry-After` header if present, otherwise wait a fixed interval.

**Done when:** you can simulate a temporary failure (e.g., by pointing at a temporarily wrong URL, then fixing it) and see a successful result after retry. A permanent failure (invalid indicator) fails cleanly after the configured retry limit, not indefinitely.

### Step 2.7: File writers (`infrastructure/file_export/`)
Implement the `FileWriterPort` interface for all three formats:

- **`csv_writer.py`:** Uses Python's built-in `csv` module. Rows = years, columns = indicator names.
- **`excel_writer.py`:** Uses `pandas` + `openpyxl` engine. Same table structure.
- **`json_writer.py`:** Uses Python's built-in `json` module. Year-keyed nested structure.

**Edge cases to handle here:**
- An empty table (zero data for all indicators): produce a file with only the header row / an empty JSON object — not a broken or zero-byte file.
- An unsupported format string: raise a clearly named `UnsupportedFormatError` from `core/exceptions.py`, not a silent failure.

**Done when:** `tests/integration/test_file_writers.py` actually opens the produced CSV, XLSX, and JSON files and asserts their contents are correct, including the empty-table case.

---

## Phase 3: The Orchestration Layer (Application)

This is where pure domain logic and infrastructure connections are composed into the actual step-by-step tool behaviors. **Application pipelines depend only on port interfaces, never directly on infrastructure classes.** This is what makes them testable with fakes.

### Step 3.1: `application/ports/` — define abstract interfaces
Write the three port interfaces:
- `SearchPort` — abstract async `search(topic: str) -> list[IndicatorCandidate]`
- `DataPort` — abstract async `fetch(indicator_code: str, country_code: str, start_year: int, end_year: int) -> list[Observation]`
- `FileWriterPort` — abstract `write(table, format: str) -> Path`

These are the contracts. Infrastructure implements them. Application pipelines depend on them. Neither side is imported directly by the other.

**Done when:** the three abstract classes exist and are importable.

### Step 3.2: Search Indicator pipeline (`application/search_indicator/`)
Compose: call `SearchPort.search()` → rank candidates (`domain/indicator/ranking.py`) → deduplicate (`domain/indicator/deduplication.py`) → return clean candidate list.

**Edge cases to handle here:**
- Zero results → return a clear not-found DTO, not an empty list with no context.
- Very large raw result set → trim to a reasonable maximum number of candidates before returning (the number should be a named constant in `core/constants.py`).

**Test approach:** `tests/unit/application/test_search_indicator_pipeline.py` uses a fake `SearchPort` that returns the Step 0.2 fixture data — no real HTTP call.

**Done when:** the pipeline produces correct, clean candidate lists for all four search fixture files.

### Step 3.3: Get Indicator Data pipeline (`application/get_indicator_data/`)
Compose: validate inputs (`domain/indicator/validation.py`) → call `DataPort.fetch()` → shape response (`domain/shaping/field_analysis.py`, `domain/shaping/series_builder.py`) → check coverage (`domain/shaping/coverage.py`) → return clean DTO.

**Edge cases to handle here:**
- Missing years within the range appear as explicit `null` entries in the result DTO — not silently skipped.
- Zero-data result → returned as a valid, clearly described outcome, not an error.
- Out-of-range request → coverage check flags the discrepancy, and the real available range is included in the response.

**Test approach:** fake `DataPort` returning fixture files.

**Done when:** each of the three edge cases above has been deliberately triggered and produces a clear, correct DTO.

### Step 3.4: Get Country Indicator pipeline (`application/get_country_indicator/`)
Compose: resolve country (`domain/country/resolution.py`) → run `search_indicator` pipeline → apply disambiguation rule (`domain/indicator/disambiguation.py`) → if auto-resolve, run `get_indicator_data` pipeline → return result.

Returns one of three outcome types (from `core/result.py`): `DataResult`, `ClarificationNeeded`, or `NotFound`.

**Edge cases to handle here:**
- All three disambiguation outcomes (A, B, C) must be exercised by the right fixture inputs.
- Ambiguous country name → `ClarificationNeeded` at the country-resolution step, before indicator search even starts.
- Country not found → `NotFound` immediately.

**Test approach:** fake `SearchPort` and `DataPort`.

**Done when:** using your real fixture files, you can demonstrate: a clean topic auto-resolves and returns data, a genuinely ambiguous topic returns `ClarificationNeeded` with a shortlist, and a nonsense topic returns `NotFound`. Each outcome is asserted in `tests/unit/application/test_get_country_indicator_pipeline.py`.

### Step 3.5: Export Report pipeline (`application/export_report/`)
Compose: for each requested topic, run the `get_country_indicator` pipeline → if any produce `ClarificationNeeded`, apply the partial-failure policy (see below) → merge resolved series with `domain/report/table_merge.py` → write file with `FileWriterPort`.

**Partial-failure policy (decided now, not left ambiguous):**
- If one indicator out of several can't be resolved cleanly (ambiguous or not found), the export **pauses and reports the unresolved indicator back to the user** — it does not silently skip it or produce a file with a silent gap. The user gets a clear message: "I couldn't resolve X — please clarify, then try again" or similar.
- If **all** requested indicators fail, the export does not produce a file at all. It returns a clear error message, not an empty or broken file.

**Edge cases to handle here:**
- Partial failure (some indicators resolve, some don't) → pause and report, per policy above.
- Total failure → clear error, no file produced.
- Unsupported file format → `UnsupportedFormatError` propagated cleanly to the MCP tool handler.

**Test approach:** fake `SearchPort`, `DataPort`, and `FileWriterPort`.

**Done when:** partial-failure and total-failure scenarios both produce clear, correct DTOs, and a successful multi-indicator export produces the correct merged table in `tests/unit/application/test_export_report_pipeline.py`.

---

## Phase 4: The Exposed-Tools Layer (Presentation / MCP)

### Step 4.1: Tool schemas (`presentation/mcp/schemas/`)
For each of the four tools, define the JSON schema in its own file:
- Required vs optional parameters clearly marked.
- `format` parameter in `export_report_schema.py` restricted to the exact enum: `["csv", "xlsx", "json"]`.
- Parameter descriptions written for an AI consumer — they should be unambiguous enough that the AI knows exactly what to pass.

**Done when:** each schema is complete enough that someone unfamiliar with the project can read it and know exactly what to send and what to expect back.

### Step 4.2: Tool handlers (`presentation/mcp/tool_handlers.py`)
Write the thin glue layer: MCP tool call → parse and validate inputs using the schema → construct the appropriate input DTO → call the application pipeline → translate the result DTO back to an MCP-formatted response.

This layer contains no business logic. It only translates between the MCP protocol's data shapes and the application layer's DTOs.

**Done when:** each of the four tools has a handler that can be called with valid input and produces a valid MCP result.

### Step 4.3: Server registration and startup (`presentation/mcp/server.py` and `run.py`)
Register all four tool handlers with the `mcp` SDK, configure the transport (stdio for Claude Desktop compatibility), and expose the server startup via `run.py`.

**Done when:** `python run.py` starts the server successfully. Using an MCP inspection tool or test client, all four tools appear with their descriptions and expected parameters. The server can receive a tool call and return a result without crashing. **`run.py` contains no HTTP server startup code of any kind — no `uvicorn`, no `gunicorn`, no `app.run()`. Its only job is constructing the MCP server instance (via `presentation/mcp/server.py`) and calling the `mcp` SDK's stdio server loop.** Verify this explicitly before marking this step done, since the habit from FastAPI-shaped projects is to start a web server here.

---

## Phase 5: End-to-End Testing With a Real Client

### Step 5.1: Connect to Claude Desktop
Add the server to Claude Desktop's MCP configuration. Point it at your `run.py` entrypoint.

**Done when:** you can ask a natural-language question in Claude Desktop and see it correctly call one of your tools and get a sensible answer back.

### Step 5.2: Deliberately exercise every edge case through conversation
Go back through every edge case from Phases 0–4 and trigger each one through a real conversation:
- Ask an ambiguous question → confirm you're asked to choose.
- Ask about a nonsense topic → confirm you get a clear not-found response.
- Ask for a very old year range → confirm you're told what's really available.
- Ask for an export with multiple indicators including one ambiguous one → confirm the export pauses and asks for clarification rather than silently skipping.
- Ask for a multi-indicator Excel export that works cleanly end-to-end → confirm the file is correct and openable.
- Ask about a country with no data for a known indicator → confirm you get a clear "no data" response, not an error.

**Done when:** every edge case from earlier phases has been triggered and correctly handled through actual conversation — not just isolated unit tests.

### Step 5.3: E2E test via MCP protocol (`tests/e2e/test_tool_calls_via_mcp.py`)
Write automated e2e tests that spin up the actual MCP server as a subprocess and send real tool calls through the protocol. These tests hit the live World Bank API (mark them as `slow` or `integration` in pytest configuration so they're not run on every commit).

**Done when:** each of the four tools has at least one passing e2e test that goes through the real MCP protocol.

### Step 5.4: Review for cost-effectiveness
Look back over the conversations from Step 5.2 and check:
- No raw, bloated API responses are making it into the AI conversation context.
- No unnecessary repeated network calls for information already available.
- No unnecessary back-and-forth where a single tool call could have resolved something directly.

**Done when:** you're satisfied that the system behaves efficiently as well as correctly.

---

## Phase 6: Wrap-Up

### Step 6.1: Document what was built
Confirm the three ADRs written in Phase 0 still accurately reflect the final implementation. Add or update any that changed during execution. Document any decisions made during implementation that weren't anticipated in the plan — if you had to make a call that wasn't written down anywhere, write it down now.

### Step 6.2: Reflect on what you learned
Go back through the architecture document and this plan, and verify in your own understanding each core MCP concept this project exercised:
- Tool design (four tools with clear, typed inputs/outputs).
- Structured clarification / human-in-the-loop behavior (the three-outcome disambiguation rule and how it surfaces to the user).
- Response shaping before it reaches an AI (the field-variance cleaning logic).
- External API error handling (the four failure types, retry policy, rate limiting).
- File-output tools (the export pipeline and its partial-failure policy).

This is the actual measure of whether the project achieved its real goal — not just "does it work," but "do I now understand MCP well."