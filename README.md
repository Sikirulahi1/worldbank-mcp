# World Bank MCP Server

A standalone Model Context Protocol (MCP) server that provides AI agents with direct access to the World Bank Data360 API. Built with Python 3.11 using **Domain-Driven Design (DDD)** and **Clean Architecture** principles.

This server exposes 4 powerful tools over standard I/O (`stdio`), allowing any MCP-compatible AI assistant (like Claude Desktop, Cursor, Copilot, or Antigravity) to automatically search for, disambiguate, fetch, and export global economic indicators.

---

## 🌟 Core System Capabilities

- 🔍 **Search & Resolution**: Smart mapping of natural language topics to precise World Bank indicator codes (e.g., "GDP" -> `WB_WDI_NY_GDP_MKTP_KD_ZG`).
- 🤖 **Human-in-the-loop Disambiguation**: Uses relevance scoring (`@search.score`) to auto-resolve clear standouts, while explicitly pausing and asking the user to clarify highly ambiguous queries.
- 📊 **Data Shaping**: Automatically compresses verbose World Bank JSON responses by separating constant metadata from varying time-series observations to protect the LLM context window.
- 💾 **File Export Pipelines**: Can automatically compile multiple indicators into a single chronological table and export directly to CSV, Excel (`.xlsx`), or JSON.

---

## 🛠️ The MCP Tools

1. **`search_indicator`**: Pass a generic topic (like "Education") to see a ranked list of available World Bank metrics.
2. **`get_indicator_data`**: The direct data fetcher. Pass an exact indicator ID and ISO country code to instantly pull time-series data.
3. **`get_country_indicator`**: The "Smart" tool. Pass natural language (e.g., Country="Nigeria", Topic="GDP growth"), and the tool automatically resolves the country, searches the topic, disambiguates the duplicates, and fetches the data.
4. **`export_report`**: The compiler. Pass a list of indicator topics, a country, and a destination path to export merged chronological data to your local machine.

---

## 🏗️ Clean Architecture

The codebase strictly follows a 4-layer architecture:
- **Domain** (`src/domain`): Pure Python business rules for deduplication, relevance ranking, data shaping, and validation. Zero network dependencies.
- **Application** (`src/application`): Object-Oriented pipelines orchestrating the domain rules via abstract Ports.
- **Infrastructure** (`src/infrastructure`): Concrete `httpx` async clients for the World Bank APIs with exponential backoff retry policies, plus `pandas`-based file writers.
- **Presentation** (`src/presentation`): The MCP interface mapping standard I/O requests directly to the application pipelines.

---

## 🚀 Usage

### Option 1: AI Assistants (Production)
You do not need to run the server manually. You just need to register it in your AI client's MCP configuration file (this works identically for **Claude Desktop**, **Cursor**, **Copilot**, **Antigravity**, etc.). 

Add the following standard JSON block to your client's config file (e.g., `%APPDATA%\Claude\claude_desktop_config.json` for Claude on Windows):

```json
{
  "mcpServers": {
    "worldbank": {
      "command": "python",
      "args": [
        "C:/path/to/your/worldbank-mcp/run.py"
      ]
    }
  }
}
```

### Option 2: MCP Inspector (Development / Testing)
To manually test the tools using the official web-based UI, run:
```bash
npx @modelcontextprotocol/inspector python run.py
```
*(Requires Node.js / npx)*

---

## 🐳 Docker Support

Because this is a `stdio` MCP server, it does not expose any web ports. 
If running via Docker for isolation, ensure the container runs interactively without detaching the standard input/output streams.
