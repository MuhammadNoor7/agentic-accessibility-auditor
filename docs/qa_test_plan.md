# Quality Assurance (QA) Test Plan
**Project:** Agentic Accessibility Auditor  
**Author:** Intern 3 (Lead)  
**Related:** [`accessibility_guidelines_report.md`](accessibility_guidelines_report.md) · [`json_schemas.md`](json_schemas.md)

## 1. Objective
To verify that the Agentic Accessibility Auditor correctly identifies UI accessibility violations based on the defined **30 guidelines (G01–G30)** and **30 detection rules (R01–R30)**, and provides accurate developer fixes via the agentic explanation layer.

## 2. Testing Scope
- **Rule Correctness:** Ensure the rule-checker logic accurately flags issues without excessive false positives.
- **Guideline Mapping:** Every violation must reference the correct G-ID and rule ID.
- **Agentic Layer Quality:** Verify that LLM explanations are clear and fixes are technically valid. The agent must **not invent** violations — it only explains rule-detected issues.
- **System Pipeline:** Ensure the pipeline (XML → Parser → Rule checker → Agent → Report) runs end-to-end without crashing.

## 3. Test Data Strategy
- **MASC dataset (7,068 screens):** Split into train (70%) / val (15%) / test (15%) via `scripts/split_masc_dataset.py`. Use train+val for development and tuning; MASC test split for internal regression only.
- **Rico holdout (1,698 screens):** Filtered from `final_rico` with zero byte-level overlap against MASC (see [`rico_holdout_dataset.md`](rico_holdout_dataset.md)). Held out entirely as **unseen final evaluation** — never used during rule development or threshold tuning.
- **Controlled Examples:** 10–15 manually crafted XML files with known injected violations (R01–R05 priority per internship acceptance criteria).

## 4. Manual Validation Process
For each screen tested, a reviewer will inspect the generated HTML/PDF report and score the findings:
- **True Positive (Correct):** The tool found an issue, and it is a real accessibility problem.
- **False Positive (Incorrect):** The tool flagged an issue, but the UI is actually accessible.
- **False Negative (Missed):** The tool missed a glaring accessibility issue on the screen.

## 5. Specific Test Cases
| Test ID | Module | Description | Expected Outcome |
|---------|--------|-------------|------------------|
| TC-01 | Parser | Upload XML with missing bounds | Parser should gracefully handle or skip the node without crashing. |
| TC-02 | Rules (R01) | Clickable Button with no `text` and no `content-desc` | Rule R01 (Missing Label) must trigger. |
| TC-03 | Rules (R04) | Clickable element sized 30×30 pixels | Rule R04 (Small Touch Target) must trigger. |
| TC-04 | Rules (R05) | EditText with empty `text` and empty `content-desc` | Rule R05 (Unlabeled Input) must trigger. |
| TC-05 | Agent | Process a violation through the LLM | Returns `agent_explanation`, `agent_why_it_matters`, `agent_developer_fix`. |
| TC-06 | Report | Generate report with 5+ violations | HTML report shows severity colors and screenshot. |

## 6. Sign-off Criteria
- Rules R01–R05 reliably detect issues on 10–15 controlled test cases.
- Pipeline processes MASC train split without fatal errors.
- Final evaluation runs on **Rico holdout** (`data/data-rico-holdout/`, unseen) with documented manual validation summary.
- Generated HTML report is readable and matches JSON output.
