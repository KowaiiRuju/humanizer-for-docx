#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_docx_integrity.py

Validates structural, XML, typography, visual and mathematical integrity of DOCX manuscripts:
- Required sections (Background, Literature Review, Methodology, References)
- Native OMML equation nodes (<m:oMath>) and absence of raw LaTeX code runs
- Diagram and figure assets (VML <v:shape> or DrawingML <w:drawing>, media PNGs)
- Tables and column layout configurations (<w:cols>)
- Word and page budget compliance (docProps/app.xml Pages and word count)
Configurable via CLI arguments to support varying university/journal formatting guidelines.
"""

import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET


def test_docx_integrity(docx_path: str, expected_figures: int = 6,
                        expected_columns: int = 2, min_pages: int = 4,
                        max_pages: int = 7, min_words: int = 2500,
                        max_words: int = 6000, required_sections: list = None):
    if required_sections is None:
        required_sections = [
            ("I. Background / Introduction", [r'^I\.\s*(?:Background|Introduction)']),
            ("II. Literature Review", [r'^II\.\s*(?:Literature Review|Related Literature|Related Work)']),
            ("III. Methodology", [r'^III\.\s*(?:Methodology|Conceptual Framework and Methodology|Methods)']),
            ("IV. References", [r'^(?:IV\.|\d+\.)?\s*References\b', r'^\[1\]'])
        ]

    print("=" * 70)
    print("DOCX STRUCTURAL & FORMATTING INTEGRITY AUDIT")
    print(f"Target Document: {docx_path}")
    print("=" * 70)

    if not os.path.exists(docx_path):
        print(f"ERROR: Target file not found: {docx_path}")
        return False

    with zipfile.ZipFile(docx_path, 'r') as z:
        namelist = z.namelist()
        if 'word/document.xml' not in namelist:
            print(f"ERROR: Invalid DOCX archive; missing word/document.xml")
            return False

        doc_xml = z.read('word/document.xml')
        app_xml = z.read('docProps/app.xml') if 'docProps/app.xml' in namelist else None
        rels_xml = z.read('word/_rels/document.xml.rels') if 'word/_rels/document.xml.rels' in namelist else None

    root = ET.fromstring(doc_xml)
    ns = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
        'v': 'urn:schemas-microsoft-com:vml',
        'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }

    failures = []
    warnings = []

    # 1. Section Headings Check
    print("\n[1] Section Headings Audit:")
    paragraphs = [''.join(p.itertext()).strip() for p in root.findall('.//w:p', ns)]
    
    for label, patterns in required_sections:
        found = False
        for p in paragraphs:
            for pat in patterns:
                if re.search(pat, p, re.IGNORECASE):
                    found = True
                    break
            if found:
                break
        if found:
            print(f"    - Section '{label}': FOUND")
        else:
            failures.append(f"Required section '{label}' was not detected in document headings.")

    # 2. Native OMML Equations & LaTeX Absence Check
    print("\n[2] Native OMML Equations & Raw Math Check:")
    math_nodes = root.findall('.//m:oMath', ns) + root.findall('.//m:oMathPara', ns)
    print(f"    - Native OMML Equation Nodes (<m:oMath>): {len(math_nodes)} detected")
    if len(math_nodes) == 0:
        failures.append("No native Word equations (<m:oMath>) found in document.")
    else:
        print("    - Native Word equation structure: PASSED")

    # Check for raw LaTeX syntax leak in plain text
    full_text = ' '.join(paragraphs)
    raw_latex = re.findall(r'\\(?:frac|sum|text\{|partial|alpha|beta|sigma|times\b)', full_text)
    if raw_latex:
        failures.append(f"Unrendered raw LaTeX commands detected in text runs: {set(raw_latex)}")
    else:
        print("    - Raw LaTeX syntax leak check (\\frac, \\sum, \\text{}): PASSED (zero leaks)")

    # 3. Figures, Images and VML / DrawingML Shapes
    print("\n[3] Figures, Diagrams & Shape Containers:")
    figure_captions = [p for p in paragraphs if re.match(r'^Figure\s+\d+[:.]', p)]
    print(f"    - Figure Captions Found: {len(figure_captions)} (Expected: {expected_figures})")
    for cap in figure_captions:
        print(f"        * {cap[:75]}...")

    if len(figure_captions) < expected_figures:
        failures.append(f"Found {len(figure_captions)} figure captions, expected at least {expected_figures}.")

    # Embedded images in archive
    media_images = [n for n in namelist if n.startswith('word/media/')]
    print(f"    - Embedded Media Assets in word/media/: {len(media_images)}")
    if len(media_images) < expected_figures:
        failures.append(f"Embedded image count ({len(media_images)}) is less than expected ({expected_figures}).")

    # Shape nodes (Word saves diagrams as VML <v:shape> or DrawingML <wp:inline>/<wp:anchor>)
    vml_shapes = root.findall('.//v:shape', ns)
    drawings = root.findall('.//wp:inline', ns) + root.findall('.//wp:anchor', ns)
    total_shapes = len(vml_shapes) + len(drawings)
    print(f"    - Diagram Container Nodes: {len(vml_shapes)} VML shapes, {len(drawings)} DrawingML nodes (Total: {total_shapes})")
    if total_shapes < expected_figures:
        failures.append(f"Total diagram shape containers ({total_shapes}) is less than expected ({expected_figures}).")
    else:
        print("    - Figure container and image asset verification: PASSED")

    # 4. Tables and Multi-Column Layout
    print("\n[4] Tables & Column Layout Configuration:")
    tables = root.findall('.//w:tbl', ns)
    print(f"    - Tables detected in document: {len(tables)}")
    if len(tables) < 1:
        failures.append("No tables found in document; expected species or experiment tables.")

    # Check column layout in section properties
    cols = root.findall('.//w:cols', ns)
    col_nums = []
    for c in cols:
        num = c.attrib.get(f'{{{ns["w"]}}}num', '1')
        col_nums.append(int(num))

    print(f"    - Column sections detected: {col_nums} (Expected: {expected_columns}-column)")
    if expected_columns > 1 and expected_columns not in col_nums:
        failures.append(f"Configured {expected_columns}-column layout (<w:cols w:num=\"{expected_columns}\">) was not found.")
    else:
        print(f"    - Layout format check ({expected_columns}-column): PASSED")

    # 5. Page and Word Budget Compliance
    print("\n[5] Page and Word Count Budget:")
    page_count = None
    word_count = None

    if app_xml:
        app_root = ET.fromstring(app_xml)
        for elem in app_root.iter():
            tag = elem.tag.split('}')[-1]
            if tag == 'Pages' and elem.text:
                try:
                    page_count = int(elem.text)
                except ValueError:
                    pass
            elif tag == 'Words' and elem.text:
                try:
                    word_count = int(elem.text)
                except ValueError:
                    pass

    # Fallback word count from text runs if app.xml is empty
    computed_words = sum(len(p.split()) for p in paragraphs if not p.startswith('[') and not p.startswith('IV.'))
    if word_count is None:
        word_count = computed_words

    print(f"    - Document Words (app.xml / computed): {word_count} (Target range: {min_words}–{max_words})")
    if page_count is not None:
        print(f"    - Document Pages (app.xml metadata): {page_count} (Target range: {min_pages}–{max_pages})")
        if page_count < min_pages or page_count > max_pages:
            warnings.append(f"Page count ({page_count}) is outside target concise range ({min_pages}–{max_pages} pages).")
    else:
        print(f"    - Page count metadata: not recorded in app.xml (use scripts/render_docx_qa.ps1 for visual page raster)")

    if word_count < min_words:
        failures.append(f"Word count ({word_count}) is below target concise minimum ({min_words}).")
    elif word_count > max_words:
        warnings.append(f"Word count ({word_count}) exceeds standard concise target ({max_words}).")
    else:
        print("    - Concise document budget: PASSED")

    # Final Summary
    print("\n" + "=" * 70)
    if warnings:
        print("WARNINGS:")
        for w in warnings:
            print(f"  [!] {w}")
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  [X] {f}")
        print("=" * 70)
        print("RESULT: FAILED")
        return False
    else:
        print("RESULT: PASSED ALL STRUCTURAL AND INTEGRITY CHECKS")
        print("=" * 70)
        return True


def main():
    parser = argparse.ArgumentParser(description="Audit DOCX layout, math, tables, figures, and page budget.")
    parser.add_argument('--docx', default=r'output\Local_Flora_Concise_Smartphone.docx', help='Path to target DOCX')
    parser.add_argument('--expected-figures', type=int, default=6, help='Number of required figures (default: 6)')
    parser.add_argument('--columns', type=int, default=2, help='Expected column layout (default: 2)')
    parser.add_argument('--min-pages', type=int, default=4, help='Minimum page count (default: 4)')
    parser.add_argument('--max-pages', type=int, default=7, help='Maximum page count (default: 7)')
    parser.add_argument('--min-words', type=int, default=2500, help='Minimum body words (default: 2500)')
    parser.add_argument('--max-words', type=int, default=6000, help='Maximum body words (default: 6000)')
    args = parser.parse_args()

    success = test_docx_integrity(
        args.docx,
        expected_figures=args.expected_figures,
        expected_columns=args.columns,
        min_pages=args.min_pages,
        max_pages=args.max_pages,
        min_words=args.min_words,
        max_words=args.max_words
    )
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
