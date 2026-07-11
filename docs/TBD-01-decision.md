# TBD-01 — LLM/model choice decision

**Status:** Resolved (provisional — revisit if Anthropic/OpenAI credits become available)
**Owners:** Noor + Ayesha
**Date:** July 2026

## Decision

**Default provider: Groq (llama-3.3-70b-versatile)**

## Why

Of the 4 configured providers, only Groq was actually testable without payment:
- **Anthropic** requires $5 minimum prepaid credit — no free tier
- **OpenAI** requires paid billing — no free credits as of 2026
- **Gemini** hit a Google-side free-tier quota bug (`429 RESOURCE_EXHAUSTED`, limit 0) even after fixing an unrelated SDK compatibility issue — a known widespread issue in 2026, not something fixable on our end without linking billing

Groq, by contrast, is free, fast, and produced good-quality output in testing: accurate explanations, specific/usable code fixes, no observed hallucination. See `docs/agent_prompt_experiments.md` for full results.

## Cost / quality / speed tradeoff

Since we could only fully test one provider, this decision is based on Groq meeting the bar (good quality, zero cost, fast) rather than a head-to-head comparison. If the team gets Anthropic/OpenAI credits later, or resolves the Gemini quota issue, we should re-run this comparison for a fuller picture — Groq may not be the best option, just the only *provable* one right now.

## Next steps if budget becomes available

1. Link a $0-capped billing account to Gemini to unblock its free tier, or
2. Get shared team credits for Anthropic/OpenAI
3. Re-run `scripts/run_explainer_sample.py` against whichever become available
4. Update this doc with a full comparison