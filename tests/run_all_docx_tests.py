#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all_docx_tests.py

Unified test harness for DOCX manuscripts. Runs the complete automated suite:
1. test_coherence_and_humanizer (burstiness, lexical cohesion, token & term integrity, AI-tells)
2. test_citation_density (reference count, bijection, single-citation discipline, no range clusters)
3. test_docx_integrity (headings, native OMML equations, figures/VML shapes, tables, columns, page budget)

Outputs an executive pass/fail table and optionally exports a structured Markdown or JSON report.
"""

import argparse
import json
import os
import subprocess
import sys
import time


def run_test(cmd: list):
    start = time.time()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    duration = time.time() - start
    return res.returncode == 0, res.stdout, duration


def main():
    parser = argparse.ArgumentParser(description="Run complete DOCX integrity, coherence, and citation test suite.")
    parser.add_argument('--docx', default=r'output\Local_Flora_Concise_Smartphone.docx', help='Path to target DOCX file')
    parser.add_argument('--report-out', default=None, help='Optional output path for Markdown or JSON report')
    parser.add_argument('--expected-refs', type=int, default=25, help='Minimum expected reference count')
    parser.add_argument('--columns', type=int, default=2, help='Expected column layout (1 or 2)')
    parser.add_argument('--burstiness-min', type=float, default=3.5, help='Minimum sentence burstiness SD')
    parser.add_argument('--cohesion-min', type=float, default=0.65, help='Minimum lexical cohesion ratio')
    parser.add_argument('--expected-figures', type=int, default=6, help='Expected figure count')
    args = parser.parse_args()

    docx_path = os.path.abspath(args.docx)
    tests_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 80)
    print("STARTING COMPLETE DOCX & COHERENCE TEST SUITE")
    print(f"Target Manuscript: {docx_path}")
    print("=" * 80)

    test_configs = [
        (
            "Coherence & Dual Humanizer Heuristics",
            [
                sys.executable,
                os.path.join(tests_dir, "test_coherence_and_humanizer.py"),
                "--docx", docx_path,
                "--burstiness-min", str(args.burstiness_min),
                "--cohesion-min", str(args.cohesion_min)
            ]
        ),
        (
            "Citation Density & Reference Bijection",
            [
                sys.executable,
                os.path.join(tests_dir, "test_citation_density.py"),
                "--docx", docx_path,
                "--expected-refs", str(args.expected_refs)
            ]
        ),
        (
            "DOCX XML Structure & OMML Equations",
            [
                sys.executable,
                os.path.join(tests_dir, "test_docx_integrity.py"),
                "--docx", docx_path,
                "--columns", str(args.columns),
                "--expected-figures", str(args.expected_figures)
            ]
        )
    ]

    results = []
    all_passed = True

    for name, cmd in test_configs:
        print(f"\n---> Executing: {name} ...")
        passed, output, duration = run_test(cmd)
        print(output.strip())
        results.append({
            "name": name,
            "passed": passed,
            "duration_sec": round(duration, 2),
            "output": output
        })
        if not passed:
            all_passed = False

    # Summary Table
    print("\n" + "=" * 80)
    print(f"{'TEST MODULE':<45} | {'STATUS':<10} | {'DURATION'}")
    print("-" * 80)
    for r in results:
        status_str = "PASSED" if r["passed"] else "FAILED"
        print(f"{r['name']:<45} | {status_str:<10} | {r['duration_sec']}s")
    print("=" * 80)

    overall_status = "ALL TESTS PASSED" if all_passed else "TEST SUITE FAILED"
    print(f"OVERALL RESULT: {overall_status} (Exit Code: {0 if all_passed else 1})")
    print("=" * 80)

    # Optional Report Export
    if args.report_out:
        out_path = os.path.abspath(args.report_out)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if out_path.endswith('.json'):
            report_data = {
                "docx": docx_path,
                "overall_passed": all_passed,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "results": results
            }
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            print(f"Report exported to JSON: {out_path}")
        else:
            # Markdown report
            lines = [
                f"# Automated DOCX Test Suite Report",
                f"",
                f"- **Target File**: `{docx_path}`",
                f"- **Overall Result**: **{'PASSED' if all_passed else 'FAILED'}**",
                f"- **Execution Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
                f"",
                f"## Summary Table",
                f"",
                f"| Test Module | Status | Duration |",
                f"| :--- | :---: | :---: |"
            ]
            for r in results:
                status_icon = "PASS" if r["passed"] else "FAIL"
                lines.append(f"| {r['name']} | {status_icon} | {r['duration_sec']}s |")
            lines.append("")
            lines.append("## Detailed Module Logs")
            for r in results:
                lines.append(f"### {r['name']}")
                lines.append("```text")
                lines.append(r['output'].strip())
                lines.append("```")
                lines.append("")
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            print(f"Report exported to Markdown: {out_path}")

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
