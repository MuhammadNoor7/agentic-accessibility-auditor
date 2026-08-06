"""Pull the key results (params, best val F1, MASC test report, Rico holdout
report) out of an executed train_crop_violation_classifier.ipynb, so they can
be logged into docs/crop_classifier_comparison_findings.md without hand-copying.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def cell_text_outputs(cell):
    texts = []
    for out in cell.get("outputs", []):
        if "text" in out:
            texts.append("".join(out["text"]))
        elif "data" in out and "text/plain" in out["data"]:
            texts.append("".join(out["data"]["text/plain"]))
    return "\n".join(texts)


def extract(path: str) -> dict:
    nb = json.load(open(path, encoding="utf-8"))
    cells = nb["cells"]
    result = {"source_file": path}

    for c in cells:
        if c["cell_type"] != "code":
            continue
        src = "".join(c.get("source", []))
        out = cell_text_outputs(c)

        if 'backbone=' in out and 'device=' in out and 'params=' in out:
            m = re.search(r"backbone=(['\"]?)([\w.]+)\1,\s*device=(\S+),\s*params=([\d,]+)", out)
            if m:
                result["backbone"] = m.group(2)
                result["device"] = m.group(3)
                result["params"] = m.group(4)

        if "Best val macro-F1" in out:
            m = re.search(r"Best val macro-F1:\s*([\d.]+)", out)
            if m:
                result["best_val_f1"] = m.group(1)

        if "def build_model" in src or "def run_epoch" in src:
            pass  # source cells, not results

        if "classification_report(" in src and "precision" in out and "recall" in out:
            # first one encountered chronologically = MASC test report (cell order),
            # second = Rico holdout report
            result.setdefault("classification_reports", []).append(out.strip())

        if "Rico holdout crops evaluated" in out:
            m = re.search(r"Rico holdout crops evaluated:\s*(\d+)", out)
            if m:
                result["rico_n_crops"] = m.group(1)

    return result


if __name__ == "__main__":
    for path in sys.argv[1:]:
        r = extract(path)
        print(f"\n{'='*70}\n{path}\n{'='*70}")
        for k, v in r.items():
            if k == "classification_reports":
                for i, rep in enumerate(v):
                    label = "MASC test" if i == 0 else "Rico holdout"
                    print(f"\n--- {label} classification_report ---\n{rep}")
            else:
                print(f"{k}: {v}")
