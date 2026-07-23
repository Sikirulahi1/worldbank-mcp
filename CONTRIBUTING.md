# Contributing Guide — World Bank MCP Server

Welcome to the `worldbank-mcp` project! This project strictly adheres to **Clean Architecture** and **Domain-Driven Design (DDD)** principles to provide AI agents with a standalone Model Context Protocol (MCP) server.

## Architecture Rules

When contributing, you must adhere to the 4-layer architecture:

1. **Domain (`src/domain`)**: Contains pure Python logic (Entities, deduplication rules, disambiguation). **No external SDKs (like `httpx` or `mcp`) are allowed here.**
2. **Application (`src/application`)**: Orchestrates the domain logic using abstract `Ports`. This layer defines the input DTOs and output Result types.
3. **Infrastructure (`src/infrastructure`)**: Implements the concrete API clients (World Bank Data360 API) and file exporters (CSV/Excel).
4. **Presentation (`src/presentation`)**: The MCP server definition (`server.py`, `tool_handlers.py`). It receives `stdio` requests and passes them to the application pipelines.

**Dependency Rule:** `presentation` → `application` → `domain` ← `infrastructure`.

## Development Setup

1. Clone the repository.
2. Install the requirements: `pip install -r requirements.txt`.
3. Test the server using the MCP Inspector: `make inspect`.

## Testing

We use `pytest` for all unit and end-to-end tests.
Run the full test suite using:
```bash
make test
```

## Adding a New Tool

1. Create a request DTO in `src/application/`.
2. Build an orchestration pipeline in `src/application/`.
3. Define the tool schema using `mcp.types.Tool` in `src/presentation/mcp/schemas/`.
4. Register the handler in `src/presentation/mcp/tool_handlers.py`.
5. Ensure tests are written for the new pipeline and tool handler.
