# Comparative Literature Report: Four Accessibility Papers  
## Toward Writing the Axion / Agentic Accessibility Auditor Paper

| Field | Value |
|-------|-------|
| Prepared for | Internship project — Agentic Accessibility Auditor (Axion) |
| Team | Muhammad Noor (Lead), Salar, Ayesha |
| Sources | `d:\internship\papers\` (4 PDFs) |
| Purpose | Deep comparison of strategies, pros/cons, limitations, innovations; map to Axion; layout plan for **our own paper** |
| Date | 18 July 2026 |

---

## 0. How to use this document

1. Read **§1** for the big picture (how the four papers relate).  
2. Read **§2–§5** for each paper in depth (strategy, pros/cons, limits, innovation, Axion relevance).  
3. Use **§6** comparison tables when writing Related Work.  
4. Follow **§7–§8** as the **layout plan** for drafting our paper (sections, claims, experiments, timeline).

---

## 1. Big picture: what these four papers are doing together

```text
                    ┌─────────────────────────────────────┐
                    │  Survey (Liu et al., TOSEM SLR)      │
                    │  Map of detection + repair research   │
                    └─────────────────┬───────────────────┘
                                      │ situates
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
   ScreenAudit (CHI'25)        TaskAudit (CHI'26)           ALVIN (IST/arXiv)
   LLM + TalkBack              Agents *use* the app         GCN on GUI graph
   on a single screen          for functiona11ity errors    for low-vision issues
