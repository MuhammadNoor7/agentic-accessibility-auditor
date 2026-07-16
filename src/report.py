"""Stage 4 report generator: HTML/PDF exports from report.json (SRS §4.6, SDS §8)."""

from __future__ import annotations

import base64
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
SEVERITY_COLORS = {
    "Critical": "#dc2626",
    "High": "#f97316",
    "Medium": "#eab308",
    "Low": "#94a3b8",
}

ReportFormat = Literal["html", "pdf"]


def _resolve_existing_path(path_str: str, project_root: Path) -> Path | None:
    if not path_str:
        return None
    raw = Path(path_str)
    candidates = [raw]
    if not raw.is_absolute():
        normalized = path_str.replace("\\", "/").lstrip("/")
        candidates.extend(
            [
                project_root / path_str,
                project_root / normalized,
            ]
        )
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:
            continue
    return None


def _sort_violations(violations: list[dict]) -> list[dict]:
    return sorted(
        violations,
        key=lambda item: (
            SEVERITY_ORDER.get(item.get("severity", "Medium"), 2),
            item.get("rule_id", ""),
            item.get("component_id", ""),
        ),
    )


def _read_xml_snippet(xml_path: Path | None, *, limit: int = 2000) -> str:
    if xml_path is None:
        return ""
    try:
        text = xml_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if len(text) <= limit:
        return text
    return f"{text[:limit]}\n…"


def _image_to_data_uri(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }.get(suffix, "image/png")
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _annotate_screenshot(image_path: Path, violations: list[dict]) -> str:
    from PIL import Image, ImageDraw

    with Image.open(image_path) as image:
        annotated = image.convert("RGBA")
        draw = ImageDraw.Draw(annotated)
        for violation in violations:
            bounds = violation.get("bounds")
            if not bounds or len(bounds) != 4:
                continue
            left, top, right, bottom = bounds
            color = SEVERITY_COLORS.get(violation.get("severity", "Medium"), "#94a3b8")
            draw.rectangle([left, top, right, bottom], outline=color, width=3)
        buffer = io.BytesIO()
        annotated.convert("RGB").save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def screenshot_data_uri(report_doc: dict, *, project_root: Path | None = None) -> str | None:
    """Return annotated screenshot as a data URI, or None if unavailable."""
    root = project_root or ROOT
    image_path = _resolve_existing_path(report_doc.get("image_path", ""), root)
    if image_path is None:
        return None
    if report_doc.get("violations"):
        try:
            return _annotate_screenshot(image_path, report_doc["violations"])
        except Exception:
            # Tiny / corrupt crops or missing PIL features — still embed the raw image.
            pass
    try:
        return _image_to_data_uri(image_path)
    except OSError:
        return None


def render_html_report(report_doc: dict, *, project_root: Path | None = None) -> str:
    """Render a standalone HTML audit report from report.json."""
    root = project_root or ROOT
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        # Template is named *.html.j2, so suffix-based select_autoescape would
        # leave escaping OFF and inject raw XML/HTML into the page. Force it on.
        autoescape=True,
    )
    template = env.get_template("audit_report.html.j2")
    xml_path = _resolve_existing_path(report_doc.get("xml_path", ""), root)
    return template.render(
        report=report_doc,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        screenshot_data_uri=screenshot_data_uri(report_doc, project_root=root),
        xml_snippet=_read_xml_snippet(xml_path),
        violations=_sort_violations(report_doc.get("violations", [])),
        severity_colors=SEVERITY_COLORS,
    )


def _html_to_pdf(html: str) -> bytes:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "PDF export requires playwright. Install with: "
            "pip install playwright && playwright install chromium"
        ) from exc

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.set_content(html, wait_until="load")
                return page.pdf(
                    format="A4",
                    print_background=True,
                    margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"},
                )
            finally:
                browser.close()
    except Exception as exc:
        raise RuntimeError(
            "PDF export failed. Install browsers with: playwright install chromium"
        ) from exc


def render_pdf_report(report_doc: dict, *, project_root: Path | None = None) -> bytes:
    """Render report.json to PDF bytes via HTML + Playwright."""
    html = render_html_report(report_doc, project_root=project_root)
    return _html_to_pdf(html)


def write_report_html(report_doc: dict, output_path: Path, *, project_root: Path | None = None) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_html_report(report_doc, project_root=project_root),
        encoding="utf-8",
    )
    return output_path


def write_report_pdf(report_doc: dict, output_path: Path, *, project_root: Path | None = None) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(render_pdf_report(report_doc, project_root=project_root))
    return output_path


def render_report_bytes(
    report_doc: dict,
    fmt: ReportFormat,
    *,
    project_root: Path | None = None,
) -> tuple[bytes, str, str]:
    """Return (content_bytes, media_type, filename_suffix) for the requested format."""
    screen_id = report_doc.get("screen_id", "audit")
    if fmt == "html":
        content = render_html_report(report_doc, project_root=project_root).encode("utf-8")
        return content, "text/html; charset=utf-8", f"{screen_id}_report.html"
    content = render_pdf_report(report_doc, project_root=project_root)
    return content, "application/pdf", f"{screen_id}_report.pdf"
