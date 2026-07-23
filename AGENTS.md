# worldbank-mcp — Agent Rules & Style Guide

This file is the project-specific companion to `~/.gemini/GEMINI.md`.
Everything here applies only to this repository. Global rules win if
they conflict with anything below.

---

## Project Context

`worldbank-mcp` is a **standalone MCP server** (not a web service).
It speaks the MCP protocol over stdio. It has no HTTP routes, no
FastAPI, no Uvicorn. It follows the same four-layer Clean Architecture
as SupportOS AI because that's a good pattern — not because the two
projects are joined.

Full design decisions are in:
- `docs/additions/architecture.md`
- `docs/additions/implementation_plan.md`
- `docs/additions/proposed_structure.md`
- `docs/architecture/adr-001-no-local-cache.md`
- `docs/architecture/adr-002-database-priority-tiebreak.md`
- `docs/architecture/adr-003-disambiguation-thresholds.md`

**Read the relevant doc before implementing any feature.** If the doc
contradicts the code, surface the conflict — don't resolve it silently.

---

## Style Reference Files

When writing new code, use the closest existing file as a style anchor.
The table below maps each new area to the right reference:

| New file area | Style reference |
|---|---|
| `src/core/` | `src/core/config.py`, `src/core/exceptions.py` |
| `src/domain/` entities | `src/domain/agent/entities.py` — **already exists**, use it as the anchor |
| `src/domain/` pure functions | `src/domain/shaping/field_analysis.py` (first created; use `src/domain/agent/entities.py` as interim anchor) |
| `src/application/ports/` | `src/domain/agent/interfaces.py` — uses `Protocol`, establish the same pattern |
| `src/application/pipelines` | `src/application/chat/pipeline.py` + `steps/load_agent_config.py` |
| `src/infrastructure/worldbank_client/` | Once first client exists, all subsequent clients follow it |
| `src/presentation/mcp/` | No analog — establish from `server.py` first |
| `tests/unit/` | Once first test file exists, all subsequent tests mirror its structure |

---

## Python Style (Derived from SupportOS AI Codebase)

These patterns come from reading the existing `src/` files. Match them exactly.

### Formatting
- **4 spaces** for indentation (no tabs).
- **Double quotes** for strings (`"value"`, not `'value'`). Match whatever
  the first file in each layer uses — do not introduce inconsistency.
- **Two blank lines** between top-level definitions (classes, functions).
- **One blank line** between methods inside a class.
- Module docstrings use `"""Triple double quotes."""` on the first line of the file.

### Imports
Order (match `isort` style, which Ruff enforces):
1. Standard library (`from __future__`, `import os`, etc.)
2. Third-party (`from fastapi import ...`, `from mcp import ...`)
3. First-party (`from src.core.config import settings`)

One blank line between each group. Absolute imports only — no relative
`from . import` unless the existing codebase already uses them.

### Type Hints
- **Always present** on function parameters and return types.
- Use `from __future__ import annotations` at the top of files with
  forward references.
- Prefer `X | None` over `Optional[X]` (Python 3.10+ syntax, since this
  project targets Python 3.11+).
- Use `list[X]` and `dict[K, V]` (lowercase, not `List` / `Dict`).

### Naming
| Kind | Convention | Example |
|---|---|---|
| Classes | `PascalCase` | `IndicatorCandidate`, `SearchClient` |
| Functions & methods | `snake_case` | `resolve_country`, `get_coverage` |
| Variables | `snake_case` | `raw_candidates`, `start_year` |
| Constants | `UPPER_SNAKE_CASE` | `DATABASE_PRIORITY`, `MAX_CANDIDATES` |
| Private attributes | Single underscore | `self._client` |
| Files | `snake_case.py` | `field_analysis.py`, `retry_policy.py` |
| Port/interface classes | `I` prefix + `PascalCase` | `ISearchPort`, `IDataPort`, `IFileWriter` |

> **Why `I` prefix?** The existing codebase uses `IAgentConfigLoader` in
> `src/domain/agent/interfaces.py`. This project follows the same convention
> for consistency, even though the architecture docs used `Port` suffix in
> prose descriptions. The code is the source of truth.

### Dataclasses
Use `@dataclass` (not Pydantic) for pure domain entities and result types.
Use `@dataclass(frozen=True)` for value objects that should be immutable.
Use Pydantic `BaseModel` only at the infrastructure boundary (DTOs that
come in from or go out to external callers), following the pattern in the
existing codebase.

```python
# ✅ Domain entity — plain dataclass
from dataclasses import dataclass

@dataclass(frozen=True)
class IndicatorCandidate:
    """A single search result candidate from the World Bank search API."""

    idno: str
    name: str
    database_id: str
    search_score: float
```

