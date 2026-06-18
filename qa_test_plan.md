# Quality Assurance (QA) Test Plan
**Project:** Agentic Accessibility Auditor
**Author:** Intern 3 (Lead)

## 1. Objective
To verify that the Agentic Accessibility Auditor correctly identifies UI accessibility violations based on the defined rules (R1-R10) and provides accurate, helpful developer fixes via the Agentic Layer.

## 2. Testing Scope
- **Rule Correctness:** Ensure the rule-checker logic accurately flags issues without excessive false positives.
- **Agentic Layer Quality:** Verify that the LLM explanations are clear and the recommended fixes are technically valid.
- **System Pipeline:** Ensure the pipeline (XML -> Parser -> Rules -> Agent -> Report) runs end-to-end without crashing.

## 3. Test Data Strategy
- **Dataset Size:** 25-40 Android screens (Screenshots + UIAutomator XML pairs).
- **Controlled Examples (Unit Tests):** 10-15 manually crafted XML files where we *intentionally* inject known accessibility violations (e.g., deleting a `content-desc` from an `ImageButton`) to ensure the rules catch them.

## 4. Manual Validation Process
For each screen tested, a reviewer will inspect the generated HTML/PDF report and score the findings:
- **True Positive (Correct):** The tool found an issue, and it is a real accessibility problem.
- **False Positive (Incorrect):** The tool flagged an issue, but the UI is actually accessible.
- **False Negative (Missed):** The tool missed a glaring accessibility issue on the screen.

## 5. Specific Test Cases to Add to Project Board
| Test ID | Module | Description | Expected Outcome |
|---------|--------|-------------|------------------|
| TC-01 | Parser | Upload XML with missing bounds | Parser should gracefully handle or skip the node without crashing. |
| TC-02 | Rules (R1) | Upload XML with a clickable Button that has no `text` and no `content-desc` | Rule R1 (Missing accessible label) must trigger. |
| TC-03 | Rules (R4) | Upload XML with a clickable element sized 30x30 pixels | Rule R4 (Small touch target) must trigger. |
| TC-04 | Rules (R5) | Upload XML with an EditText that has empty `text` and empty `content-desc` | Rule R5 (Unlabeled input field) must trigger. |
| TC-05 | Agent | Process a violation through the LLM | LLM must return valid JSON with `agent_explanation`, `why_it_matters`, and `developer_fix`. |
| TC-06 | Report | Generate report with 5+ violations | HTML Report must render correctly, showing severity colors and the screenshot. |

## 6. Sign-off Criteria
- All core rules (R1-R5) reliably detect issues on the 10-15 controlled test cases.
- The pipeline processes the full 25-40 screen dataset without fatal errors.
- The generated HTML report is readable and accurately reflects the JSON output.
