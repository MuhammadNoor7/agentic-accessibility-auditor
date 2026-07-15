# Figma vs Live App — Implementation Gap List

**Author:** Ayesha Naveed
**Purpose:** One-page reference of what's real vs still mock UI, for supervisor review.

## ✅ Fully implemented (real backend)

| Feature | Notes |
|---|---|
| Sign up / Log in | Real JWT auth (`backend/auth.py`), bcrypt-hashed passwords |
| Upload → Audit | Sends real screenshot + XML, runs full parse → rules → agent explain pipeline |
| Dashboard | Real violations, real accessibility score |
| Report view | Real score, real per-violation explanations (via Groq) |
| Report download (HTML) | Real file download |
| Report download (PDF) | Real file download (needs local Playwright browser install) |
| Records / Audit History | Real per-user history via `GET /records` |
| Reopening a past record | Real — refetches the actual saved report |

## ⚠️ Still mock / not implemented

| Feature | What's mocked | Notes |
|---|---|---|
| **Email verification (OTP)** | `VerifyCode.jsx` shows a 6-digit code entry screen, but no email is ever sent — no SMTP/OTP service exists on the backend | Needs real email service before this page is usable, or should be hidden from the flow for now |
| **Google Sign-In** | Button exists (`GoogleButton.jsx`), click handler explicitly shows "Google auth not yet implemented" | Needs OAuth integration |
| **Forgot Password / Reset Password** | `ForgotPassword.jsx`, `SetPassword.jsx`, `ResetSuccess.jsx` — no API calls anywhere in these files | Purely UI, no backend support |
| **Report screenshot/XML preview in downloads** | Exported PDF/HTML shows "No screenshot available" / "XML source not available" | Backend stores uploaded files in a temp folder that's cleaned up before the download request can read it — needs persistent storage |

## Known limitations (not gaps, just current scope)

- Only Groq is free-to-test for the agent explanation layer; Anthropic/OpenAI need paid credits, Gemini blocked by a Google-side quota bug (see `docs/agent_prompt_experiments.md`)
- Report timestamps are hardcoded to UTC, not localized