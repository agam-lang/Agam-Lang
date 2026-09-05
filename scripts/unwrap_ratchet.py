#!/usr/bin/env python3
"""
Unwrap Ratchet for Agam-Lang.
Scans compiler source crates in `agam/crates/` for `.unwrap()`, `.expect(`, and `panic!(`.
Maintains a strict ratchet baseline in `.agent/ratchet/unwrap_baseline.json`.
Fails if any PR or commit increases the total unwrap/expect/panic count.
"""

import os
import re
import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CRATES_DIR = ROOT_DIR / "agam" / "crates"
BASELINE_FILE = ROOT_DIR / ".agent" / "ratchet" / "unwrap_baseline.json"

# Patterns to detect dangerous calls
PATTERNS = {
    "unwrap": re.compile(r"\.unwrap\(\)"),
    "expect": re.compile(r"\.expect\("),
    "panic": re.compile(r"panic!\("),
    "todo": re.compile(r"todo!\("),
}

def is_test_file(path: Path) -> bool:
    parts = path.parts
    if "tests" in parts or "benches" in parts:
        return True
    if path.name.endswith("_test.rs") or path.name.startswith("test_"):
        return True
    # Ignore testing harness crate
    if "agam_test" in parts:
        return True
    return False

def scan_crates():
    counts = {}
    details = {}

    if not CRATES_DIR.exists():
        print(f"[ERROR] Crates directory not found: {CRATES_DIR}")
        sys.exit(1)

    for rs_file in CRATES_DIR.rglob("*.rs"):
        if is_test_file(rs_file):
            continue

        rel_path = rs_file.relative_to(CRATES_DIR)
        crate_name = rel_path.parts[0] if len(rel_path.parts) > 1 else "root"
        # If crate is inside a tier like core/agam_ast
        if len(rel_path.parts) > 2 and rel_path.parts[0] in ["core", "middle", "backends", "runtime", "tooling"]:
            crate_name = f"{rel_path.parts[0]}/{rel_path.parts[1]}"

        try:
            content = rs_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        in_cfg_test = False
        file_counts = {"unwrap": 0, "expect": 0, "panic": 0, "todo": 0}

        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            if "#[cfg(test)]" in stripped:
                in_cfg_test = True
                continue
            if in_cfg_test and stripped.startswith("mod tests"):
                # rest of file is test module
                break

            for key, pattern in PATTERNS.items():
                matches = len(pattern.findall(stripped))
                file_counts[key] += matches

        file_total = sum(file_counts.values())
        if file_total > 0:
            if crate_name not in counts:
                counts[crate_name] = {"unwrap": 0, "expect": 0, "panic": 0, "todo": 0, "total": 0}
            for k in file_counts:
                counts[crate_name][k] += file_counts[k]
            counts[crate_name]["total"] += file_total

    total_unwraps = sum(c["total"] for c in counts.values())
    return counts, total_unwraps

def main():
    update_mode = "--update" in sys.argv
    verbose_mode = "-v" in sys.argv or "--verbose" in sys.argv

    counts, current_total = scan_crates()

    print(f"=== Agam Zero-Panic Unwrap Ratchet ===")
    print(f"Scanned compiler crates in: {CRATES_DIR}")
    print(f"Total non-test unwrap/expect/panic instances: {current_total}")

    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if update_mode or not BASELINE_FILE.exists():
        baseline_data = {
            "total": current_total,
            "crates": counts
        }
        BASELINE_FILE.write_text(json.dumps(baseline_data, indent=2), encoding="utf-8")
        print(f"[OK] Ratchet baseline recorded to {BASELINE_FILE.relative_to(ROOT_DIR)} (Baseline: {current_total})")
        sys.exit(0)

    try:
        baseline_data = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
        baseline_total = baseline_data.get("total", current_total)
    except Exception as e:
        print(f"[WARN] Failed to read baseline file ({e}); updating baseline now.")
        BASELINE_FILE.write_text(json.dumps({"total": current_total, "crates": counts}, indent=2), encoding="utf-8")
        baseline_total = current_total

    print(f"Baseline Allowed Maximum: {baseline_total}")

    if verbose_mode:
        print("\nBreakdown by Crate:")
        for crate, data in sorted(counts.items(), key=lambda x: -x[1]["total"]):
            print(f"  - {crate:30}: total={data['total']} (unwrap={data['unwrap']}, expect={data['expect']}, panic={data['panic']}, todo={data['todo']})")

    if current_total > baseline_total:
        delta = current_total - baseline_total
        print(f"\n[FAIL] RATCHET VIOLATION: Current count ({current_total}) exceeds baseline ({baseline_total}) by +{delta}!")
        print("Do not introduce new .unwrap(), .expect(), or panic!() calls in production compiler code.")
        print("Handle errors with `Result` or `agam_errors::Diagnostic`.")
        sys.exit(1)
    elif current_total < baseline_total:
        reduction = baseline_total - current_total
        print(f"\n[SUCCESS] IMPROVEMENT: You reduced panic instances by {reduction}! (Now {current_total} vs baseline {baseline_total})")
        print("Updating baseline to lock in this improvement...")
        BASELINE_FILE.write_text(json.dumps({"total": current_total, "crates": counts}, indent=2), encoding="utf-8")
        sys.exit(0)
    else:
        print(f"\n[PASS] Ratchet check passed! ({current_total} <= {baseline_total})")
        sys.exit(0)

if __name__ == "__main__":
    main()
