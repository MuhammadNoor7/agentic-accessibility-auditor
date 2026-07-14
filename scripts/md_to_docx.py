"""Convert Markdown (.md) to a formatted Word document (.docx).

Usage:
  python scripts/md_to_docx.py docs/progress/Supplementary_Progress_Report_v1.0.md
  python scripts/md_to_docx.py input.md -o output.docx
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.shared import Inches, Pt


IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")


def _add_formatted_run(paragraph, text: str) -> None:
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)")
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            paragraph.add_run(text[pos : match.start()])
        token = match.group(0)
        if token.startswith("**"):
            run = paragraph.add_run(token[2:-2])
            run.bold = True
        elif token.startswith("`"):
            run = paragraph.add_run(token[1:-1])
            run.font.name = "Consolas"
        else:
            run = paragraph.add_run(token[1:-1])
            run.italic = True
        pos = match.end()
    if pos < len(text):
        paragraph.add_run(text[pos:])


def _parse_table_row(line: str) -> list[str]:
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return cells


def _is_table_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|?[\s:\-|]+\|?", line.strip()))


def md_to_docx(md_path: Path, docx_path: Path) -> Path:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    md_dir = md_path.parent
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue
        if stripped == "---":
            i += 1
            continue
        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            text = stripped[level:].strip()
            doc.add_heading(text, level=min(level, 4))
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and _is_table_separator(lines[i + 1]):
            headers = _parse_table_row(stripped)
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_parse_table_row(lines[i]))
                i += 1
            table = doc.add_table(rows=1 + len(rows), cols=len(headers))
            table.style = "Table Grid"
            for col, header in enumerate(headers):
                table.rows[0].cells[col].text = header
            for row_idx, row in enumerate(rows, start=1):
                for col, cell in enumerate(row):
                    if col < len(table.rows[row_idx].cells):
                        table.rows[row_idx].cells[col].text = cell
            continue
        if stripped.startswith(">"):
            paragraph = doc.add_paragraph()
            _add_formatted_run(paragraph, stripped.lstrip("> ").strip())
            i += 1
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            paragraph = doc.add_paragraph(style="List Bullet")
            _add_formatted_run(paragraph, stripped[2:].strip())
            i += 1
            continue
        if stripped.startswith("```"):
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            paragraph = doc.add_paragraph()
            run = paragraph.add_run("\n".join(code_lines))
            run.font.name = "Consolas"
            run.font.size = Pt(9)
            i += 1
            continue
        image_match = IMAGE_RE.match(stripped)
        if image_match:
            alt, rel_path = image_match.group(1), image_match.group(2)
            image_path = (md_dir / rel_path).resolve()
            paragraph = doc.add_paragraph()
            if alt:
                caption = paragraph.add_run(alt)
                caption.italic = True
            if image_path.is_file():
                doc.add_picture(str(image_path), width=Inches(6.0))
            else:
                missing = doc.add_paragraph()
                missing.add_run(f"[Missing image: {rel_path}]")
            i += 1
            continue

        paragraph = doc.add_paragraph()
        _add_formatted_run(paragraph, stripped)
        i += 1

    docx_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(docx_path)
    return docx_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Markdown to DOCX")
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.input.with_suffix(".docx")
    result = md_to_docx(args.input.resolve(), output.resolve())
    print(f"Wrote {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
