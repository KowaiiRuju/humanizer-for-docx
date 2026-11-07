# -*- coding: utf-8 -*-
"""
Non-destructive VML Diagram & Embedded Image Updater for Microsoft Word DOCX files.
Updates Figure 1..6 VML bounding boxes and embedded PNG images without altering a
single character or paragraph format in the document XML.
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile


def update_diagrams(docx_path: str, diag_dir: str):
    docx_path = os.path.abspath(docx_path)
    diag_dir = os.path.abspath(diag_dir)

    manifest_path = os.path.join(diag_dir, 'manifest.json')
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Diagram manifest not found at: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    if not os.path.exists(docx_path):
        raise FileNotFoundError(f"Target DOCX not found at: {docx_path}")

    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.docx')
    os.close(tmp_fd)

    try:
        with zipfile.ZipFile(docx_path, 'r') as zin:
            doc_xml = zin.read('word/document.xml').decode('utf-8')

            for i, item in enumerate(manifest):
                fig_num = i + 1
                width_pt = 243.25
                height_pt = round(width_pt * item['height'] / 1000.0, 2)

                # Update VML <v:shape id="Figure X" ... style="width:...pt;height:...pt;...">
                vml_pattern = (
                    rf'(<v:shape id="Figure {fig_num}"[^>]*style="width:)([0-9.]+pt)(;height:)([0-9.]+pt)([^"]*"[^>]*>)'
                )
                doc_xml, count = re.subn(
                    vml_pattern,
                    rf'\g<1>{width_pt}pt\g<3>{height_pt}pt\g<5>',
                    doc_xml,
                )
                assert count == 1, f"Expected 1 VML shape match for Figure {fig_num}, got {count}"

            with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for info in zin.infolist():
                    if info.filename == 'word/document.xml':
                        zout.writestr(info, doc_xml.encode('utf-8'))
                    elif re.match(r'^word/media/image[1-6]\.png$', info.filename):
                        idx = int(re.findall(r'\d+', info.filename)[0])
                        img_path = os.path.join(diag_dir, f'figure_{idx}.png')
                        if os.path.exists(img_path):
                            with open(img_path, 'rb') as imgf:
                                img_bytes = imgf.read()
                            zout.writestr(info, img_bytes)
                        else:
                            zout.writestr(info, zin.read(info.filename))
                    else:
                        zout.writestr(info, zin.read(info.filename))

        shutil.move(tmp_path, docx_path)
        print(f"Successfully updated ONLY the {len(manifest)} diagrams in: {docx_path}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def main():
    parser = argparse.ArgumentParser(description="Update VML diagram bounding boxes and image assets in DOCX.")
    parser.add_argument('--docx', default=r'output\Local_Flora_Concise_Smartphone.docx', help='Path to target DOCX file')
    parser.add_argument('--diagrams-dir', default=r'tmp\chapters\revised-diagrams', help='Directory containing manifest.json and figure_*.png')
    args = parser.parse_args()

    update_diagrams(args.docx, args.diagrams_dir)


if __name__ == '__main__':
    main()
