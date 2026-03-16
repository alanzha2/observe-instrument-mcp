# observe-instrument-mcp

<!-- mcp-name: io.github.alanzha2/observe-instrument-mcp -->

An MCP server that automatically instruments Python AI agents with the [ioa-observe-sdk](https://github.com/agntcy/observe) — adding OpenTelemetry-based tracing, metrics, and logs with zero manual effort.

Works with any MCP-compatible AI coding assistant: Claude Desktop, Cursor, Windsurf, and others.

## What it does

Two tools:

**`instrument_agent`** — reads a Python agent file, applies full observe SDK instrumentation, writes it back, and returns a summary of changes. Creates a `.bak` backup before modifying.

**`check_instrumentation`** — audits a file for missing instrumentation without modifying it.

Supported frameworks: LlamaIndex, LangGraph, CrewAI, raw OpenAI SDK.

## Installation

```bash
pip install observe-instrument-mcp
# or
uv add observe-instrument-mcp
```

Requires an API key for your chosen LLM provider. Defaults to Claude (`ANTHROPIC_API_KEY`). See [supported providers](#supported-providers) below.

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "observe-instrument": {
      "command": "uvx",
      "args": ["observe-instrument-mcp"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "observe-instrument": {
      "command": "uvx",
      "args": ["observe-instrument-mcp"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "observe-instrument": {
      "command": "uvx",
      "args": ["observe-instrument-mcp"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

## Examples

Ready-to-use uninstrumented agent files are included in the `examples/` folder:

```
examples/
  single-agent/
    openai-sdk-example.py      # OpenAI SDK customer support agent
    langgraph-example.py       # LangGraph currency converter
    llama-index-example.py     # LlamaIndex math agent
    crewai-example.py          # CrewAI research crew
  multi-agent/
    openai-sdk-multi-agent-example.py   # OpenAI SDK orchestrator pipeline
    langgraph-multi-agent-example.py    # LangGraph supervisor pattern
    llama-index-multi-agent-example.py  # LlamaIndex research + writing pipeline
    crewai-multi-agent-example.py       # CrewAI research + publishing crews
```

## Usage

Once configured, ask your AI assistant:

```
Instrument my agent with the observe SDK: path/to/my_agent.py
```

```
Check what observe SDK instrumentation is missing from path/to/my_agent.py
```

## Environment variables

| Variable | Description |
|---|---|
| `LLM_MODEL` | Model to use (default: `claude-sonnet-4-6`). See provider table below. |
| `ANTHROPIC_API_KEY` | Required for Anthropic models |
| `OPENAI_API_KEY` | Required for OpenAI models |
| `GEMINI_API_KEY` | Required for Google Gemini models |
| `GROQ_API_KEY` | Required for Groq models |

### Supported providers

| Provider | Key variable | `LLM_MODEL` example |
|---|---|---|
| Anthropic | `ANTHROPIC_API_KEY` | `claude-sonnet-4-6` |
| OpenAI | `OPENAI_API_KEY` | `gpt-4o` |
| Google Gemini | `GEMINI_API_KEY` | `gemini/gemini-2.0-flash` |
| Groq | `GROQ_API_KEY` | `groq/llama-3.3-70b` |
| Ollama (local, free) | none | `ollama/llama3.2` |

## After instrumentation

Install the SDK in your project:

```bash
pip install ioa-observe-sdk
# or
uv add ioa-observe-sdk
```

Start the observability stack (OTel Collector + ClickHouse):

```bash
cd path/to/observe/deploy
docker compose up -d
```

Run your agent:

```bash
OPENAI_API_KEY=sk-... OTLP_HTTP_ENDPOINT=http://localhost:4318 python my_agent.py
```

Query traces:

```bash
docker exec -it clickhouse-server clickhouse-client --user admin --password admin
```

```sql
SELECT SpanName, ServiceName, Duration / 1000000. AS ms, Timestamp
FROM otel_traces
ORDER BY Timestamp DESC
LIMIT 20;
```

## Development

```bash
git clone https://github.com/alanzha2/observe-instrument-mcp
cd observe-instrument-mcp
pip install -e .

# Test the server locally
mcp dev observe_instrument_mcp/server.py
```

## License

Apache-2.0
