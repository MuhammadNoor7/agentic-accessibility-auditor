"""Unattended overnight sweep: runs notebooks/train_crop_violation_classifier.ipynb
once per remaining backbone, changing only CFG["backbone"]/CFG["run_name"] each
time, saves the executed notebook per backbone, and appends results into
docs/crop_classifier_comparison_findings.md as each one finishes.

Designed to run unattended for many hours: catches per-backbone errors and
keeps going (logs a FAILED row instead of dying), monitors disk space and
stops gracefully rather than risk a corrupt write, and writes a live status
JSON so progress can be checked without waiting for the whole sweep.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
from pathlib import Path

import nbformat
from nbclient import NotebookClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_NB = REPO_ROOT / "notebooks" / "train_crop_violation_classifier.ipynb"
OUT_NB_DIR = REPO_ROOT / "runs" / "notebooks"
FINDINGS_PATH = REPO_ROOT / "docs" / "crop_classifier_comparison_findings.md"
STATUS_PATH = REPO_ROOT / "runs" / "crop_violation_classifier" / "overnight_sweep_status.json"
MIN_FREE_MB = 500  # stop rather than risk a corrupt write below this

REMAINING_BACKBONES = [
    # RESUMED after the sweep process was orphaned/killed by a session
    # reconnect (confirmed via checkpoint files under runs/ - 15 backbones
    # done: mobilenet_v3_small/large, mobilenetv1_100, efficientnet_b0,
    # mobilevit_s, vit_b_16, resnet50, shufflenet_v2_x1_0, regnet_y_800mf,
    # mnasnet1_0, efficientnet_v2_s, densenet121, squeezenet1_1,
    # mobilenetv1_125, mobilenetv2_050, mobilenetv2_100).
    # mobilenetv2_140 did NOT complete (no checkpoint saved) - redo it.
    "mobilenetv2_140",
    "mobilenetv3_small_050",
    # mobilenetv3_small_100 and mobilenetv3_large_100 removed: same
    # architecture + width multiplier as mobilenet_v3_small/large
    # (torchvision), already done - just a different pretrain recipe
    # (timm's .lamb_in1k vs torchvision's own). Not worth the ~30-60 min.
    "mobilenetv4_conv_small", "mobilenetv4_conv_medium", "mobilenetv4_conv_large",
    "mobilevit_xxs", "mobilevit_xs",
    "mobilevitv2_050", "mobilevitv2_100", "mobilevitv2_200",
    "mobileone_s0", "mobileone_s1", "mobileone_s4",
    "ghostnet_100", "ghostnetv2_100",
    "convnext_tiny", "swin_tiny_patch4_window7_224",
]


def free_mb(drive="D:"):
    total, used, free = shutil.disk_usage(drive + "\\")
    return free / (1024 * 1024)


def _source_to_str(source) -> str:
    return "".join(source) if isinstance(source, list) else source


def patch_backbone(nb, backbone: str):
    """Format-agnostic: nbformat.read() gives cell['source'] as a plain str,
    while raw json.load() gives a list of lines - handle both by always
    working on the joined string and doing a regex substitution, so this
    can't silently no-op depending on which loader was used."""
    cfg_cell = None
    for c in nb["cells"]:
        src_joined = _source_to_str(c.get("source", ""))
        if c["cell_type"] == "code" and '"backbone":' in src_joined and '"run_name":' in src_joined:
            cfg_cell = c
            break
    if cfg_cell is None:
        raise RuntimeError('Could not find the CFG cell (no cell has both "backbone": and "run_name":)')

    src = _source_to_str(cfg_cell["source"])
    new_src, n1 = re.subn(r'"backbone":\s*"[^"]*"', f'"backbone": "{backbone}"', src, count=1)
    new_src, n2 = re.subn(r'"run_name":\s*"[^"]*"', f'"run_name": "crop_violation_classifier_{backbone}"', new_src, count=1)
    if n1 != 1 or n2 != 1:
        raise RuntimeError(f'patch_backbone: expected exactly 1 "backbone"/"run_name" replacement each, got {n1}/{n2}')
    cfg_cell["source"] = new_src


def cell_text(cell):
    texts = []
    for out in cell.get("outputs", []):
        if "text" in out:
            texts.append("".join(out["text"]))
        elif "data" in out and "text/plain" in out["data"]:
            texts.append("".join(out["data"]["text/plain"]))
    return "\n".join(texts)


