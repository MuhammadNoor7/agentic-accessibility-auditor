# Figma vs Live App — Implementation Gap List

**Author:** Ayesha Naveed (updated by Muhammad Noor, Week 6)
**Purpose:** One-page reference of what's real vs still mock UI, for supervisor review.

## ✅ Fully implemented (real backend)

| Feature | Notes |
|---|---|
| Sign up / Log in | Real JWT auth (`backend/auth.py`), bcrypt-hashed passwords; optional `name` stored and returned |
| Profile initials (top-right) | Real — avatar shows the logged-in user's initials from name (signup) or email local-part (login-only / legacy accounts) |
| **Email verification (OTP)** | Real — signup → `POST /auth/register` + OTP email → `/verify-code` (`purpose=email_verify`) → JWT session |
| **Forgot / Reset Password** | Real — `/forgot-password` → OTP → `/set-password` via `reset_token` (`POST /auth/forgot-password`, `/auth/verify-otp`, `/auth/reset-password`) |
| **Google Sign-In** | Real OAuth ID-token flow — GIS on frontend + `POST /auth/google` (requires `GOOGLE_CLIENT_ID`) |
| Upload → Audit | Sends real screenshot + XML, runs full parse → rules → agent explain pipeline |
| Dashboard | Real violations, real accessibility score |
| Report view | Real score, real per-violation explanations (via Groq) |
| Report download (HTML) | Real file download — embeds annotated screenshot, XML snippet, and detected violations |
| Report download (PDF) | Real file download (needs local Playwright browser install) — same content as HTML |
| Records / Audit History | Real per-user history via `GET /records` |
| Reopening a past record | Real — refetches the actual saved report |

## ⚠️ Still mock / not implemented

None for the previous Figma auth shell. Remaining items are **config dependencies**, not missing UI/API:

| Feature | Status | Notes |
|---|---|---|
| SMTP delivery | Optional config | Set `SMTP_HOST`, `SMTP_FROM`, and usually `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_PORT` for real email. Without SMTP, codes are logged and returned as `debug_code` when `AUTH_DEV_SHOW_OTP=1` (default when SMTP is unset) for local demos/tests |
| Google Console project | Optional config | Set `GOOGLE_CLIENT_ID` (OAuth Web client) on the backend; frontend reads it via `GET /auth/config`. Until set, the Google button shows a clear configuration error |

## Known limitations (not gaps, just current scope)

- Only Groq is free-to-test for the agent explanation layer; Anthropic/OpenAI need paid credits, Gemini blocked by a Google-side quota bug (see `docs/agent_prompt_experiments.md`)
- Report timestamps are hardcoded to UTC, not localized
- Users registered before the `name` field was added get initials from their email until they re-register with a name
- Google-only accounts must use Continue with Google (or complete password reset) before email/password login works
