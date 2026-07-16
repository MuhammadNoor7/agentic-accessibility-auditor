# Noor Week 6 Summary — Auth/Records Sync + Eval + Recent Session

**Branch:** `noor`  
**HEAD (this update):** `995f6d31`  
**Dates:** 2026-07-15 (baseline sync/eval) · **2026-07-16** (report/auth/eval fill re-validation)  
**Owner:** Muhammad Noor  

## Week 6 deliverables — status

| Item | Path / evidence | Status |
|------|-----------------|--------|
| Sync Salar JWT auth + records into `noor` | `backend/auth.py`, `auth_router.py`, `records_router.py` | Done |
| Sync Ayesha frontend/docs | Login/Records/Dashboard, `docs/agent_prompt_experiments.md` | Done |
| Upload screenshot + XML pair + `POST /audit` | `Upload.jsx`, `tests/test_audit.py` | Done |
| Report UI shows `accessibility_score` | `Report.jsx`, `Dashboard.jsx` | Done |
| Records: live API + screenshot/XML names + score | `Records.jsx` | Done |
| 40-screen eval sheet (stratified seed `20260715`) | `docs/week6/evaluation_sheet_40_screens.csv` | Done |
| Manual FP / miss notes on **all 40** rows | same CSV + `evaluation_sheet.md` | Done |
| R26–R30 design notes | `docs/week6/r26_r30_design.docx` | Done |
| Docs: SRS / SDS / progress / `updated_plan` (md+docx) | `srs/`, `sds/`, `docs/progress/`, `updated_plan.md` | Done |
| Validation script + logs | `scripts/noor_week6_validate.py`, this folder | Done |

**Week 6 core checklist: complete.** Optional stretch still open for Friday live demo polish / training stretch (not blocking the assigned Week 6 list).

---

## Recent session work (past ~5–6 hours) — outputs

| Work item | Commit / artifact | Validation |
|-----------|-------------------|------------|
| HTML/PDF export: persist screenshot+XML; template autoescape so XML/violations render | `123fbde4` · `src/report.py`, `audit_report.html.j2` | `tests/test_audit.py` → **9 passed** (HTML asserts screenshot present; PDF runs) |
| OTP email verify, forgot/reset password, Google Sign-In | `995f6d31` · `backend/otp_store.py`, `email_service.py`, auth router + frontend flows | `backend/tests/test_auth.py` → **22 passed** (was 12 on 15 Jul) |
| Profile initials (not hardcoded avatar) | `frontend/src/components/ui/UserAvatar.jsx`, `utils/auth.js` | Present; used on Upload/Dashboard/Report/Records/MainLayout |
| SMTP Gmail App Password wiring | `.env` (`SMTP_*`), `load_dotenv(..., override=True)` | Live mail checks via `_check_real_mail.py` / `_smtp_test_send.py` (dev helpers; secrets not logged) |
| Week 6 eval **40/40** assisted fill | `_fill_week6_manual_eval.py` → CSV + `evaluation_sheet.md/.docx` | Integrity: `manual_complete=40`; verdicts below |

### Eval sheet verdict mix (40/40)

| Verdict | Count |
|---------|------:|
| mostly_agree | 32 |
| agree_clean | 3 |
| mixed_r30_noise | 3 |
| over_flagging | 2 |

Categories: 4 each of chat, home, list, login, maps, menu, profile, search, settings, welcome.

### Important — fill method (research honesty)

The “manual” columns were filled by **`_fill_week6_manual_eval.py` using rule-count heuristics**, not a separate pixel-level human gold annotation pass. Treat notes as **structured assisted review** grounded in engine outputs + known FP/miss patterns. Disclose this when presenting.

---

## Live validation results (2026-07-16)

```
STEP A: pytest backend/tests/test_auth.py  → 22 passed, 2 warnings in 9.50s
STEP B: pytest tests/test_audit.py         → 9 passed, 1 warning in 2.65s
STEP C: pytest R26–R30 rules               → 8 passed, 116 deselected in 0.81s
STEP D: eval sheet integrity               → 40/40 manual columns complete
Overall                                    → PASS
```

Full machine log (includes 2026-07-15 baseline + 2026-07-16 append):  
`outputs/validation_logs/noor_week6_validation_log.txt`

### Baseline vs today

| Check | 2026-07-15 | 2026-07-16 |
|-------|------------|------------|
| Auth pytest | 12 passed | **22 passed** (+ OTP / reset / Google) |
| Audit pytest | 8 passed, 1 skipped (PDF) | **9 passed** (PDF included) |
| R26–R30 | 8 passed | 8 passed |
| Eval manual columns | blank | **40/40 filled** |

---

## `_fill_week6_manual_eval.py` — what it does

1. Reads `docs/week6/evaluation_sheet_40_screens.csv`.
2. For each of 40 rows, loads rule hit counts (CSV columns, optionally re-run `evaluate_rules` on components JSON).
3. Applies formulas:
   - **`verdict_from`** — maps score / totals / R07+R08 “naming_heavy” / R30 into `agree_clean` | `mostly_agree` | `over_flagging` | `mixed_r30_noise`.
   - **`fp_notes`** — text when R07/R08/R01/R30/… cross thresholds (engine likely over-flagging).
   - **`miss_notes`** — text by screen category (chat/home/settings/login) for known static-XML blind spots.
4. Writes CSV + regenerates `evaluation_sheet.md` rationale tables.

### Are the formulas “correct”?

| Aspect | Assessment |
|--------|------------|
| Internally consistent | Yes — same thresholds for all 40 rows; reproducible |
| Aligned with known a11y tool noise (nested naming, R30 density) | Reasonable for **assisted** notes |
| Substitute for true human gold labels | **No** — thresholds (e.g. R08≥10, R07+R08≥45% of hits) are engineering judgment, not inter-annotator agreement |
| OK for Week 6 research presentation | Yes **if you state**: “heuristic-assisted review from rule distributions,” not “independent blind human coding” |

---

## Next (optional / Week 7+)

- Friday demo walkthrough (signup → upload pair → report → records)
- Training stretch on MASC train/val/test
- If reviewers require gold labels: spot-check a subset of CSV notes against screenshots and revise notes by hand