def extract_results(nb):
    result = {}
    reports = []
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        out = cell_text(c)
        m = re.search(r"backbone=(['\"]?)([\w.]+)\1,\s*device=(\S+),\s*params=([\d,]+)", out)
        if m:
            result["params"] = m.group(4)
        m = re.search(r"Best val macro-F1:\s*([\d.]+)", out)
        if m:
            result["best_val_f1"] = m.group(1)
        if "classification_report(" in "".join(c.get("source", [])) or (
            "precision" in out and "recall" in out and "support" in out
        ):
            if "precision" in out and "recall" in out:
                reports.append(out.strip())
    result["reports"] = reports
    return result


def parse_report_f1s(report_text):
    """Pull macro avg F1 and per-rule R04/R17/R08 F1 out of a classification_report string."""
    vals = {}
    m = re.search(r"macro avg\s+[\d.]+\s+[\d.]+\s+([\d.]+)", report_text)
    if m:
        vals["macro_f1"] = m.group(1)
    for rule in ("R04", "R17", "R08"):
        m = re.search(rf"{rule}\s+[\d.]+\s+[\d.]+\s+([\d.]+)", report_text)
        if m:
            vals[f"{rule}_f1"] = m.group(1)
    return vals


def insert_table_row(backbone: str, params: str, val_f1: str, masc: dict, rico: dict):
    text = FINDINGS_PATH.read_text(encoding="utf-8")
    marker = "| ... | | | | | | | | | |"
    if marker not in text:
        return  # table already finalized/edited by hand - don't guess where to insert
    gap = "?"
    try:
        gap = f"{float(masc.get('macro_f1', 0)) - float(rico.get('macro_f1', 0)):.2f} drop" if masc.get("macro_f1") and rico.get("macro_f1") else "?"
    except ValueError:
        pass
    row = (
        f"| `{backbone}` | {params} | {val_f1} | {masc.get('macro_f1', '?')} | "
        f"{masc.get('R04_f1', '?')} | {masc.get('R17_f1', '?')} | {masc.get('R08_f1', '?')} | "
        f"{rico.get('macro_f1', '?')} | {gap} | auto-logged, overnight sweep — see detail below |\n"
    )
    text = text.replace(marker, row + marker)
    FINDINGS_PATH.write_text(text, encoding="utf-8")


def append_to_findings(backbone: str, status: str, elapsed_min: float, result: dict | None, error: str | None):
    if status == "ok" and result:
        reports = result.get("reports", [])
        masc = parse_report_f1s(reports[0]) if len(reports) >= 1 else {}
        rico = parse_report_f1s(reports[1]) if len(reports) >= 2 else {}
        insert_table_row(backbone, result.get("params", "?"), result.get("best_val_f1", "?"), masc, rico)

    with open(FINDINGS_PATH, "a", encoding="utf-8") as f:
        if status == "ok" and result:
            params = result.get("params", "?")
            val_f1 = result.get("best_val_f1", "?")
            reports = result.get("reports", [])
            masc = parse_report_f1s(reports[0]) if len(reports) >= 1 else {}
            rico = parse_report_f1s(reports[1]) if len(reports) >= 2 else {}

            f.write(
                f"\n## Detail: `{backbone}` (auto-logged, overnight sweep)\n\n"
                f"- **Params:** {params}\n"
                f"- **Best val macro-F1:** {val_f1}\n"
                f"- **Run time:** {elapsed_min:.1f} min\n\n"
            )
            if reports:
                f.write("**MASC test-split report:**\n```\n" + reports[0] + "\n```\n\n")
            if len(reports) >= 2:
                f.write("**Rico holdout report:**\n```\n" + reports[1] + "\n```\n\n")
            f.write(
                f"MASC macro-F1: {masc.get('macro_f1', '?')} | "
                f"Rico macro-F1: {rico.get('macro_f1', '?')} | "
                f"R04 F1 (MASC->Rico): {masc.get('R04_f1', '?')} -> {rico.get('R04_f1', '?')} | "
                f"R17 F1: {masc.get('R17_f1', '?')} -> {rico.get('R17_f1', '?')} | "
                f"R08 F1: {masc.get('R08_f1', '?')} -> {rico.get('R08_f1', '?')}\n\n"
                "*(Auto-logged - light on analysis, full numbers above. Add narrative later if useful.)*\n\n---\n"
            )
        else:
            f.write(
                f"\n## Detail: `{backbone}` - **FAILED** (overnight sweep, after {elapsed_min:.1f} min)\n\n"
                f"```\n{error}\n```\n\n---\n"
            )


