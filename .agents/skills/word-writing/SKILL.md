---
name: word-writing
description: Create or revise Microsoft Word DOCX documents while preserving academic formatting, editable equations, and a visually verified final layout. Use for Word writing, DOCX formatting, equation repair, or math that appears as raw LaTeX or plain-text notation.
---

# Word writing and equations

Use this skill for the Word artifact layer. Apply scientific-writing for scientific content and humanizer for prose edits, as required by the project's AGENTS.md.

## Preserve the document

- Read the target document and inspect its layout before editing. Match supplied references, styles, section geometry, columns, captions, and citations.
- Make the requested change in a separate review copy unless the user explicitly requests replacement. Preserve the original and limit changes to the affected content.
- Use the installed documents skill and its dependency/rendering workflow when supported by the host. Read its relevant editing and equation guidance. If the managed artifact runtime is unavailable on Windows, report that limitation and use the installed Word application's native authoring and PDF export capabilities where available. Do not claim a different renderer was tested.

## Render mathematical notation

- In a DOCX, prefer editable native Office Math (OMML). LaTeX is an input format, not proof of rendering: convert it into Word's professional equation representation. Do not leave dollar delimiters, commands such as `\frac`, or ASCII substitutes such as `Gap_m` and `100 * (...)` visible as the finished equation.
- Use actual fraction, subscript, superscript, summation, and delimiter structures where the formula needs them. Preserve the original variables, operators, denominators, units, and scientific meaning.
- On Windows, Word's `OMaths.Add` and `OMath.BuildUp` can convert tested UnicodeMath input into native professional equations. Check the saved OMML rather than assuming BuildUp parsed every token correctly. Word's equation input mode affects LaTeX parsing; never assume arbitrary LaTeX will be understood by a UnicodeMath path.
- If automatic conversion leaves literal slashes or quotes, author explicit OMML fractions and scripts and test them in Word. Inspect Word's OMath function structures too: in legacy compatibility mode, `WordOpenXML` may wrap equation XML in an encoded `equationxml` attribute instead of exposing direct math elements.
- Keep long expressions within the actual column width. Use separate equation paragraphs when inline math becomes crowded. Replace exact line heights with automatic or sufficient minimum spacing in affected paragraphs so fractions and scripts are not clipped.
- If an equation cannot be converted reliably, state the problem. Use an image fallback only when compatible with the user's editability requirements, and identify it as an image.
- Flag scientific ambiguities separately; a formatting repair does not authorize changing a metric, adding a zero-denominator convention, or claiming a result has been validated.

## Verify the saved result

1. Reopen the saved DOCX in Word or the supported document renderer. Check that it opens without a repair prompt and that formulas are native equation objects when promised.
2. Inspect OMML for the expected fractions and scripts; check for leftover raw math markup in the affected text.
3. Render the final DOCX to PDF/page images through the supported workflow. Inspect every page, then inspect each affected equation at readable magnification. Check grouping, glyphs, fraction bars, subscripts, clipping, column fit, and pagination.
4. Confirm unaffected text, figures, tables, and section geometry were preserved. Keep QA artifacts separate from the delivered document.
5. Report the final document, checks actually performed, and remaining limitations. Never label XML-only inspection as visual verification.

## Primary references

- [Microsoft OMath API](https://learn.microsoft.com/en-us/office/vba/api/word.omath): native equation creation and BuildUp.
- [Microsoft equation input formats](https://support.microsoft.com/en-gb/word/linear-format-equations-using-unicodemath-and-latex-in-word): UnicodeMath versus LaTeX.
- [Microsoft OfficeMath format](https://devblogs.microsoft.com/math-in-office/officemath/): native structured mathematical notation.
