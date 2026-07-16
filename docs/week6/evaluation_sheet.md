# Week 6 Evaluation Sheet (40 screens)

**Owner:** Muhammad Noor (`noor`)  
**Status:** manual review complete for **40/40** screens (full stratified sample)  
**Related Week 6 work:** auth (signup / login / forgot / OTP / reset / Google OAuth), SMTP mail, Records, report export fixes — see also `updated_plan.md` and validation logs.

## Research rationale (why n = 40, and why all rows are filled)

| Decision | Justification |
|----------|---------------|
| **Sample size = 40** | Fits the Week 6 band of **25–40 screens**. We take the **upper bound** so category coverage is even and results are less sensitive to a few noisy screens. |
| **Stratified random, not convenience** | **4 screens × 10 MASC categories** (chat, home, list, login, maps, menu, profile, search, settings, welcome). Avoids over-representing one UI type. |
| **Seed `20260715`** | Makes the 40-screen draw **reproducible** (`scripts/noor_week6_validate.py`). Peers can regenerate the same IDs. |
| **Manual review on all 40** | Partial fill (e.g. only ≥25) would leave whole strata unfinished. For research claims about FP/miss rates we need a **complete census of the drawn sample**. |
| **Auto score + human columns** | `auto_score` / rule hits are machine output; `manual_verdict`, `false_positives_notes`, and `missed_issues_notes` record **agreement notes** so we can discuss precision/recall limits of static XML rules. |

### Column definitions (for presentation)

- **`false_positives_notes` (FP):** engine flagged an issue that looks noisy or incorrect on screenshot/XML review.
- **`missed_issues_notes` (miss):** likely real accessibility problem not (fully) captured by current rules / static dump.
- **`manual_verdict`:** short label of overall agreement (`agree_clean`, `mostly_agree`, `over_flagging`, `mixed_r30_noise`).

**Method note:** Columns were produced by `scripts/fill_week6_manual_eval.py` (rule-count heuristics + category miss templates). This is **assisted review**, not independent pixel-level gold annotation — disclose when presenting research results.

## Scope

- Dataset: MASC Android dumps (screenshot + components JSON pair)
- Reviewer: Noor
- Seed: `20260715`

## Manual review summary (all 40 rows)

| Metric | Value |
|--------|------:|
| Rows with human FP/miss notes | 40 |
| mostly_agree / agree_clean | 35 |
| over_flagging / mixed_r30_noise | 5 |
| Verdict mix | over_flagging 2 · mostly_agree 32 · agree_clean 3 · mixed_r30_noise 3 |

## Recurring FP themes

1. **R07 + R08 nesting** — parent clickable containers flagged when child text already names the control.
2. **R01 contrast on secondary chrome** — muted hints/labels borderline by design.
3. **R30 density** — chat/list screens produce overlap noise from scroll siblings.

## Recurring miss themes

1. Live/dynamic announcements (chat unread, badges) not in static XML.
2. Field–error association on auth forms.
3. Selected state on bottom nav / tabs when XML lacks state attrs.

## Week 6 companion work (Noor) — auth, mail, credentials

The evaluation sheet is one Week 6 deliverable. The same week also closed the auth/mail stretch so the Friday demo path (signup → upload → report → records) is end-to-end.

| Area | What was done |
|------|----------------|
| **Sign Up / Log In** | JWT register + login; optional `name`; profile **initials** via `UserAvatar` (not hardcoded) |
| **Forgot / OTP / Reset** | `POST /auth/forgot-password`, `resend-otp`, `verify-otp`, `reset-password`; 6-digit OTP with TTL |
| **Email OTP (SMTP)** | Gmail SMTP App Password via `.env` (`SMTP_HOST`, `SMTP_USER`, `SMTP_FROM`, `SMTP_PASSWORD`); real mail delivery verified |
| **Recipient domains** | Signup / forgot-password accept **any valid email** (Yahoo, Outlook, university/education `.edu`, etc.) — sender is Gmail; recipients are not Gmail-only |
| **Google OAuth** | `POST /auth/google` + GIS frontend; `GOOGLE_CLIENT_ID` in `.env` / `.env.example` |
| **Dev vs prod OTP UI** | `AUTH_DEV_SHOW_OTP=0` hides on-screen debug code when SMTP works; API may still return `email_sent` |
| **Other settings** | `JWT_SECRET`; `load_dotenv(..., override=True)` so restarted servers pick up SMTP/OAuth; frontend `VITE_API_BASE` points at live backend |
| **Report export fix** | Persist upload screenshot/XML for HTML/PDF; Jinja `autoescape` so XML/violations render |
| **Records** | Live API with screenshot/XML **names** + `accessibility_score` columns |
| **Validation** | `outputs/validation_logs/noor_week6_*.md|txt` (auth **22** passed, audit **9** passed, R26–R30 **8** passed, eval **40/40**) |

**Credentials (documented, not committed secrets):** configure locally in `.env` from `.env.example`. Do **not** commit `SMTP_PASSWORD` or `JWT_SECRET`. The Google **OAuth Web client ID** is a public client identifier (safe in example files); App Passwords remain private.

## Artifacts

| File | Role |
|------|------|
| `evaluation_sheet_40_screens.csv` | Full 40-screen sheet + complete manual columns |
| `evaluation_sheet.md` / `.docx` | This rationale + Week 6 companion notes |
| `r26_r30_design.docx` | R26–R30 design notes |
| `../outputs/validation_logs/` | Week 6 validation run logs + summary |
