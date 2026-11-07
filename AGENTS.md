# Project Instructions: Humanizer for DOCX & Scientific Document Integrity

These instructions apply throughout this repository. This project provides a production-grade framework for drafting, refining, humanizing, and mathematically verifying academic research manuscripts in Microsoft Word (`.docx`) format, with automated structural, citation, and coherence testing.

---

## Phase 0: Document Format & Template Grilling Gate (MANDATORY)

> [!CRITICAL]
> **NEVER ASSUME OR HARDCODE A DEFAULT DOCX FORMAT.**
> Do **NOT** default to IEEE two-column, single-column thesis, standard 1-inch margins, or any specific layout without explicit confirmation.
> Before generating, formatting, or editing any `.docx` or `.pdf` file, the agent **MUST GRILL THE USER** via interactive question prompts (`ask_question` tool or structured interview dialog).

### Mandatory Grilling Interview Checklist

1. **Existing Draft vs. From-Scratch Creation**:
   - *Question*: "Do you already have an existing `.docx` draft or started manuscript file you want edited in-place, or are we creating a brand-new document from scratch?"
   - If an existing file exists, request its path and inspect its styles, XML layout, and headings before making any changes.

2. **Reference Template / Style Sample**:
   - *Question*: "Do you have a style template (`.docx` or `.pdf` sample/author guidelines from your university, department, or target journal/conference) that we should extract exact margins, column settings, typography, and citation format from?"
   - If provided, extract the template's page width, margins, column count, heading font/sizes, body line spacing, and paragraph indentation.

3. **Page, Column & Layout Specifications (if no template file is supplied)**:
   - *Paper Size*: A4 (`210 mm x 297 mm`) or US Letter (`8.5 in x 11.0 in`)?
   - *Column Architecture*: Single-column (standard university thesis/dissertation) or Two-column (IEEE/ACM/Elsevier conference/journal)?
   - *Typography & Spacing*: Font family (Times New Roman, Arial, Calibri, Cambria), font size (10pt, 11pt, 12pt), and line spacing (single, 1.15x, 1.5x, double)?
   - *Citation Style*: IEEE numbered brackets (`[1]`), APA 7th author-date (`(Author, 2024)`), ACM numbered, or Harvard?
   - *Page Budget*: Target concise page count (e.g., 4–6 pages concise vs. 15–30 pages full thesis)?

4. **Citation Discipline & Humanizer Preferences**:
   - *Citation Density*: Single-citation-per-statement rule (`1` citation per sentence) or multi-citation clusters permitted?
   - *External Humanizer Step*: Will you pass section drafts through **CleverHumanizer** (`https://cleverhumanizer.ai/`) for sentence smoothing, or rely solely on local humanizer skill passes?

---

## Required Skill Use & Matrix

Before writing, revising, researching, or reviewing scientific content:
1. Select the relevant skills from the table below. Read each selected `SKILL.md` in full before starting work.
2. Follow the skill's specific workflow, verification scripts, and acceptance criteria.
3. Apply the humanizer skills in combination: `blader/humanizer` for Wikipedia AI-tell pattern removal and `the-humanizer` for scoring, burstiness, and tone authenticity.

| Task | Required Skills to Read & Apply |
| :--- | :--- |
| **Document Discovery & Layout Setup** | [word-writing](.agents/skills/word-writing/SKILL.md), plus Phase 0 User Grilling Gate |
| **Literature Search & Citation Architecture** | [literature-review](.agents/skills/literature-review/SKILL.md) and [citation-management](.agents/skills/citation-management/SKILL.md) |
| **Drafting Academic Prose & Methodology** | [scientific-writing](.agents/skills/scientific-writing/SKILL.md) |
| **Local AI-Tell Detection & Removal** | [humanizer](.agents/skills/humanizer/SKILL.md) followed by [the-humanizer](.agents/skills/the-humanizer/SKILL.md) |
| **Statistical & Experimental Validity Audit** | [scientific-critical-thinking](.agents/skills/scientific-critical-thinking/SKILL.md) |
| **Formal Manuscript Peer-Review** | [peer-review](.agents/skills/peer-review/SKILL.md) |
| **Equation Repair & Native OMML Math** | [word-writing](.agents/skills/word-writing/SKILL.md) |
| **Codebase & Architecture Mapping** | [graphify](.agents/skills/graphify/SKILL.md) |

---

## The 8-Stage Publication-Grade Workflow

All manuscript updates follow this linear quality pipeline:

```
[Stage 0: Format Grilling Gate] 
         │ (User confirms template, columns, citations, page target)
         ▼
[Stage 1: Evidence & Citation Gate] 
         │ (25+ references, 100% verified DOIs, single-citation discipline)
         ▼
[Stage 2: Concise Academic Drafting] 
         │ (Focused on operational methods, specimen independence, mathematical rigor)
         ▼
[Stage 3: Dual Local Humanizer Pass] 
         │ (Remove 24 Wikipedia AI tells + the-humanizer structural scoring)
         ▼
[Stage 4: CleverHumanizer External Smoothing Pass] 
         │ (https://cleverhumanizer.ai/ for high-burstiness sentence rhythm)
         ▼
[Stage 5: Post-Humanizer Regression Testing] 
         │ (Detect and fix spaced-dot code artifacts like 'skimage. feature' & broken commas)
         ▼
[Stage 6: Non-Destructive VML Diagram & OMML Math Injection] 
         │ (Update figures and math in-place without touching prose XML)
         ▼
[Stage 7: Visual Page-Render QA & Automated Test Suite]
           (tests/run_all_docx_tests.py -> Exit code 0)
```

---

## Automated Verification Commands

Run the test suite at every major milestone:

```bash
# Unified test harness running all 3 verification modules
python tests/run_all_docx_tests.py --docx path/to/document.docx

# Export a structured Markdown report
python tests/run_all_docx_tests.py --docx path/to/document.docx --report-out docx_audit_report.md

# Individual test modules
python tests/test_coherence_and_humanizer.py --docx path/to/document.docx
python tests/test_citation_density.py --docx path/to/document.docx --expected-refs 25
python tests/test_docx_integrity.py --docx path/to/document.docx --columns 2 --expected-figures 6
```

---

## Research and Writing Standards

1. **Never Invent Data or Citations**: Every citation must link to a real DOI, published paper, or official government herbarium/statistical record.
2. **Preserve Supported Meaning During Humanizing**: Do not alter technical variables, sample sizes ($N=2,000$), species binomials (*Plectranthus amboinicus*), or statistical test names (paired Wilcoxon, Holm-Bonferroni) when polishing rhythm.
3. **Native Editable Word Equations**: Convert all mathematical formulas to native OpenXML Math (`<m:oMath>`). Never leave raw LaTeX commands (`\frac`, `\sum`) in Word prose.
4. **Non-Destructive Diagram Preservation**: Word converts DrawingML diagrams into VML `<v:shape>` wrappers upon saving. Always update figures using non-destructive script tools (`scripts/update_diagrams_only.py`) that preserve all XML formatting.

