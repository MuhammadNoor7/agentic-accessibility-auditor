"""Compare formatted DOCX vs markdown and list formatted-only content."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


def extract_items(path: Path) -> list[dict]:
    doc = Document(path)
    items: list[dict] = []
    for el in doc.element.body:
        tag = el.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(el, doc)
            text = p.text.strip()
            if text:
                items.append(
                    {
                        "type": "p",
                        "style": p.style.name if p.style else "",
                        "text": text,
                    }
                )
        elif tag == "tbl":
            t = Table(el, doc)
            rows = [[c.text.strip() for c in row.cells] for row in t.rows]
            items.append({"type": "table", "rows": rows})
    return items


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()


def media_files(path: Path) -> list[str]:
    with ZipFile(path) as zf:
        return sorted(n for n in zf.namelist() if n.startswith("word/media/"))


def compare(kind: str) -> None:
    base = Path(kind)
    fmt = base / f"{kind.upper()}_Agentic_Accessibility_Auditor_v2.0_formatted.docx"
    md_path = base / f"{kind.upper()}_Agentic_Accessibility_Auditor_v2.0.md"
    md_text = md_path.read_text(encoding="utf-8")
    md_norm = normalize(md_text)

    items = extract_items(fmt)
    only_fmt: list[str] = []
    for item in items:
        if item["type"] != "p":
            continue
        text = item["text"]
        if len(text) < 25:
            continue
        n = normalize(text)
        if n and n not in md_norm:
            # allow partial heading matches
            words = n.split()
            if len(words) >= 4:
                chunk = " ".join(words[:8])
                if chunk not in md_norm:
                    only_fmt.append(text)

    print(f"=== {kind.upper()} ===")
    print("formatted items:", len(items))
    print("embedded media:", media_files(fmt))
    print("formatted-only paragraphs:", len(only_fmt))
    for text in only_fmt[:30]:
        print("---")
        print(text[:500])
    print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for k in ("srs", "sds"):
        compare(k)
