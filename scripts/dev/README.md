# Local / optional smoke helpers

These scripts are for **local debugging** of SMTP and auth flows. They are not part of the production pipeline.

| Script | Purpose |
|--------|---------|
| `_check_real_mail.py` | Quick SMTP send check |
| `_smtp_test_send.py` | Minimal SMTP test |
| `_verify_auth_flow.py` | Auth endpoint flow smoke |
| `_verify_auth_live.py` | Live server auth checks |

Prefer unit tests: `python -m pytest backend/tests/test_auth.py -q`.

**Never put App Passwords or real user emails into committed files.** Use local `.env` only.
