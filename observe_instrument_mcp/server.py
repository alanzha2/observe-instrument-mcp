"""
observe-instrument-mcp: MCP server that instruments Python AI agents with ioa-observe-sdk.

Run as a stdio MCP server:
    observe-instrument-mcp
    uvx observe-instrument-mcp
    python -m observe_instrument_mcp
"""

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from observe_instrument_mcp.claude_client import check_with_claude, instrument_with_claude
from observe_instrument_mcp.file_utils import (
    build_diff_summary,
    make_backup,
    read_python_file,
    write_python_file,
)

load_dotenv()

mcp = FastMCP(
    "observe-instrument",
    instructions=(
        "This server instruments Python AI agent files with the ioa-observe-sdk "
        "for OpenTelemetry-based observability. "
        "Use instrument_agent to add tracing decorators and initialization to a file. "
        "Use check_instrumentation to audit what is missing without modifying anything."
    ),
)


@mcp.tool(
    name="instrument_agent",
    annotations={
        "title": "Instrument Python Agent with Observe SDK",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def instrument_agent(file_path: str, app_name: str = "") -> str:
    """
    Read a Python AI agent file, add ioa-observe-sdk instrumentation, and write it back.

    Adds Observe.init(), SDK imports, @tool/@agent/@graph/@workflow decorators, and
    session_start() — covering LlamaIndex, LangGraph, CrewAI, and raw OpenAI SDK agents.
    Creates a .bak backup before modifying the file.

    Args:
        file_path: Path to the Python file to instrument.
        app_name: Optional app name for Observe.init(). Inferred from file if omitted.

    Returns:
        Summary of all changes made, the diff, and next steps.
    """
    try:
        original = read_python_file(file_path)
        instrumented, summary = await instrument_with_claude(original, file_path, app_name)
        backup = make_backup(file_path)
        write_python_file(file_path, instrumented)
        diff = build_diff_summary(original, instrumented)
        return (
            f"## Instrumentation Complete\n\n"
            f"**File**: `{file_path}`\n"
            f"**Backup**: `{backup}`\n\n"
            f"### Changes Made\n{summary}\n\n"
            f"### Diff\n{diff}\n\n"
            f"### Next Steps\n"
            f"- Install the SDK: `pip install ioa-observe-sdk` or `uv add ioa-observe-sdk`\n"
            f"- Set env var: `export OTLP_HTTP_ENDPOINT=http://localhost:4318`\n"
        )
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


@mcp.tool(
    name="check_instrumentation",
    annotations={
        "title": "Check Agent Instrumentation Coverage",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def check_instrumentation(file_path: str) -> str:
    """
    Audit a Python AI agent file for missing ioa-observe-sdk instrumentation.

    Read-only — does not modify the file. Use instrument_agent to apply changes.

    Args:
        file_path: Path to the Python file to audit.

    Returns:
        Audit report: what is present, what is missing, and specific recommendations.
    """
    try:
        content = read_python_file(file_path)
        return await check_with_claude(content, file_path)
    except FileNotFoundError:
        return f"Error: File not found: {file_path}"
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
