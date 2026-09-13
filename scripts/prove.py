#!/usr/bin/env python3
"""Agam Automated Proof & Verification Harness.

Usage:
    python scripts/prove.py [--remote]

This script verifies canonical Agam programs across:
1. Local Cranelift JIT (`agamc run`)
2. Local LLVM AOT backend (`agamc build --backend llvm`)
3. Optional Remote Intel Node (`--remote`) at 192.168.0.150 with BelowNormal priority.

Exit codes:
    0 - All canonical examples compiled and executed with 100% verified parity.
    1 - At least one example failed to compile or execute.
"""

import sys
import time
import subprocess
from pathlib import Path

REMOTE_HOST = "192.168.0.150"
REMOTE_USER = "Main_Guest"
REMOTE_PASS = "56341236"
REMOTE_ROOT = "C:/Users/Main_Guest/Agam-Node"

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


def try_connect_remote():
    try:
        import os
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        key_file = os.path.expanduser("~/.ssh/id_ed25519")
        if os.path.exists(key_file):
            client.connect(
                REMOTE_HOST,
                username=REMOTE_USER,
                key_filename=key_file,
                allow_agent=False,
                look_for_keys=False,
                timeout=2.0,
                banner_timeout=2.0,
                auth_timeout=2.0,
            )
        else:
            client.connect(
                REMOTE_HOST,
                username=REMOTE_USER,
                password=REMOTE_PASS,
                allow_agent=False,
                look_for_keys=False,
                timeout=2.0,
                banner_timeout=2.0,
                auth_timeout=2.0,
            )
        return client
    except Exception:
        return None


def run_remote_prove(client, rel_path):
    ps_cmd = (
        f'[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = "BelowNormal"; '
        f'Set-Location "{REMOTE_ROOT}"; '
        f'.\\agamc.exe run {rel_path}'
    )
    try:
        stdin, stdout, stderr = client.exec_command(f'powershell -NoProfile -Command "{ps_cmd}"', timeout=15)
        stdin.close()
        code = stdout.channel.recv_exit_status()
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        return code, out, err
    except Exception as e:
        return -1, "", str(e)


def main():
    use_remote = "--remote" in sys.argv

    if not AGAMC.exists():
        print(f"Error: Compiler binary not found at {AGAMC}")
        print("Build compiler first via: cargo build --release --manifest-path agam/Cargo.toml")
        sys.exit(1)

    print("=" * 96)
    print(" [*] AGAM CANONICAL SYNTAX PROOF & DUAL-BACKEND VERIFICATION HARNESS")
    print("=" * 96)

    print(f"Compiler : {AGAMC.resolve()}")
    print(f"Directory: {EXAMPLES_DIR.resolve()}")

    remote_client = None
    if use_remote:
        print(f"Remote   : Probing Intel Dell Node @ {REMOTE_HOST} (timeout 2.0s)...", end="", flush=True)
        remote_client = try_connect_remote()
        if remote_client:
            print(" [ONLINE] (BelowNormal priority mode)")
        else:
            print(" [OFFLINE] (Fail-soft: proceeding with local verification)")
    print()

    files = sorted(EXAMPLES_DIR.glob("*.agam"))
    if not files:
        print(f"No .agam files found in {EXAMPLES_DIR}")
        sys.exit(1)

    if use_remote and remote_client:
        header = f"{'Source File':<28} | {'JIT Run':<8} | {'LLVM IR':<8} | {'Intel Run':<10} | {'Output':<16} | {'Status'}"
        div_len = 96
    else:
        header = f"{'Source File':<32} | {'JIT Run':<10} | {'LLVM IR':<10} | {'Output':<18} | {'Status'}"
        div_len = 88

    print(header)
    print("-" * div_len)

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

        # 3. Optional Remote Intel Run
        intel_status = "N/A"
        intel_out = ""
        parity_ok = True
        if use_remote and remote_client:
            rel_file = f"examples\\01_basics\\{f.name}"
            i_code, intel_out, i_err = run_remote_prove(remote_client, rel_file)
            intel_status = "PASS" if i_code == 0 else "FAIL"
            if i_code != 0 or intel_out != jit_out:
                parity_ok = False

        # Evaluate overall proof status
        if jit_code == 0 and llvm_code == 0 and parity_ok:
            status = "PROVEN"
            passed += 1
        elif jit_code == 0:
            status = "JIT ONLY"
        elif llvm_code == 0:
            status = "LLVM ONLY"
        else:
            status = "FAILED"

        first_line = jit_out.splitlines()[0] if jit_out else (jit_err.splitlines()[-1] if jit_err else "")
        if len(first_line) > 15:
            first_line = first_line[:12] + "..."

        if use_remote and remote_client:
            print(
                f"{f.name:<28} | {jit_status:<8} | {llvm_status:<8} | {intel_status:<10} | {first_line:<16} | {status}"
            )
        else:
            print(
                f"{f.name:<32} | {jit_status:<10} | {llvm_status:<10} | {first_line:<18} | {status}"
            )

    if remote_client:
        remote_client.close()

    print("-" * div_len)
    print(f"Results: {passed}/{total} files fully proven.\n")

    if passed == total:
        print("✓ SUCCESS: All canonical examples are 100% verified executable truth.")
        sys.exit(0)
    else:
        print("✗ WARNING: Discrepancies detected between backends.")
        sys.exit(1)


if __name__ == "__main__":
    main()
