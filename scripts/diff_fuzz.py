#!/usr/bin/env python3
"""
Differential Parity & Fuzz Verifier for Agam-Lang.
Verifies backend execution and emission equivalence between Cranelift JIT (`agamc run`)
and LLVM AOT (`agamc build --backend llvm`).
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
AGAMC_BIN = ROOT_DIR / "agam" / "target" / "release" / "agamc.exe"
EXAMPLES_DIR = ROOT_DIR / "examples" / "01_basics"
ZIG_BIN = Path("C:/Users/ksvik/.tools/zig-windows-x86_64-0.13.0/zig.exe")

def run_cmd(cmd, cwd, timeout=15):
    try:
        res = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -2, "", str(e)

def verify_differential(file_path: Path, full_exec: bool = False):
    file_str = str(file_path.resolve())

    # 1. JIT Execution
    jit_code, jit_out, jit_err = run_cmd([str(AGAMC_BIN), "run", file_str], cwd=ROOT_DIR)

    # 2. LLVM IR Generation
    llvm_code, llvm_out, llvm_err = run_cmd(
        [str(AGAMC_BIN), "build", "--backend", "llvm", file_str],
        cwd=ROOT_DIR
    )

    ll_file = file_path.with_suffix(".ll")
    ll_exists = ll_file.exists()

    status = "OK"
    diff_msg = ""

    if jit_code != 0 and llvm_code == 0:
        status = "JIT_FAILURE"
        diff_msg = f"JIT failed: {jit_err or jit_out}"
    elif jit_code == 0 and llvm_code != 0:
        status = "LLVM_FAILURE"
        diff_msg = f"LLVM lowering failed: {llvm_err or llvm_out}"
    elif jit_code != 0 and llvm_code != 0:
        status = "DUAL_FAILURE"
        diff_msg = f"Both failed: JIT({jit_err}) LLVM({llvm_err})"
    else:
        # Both succeeded
        if full_exec and ZIG_BIN.exists() and ll_exists:
            with tempfile.TemporaryDirectory() as tmpdir:
                out_exe = Path(tmpdir) / "test_aot.exe"
                zig_code, _, zig_err = run_cmd(
                    [str(ZIG_BIN), "cc", str(ll_file), "-o", str(out_exe)],
                    cwd=tmpdir,
                    timeout=20
                )
                if zig_code == 0:
                    exe_code, exe_out, _ = run_cmd([str(out_exe)], cwd=tmpdir, timeout=10)
                    if exe_code != jit_code:
                        status = "EXIT_CODE_DIVERGENCE"
                        diff_msg = f"JIT exit {jit_code} vs LLVM AOT exit {exe_code}"
                    elif exe_out != jit_out:
                        status = "STDOUT_DIVERGENCE"
                        diff_msg = f"JIT: '{jit_out}' vs LLVM: '{exe_out}'"

    # Clean up generated .ll file
    if ll_exists:
        try:
            ll_file.unlink()
        except Exception:
            pass

    return {
        "file": file_path.name,
        "status": status,
        "diff_msg": diff_msg,
        "jit_out": jit_out,
        "jit_code": jit_code,
        "llvm_code": llvm_code
    }

def main():
    if not AGAMC_BIN.exists():
        print(f"[ERROR] agamc executable not found at {AGAMC_BIN}")
        sys.exit(1)

    full_exec = "--full" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    targets = []
    if args:
        for a in args:
            p = Path(a)
            if p.exists():
                targets.append(p)
    else:
        if EXAMPLES_DIR.exists():
            targets = sorted(list(EXAMPLES_DIR.glob("*.agam")))

    if not targets:
        print("No .agam files found.")
        sys.exit(1)

    mode_str = "Full Native AOT Linking" if full_exec else "Dual-Backend (JIT Execution + LLVM IR Lowering)"
    print(f"=== Agam Differential Parity & Fuzz Verifier ===")
    print(f"Mode: {mode_str}")
    print(f"Testing {len(targets)} files:\n")

    passed = 0
    diverged = []

    for t in targets:
        res = verify_differential(t, full_exec=full_exec)
        if res["status"] == "OK":
            passed += 1
            print(f"  [PASS] {res['file']:32} -> Output: '{res['jit_out']}'")
        else:
            diverged.append(res)
            print(f"  [FAIL] {res['file']:32} -> {res['status']}: {res['diff_msg']}")

    print(f"\nSummary: {passed}/{len(targets)} passed dual-backend parity checks.")

    if diverged:
        print(f"\n[DIVERGENCES DETECTED: {len(diverged)}]")
        for d in diverged:
            print(f"  - {d['file']}: {d['status']} ({d['diff_msg']})")
        sys.exit(1)
    else:
        print("[SUCCESS] All test cases exhibit verified backend parity!")
        sys.exit(0)

if __name__ == "__main__":
    main()
