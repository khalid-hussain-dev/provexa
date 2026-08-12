"""
Utility helpers for the AI Interview & Assessment System.
"""

import json
import re
from typing import Any


def parse_crew_result(result: Any, fallback: Any = None) -> Any:
    """
    Robustly parse a CrewAI crew.kickoff() result into a Python dict or list.

    CrewAI >= 1.x returns a `CrewOutput` object, not a plain string.
    LLMs also frequently wrap JSON inside markdown code fences:
        ```json
        { ... }
        ```
    This helper handles all of these cases gracefully.

    Args:
        result: The raw value returned by crew.kickoff().
        fallback: Value to return if parsing fails entirely.

    Returns:
        Parsed Python dict/list, or `fallback` on failure.
    """
    if fallback is None:
        fallback = {}

    # If already a dict or list, return as-is
    if isinstance(result, (dict, list)):
        return result

    # CrewOutput objects expose the LLM text via .raw
    if hasattr(result, "raw"):
        text = result.raw or ""
    else:
        text = str(result)

    text = text.strip()

    if not text:
        return fallback

    # Strip markdown code fences:  ```json ... ```  or  ``` ... ```
    # Try ```json first, then generic ```
    for fence_start in ("```json", "```"):
        if fence_start in text:
            parts = text.split(fence_start, 1)
            if len(parts) == 2:
                inner = parts[1].split("```", 1)[0].strip()
                if inner:
                    text = inner
                    break

    # Direct parse attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting the first {...} or [...] block from surrounding prose
    match_obj = re.search(r"\{.*\}", text, re.DOTALL)
    match_arr = re.search(r"\[.*\]", text, re.DOTALL)

    # Pick whichever comes first
    candidates = [m for m in [match_obj, match_arr] if m is not None]
    candidates.sort(key=lambda m: m.start())

    for match in candidates:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            continue

    return fallback


# ── Patch LiteLLM to strip unsupported properties (e.g. cache_breakpoint) ──
import litellm
litellm.drop_params = True

_original_litellm_completion = litellm.completion

def _patched_litellm_completion(*args, **kwargs):
    if "messages" in kwargs and isinstance(kwargs["messages"], list):
        for msg in kwargs["messages"]:
            if isinstance(msg, dict):
                msg.pop("cache_breakpoint", None)
    return _original_litellm_completion(*args, **kwargs)

litellm.completion = _patched_litellm_completion


def get_default_llm(temperature: float = 0.7):
    """
    Returns a crewai.LLM instance.

    Priority: Gemini (primary) → Groq (fallback)
    Both are wrapped in crewai.LLM so CrewAI Agent(llm=...) accepts them.

    Why crewai.LLM instead of ChatOpenAI?
    CrewAI v1.x Agent() only accepts crewai.LLM objects or a model-name string
    for the `llm` parameter — raw langchain ChatOpenAI objects are rejected.
    crewai.LLM wraps any OpenAI-compatible endpoint via its `base_url` param.
    """
    from crewai import LLM
    from config import settings

    # ── Primary: Gemini ──────────────────────────────────────────────────────
    gemini_key = getattr(settings, "GEMINI_API_KEY", None)
    if gemini_key and not gemini_key.startswith("AQ."):
        model_name = (
            settings.GEMINI_MODEL
            if settings.GEMINI_MODEL.startswith("gemini/")
            else f"gemini/{settings.GEMINI_MODEL}"
        )
        try:
            return LLM(
                model=model_name,
                api_key=gemini_key,
                temperature=temperature
            )
        except Exception as e:
            print(f"[LLM] Gemini init failed ({e}), trying Groq fallback...")

    # ── Fallback: Groq ───────────────────────────────────────────────────────
    groq_key = getattr(settings, "GROQ_API_KEY", None)
    if groq_key:
        try:
            return LLM(
                model=f"groq/{settings.GROQ_MODEL}",
                api_key=groq_key,
                temperature=temperature
            )
        except Exception as e:
            print(f"[LLM] Groq init also failed ({e}).")

    raise RuntimeError(
        "No LLM provider is configured. "
        "Set GEMINI_API_KEY or GROQ_API_KEY in your .env file."
    )

