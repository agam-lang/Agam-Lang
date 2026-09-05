#!/usr/bin/env python3
"""cargo-lens: Ultra-compact Cargo output filter for AI agents.

Compresses cargo build/check/test outputs to errors, warnings, and summary lines only.
Saves up to 90% of context tokens during development.

Usage:
    python scripts/cargo_lens.py check [args...]
    python scripts/cargo_lens.py test [args...]
    python scripts/cargo_lens.py clippy [args...]
"""

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARGO_TOML = ROOT / "agam" / "Cargo.toml"


def run_filtered(args):
    cmd = ["cargo"] + args
    if "--manifest-path" not in " ".join(args):
        cmd.extend(["--manifest-path", str(CARGO_TOML)])

    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    combined = (res.stdout + "\n" + res.stderr).splitlines()

    compiling_count = 0
    clean_lines = []
    error_lines = []
    warning_lines = []
    summary_lines = []

    in_error = False

    for line in combined:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("Compiling ") or stripped.startswith("Checking "):
            compiling_count += 1
            continue

        if "error[" in stripped or stripped.startswith("error:"):
            in_error = True
            error_lines.append(line)
        elif "warning[" in stripped or stripped.startswith("warning:"):
            in_error = False
            warning_lines.append(line)
        elif in_error:
            error_lines.append(line)
        elif "test result:" in stripped or "Finished " in stripped or "Doc-tests" in stripped:
            summary_lines.append(line)

    print(f"[*] cargo-lens: processed {compiling_count} compilation units (exit code: {res.returncode})")

    if error_lines:
        print("\n--- ERRORS ---")
        print("\n".join(error_lines[:40]))
        if len(error_lines) > 40:
            print(f"... ({len(error_lines) - 40} error lines truncated for token efficiency)")

    if warning_lines and not error_lines:
        print("\n--- WARNINGS ---")
        print("\n".join(warning_lines[:20]))
        if len(warning_lines) > 20:
            print(f"... ({len(warning_lines) - 20} warning lines truncated)")

    if summary_lines:
        print("\n--- SUMMARY ---")
        for s in summary_lines:
            print(s)

    sys.exit(res.returncode)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/cargo_lens.py <check|test|build|clippy> [args...]")
        sys.exit(1)
    run_filtered(sys.argv[1:])
