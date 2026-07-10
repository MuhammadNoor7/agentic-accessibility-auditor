"""Provider-agnostic LLM call layer for the explanation module (src/explainer.py).

Select a provider with the LLM_PROVIDER env var: "anthropic" (default),
"openai", "gemini", or "groq". Each provider's SDK is imported lazily inside
its own call function, so only the SDK for the provider actually in use needs
to be installed. API keys and model names are read from env vars so this file
never hardcodes a secret.

Env vars:
    LLM_PROVIDER        anthropic | openai | gemini | groq (default: anthropic)
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL   (default model: claude-opus-4-8)
    OPENAI_API_KEY, OPENAI_MODEL         (default model: gpt-4o)
    GEMINI_API_KEY / GOOGLE_API_KEY, GEMINI_MODEL   (default model: gemini-2.0-flash)
    GROQ_API_KEY, GROQ_MODEL             (default model: llama-3.3-70b-versatile)
"""

from __future__ import annotations

import os

DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-opus-4-8",
    "openai": "gpt-4o",
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
}


class LLMError(RuntimeError):
    """Raised when an LLM provider call fails for any reason (auth, network, API error).

    Callers (src/explainer.py) catch this single type rather than the many
    distinct exception classes each provider SDK raises.
    """


def _provider_name() -> str:
    return os.environ.get("LLM_PROVIDER", "anthropic").strip().lower()


def _model_name(provider: str) -> str:
    env_key = f"{provider.upper()}_MODEL"
    return os.environ.get(env_key) or DEFAULT_MODELS.get(provider, "")


def llm_configured() -> bool:
    """Return True when the active LLM_PROVIDER has a non-empty API key set."""
    provider = _provider_name()
    if provider not in DEFAULT_MODELS:
        return False
    key_names = {
        "anthropic": ("ANTHROPIC_API_KEY",),
        "openai": ("OPENAI_API_KEY",),
        "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        "groq": ("GROQ_API_KEY",),
    }
    return any(os.environ.get(name, "").strip() for name in key_names.get(provider, ()))


def call_llm(system: str, user: str, *, max_tokens: int = 4096) -> str:
    """Call the configured LLM provider and return its raw text response.

    Input: system - system/instructions prompt; user - the per-batch user
        message (expected to ask for a single JSON object back); max_tokens -
        output token cap for this call.
    Output: raw text response, unparsed (the caller is responsible for JSON
        parsing/validation - see src/explainer.py's anti-hallucination guard).
    Raises: LLMError on any provider/network/API/config failure, or if
        LLM_PROVIDER names an unsupported provider.
    """
    provider = _provider_name()
    if provider not in DEFAULT_MODELS:
        raise LLMError(
            f"Unknown LLM_PROVIDER '{provider}'. Expected one of: {', '.join(DEFAULT_MODELS)}."
        )
    model = _model_name(provider)
    try:
        if provider == "anthropic":
            return _call_anthropic(system, user, model, max_tokens)
        if provider == "openai":
            return _call_openai(system, user, model, max_tokens)
        if provider == "gemini":
            return _call_gemini(system, user, model, max_tokens)
        return _call_groq(system, user, model, max_tokens)
    except LLMError:
        raise
    except Exception as exc:  # provider SDKs each raise their own exception hierarchy
        raise LLMError(f"{provider} call failed: {type(exc).__name__}: {exc}") from exc


def _call_anthropic(system: str, user: str, model: str, max_tokens: int) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY")) if os.environ.get(
        "ANTHROPIC_API_KEY"
    ) else anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _call_openai(system: str, user: str, model: str, max_tokens: int) -> str:
    import openai

    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


def _call_gemini(system: str, user: str, model: str, max_tokens: int) -> str:
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        ),
    )
    return response.text or ""


def _call_groq(system: str, user: str, model: str, max_tokens: int) -> str:
    from groq import Groq

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""
