#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_citation_density.py

Validates academic citation discipline, Section IV reference integrity,
body-to-reference bijection, absence of lazy range-clustering ([1]-[6]),
and reports per-sentence citation density distribution and first-appearance order.
Configurable via CLI flags to support diverse journal and thesis formatting guidelines.
"""

import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET


def extract_document_paragraphs(docx_path: str):
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Target DOCX file not found: {docx_path}")

    with zipfile.ZipFile(docx_path, 'r') as z:
        if 'word/document.xml' not in z.namelist():
            raise ValueError(f"Invalid DOCX structure: 'word/document.xml' missing in {docx_path}")
        xml_data = z.read('word/document.xml')

    root = ET.fromstring(xml_data)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs = []
    for p in root.findall('.//w:p', ns):
        text = ''.join(p.itertext()).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def parse_body_and_references(paragraphs):
    """
    Separates document into body paragraphs (Sections I..III) and
    Section IV References list.
    """
    body_paras = []
    ref_entries = []
    in_references_section = False

    for p in paragraphs:
        # Check if we crossed into Section IV / References heading
        if re.match(r'^(?:IV\.|\d+\.)\s*References\b', p, re.IGNORECASE) or p.strip().lower() == 'references':
            in_references_section = True
            continue

        ref_match = re.match(r'^\[(\d+)\]\s*(.*)', p)
        if ref_match:
            in_references_section = True
            ref_id = int(ref_match.group(1))
            ref_entries.append((ref_id, ref_match.group(2).strip(), p))
        elif in_references_section:
            # Check if paragraph is continuation of reference or new section
            if len(p.split()) > 3:
                # May be unnumbered reference or continuation
                pass
        else:
            body_paras.append(p)

    return body_paras, ref_entries


def test_citation_density(docx_path: str, min_expected_refs: int = 25,
                          max_citations_per_sentence: int = 4,
                          disallow_clusters: bool = True):
    print("=" * 70)
    print("CITATION DENSITY & REFERENCE BIJECTION VERIFICATION")
    print(f"Target Document: {docx_path}")
    print("=" * 70)

    paragraphs = extract_document_paragraphs(docx_path)
    body_paras, ref_entries = parse_body_and_references(paragraphs)

    failures = []
    warnings = []

    # 1. Total Reference Count in Section IV
    ref_ids = [r[0] for r in ref_entries]
    print(f"\n[1] Reference List Audit (Section IV):")
    print(f"    - Total References Parsed: {len(ref_ids)}")
    print(f"    - Reference Range: [{min(ref_ids) if ref_ids else 0}] .. [{max(ref_ids) if ref_ids else 0}]")
    print(f"    - Configured Minimum Target: {min_expected_refs}")

    if len(ref_ids) < min_expected_refs:
        failures.append(f"Parsed references count ({len(ref_ids)}) is below minimum requirement ({min_expected_refs}).")

    # Check for consecutive 1..N ordering in References
    expected_sequence = list(range(1, len(ref_ids) + 1))
    if ref_ids != expected_sequence:
        missing_in_list = set(expected_sequence) - set(ref_ids)
        failures.append(f"References list does not form a continuous sequence 1..N. Missing: {sorted(missing_in_list)}")
    else:
        print(f"    - References form continuous sequence [1]..[{len(ref_ids)}]: PASSED")

    # 2. Body Citations and Bijection Audit
    body_text = ' '.join(body_paras)
    body_citations_raw = re.findall(r'\[(\d+)\]', body_text)
    body_cited_ids = sorted(list(set(int(x) for x in body_citations_raw)))

    print(f"\n[2] Body Citation Bijection Audit:")
    print(f"    - Total Citation Instances in Body: {len(body_citations_raw)}")
    print(f"    - Unique Reference IDs Cited in Body: {len(body_cited_ids)}")

    # Check out-of-range citations
    max_ref_id = max(ref_ids) if ref_ids else 0
    out_of_range = [c for c in body_cited_ids if c > max_ref_id or c < 1]
    if out_of_range:
        failures.append(f"Out-of-range citations found in body text (exceeds max ref [{max_ref_id}]): {out_of_range}")
    else:
        print(f"    - Out-of-range citation check (no id > {max_ref_id}): PASSED")

    # Check uncited references (references in list never cited in text)
    uncited_refs = set(ref_ids) - set(body_cited_ids)
    if uncited_refs:
        failures.append(f"References listed in Section IV but NEVER cited in body text: {sorted(uncited_refs)}")
    else:
        print(f"    - Complete Bijection: All {len(ref_ids)} references are cited in body prose: PASSED")

    # 3. Citation Density per Sentence & Banned Clustering
    print(f"\n[3] Citation Density & Sentence Discipline:")

    # Check for banned range clusters: [1]-[6], [1]–[6], [1], [2], [3], [1-6]
    banned_range_clusters = re.findall(r'\[\d+\]\s*[-–—]\s*\[\d+\]|\[\d+[-–—]\d+\]', body_text)
    banned_comma_clusters = re.findall(r'\[\d+\]\s*,\s*\[\d+\]|\[\d+(?:,\s*\d+)+\]', body_text)

    if disallow_clusters and (banned_range_clusters or banned_comma_clusters):
        all_clusters = banned_range_clusters + banned_comma_clusters
        failures.append(f"Banned lazy citation clusters detected (must cite individually per statement): {all_clusters}")
    else:
        print("    - Banned citation range clusters ([1]-[6], [1], [2], etc.): PASSED (none found)")

    # Analyze sentence-level citation count
    all_sentences = []
    for p in body_paras:
        if len(p.split()) < 5 or p.startswith('Figure ') or p.startswith('Table '):
            continue
        s_list = [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', p) if len(s.strip()) > 3]
        all_sentences.extend(s_list)

    density_dist = {}
    over_limit_sentences = []

    for s in all_sentences:
        c_count = len(re.findall(r'\[\d+\]', s))
        density_dist[c_count] = density_dist.get(c_count, 0) + 1
        if c_count > max_citations_per_sentence:
            over_limit_sentences.append((s[:90] + '...', c_count))

    print(f"    - Total Sentences Evaluated: {len(all_sentences)}")
    print("    - Citation Distribution per Sentence:")
    for k in sorted(density_dist.keys()):
        print(f"        * {k} citations: {density_dist[k]} sentences ({density_dist[k]/len(all_sentences)*100:.1f}%)")

    if over_limit_sentences:
        failures.append(
            f"{len(over_limit_sentences)} sentence(s) exceed maximum permitted citations ({max_citations_per_sentence}): {over_limit_sentences[:3]}"
        )
    else:
        print(f"    - Max citations per sentence discipline (<= {max_citations_per_sentence}): PASSED")

    # 4. First-Appearance Sequence
    first_seen = {}
    order_list = []
    for m in re.finditer(r'\[(\d+)\]', body_text):
        cid = int(m.group(1))
        if cid not in first_seen:
            first_seen[cid] = len(order_list) + 1
            order_list.append(cid)

    print(f"\n[4] First-Appearance Citation Sequence:")
    print(f"    - First 10 cited in body: {order_list[:10]}")
    print(f"    - Total unique references introduced: {len(order_list)}")

    # Results Summary
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
        print("RESULT: PASSED ALL CITATION DISCIPLINE CHECKS")
        print("=" * 70)
        return True


def main():
    parser = argparse.ArgumentParser(description="Audit DOCX academic citation density and reference bijection.")
    parser.add_argument('--docx', default=r'output\Local_Flora_Concise_Smartphone.docx', help='Target DOCX file')
    parser.add_argument('--expected-refs', type=int, default=25, help='Minimum expected reference count (default: 25)')
    parser.add_argument('--max-citations-per-sentence', type=int, default=4, help='Max citations allowed per single sentence (default: 4)')
    parser.add_argument('--allow-clusters', action='store_true', help='Allow range clusters like [1]-[6]')
    args = parser.parse_args()

    success = test_citation_density(
        args.docx,
        min_expected_refs=args.expected_refs,
        max_citations_per_sentence=args.max_citations_per_sentence,
        disallow_clusters=not args.allow_clusters
    )
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
