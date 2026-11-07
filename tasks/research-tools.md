# Paper-writing tools

Setup checked on 2026-11-03. Project skills live in `.agents/skills/` and are available on the next Codex turn.

| Skill | Status | Use |
| --- | --- | --- |
| `humanizer` | Already installed; preserved | Edit prose while preserving claims, citations, and the author's voice. |
| `scientific-writing` | Already installed; preserved | Draft and revise manuscript sections with traceable evidence. |
| `literature-review` | Added | Plan searches, screen studies, and synthesize related work. |
| `citation-management` | Added | Find papers, check bibliographic metadata, and manage references. |
| `scientific-critical-thinking` | Added | Assess methods, bias, statistical interpretation, and claim strength. |
| `peer-review` | Added | Prepare a structured assessment and revision plan for an authorized manuscript. |
| `graphify` | Added | Map relationships across project code and research documents. |
| `word-writing` | Added | Preserve Word layout and produce editable, visually checked equations. |

## Sources

- Graphify: https://github.com/Graphify-Labs/graphify — existing `graphifyy` CLI version 0.9.77; project skill installed with `graphify agents install --project`.
- Humanizer: https://github.com/blader/humanizer — existing local skill version 3.1.0.
- Scientific skills: https://github.com/K-Dense-AI/scientific-agent-skills — four additions pinned to commit `a25cf9ec00e2745d03f8704acf6f6919694ccd9a`, with their bundled references, scripts, and assets.

## Suggested workflow

1. Use Literature Review to plan the related-work search.
2. Use Citation Management to verify references against their actual sources.
3. Use Scientific Writing to draft or revise the requested section.
4. Use Scientific Critical Thinking or Peer Review to check methods and claims.
5. Use Humanizer for a final prose edit without changing evidence or meaning.

Example request: "Use scientific-writing and humanizer to revise the introduction in [file], preserving its citations and supported claims."

For this flora project, keep proposed experiments separate from completed pilot results. Installation does not validate the paper, citations, datasets, or research conclusions.

## Graphify

The CLI runs from the existing isolated uv tool environment, separate from the project's ML `.venv`. PDF and Office extras support PDF and DOCX ingestion. Use the Graphify skill through a request such as "Use graphify to map reference_doc".

A preliminary scan found about 11 million words across drafts and temporary artifacts. No knowledge graph was built. Choose a focused input folder before indexing; a scan cache alone is not a completed graph.

## Optional dependencies

The installed skills provide instructions and bundled resources. Some script features need additional packages or services: citation searches use `requests`, Google Scholar additionally uses `scholarly`, and literature-review PDF export uses Pandoc and XeLaTeX. Optional image-generation steps need an external API. Those optional features were not installed or exercised by this setup.

## Verification

All seven skill entrypoints passed name and frontmatter checks; all 30 bundled Python scripts parsed successfully. Graphify successfully extracted text locally from the reference PDF and `output/Local_Flora_Chapters_1_to_3.docx`. The source documents were unchanged. Live literature searches, citation-validation workflows, and manuscript audits were not run.

The later `word-writing` addition passed the skill validator and is required by `AGENTS.md` for DOCX and equation work. Its first repair produced `output/Local_Flora_Equations_Corrected.docx` from `Local_Flora_PDF_Format_Updated.docx`, preserving the original file. Word reopened the corrected copy and recognized seven equation objects, including four fraction functions. Only the metrics paragraph in `word/document.xml` changed; other document nodes, package assets, and section geometry were preserved. All six rendered pages and the enlarged equation page were visually inspected.

Rendering limitation: the packaged renderer lacked `pdf2image`, and native Word PDF export did not complete. Visual QA used the installed Windows LibreOffice PDF converter and PyMuPDF page images; Word's native object model separately verified the editable equations. This formatting repair did not audit research claims or citations.
