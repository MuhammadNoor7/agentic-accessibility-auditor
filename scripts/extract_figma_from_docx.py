"""Extract embedded images from formatted SRS/SDS DOCX into docs/assets/figma/."""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


ROOT = Path(__file__).resolve().parents[1]
FIGMA_DIR = ROOT / "docs" / "assets" / "figma"

SRS_NAMES = [
    "figma-01-signup-login.png",
    "figma-02-forgot-verify-otp.png",
    "figma-03-reset-password-success.png",
    "figma-04-upload-progress-states.png",
    "figma-08-upload-files-matched.png",
    "figma-05-audit-complete-dashboard.png",
    "figma-06-dashboard-detail-report.png",
    "figma-07-generate-report-modal-pdf.png",
]


def _paragraph_has_image(paragraph: Paragraph) -> bool:
    return bool(paragraph._element.xpath(".//a:blip"))


def _image_rids_in_paragraph(paragraph: Paragraph) -> list[str]:
    rids: list[str] = []
    for blip in paragraph._element.xpath(".//a:blip"):
        rid = blip.get(qn("r:embed"))
        if rid:
            rids.append(rid)
    return rids


def extract_with_context(docx_path: Path) -> list[dict]:
    doc = Document(docx_path)
    items: list[dict] = []
    for el in doc.element.body:
        tag = el.tag.split("}")[-1]
        if tag != "p":
            continue
        p = Paragraph(el, doc)
        text = p.text.strip()
        if _paragraph_has_image(p):
            items.append({"kind": "image", "text": text, "rids": _image_rids_in_paragraph(p)})
        elif text:
            items.append({"kind": "text", "text": text})
    return items


def export_media(docx_path: Path, out_dir: Path, names: list[str] | None = None) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(docx_path) as zf:
        media = sorted(n for n in zf.namelist() if n.startswith("word/media/"))
        written: list[Path] = []
        for idx, media_name in enumerate(media):
            suffix = Path(media_name).suffix or ".png"
            if names and idx < len(names):
                target = out_dir / names[idx]
            else:
                target = out_dir / f"extracted-{idx + 1}{suffix}"
            target.write_bytes(zf.read(media_name))
            written.append(target)
        return written


def main() -> None:
    srs_fmt = ROOT / "srs" / "SRS_Agentic_Accessibility_Auditor_v2.0_formatted.docx"
    sds_fmt = ROOT / "sds" / "SDS_Agentic_Accessibility_Auditor_v2.0_formatted.docx"

    print("SRS image contexts:")
    for item in extract_with_context(srs_fmt):
        if item["kind"] == "image":
            print(" -", item["text"][:80] or "(no caption)")

    srs_written = export_media(srs_fmt, FIGMA_DIR, SRS_NAMES)
    print("\nExported SRS images:")
    for p in srs_written:
        print(" ", p.name, p.stat().st_size)

    # SDS images should match subset already exported; only copy if missing
    print("\nSDS image contexts:")
    for item in extract_with_context(sds_fmt):
        if item["kind"] == "image":
            print(" -", item["text"][:80] or "(no caption)")

    sds_media_count = len([n for n in ZipFile(sds_fmt).namelist() if n.startswith("word/media/")])
    print("SDS embedded media count:", sds_media_count)


if __name__ == "__main__":
    main()
