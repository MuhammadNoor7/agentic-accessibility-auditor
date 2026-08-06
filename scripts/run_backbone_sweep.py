"""Run notebooks/train_crop_violation_classifier.ipynb once per backbone in a
loop, changing only CFG["backbone"] (and CFG["run_name"] so checkpoints don't
collide) each iteration. Saves each executed notebook next to the existing
mobilenet_v3_small result at runs/notebooks/, same storage convention.
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_NB = REPO_ROOT / "notebooks" / "train_crop_violation_classifier.ipynb"
OUT_DIR = REPO_ROOT / "runs" / "notebooks"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BACKBONES = sys.argv[1:]


def patch_backbone(nb, backbone: str):
    cfg_cell = nb["cells"][6]
    src = cfg_cell["source"]
    for i, line in enumerate(src):
        if line.strip().startswith('"backbone":'):
            src[i] = f'    "backbone": "{backbone}",\n'
        if line.strip().startswith('"run_name":'):
            src[i] = f'    "run_name": "crop_violation_classifier_{backbone}",\n'
    cfg_cell["source"] = src


for backbone in BACKBONES:
    print(f"\n{'='*70}\n[sweep] backbone={backbone}\n{'='*70}", flush=True)
    nb = nbformat.read(SRC_NB, as_version=4)
    patch_backbone(nb, backbone)

    client = NotebookClient(nb, timeout=-1, kernel_name="python3",
                             resources={"metadata": {"path": str(REPO_ROOT)}})
    try:
        client.execute()
        status = "ok"
    except Exception as exc:
        status = f"FAILED: {exc}"
        print(f"[sweep] {backbone} FAILED: {exc}", flush=True)

    out_path = OUT_DIR / f"train_crop_violation_classifier_{backbone}.ipynb"
    nbformat.write(nb, out_path)
    print(f"[sweep] {backbone}: {status} -> {out_path}", flush=True)
