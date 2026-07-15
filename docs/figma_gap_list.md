# Figma vs Live App — Implementation Gap List

**Author:** Ayesha Naveed (updated by Muhammad Noor, Week 6)
**Purpose:** One-page reference of what's real vs still mock UI, for supervisor review.

## ✅ Fully implemented (real backend)

| Feature | Notes |
|---|---|
| Sign up / Log in | Real JWT auth; email + password rules enforced (valid domain, ≥8 chars with letter+number) |
| Profile initials (top-right) | Real — initials from name or email local-part |
| Email verification (OTP) | Real — signup → OTP → `/verify-code` → JWT |
| Forgot / Reset Password | Real — forgot → OTP → set password via `reset_token` |
| Google Sign-In | Real OAuth ID-token flow (`GOOGLE_CLIENT_ID` required) |
| **SMTP email delivery** | Real — Gmail SMTP via App Password (`SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM`). Sends **to any recipient domain** (Yahoo, Outlook, `.edu`, …) |
| Upload → Audit | Real screenshot + XML pipeline |
| Dashboard | Real violations + accessibility score |
| Report view | Real score + explanations |
| Report download (HTML/PDF) | Real — embeds screenshot, XML, violations |
| Records / Audit History | Real `GET /records` |
| Reopening a past record | Real saved report refetch |

## ⚠️ Still mock / not implemented

None remaining from the Figma auth / report shell.

**Config you must set locally (not code gaps):**

| Setting | Why |
|---|---|
| `SMTP_USER` + `SMTP_PASSWORD` (Gmail App Password) + `SMTP_FROM` | Real OTP emails |
| `GOOGLE_CLIENT_ID` | Google button works end-to-end |
| `JWT_SECRET` | Production-safe tokens |

Until SMTP is configured, `AUTH_DEV_SHOW_OTP` exposes `debug_code` so the verify screen still works offline.

## Known limitations

- Agent LLM: Groq is free-to-test; Anthropic/OpenAI need credits
- Report timestamps are UTC
- Google-only accounts must use Continue with Google (or password-reset) before email/password login
- **Email accounts:** signup/login accept **any valid email domain** (not Gmail-only). Gmail is only used as the *SMTP sender* when delivering OTP codes