```

| Paper (short name) | Venue / type | Core question | Method family |
|--------------------|--------------|---------------|---------------|
| **ScreenAudit** | CHI ’25, system + expert study | Can an LLM audit **screen-reader output** better than rule checkers? | Runtime SR capture + LLM report |
| **TaskAudit** | CHI ’26, system + RQs | Can **agents** detect a11y bugs that only appear **during interaction**? | Task gen + agentic SR execution + LLM analysis |
| **SLR (Liu et al.)** | ACM TOSEM survey | What exists for mobile a11y **detection & repair** up to 2025? | PRISMA SLR (76 papers) |
| **ALVIN** | Info. & Softw. Technology / arXiv | Can a **GCN** detect low-vision GUI issues better than brittle rules? | GUI-as-graph + supervised GCN |

**Where Axion sits today**

| Axion capability (built) | Closest literature neighbor |
|--------------------------|----------------------------|
| Hybrid XML parser → `components.json` | Survey “static / hierarchy” detection |
| Deterministic R01–R30 rule engine | Survey rule era; contrast with ALVIN/ScreenAudit limits |
| Score + LLM / template explanations → report | ScreenAudit (LLM explanations) |
| HTML/PDF + Axion UI + auth/records | Productization (less emphasized in CHI systems papers) |
| 40-screen stratified eval + FP/miss notes | Empirical eval pattern from all four |
| **Not yet:** live TalkBack crawl | ScreenAudit |
| **Not yet:** agentic task execution | TaskAudit |
| **Not yet:** trained CV/GCN for contrast/size | ALVIN |

Our paper’s opportunity is not to copy one CHI system, but to present a **complete, reproducible auditor pipeline** (dataset → parse → rules → agent explanations → deliverable reports + product UI + structured evaluation on MASC), then honestly position limitations against these four lines of work.

---

## 2. Paper 1 — ScreenAudit (CHI ’25)

### 2.1 Bibliographic identity

- **Title:** ScreenAudit: Detecting Screen Reader Accessibility Errors in Mobile Apps Using Large Language Models  
- **Authors:** Mingyuan Zhong, Ruolin Chen, Xia Chen, James Fogarty, Jacob O. Wobbrock (UW / CMU)  
- **Venue:** CHI 2025  
- **DOI:** https://doi.org/10.1145/3706598.3713797  
- **File:** `papers/3706598.3713797.pdf` (~19 pages)

### 2.2 Problem they attack

Mobile apps remain inaccessible despite guidelines and tools. Industry checkers (e.g. Google Accessibility Scanner) cover only a **small fraction** of real screen-reader (SR) problems. Developers find checkers incomplete and hard to interpret. Static linters cannot see runtime SR announcements.

### 2.3 Strategy / method (detailed)

1. **Traverse / focus** the Android screen with **TalkBack** (default SR).  
2. **Capture** accessibility metadata + **speech transcripts** (what TalkBack actually announces).  
3. **Prompt GPT-4o** with general TalkBack/accessibility guidance (not only a tiny fixed checklist).  
4. **Emit a developer report**: issues, explanations, suggested repairs, tied to SR output.  
5. **Evaluate** with 6 accessibility experts (incl. 1 blind SR user) on 14 unique app screens; also compare prompting strategies.

**Pipeline intuition:** *Listen like a blind user → ask an LLM “what’s wrong?” → explain to developers.*

### 2.4 Innovation vs previous work

| Previous approaches | ScreenAudit innovation |
|---------------------|------------------------|
| Rule scanners on view hierarchy | Uses **actual TalkBack speech**, not only node attributes |
| Manual SR testing (expensive) | Automates capture + LLM judgment for early feedback |
| LLM UI agents that “see” the screen | Focuses on **SR experience** quality and developer reports |
| Fixed guideline subset | Broader, contextual LLM reasoning over transcripts |

### 2.5 Pros (strengths)

- Strong **ecological validity** for blind/SR users (TalkBack-centric).  
- Higher reported **coverage** (~69%) vs a common checker (~31%) in their expert study.  
- Reports include **explanations and repair advice** (developer usability).  
- Prompt ablation gives reusable insight for LLM a11y auditors.  
- Explicitly frames tool as **complement** to human testing, not a replacement.

### 2.6 Cons / limitations

- Depends on **LLM cost, latency, and non-determinism**.  
- Evaluation scale is **small** (14 screens, 6 experts)—hard to claim universal coverage.  
- Still **screen-level / traversal**, not full multi-screen business workflows.  
- May **hallucinate** or mis-prioritize without strong grounding (they mitigate via expert review).  
- Requires Android TalkBack instrumentation—harder to reproduce on static XML dumps alone.  
- Not primarily about low-vision visual issues (contrast/size)—different user group than ALVIN.

### 2.7 Relevance to Axion (detailed)

| Axion part | How ScreenAudit informs us |
|------------|----------------------------|
| `src/explainer.py` / agent report | Same product goal: **actionable LLM explanations** for developers |
| Rule engine R01–R30 | ScreenAudit argues rules alone under-cover SR semantics—use this to motivate **hybrid** rules + LLM |
| Input = screenshot + XML | We do **not** capture TalkBack yet; cite ScreenAudit as future work / limitation |
| Evaluation | Their expert protocol (precision/coverage, FP discussion) models how we should **upgrade** our 40-screen assisted notes toward stronger human validation |

**What to cite them for in our paper:** “LLM-augmented screen-reader auditing improves coverage and explanation quality over rule checkers alone [ScreenAudit].”

---

## 3. Paper 2 — TaskAudit (CHI ’26)

### 3.1 Bibliographic identity

- **Title:** TaskAudit: Detecting Functiona11ity Errors in Mobile Apps via Agentic Task Execution  
- **Authors:** Mingyuan Zhong, Xia Chen, Davin Win Kyi, Chen Li, James Fogarty, Jacob O. Wobbrock  
- **Venue:** CHI 2026  
- **DOI:** https://doi.org/10.1145/3772318.3791415  
- **File:** `papers/3772318.3791415.pdf` (~20 pages)

### 3.2 Problem they attack

Even when a screen **looks** accessible in a static dump, interaction can fail: cannot focus control, cannot activate, label ≠ behavior, no feedback, confusing navigation. They call these **functiona11ity errors** (functionality + accessibility). Prior crawlers (e.g. Groundhog) catch some locatability/actionability issues but generate FPs and miss semantic mismatches. Vision-based agents (e.g. AXNav) do not fully simulate SR-only interaction.

### 3.3 Strategy / method (detailed)

Three components:

1. **Task Generator** — From the screen, invent interactive tasks (what a user would try to do).  
2. **Task Executor** — Multi-agent system performs tasks via a **screen-reader proxy**, **without vision** (fair simulation of SR use).  
3. **Accessibility Analyzer** — LLM examines **interaction traces** (observations, successes/failures) and reports issues.

**Error categories:** Locatability, Actionability, Label, Feedback, Navigation (mapped partly to WCAG keyboard / name / feedback criteria).

**Evaluation structure (clean for copying in our paper):**
- RQ1: Can tasks be identified?  
- RQ2: Can agents succeed when no a11y bugs?  
- RQ3: Can the system detect functiona11ity errors on real apps?

### 3.4 Innovation vs previous work (esp. ScreenAudit & Groundhog)

| Prior | TaskAudit step forward |
|-------|------------------------|
| ScreenAudit | From “audit what TalkBack says on a screen” → “**try to complete tasks** and judge outcomes” |
| Groundhog | From mechanical crawl + pixel compare → **semantic agent goals** + LLM analysis |
| AXNav | From heuristic loops/missing buttons with vision → SR-proxy execution **without** vision |

### 3.5 Pros

- Addresses a **real gap**: interaction-time a11y failures.  
- Clear **RQ-driven** evaluation (easy to emulate in our paper structure).  
- Strong headline result: **48** functiona11ity errors on 54 screens vs **4–20** for existing checkers.  
- Finds **new qualitative patterns** (label–function mismatch, cluttered nav, bad feedback).  
- Designed for possible IDE / CI integration narrative.

### 3.6 Cons / limitations

- High **system complexity** (multi-agent, SR proxy, LLM)—hard to reproduce in an 8-week internship.  
- Costly and slower than static XML rules.  
- Within-screen focus; full app workflows still hard.  
- Agent failures can confound “a11y bug” vs “agent bug” (they study success rates when no errors).  
- Overlap with ScreenAudit team/venue—cite carefully as **evolution**, not independent contradictory claims.

### 3.7 Relevance to Axion (detailed)

Axion today is **offline**: uploaded screenshot + UIAutomator XML → parse → rules → report. We **cannot** claim TaskAudit-style functiona11ity detection yet.

| Use in our paper | How |
|------------------|-----|
| Related Work | “Interaction-dependent errors require agentic execution [TaskAudit]; our system targets **static hierarchy + explanation** as a complementary first line.” |
| Limitations | Explicitly list absence of task execution / SR proxy. |
| Future work (Week 7–8 / post-internship) | Pilot 1–2 flows with agent tasks on MASC/Rico screens. |
| Design inspiration | Their **three-module** split (generate / execute / analyze) mirrors our **parse / check / explain**—good analogy diagram. |

---

## 4. Paper 3 — Systematic Literature Review (Liu et al.)

### 4.1 Bibliographic identity

- **Title:** Accessibility Issue Detection and Repair in Mobile Applications: A Systematic Literature Review  
- **Authors:** Zhenyu Liu, Dengfeng Yao*, Hongzhe Liu, Cheng Xu, Huiyue Huang (Beijing Union University / Tsinghua)  
- **Venue:** ACM Transactions on Software Engineering and Methodology (TOSEM-style)  
- **DOI:** https://doi.org/10.1145/3809496  
- **File:** `papers/3809496.pdf` (~48 pages)  
- **Corpus:** 76 high-quality studies through ~July 2025; PRISMA process; 9 databases.

### 4.2 Problem they attack

The field is fragmented: many detectors, fewer repair systems, inconsistent taxonomies, high false positives, weak coupling between detect→fix. No single up-to-date SE-oriented survey tying WCAG, user abilities, and engineering lifecycle.

### 4.3 Strategy / method (detailed)

1. **PRISMA SLR** — search, dedupe, dual screening, quality gates, snowballing.  
2. **Issue taxonomy** — map to **POUR** (perceivable, operable, understandable, robust) + user capabilities.  
3. **Detection evolution pathway:** static → dynamic → hybrid → model-driven → **LLM-assisted**.  
4. **Repair taxonomy:** rule-driven / learning-based / LLM-assisted.  
5. **Gap analysis** — FP rates, fragmented modules, missing unified evaluation standards.  
6. **Outlook** — semantic detection, multimodal repair, richer user models, accessibility-by-default.

### 4.4 Innovation vs previous surveys / papers

- Broader and newer corpus including **LLM era** (post-2023).  
- Bridges **SE methodology** (ISO 25010 accessibility as quality) with HCI a11y tools.  
- Separates **detection vs repair** and calls out the broken feedback loop—useful framing for “our system does detection + explanation, not auto-patch.”

### 4.5 Pros

- Best single source for **Related Work scaffolding**.  
- Gives standard vocabulary (POUR, detection stages, repair classes).  
- Helps justify hybrid architectures (rules + ML + LLM).  
- Lists open problems that match our honest limitations (FPs, eval standards).

### 4.6 Cons / limitations (of the survey itself)

- Survey papers **do not** prove a new system—cite for context, not as empirical competitor.  
- Inclusion cut-off will miss newest CHI’26 work unless updated (TaskAudit may be edge).  
- Aggregation can blur **Android vs iOS vs web** differences—we must stay Android/UIAutomator-specific.  
- “76 papers” claims need careful citation of **their** criteria, not ours.

### 4.7 Relevance to Axion (detailed)

This paper should be the **backbone of §Related Work**:

1. Introduce mobile a11y as SE quality attribute (WCAG + ISO framing).  
2. Summarize detection evolution → place Axion as **static/hybrid hierarchy rules + LLM explanation layer**.  
3. Note repair is out of scope (we recommend, we don’t auto-edit APKs)—aligns with survey’s detection–repair gap.  
4. Use their FP / evaluation critique to motivate our Week 6 eval sheet and future gold labeling.

---

## 5. Paper 4 — ALVIN (GCN for low vision)

### 5.1 Bibliographic identity

- **Title:** Are Your Apps Accessible? A GCN-based Accessibility Checker for Low Vision Users  
- **Authors:** Mengxi Zhang, Huaxiao Liu*, Shenning Song, Chunyang Chen, Pei Huang, Jian Zhao  
- **Venue:** Information and Software Technology (preprint arXiv:2502.14288)  
- **File:** `papers/Are your apps accessible.pdf` (~27 pages)

### 5.2 Problem they attack

**Low vision** users (blurry vision, not necessarily screen-reader users) struggle with small targets, tight spacing, low contrast, unclear alerts. Rule tools on nested GUI hierarchies:

1. Flag **invisible** redundant nodes.  
2. Over-penalize **tiny deviations** from numeric thresholds.  
3. **Omit** similar components (e.g. nav items).  
4. Are **hard to extend** when new issue types appear.

### 5.3 Strategy / method (detailed)

1. Prior empirical work on low-vision issues → focus on four issue types (size, interval, contrast, unclear alerts).  
2. Build **GUI-graph**: visible components + containers + relations (drop invisible noise).  
3. Annotate large set of GUIs **with low-vision users** (not pure rule labels).  
4. Train **GCN** multi-class classifier to label inaccessible nodes.  
5. Evaluate precision/recall/F1 (~83.5 / 78.9 / 81.2), ablations, open-source issue usefulness.

### 5.4 Innovation vs previous work

| Previous | ALVIN |
|----------|--------|
| Accessibility Scanner-style rules | Learning from **human low-vision annotations** |
| Independent per-node thresholds | **Graph relations** reduce omission of similar widgets |
| Hard-coded new rules | Extend by **annotating new data**, not rewriting scanners |
| SR-centric tools (ScreenAudit/TaskAudit) | Explicit **low-vision visual** focus |

### 5.5 Pros

- Directly targets **visual** issues our XML rules struggle with (esp. R09 contrast, size/spacing without rendering).  
- Strong quantitative metrics and user-grounded labels.  
- Clear critique of rule scanners—valuable for motivating future CV/GCN stretch.  
- Demonstrates usefulness via real open-source issue submissions.

### 5.6 Cons / limitations

- Needs **large annotated datasets** and ML training pipeline—out of scope for current Axion MVP.  
- Graph construction assumptions may not match every UIAutomator dump.  
- Focused on low vision, not full POUR / SR issues.  
- Model generalization across app categories / themes may vary.  
- Does not produce rich **LLM-style explanations** (classification labels ≠ narrative reports).

### 5.7 Relevance to Axion (detailed)

| Axion today | ALVIN lesson |
|-------------|--------------|
| R09 / R28 limited without colors/text-size | Pure XML cannot fully solve low-vision perception—cite ALVIN |
| Screenshot available but underused for detection | Future: use screenshot features / GUI-graph learning |
| 40-screen eval notes on FP | ALVIN’s “small deviation” critique explains some of our R01/size FPs |
| Guideline training stretch (G09/G11) | ALVIN is the methodological pointer for that stretch |

---

## 6. Cross-paper comparison (for Related Work tables)

### 6.1 What each paper optimizes

| Dimension | ScreenAudit | TaskAudit | SLR | ALVIN | **Axion (ours)** |
|-----------|-------------|-----------|-----|-------|------------------|
| Primary user group | Screen-reader | Screen-reader + interaction | All (survey) | Low vision | Developers + mixed guidelines G01–G30 |
| Input | Live app + TalkBack | Live app + SR proxy | Literature | GUI + annotations | Screenshot + XML dump |
| Detection | LLM on transcripts | LLM on agent traces | N/A | GCN on graph | Deterministic R01–R30 |
| Explanation | Strong (LLM report) | Strong (trace + issue) | N/A | Weak (class label) | LLM/template explanations |
| Repair | Advice only | Advice only | Taxonomy of repair | Advice / issues to fix | Advice in report (no auto-repair) |
| Product UI | Research prototype | Research prototype | N/A | Research tool | Full Axion web app + auth/records |
| Dataset | 14 screens expert | 54 screens + task sets | 76 papers | 2390 GUIs annotated | MASC 7k + Rico holdout + 40 eval |

### 6.2 Pros / cons at a glance

| Paper | Biggest pro | Biggest con for *our* reuse |
|-------|-------------|------------------------------|
| ScreenAudit | SR + LLM explanations | Needs TalkBack runtime |
| TaskAudit | Finds interaction bugs rules miss | Too heavy for current internship scope |
| SLR | Best Related Work map | Not an empirical competitor |
| ALVIN | Fixes low-vision rule brittleness | Needs training data / GCN stack |

### 6.3 Innovation timeline (how to narrate “progress”)

1. **Rules & scanners** dominate early practice (survey).  
2. **ALVIN** shows learning beats brittle numeric rules for **low vision**.  
3. **ScreenAudit** shows LLMs beat scanners for **SR transcript** understanding.  
4. **TaskAudit** shows agents are needed for **interaction-time** failures.  
5. **Axion** (our claim) delivers an **end-to-end, reproducible SE pipeline** combining hierarchy rules, scoring, LLM explanations, exportable reports, and productized UI—on public MASC-scale data—while acknowledging the above research frontiers as future work.

---

## 7. Layout plan for **our** paper (recommended structure)

Use a standard empirical SE / HCI systems paper shape (~8–12 pages depending on venue).

### Title options (draft)

- *Axion: An Agentic Accessibility Auditor for Android UI Hierarchies*  
- *From XML to Actionable Reports: A Rule-and-LLM Pipeline for Mobile Accessibility Auditing*

### Abstract (what must appear)

Problem → gap (checkers incomplete; research tools not productized / not hierarchy-complete) → approach (parse, R01–R30, score, LLM explain, HTML/PDF, UI) → eval (fixtures + 40 stratified MASC screens + FP/miss analysis) → findings → limitations.

### Section-by-section layout

#### §1 Introduction
- Mobile apps + disability stats (borrow carefully from SLR/ALVIN intros; cite WHO etc. via survey).  
- Failure of status-quo checkers (cite ScreenAudit / TaskAudit coverage stats).  
- **Our gap:** need a **complete auditor** that (a) consumes **screenshot+XML pairs**, (b) runs **deterministic, reviewable rules** mapped to guidelines, (c) adds **LLM explanations**, (d) exports reports, (e) supports developer workflow (upload, history).  
- Contributions list (3–5 bullets)—be precise; do not claim TalkBack agents or GCN.

#### §2 Background & Related Work
Use SLR as spine; then subsections:
1. Rule-based and static hierarchy analysis  
2. Learning-based visual / low-vision checkers (ALVIN)  
3. LLM and screen-reader auditing (ScreenAudit)  
4. Agentic interaction testing (TaskAudit)  
5. **Positioning Axion** (table from §6.1)

#### §3 System design (Axion)
Diagram: Upload → Parser → Rules → Agent/Explainer → Report → Records  
Modules matching repo: `parser.py`, `rules.py`, `agent.py`, `explainer.py`, `report.py`, FastAPI, Axion UI.  
Schema contracts (`components.json`, `violations.json`, `report.json`).  
Auth/records as **deployment/product** subsection (short)—not the research core.

#### §4 Rule & guideline mapping
G01–G30 ↔ R01–R30 ownership summary; note R09/R28 limitations (bridge to ALVIN).

#### §5 Evaluation
1. **Unit / fixture eval:** 57 XML fixtures, pytest counts.  
2. **Dataset-scale:** MASC parse sign-off numbers.  
3. **Screen sample study:** 40 stratified screens (seed `20260715`), auto scores, **manual/assisted FP–miss notes**—disclose method honestly.  
4. Optional: compare to Accessibility Scanner on a subset (stretch).  
5. Metrics: issue counts, score distribution, verdict mix, qualitative FP themes (R07/R08 nesting, R30 density).

#### §6 Discussion
- What rules catch well vs miss (static XML blind spots → TaskAudit/ScreenAudit).  
- LLM explanation value vs hallucination risk (ScreenAudit prompt lessons).  
- Productization as SE contribution (survey’s “engineering practice” theme).

#### §7 Limitations
Bullet list mapped to papers: no TalkBack (ScreenAudit), no agent tasks (TaskAudit), weak contrast without vision (ALVIN), assisted not gold labels, Android XML focus.

#### §8 Future work
Short roadmap: SR capture; agentic tasks on critical flows; GCN/CV for G09/G11; Rico holdout final eval; stronger human gold labels.

#### §9 Conclusion
Restate contributions; one paragraph on inclusive mobile SE.

### Figures / tables we should prepare

| Artifact | Source in repo |
|----------|----------------|
| Pipeline architecture figure | SDS / README layout |
| Example report screenshot | Axion Report / HTML sample |
| Eval sampling table | `docs/week6/evaluation_sheet.md` |
| Related Work comparison table | §6.1 above |
| FP theme examples | week6 CSV notes |

### Claims we **can** make vs **must not** make

| Can claim | Must not claim |
|-----------|----------------|
| End-to-end Android XML auditor with 30 rules + explanations + exports | Better SR coverage than ScreenAudit without TalkBack study |
| Reproducible MASC-oriented evaluation protocol | Gold-standard human labels for all 40 screens (unless we re-annotate) |
| Hybrid rules + LLM explanations are complementary | We detect all functiona11ity errors |
| Product UI supports realistic developer workflow | We auto-repair apps like full repair systems in the SLR |

---

## 8. Execution plan — what we need to do to write the paper

### Phase A — Freeze research claims (1–2 days)
- [ ] Agree contribution bullets with Salar & Ayesha.  
- [ ] Decide venue style (internship report vs workshop vs full conference).  
- [ ] Freeze “what is research core” vs “product scaffolding” (auth/SMTP = short mention).

### Phase B — Related Work draft (2–3 days)
- [ ] Write §2 using SLR structure + one paragraph each for ScreenAudit, TaskAudit, ALVIN.  
- [ ] Insert comparison table (§6.1).  
- [ ] Collect exact citation keys (BibTeX from DOIs).

### Phase C — System description (2–3 days)
- [ ] Redraw pipeline figure (clean, paper-ready).  
- [ ] Describe schemas + example violation/report snippets (anonymized).  
- [ ] Document score formula briefly (`compute_accessibility_score`).

### Phase D — Evaluation write-up (3–5 days) **critical**
- [ ] Report fixture/pytest results with versions.  
- [ ] Publish 40-screen methodology (stratified, seed, categories).  
- [ ] **Upgrade honesty:** either (a) keep “assisted review” and state limits, or (b) manually spot-check N≥10 screens against screenshots for a “gold subset.”  
- [ ] Summarize FP/miss themes with 2–3 concrete examples.  
- [ ] Optional: Rico holdout smoke numbers if ready.

### Phase E — Discussion / limitations / future (1–2 days)
- [ ] Map each limitation to ScreenAudit / TaskAudit / ALVIN.  
- [ ] Propose one feasible next experiment per paper line.

### Phase F — Polish (2–3 days)
- [ ] Abstract + intro punch-up.  
- [ ] Consistency pass (numbers match validation logs).  
- [ ] Supervisor review; regenerate DOCX if needed via `scripts/md_to_docx.py`.

### Suggested writing order (efficiency)
1. Comparison table + Related Work  
2. System section (easiest—code exists)  
3. Evaluation (hardest—needs careful wording)  
4. Introduction + Abstract (write last)  
5. Limitations / Future / Conclusion  

### Team split suggestion

| Person | Paper sections |
|--------|----------------|
| **Noor** | System (API/agent/report), Evaluation coordination, Limitations mapping to CHI papers |
| **Salar** | Parser/rules technical depth, fixture results, MASC scale numbers |
| **Ayesha** | UI/workflow figures, Related Work on guidelines/Figma motivation, Rico holdout paragraph |

---

## 9. One-page “elevator” positioning (paste into intro)

> Automated accessibility checkers for Android remain limited: rule-based scanners miss many screen-reader and interaction failures, while recent research systems explore LLM audits of TalkBack output [ScreenAudit], agentic task execution [TaskAudit], and graph learning for low-vision issues [ALVIN]. Complementary to these directions, we present **Axion**, an end-to-end **Agentic Accessibility Auditor** that ingests screenshot–XML pairs, applies a deterministic guideline-mapped rule set (R01–R30), computes an accessibility score, generates LLM- or template-based explanations, and exports HTML/PDF reports through a developer-facing web application. We evaluate the pipeline on controlled fixtures and a stratified 40-screen MASC sample with structured false-positive and miss analysis. Axion does not replace TalkBack-driven or agentic interaction testing; instead, it provides a reproducible static-hierarchy baseline and explanation layer that those richer analyses can extend.

---

## 10. Source files checklist

| Paper | Local PDF |
|-------|-----------|
| ScreenAudit | `papers/3706598.3713797.pdf` |
| TaskAudit | `papers/3772318.3791415.pdf` |
| SLR Liu et al. | `papers/3809496.pdf` |
| ALVIN | `papers/Are your apps accessible.pdf` |

**Axion evidence to attach when writing:**  
`docs/week6/`, `outputs/validation_logs/noor_week6_*`, `srs/`, `sds/`, `docs/progress/Supplementary_Progress_Report_v1.0.md`, `README.md`.

---

## 11. Document history

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 18 Jul 2026 | Initial comprehensive comparative report + Axion paper layout plan |

---

*End of report — use §7–§8 as the working checklist for drafting the team paper.*