### Docstrings
The codebase strictly uses **single-line docstrings for all files, classes, and methods**.

```python
class SearchIndicatorPipeline:
    """Pipeline for searching and ranking indicators."""

    async def execute(self, request: SearchIndicatorRequest) -> list[IndicatorCandidate] | NotFound:
        """Search for indicators matching a topic."""
```
Do NOT use multi-line Google-style docstrings (`Args:`, `Returns:`, etc.) under any circumstances. Keep it clean and concise.

### Comments
The code must be self-documenting. **Do NOT leave useless step-by-step inline comments** (e.g., `# 1. Resolve country`, `# Fetch candidates`, `# Loop over results`). Remove dead code or commented-out alternatives before presenting your work. Only use inline comments for truly non-obvious business logic explanations.

### Application Pipelines
Application layer use cases must be structured as Object-Oriented **Pipeline Classes**, not loose procedural functions.
1. Define an input DTO using `@dataclass(frozen=True)` (e.g., `ExportReportRequest`).
2. Inject dependencies (ports or other pipelines) via `__init__`.
3. Implement business logic inside a clean `async def execute(self, request: DTO) -> Result` method.

### Error Handling
- Raise named exceptions from `src/core/exceptions.py`, never bare
  `Exception` or `RuntimeError`.
- No silent catches. Every `except` block must either re-raise or log
  and raise a domain exception.
- Infrastructure errors are raised as exceptions — not wrapped in
  `core/result.py` outcome types. Result types are for expected,
  plannable pipeline outcomes only.

```python
# ✅ Correct
try:
    response = await self._client.get(url)
except httpx.TimeoutException as exc:
    raise WorldBankTimeoutError(f"Search timed out after {timeout}s") from exc

# ❌ Wrong
try:
    response = await self._client.get(url)
except Exception:
    pass  # Never
```

### Port/Interface Definitions
The codebase uses `typing.Protocol` for interfaces (not `abc.ABC`). Confirmed
from `src/domain/agent/interfaces.py`. Use the same pattern:

```python
from typing import Protocol

class ISearchPort(Protocol):
    """Interface for indicator search operations."""

    async def search(self, topic: str) -> list[IndicatorCandidate]: ...
```

`Protocol` enables structural subtyping — any class with a matching `search`
method satisfies the interface without explicit inheritance. This makes fakes
for testing trivial to write.

### `core/result.py` Pipeline Outcomes
Every application pipeline returns one of three types — never a bare value,
never a raw exception. Check type with `isinstance` at the caller:

```python
result = await pipeline.run(request)

if isinstance(result, DataResult):
    ...
elif isinstance(result, ClarificationNeeded):
    ...
elif isinstance(result, NotFound):
    ...
```

---

## Architecture Rules (Hard Constraints)

These are not style preferences — violations break the design:

1. **Domain layer has zero imports from `infrastructure/` or `application/`.**
   `domain/` may only import from `core/` and standard library.

2. **Application pipelines import from `ports/` interfaces, never from
   `infrastructure/` concrete classes directly.**

3. **`infrastructure/worldbank_client/metadata_client.py` fetches year
   coverage only.** It must not grow into a general metadata wrapper.
   If a new metadata query is needed, open a discussion first.

4. **`run.py` contains no HTTP server startup code of any kind.**
   Its only job: construct the MCP server instance and call the `mcp`
   SDK's stdio server loop. No `uvicorn`, no `gunicorn`, no `app.run()`.

5. **`presentation/mcp/tool_handlers.py` contains no business logic.**
   It translates: MCP call → input DTO → pipeline → result → MCP response.
   If logic creeps in, it belongs in the application layer instead.

---

## Implementation Plan Protocol

Before writing code for any step in `docs/additions/implementation_plan.md`:

1. State which step you're implementing (e.g., "Step 1.3 — Deduplication").
2. Name the style reference file(s) you studied.
3. List the "Done when" criteria from the plan.
4. Write the code.
5. Confirm each "Done when" criterion is met before marking the step complete.

If a "Done when" criterion can't be met, say so explicitly and explain why
before moving to the next step.

---

## Pre-Commit Checklist

Before presenting any code:

- [ ] Style matches an existing file in the same layer (named above)
- [ ] Imports are ordered correctly (stdlib → third-party → first-party)
- [ ] All public functions have docstrings
- [ ] All parameters and return values have type hints
- [ ] No bare `except` blocks
- [ ] Named exceptions from `src/core/exceptions.py` only
- [ ] No layer boundary violations (domain imports nothing from infra)
- [ ] "Done when" criteria from the implementation plan are addressed
- [ ] File has a module-level docstring
- [ ] Constants are in `core/constants.py`, not magic literals in code
