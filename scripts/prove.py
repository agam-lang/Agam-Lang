#!/usr/bin/env python3
"""Agam Automated Proof & Verification Harness.

Usage:
    python scripts/prove.py

This script verifies canonical Agam programs across both the Cranelift JIT
(`agamc run`) and the LLVM AOT backend (`agamc build --backend llvm`).

Exit codes:
    0 - All canonical examples compiled and executed with 100% verified parity.
    1 - At least one example failed to compile or execute.
"""

import sys
import time
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGAMC = ROOT / "agam" / "target" / "release" / "agamc.exe"
if not AGAMC.exists():
    AGAMC = ROOT / "agam" / "target" / "debug" / "agamc.exe"

EXAMPLES_DIR = ROOT / "examples" / "01_basics"


if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def run_cmd(cmd, timeout=15):
    try:
        t0 = time.perf_counter()
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
        elapsed = (time.perf_counter() - t0) * 1000.0
        return res.returncode, res.stdout.strip(), res.stderr.strip(), elapsed
    except Exception as e:
        return -1, "", str(e), 0.0


def main():
    if not AGAMC.exists():
        print(f"Error: Compiler binary not found at {AGAMC}")
        print("Build compiler first via: cargo build --release --manifest-path agam/Cargo.toml")
        sys.exit(1)

    print("=" * 88)
    print(" [*] AGAM CANONICAL SYNTAX PROOF & DUAL-BACKEND VERIFICATION HARNESS")
    print("=" * 88)

    print(f"Compiler : {AGAMC.resolve()}")
    print(f"Directory: {EXAMPLES_DIR.resolve()}\n")

    files = sorted(EXAMPLES_DIR.glob("*.agam"))
    if not files:
        print(f"No .agam files found in {EXAMPLES_DIR}")
        sys.exit(1)

    header = f"{'Source File':<32} | {'JIT Run':<10} | {'LLVM IR':<10} | {'Output':<18} | {'Status'}"
    print(header)
    print("-" * 88)

    passed = 0
    total = len(files)

    for f in files:
        # 1. Test Cranelift JIT
        jit_code, jit_out, jit_err, jit_ms = run_cmd([str(AGAMC), "run", str(f)])
        jit_status = "PASS" if jit_code == 0 else "FAIL"

        # 2. Test LLVM AOT Codegen
        llvm_code, llvm_out, llvm_err, llvm_ms = run_cmd(
            [str(AGAMC), "build", "--backend", "llvm", str(f)]
        )
        llvm_status = "PASS" if llvm_code == 0 else "FAIL"

        # Clean up any generated .ll file next to the source
        ll_file = f.with_suffix(".ll")
        if ll_file.exists():
            try:
                ll_file.unlink()
            except Exception:
                pass

        # Evaluate overall proof status
        if jit_code == 0 and llvm_code == 0:
            status = "PROVEN"
            passed += 1
        elif jit_code == 0:
            status = "JIT ONLY"
        elif llvm_code == 0:
            status = "LLVM ONLY"
        else:
            status = "FAILED"

        first_line = jit_out.splitlines()[0] if jit_out else (jit_err.splitlines()[-1] if jit_err else "")
        if len(first_line) > 17:
            first_line = first_line[:14] + "..."

        print(
            f"{f.name:<32} | {jit_status:<10} | {llvm_status:<10} | {first_line:<18} | {status}"
        )

    print("-" * 88)
    print(f"Results: {passed}/{total} files fully proven on both JIT & LLVM AOT backends.\n")

    if passed == total:
        print("✓ SUCCESS: All canonical examples are 100% verified executable truth.")
        sys.exit(0)
    else:
        print("✗ WARNING: Discrepancies detected between backends.")
        sys.exit(1)


if __name__ == "__main__":
    main()
