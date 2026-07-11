# Agent Prompt Experiments — Week 4

**Author:** Ayesha Naveed
**Date:** July 2026
**Goal:** Compare the 4 configured LLM providers (Anthropic, OpenAI, Gemini, Groq) for the explainer agent, to resolve TBD-01.

## Method

Ran `scripts/run_explainer_sample.py --count 3 --max-violations-per-screen 5` against each provider — 3 sample screens, 5 violations each (15 total), using the existing `src/explainer.py` prompt template. No prompt changes were made; this round tests provider quality, not prompt variants.

## Results by provider

### Groq (llama-3.3-70b-versatile) — ✅ Tested, working

Groq successfully explained all 15 of 15 violations. The full run completed in well under a minute, and since it's on the free tier, no billing was required.

The tone throughout was clear, professional, and consistent. Explanations correctly matched the actual violation — missing labels and duplicate labels were correctly identified with the right resource IDs — and the suggested fixes were concrete, real code (e.g. `android:contentDescription="Chat"`) rather than vague advice. No hallucination was observed; explanations stayed grounded in the violation data provided, with no invented details.

The one weakness: explanations for the same rule (e.g. R01) were fairly template-like across different screens, with low variation in phrasing.

### Gemini (gemini-2.0-flash) — ⚠️ Blocked

The initial attempt failed with `API_KEY_INVALID`. The root cause was that the repo's `google-generativeai` package is deprecated and doesn't support Google's newer API key format (keys starting `AQ.Ab...` instead of `AIza...`). Noor fixed this by switching the dependency to `google-genai` (requirements.txt + `src/llm_providers.py` updated).

After that fix, authentication succeeded but hit a second blocker: `429 RESOURCE_EXHAUSTED`, quota limit `0` on the free tier — a known, widely-reported issue in 2026 where Google requires a billing account linked (with a $0 spend cap) to unlock free-tier quota.

**Status:** Not tested end-to-end. Would need billing linked to retry.

### Anthropic (claude-opus-4-8) — ⚠️ Blocked

No free tier is available — a minimum $5 prepaid credit is required to generate an API key.

**Status:** Not tested. Awaiting team decision on shared budget.

### OpenAI (gpt-4o) — ⚠️ Blocked

No free credits are available as of 2026 — paid billing is required to generate an API key.

**Status:** Not tested. Awaiting team decision on shared budget.

## Summary comparison

Of the four providers, only Groq could actually be tested, and it performed well: clear, accurate explanations with specific, code-level fixes, delivered fast and at no cost.

Gemini was free to test in principle but was blocked by a quota bug requiring a linked billing account, so no quality assessment could be made. Anthropic and OpenAI were both blocked outright — Anthropic requires a $5 minimum prepaid credit, and OpenAI has no free tier at all — so neither could be evaluated either.

## Recommendation

See `docs/TBD-01-decision.md` for the formal resolution.

## Sample output

Full side-by-side input/output for all 15 tested violations is in `outputs/recommendations/sample_review.md`.