VENV_PY = str(REPO_ROOT / ".venv-cropcls" / "Scripts" / "python.exe").lower()


def kill_stray_kernels():
    """Only kills python.exe processes running from OUR venv (.venv-cropcls) -
    never touches other python processes on this shared machine (e.g. other
    conda envs some other project might be using), and NEVER kills our own
    process (os.getpid()) - this script itself runs from that same venv, so
    without this exclusion it would self-terminate every time it's called."""
    my_pid = str(os.getpid())
    try:
        ps_cmd = (
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "Select-Object ProcessId, ExecutablePath | ConvertTo-Csv -NoTypeInformation"
        )
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=20,
        ).stdout
        for line in out.splitlines()[1:]:
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) >= 2:
                pid, exe_path = parts[0], parts[1]
                if pid == my_pid:
                    continue  # never kill ourselves
                if exe_path.lower() == VENV_PY:
                    try:
                        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True, timeout=10)
                    except Exception:
                        pass
    except Exception:
        pass


def main():
    status = {"started": time.strftime("%Y-%m-%d %H:%M:%S"), "results": {}}
    OUT_NB_DIR.mkdir(parents=True, exist_ok=True)

    for backbone in REMAINING_BACKBONES:
        avail = free_mb("D:")
        if avail < MIN_FREE_MB:
            print(f"[sweep] STOPPING: D: free space {avail:.0f}MB below {MIN_FREE_MB}MB threshold", flush=True)
            status["results"][backbone] = {"status": "SKIPPED_LOW_DISK", "free_mb": avail}
            with open(FINDINGS_PATH, "a", encoding="utf-8") as f:
                f.write(
                    f"\n## `{backbone}` and later - **SWEEP STOPPED**\n\n"
                    f"D: drive free space dropped to {avail:.0f}MB (below the {MIN_FREE_MB}MB safety threshold). "
                    "Stopped rather than risk a corrupted checkpoint write. Free up space and resume "
                    "scripts/overnight_sweep.py with the remaining backbone names.\n\n---\n"
                )
            STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")
            break

        print(f"\n{'='*70}\n[sweep] backbone={backbone}  (D: free={avail:.0f}MB)\n{'='*70}", flush=True)
        t0 = time.time()
        try:
            nb = nbformat.read(SRC_NB, as_version=4)
            patch_backbone(nb, backbone)
            client = NotebookClient(nb, timeout=-1, kernel_name="cropcls-cuda",
                                     resources={"metadata": {"path": str(REPO_ROOT)}})
            client.execute()

            out_path = OUT_NB_DIR / f"train_crop_violation_classifier_{backbone}.ipynb"
            nbformat.write(nb, out_path)

            result = extract_results(nb)
            elapsed = (time.time() - t0) / 60
            append_to_findings(backbone, "ok", elapsed, result, None)
            status["results"][backbone] = {"status": "ok", "elapsed_min": elapsed, **result}
            print(f"[sweep] {backbone}: OK, {elapsed:.1f} min -> {out_path}", flush=True)

        except Exception as exc:
            elapsed = (time.time() - t0) / 60
            err = f"{exc}\n\n{traceback.format_exc()}"
            append_to_findings(backbone, "failed", elapsed, None, err)
            status["results"][backbone] = {"status": "FAILED", "elapsed_min": elapsed, "error": str(exc)}
            print(f"[sweep] {backbone}: FAILED after {elapsed:.1f} min: {exc}", flush=True)

        finally:
            # kill_stray_kernels() removed from the automatic path: Win32_Process
            # reports the *resolved* interpreter path (C:\Python311\python.exe),
            # not the venv launch path, so the PID-exclusion check for "don't
            # kill myself" never actually matched this process either way - the
            # whole mechanism was unreliable here and killed the sweep twice.
            # nbclient already tears down its own kernel per NotebookClient
            # instance; a fresh instance is created every iteration, so this
            # isn't needed for normal operation.
            STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")

    status["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print("\n[sweep] ALL DONE.", flush=True)


if __name__ == "__main__":
    main()
