# -*- coding: utf-8 -*-
"""从渲染后的 PDF 反查各级标题所在页码，供 build_design_docx.py 生成目录。

用法：
    python tools/toc_pages.py <design.pdf> <out.json> [headings.json]
"""
import json
import os
import re
import sys

import fitz

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(s):
    return re.sub(r"\s+", "", s)


def main():
    pdf_path = sys.argv[1]
    out_path = sys.argv[2]
    head_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(BASE, "tools", "_headings.json")

    with open(head_path, encoding="utf-8") as f:
        headings = json.load(f)

    doc = fitz.open(pdf_path)
    # 收集每页中字号 >= 13 的行文本（正文 12pt、目录条目 <=11.5pt，均低于阈值）
    page_lines = []
    for page in doc:
        lines = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                spans = [s for s in line["spans"] if s["text"].strip()]
                if not spans:
                    continue
                if max(s["size"] for s in spans) >= 13.0:
                    lines.append((max(s["size"] for s in spans), "".join(s["text"] for s in spans)))
        page_lines.append(lines)

    pages = {}
    missing = []
    for h in headings:
        target = norm((h["num"] + " " + h["title"]) if h["num"] else h["title"])
        found = None
        for idx, lines in enumerate(page_lines):
            for _size, text in lines:
                nt = norm(text)
                if nt and nt.startswith(target):
                    found = idx + 1
                    break
            if found:
                break
        if found:
            pages[h["num"] or h["title"]] = found
        else:
            missing.append(h["num"] or h["title"])

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=1)

    print("pages:", len(pages), "| missing:", missing[:8], "| total pdf pages:", doc.page_count)


if __name__ == "__main__":
    main()
