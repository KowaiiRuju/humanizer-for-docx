#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_coherence_and_humanizer.py

Evaluates body prose coherence, sentence rhythm/burstiness, lexical cohesion,
post-CleverHumanizer token/symbol integrity, and dual AI-tell heuristics
(combining blader/humanizer v3.1.0 and the-humanizer v2.4 rules).
"""

import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
import numpy as np

# Banned AI vocabulary and cliches from blader/humanizer v3.1.0 and the-humanizer v2.4
BANNED_AI_PATTERNS = [
    (r'\bdelve\b', "banned AI verb 'delve'"),
    (r'\btapestry\b', "banned AI metaphor 'tapestry'"),
    (r'\btestament to\b', "banned AI idiom 'testament to'"),
    (r'\bin the ever[- ]evolving landscape\b', "banned AI cliche 'in the ever-evolving landscape'"),
    (r'\bnot only\b.*?\bbut also\b', "banned syntactic formula 'not only ... but also'"),
    (r'\blet that sink in\b', "banned dramatic closer 'let that sink in'"),
    (r'\bwhat if I told you\b', "banned conversational hook 'what if I told you'"),
    (r'\bhere[\'’]s what nobody tells you\b', "banned sensational opener 'here\'s what nobody tells you'"),
    (r'\bmultifaceted\b', "banned inflated adjective 'multifaceted'"),
    (r'\boverarching\b', "banned vague transition 'overarching'"),
    (r'\bunderscores\b', "banned AI verb 'underscores'"),
    (r'\bpivotal\b', "banned inflated adjective 'pivotal'"),
    (r'\brealm\b', "banned inflated noun 'realm'"),
    (r'\belevate\b', "banned marketing verb 'elevate'"),
]

# Common English stopwords to ignore when measuring lexical content-word overlap
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'aren\'t',
    'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can',
    'can\'t', 'cannot', 'could', 'did', 'do', 'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'has', 'have', 'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his',
    'how', 'i', 'if', 'in', 'into', 'is', 'it', 'its', 'itself', 'let\'s', 'me', 'more', 'most', 'my', 'myself',
    'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves',
    'out', 'over', 'own', 'same', 'she', 'should', 'so', 'some', 'such', 'than', 'that', 'the', 'their',
    'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to', 'too',
    'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where', 'which', 'while', 'who',
    'whom', 'why', 'with', 'won\'t', 'would', 'you', 'your', 'yours', 'yourself', 'yourselves'
}

# Discourse transition markers signaling explicit logical connection between sentences
TRANSITION_MARKERS = {
    'however', 'moreover', 'furthermore', 'therefore', 'consequently', 'specifically', 'additionally',
    'thus', 'hence', 'similarly', 'conversely', 'meanwhile', 'subsequently', 'further', 'overall',
    'instead', 'nevertheless', 'nonetheless', 'accordingly', 'importantly', 'notably', 'first', 'second',
    'third', 'finally', 'under', 'in contrast', 'in addition', 'for example', 'for instance', 'in particular'
}


def extract_paragraphs(docx_path: str):
    """Extracts raw text paragraphs from the main Word document XML."""
    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"DOCX file not found: {docx_path}")

    with zipfile.ZipFile(docx_path, 'r') as z:
        if 'word/document.xml' not in z.namelist():
            raise ValueError(f"Invalid DOCX: 'word/document.xml' missing in {docx_path}")
        xml_data = z.read('word/document.xml')

    root = ET.fromstring(xml_data)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs = []
    for p in root.findall('.//w:p', ns):
        text = ''.join(p.itertext()).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def filter_body_paragraphs(paragraphs):
    """Separates body text paragraphs from reference list items and headings."""
    body = []
    for p in paragraphs:
        # Ignore reference list items ([1] ...), section headers, and short captions
        if re.match(r'^\[\d+\]', p):
            continue
        if re.match(r'^(?:[I|V|X]+\.|\d+\.)\s+', p) and len(p.split()) < 12:
            continue
        if p.startswith('Figure ') and len(p.split()) < 20:
            continue
        if len(p.split()) >= 10:
            body.append(p)
    return body


def test_coherence_and_humanizer(docx_path: str, burstiness_min: float = 3.5, cohesion_min: float = 0.65,
                                  max_em_dashes: int = 40, technical_terms: list = None):
    if technical_terms is None:
        technical_terms = [
            'MobileNetV3-Large', 'GLCM', 'LBP', 'HOG', 'HSV', 'SVM', 'XGBoost',
            'Macro F1', 'Protocol A', 'Protocol B'
        ]

    print("=" * 70)
    print("COHERENCE, BURSTINESS & DUAL HUMANIZER VERIFICATION")
    print(f"Target Document: {docx_path}")
    print("=" * 70)

    paragraphs = extract_paragraphs(docx_path)
    body_paragraphs = filter_body_paragraphs(paragraphs)
    full_text = ' '.join(body_paragraphs)

    failures = []
    warnings = []

    # 1. Burstiness (Sentence-Length Standard Deviation)
    all_sentences = []
    for p in body_paragraphs:
        s_list = [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', p) if len(s.strip()) > 3]
        all_sentences.extend(s_list)

    sentence_lengths = [len(s.split()) for s in all_sentences if len(s.split()) >= 3]
    if not sentence_lengths:
        failures.append("No valid sentences parsed from body paragraphs.")
        sd_len = 0.0
        mean_len = 0.0
    else:
        sd_len = float(np.std(sentence_lengths))
        mean_len = float(np.mean(sentence_lengths))

    print(f"\n[1] Sentence Burstiness & Rhythm:")
    print(f"    - Total Sentences: {len(sentence_lengths)}")
    print(f"    - Mean Sentence Length: {mean_len:.2f} words")
    print(f"    - Sentence Length SD (Burstiness): {sd_len:.2f} words (Minimum required: {burstiness_min})")

    if sd_len < burstiness_min:
        failures.append(f"Sentence burstiness SD ({sd_len:.2f}) is below threshold ({burstiness_min}). Rhythm is too uniform.")

    # 2. Adjacent Sentence Lexical & Transition Cohesion
    total_transitions = 0
    cohesive_transitions = 0

    for p in body_paragraphs:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', p) if len(s.strip()) > 3]
        if len(sentences) < 2:
            continue
        for i in range(len(sentences) - 1):
            s1 = sentences[i].lower()
            s2 = sentences[i + 1].lower()
            w1 = set(re.findall(r'\b[a-z]{3,}\b', s1)) - STOPWORDS
            w2 = set(re.findall(r'\b[a-z]{3,}\b', s2)) - STOPWORDS
            overlap = w1 & w2
            has_marker = any(marker in s2 for marker in TRANSITION_MARKERS)
            total_transitions += 1
            if len(overlap) >= 1 or has_marker:
                cohesive_transitions += 1

    cohesion_ratio = (cohesive_transitions / total_transitions) if total_transitions > 0 else 0.0
    print(f"\n[2] Paragraph Flow & Cohesion:")
    print(f"    - Total Adjacent Transitions Evaluated: {total_transitions}")
    print(f"    - Cohesive Transitions (Content Overlap or Marker): {cohesive_transitions} ({cohesion_ratio * 100:.1f}%)")
    print(f"    - Minimum Required Ratio: {cohesion_min * 100:.1f}%")

    if cohesion_ratio < cohesion_min:
        failures.append(f"Lexical cohesion ratio ({cohesion_ratio:.2f}) is below requirement ({cohesion_min}).")

    # 3. Post-CleverHumanizer Token & Terminology Integrity
    print(f"\n[3] Post-CleverHumanizer Token & Terminology Integrity:")
    spaced_dot_issues = re.findall(r'\b(?:skimage|cv2|scipy|torch|np)\s+\.\s*[a-zA-Z_]\w*', full_text)
    if spaced_dot_issues:
        failures.append(f"Spaced-dot code corruption detected: {spaced_dot_issues}")
    else:
        print("    - Spaced-dot code identifier check: PASSED (no broken module names)")

    broken_number_commas = re.findall(r'\b(?:1,\s+704|2,\s+000|\d{1,3},\s+\d{3}-(?:[Dd]|dimensional))\b', full_text)
    if broken_number_commas:
        failures.append(f"Broken numeric commas detected (e.g. 1, 704): {broken_number_commas}")
    else:
        print("    - Broken thousands-separator commas: PASSED (no '1, 704' or '2, 000' artifacts)")

    missing_terms = []
    for term in technical_terms:
        # Flexible matching for terms like 'Macro F1' vs 'macro-F1'
        if term == 'Macro F1':
            pattern = r'\bmacro[-\s]f1\b'
        else:
            pattern = re.escape(term)
        if not re.search(pattern, full_text, re.IGNORECASE):
            missing_terms.append(term)

    if missing_terms:
        failures.append(f"Required technical terms missing or corrupted: {missing_terms}")
    else:
        print(f"    - Core technical terms check ({len(technical_terms)} terms): PASSED")

    # 4. Dual Humanizer AI-Tell Scanner
    print(f"\n[4] Dual Humanizer AI-Vocabulary & Pattern Scanner:")
    found_ai_tells = []
    for pattern, desc in BANNED_AI_PATTERNS:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            found_ai_tells.append(f"{desc} (count: {len(matches)})")

    if found_ai_tells:
        failures.append(f"Banned AI vocabulary/cliches detected: {found_ai_tells}")
    else:
        print("    - Banned high-frequency AI patterns: PASSED (zero occurrences)")

    # Em-dash check
    em_dash_count = full_text.count('—') + full_text.count('--')
    print(f"    - Em-dash count: {em_dash_count} (Limit: {max_em_dashes})")
    if em_dash_count > max_em_dashes:
        warnings.append(f"High em-dash frequency ({em_dash_count} > {max_em_dashes}). Consider diversifying punctuation.")

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
        print("RESULT: PASSED ALL CHECKS")
        print("=" * 70)
        return True


def main():
    parser = argparse.ArgumentParser(description="Test prose coherence, burstiness, and AI-tell compliance.")
    parser.add_argument('--docx', default=r'output\Local_Flora_Concise_Smartphone.docx', help='Target DOCX file')
    parser.add_argument('--burstiness-min', type=float, default=3.5, help='Minimum sentence-length std dev (default: 3.5)')
    parser.add_argument('--cohesion-min', type=float, default=0.65, help='Minimum adjacent-sentence cohesion ratio (default: 0.65)')
    parser.add_argument('--max-em-dashes', type=int, default=40, help='Maximum permitted em-dashes (default: 40)')
    parser.add_argument('--terms', nargs='*', default=None, help='List of core technical terms to verify')
    args = parser.parse_args()

    success = test_coherence_and_humanizer(
        args.docx,
        burstiness_min=args.burstiness_min,
        cohesion_min=args.cohesion_min,
        max_em_dashes=args.max_em_dashes,
        technical_terms=args.terms
    )
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
