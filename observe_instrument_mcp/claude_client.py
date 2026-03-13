"""LLM client for applying observe SDK instrumentation.

Supports any provider via LiteLLM. Configure with env vars:

  Provider       | Env var              | LLM_MODEL value
  ---------------|----------------------|---------------------------
  Anthropic      | ANTHROPIC_API_KEY    | claude-sonnet-4-6
  OpenAI         | OPENAI_API_KEY       | gpt-4o
  Google Gemini  | GEMINI_API_KEY       | gemini/gemini-2.0-flash
  Groq           | GROQ_API_KEY         | groq/llama-3.3-70b
  Ollama (local) | (none)               | ollama/llama3.2
"""

import asyncio
import importlib.resources
import os
import re
from typing import Tuple

import litellm

litellm.suppress_debug_info = True

_SKILL_MD: str | None = None
_MODEL = os.environ.get("LLM_MODEL", "claude-sonnet-4-6")
_MAX_TOKENS = 8192

_INSTRUMENT_USER_TEMPLATE = """\
Please instrument the following Python file with the ioa-observe-sdk following the guide in your system prompt.

File path: {file_path}
{app_name_hint}

Return your response in exactly this format:
1. The complete instrumented Python file enclosed in ```python ... ``` code fences
2. A "## Changes Made" section summarizing what was added (bullet list)

File contents:
```python
{content}
```
"""

_CHECK_USER_TEMPLATE = """\
Please audit the following Python AI agent file for ioa-observe-sdk instrumentation coverage.

File path: {file_path}

Report:
- What instrumentation is already present
- What is missing (imports, Observe.init(), decorator coverage, session_start())
- Specific recommendations for each missing item

File contents:
```python
{content}
```
"""


def _load_skill_md() -> str:
    global _SKILL_MD
    if _SKILL_MD is None:
        with importlib.resources.open_text(
            "observe_instrument_mcp.resources", "SKILL.md"
        ) as f:
            _SKILL_MD = f.read()
    return _SKILL_MD


def _check_api_key() -> None:
    """Warn if no known API key is set (best-effort — Ollama needs none)."""
    known_keys = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "COHERE_API_KEY",
    ]
    model = _MODEL.lower()
    # Ollama and other local models don't need a key
    if any(model.startswith(p) for p in ("ollama/", "ollama_chat/", "huggingface/")):
        return
    if not any(os.environ.get(k) for k in known_keys):
        raise ValueError(
            f"No LLM API key found for model '{_MODEL}'. "
            "Set one of: ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, GROQ_API_KEY. "
            "For local models use LLM_MODEL=ollama/llama3.2 (no key required)."
        )


def _parse_instrument_response(raw: str) -> Tuple[str, str]:
    """Extract (python_code, changes_summary) from the LLM response."""
    code_match = re.search(r"```python\s*\n(.*?)```", raw, re.DOTALL)
    if not code_match:
        raise ValueError(
            "LLM response did not contain a ```python ... ``` code block. "
            f"Response preview: {raw[:300]}"
        )
    code = code_match.group(1).strip()
    remainder = raw[code_match.end():]
    summary_match = re.search(r"##\s*Changes Made\s*\n(.*?)(?=\n##|$)", remainder, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else remainder.strip() or "(No summary provided)"
    return code, summary


async def instrument_with_claude(
    content: str, file_path: str, app_name: str = ""
) -> Tuple[str, str]:
    """Call LLM to instrument a Python file. Returns (instrumented_code, summary)."""
    def _call() -> Tuple[str, str]:
        _check_api_key()
        app_hint = f"Preferred app_name for Observe.init(): {app_name}" if app_name else ""
        user_msg = _INSTRUMENT_USER_TEMPLATE.format(
            file_path=file_path,
            app_name_hint=app_hint,
            content=content,
        )
        response = litellm.completion(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            messages=[
                {"role": "system", "content": _load_skill_md()},
                {"role": "user", "content": user_msg},
            ],
        )
        return _parse_instrument_response(response.choices[0].message.content)

    return await asyncio.to_thread(_call)


async def check_with_claude(content: str, file_path: str) -> str:
    """Call LLM to audit instrumentation coverage."""
    def _call() -> str:
        _check_api_key()
        user_msg = _CHECK_USER_TEMPLATE.format(file_path=file_path, content=content)
        response = litellm.completion(
            model=_MODEL,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": _load_skill_md()},
                {"role": "user", "content": user_msg},
            ],
        )
        return response.choices[0].message.content

    return await asyncio.to_thread(_call)
