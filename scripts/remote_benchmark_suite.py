import os
import sys
import time
import json
import subprocess
import paramiko

REMOTE_HOST = '192.168.0.150'
REMOTE_USER = 'Main_Guest'
REMOTE_PASS = '56341236'
REMOTE_ROOT = 'C:/Users/Main_Guest/Agam-Node'
LOCAL_ROOT = os.path.abspath('.')
LOCAL_AGAMC = os.path.join(LOCAL_ROOT, 'agam', 'target', 'release', 'agamc.exe')

TEST_CASES = [
    {
        "name": "Hello World",
        "category": "Smoke / IO",
        "path": "examples/01_basics/01_hello_world_base.agam"
    },
    {
        "name": "Fibonacci (Recursive)",
        "category": "Recursion & Arithmetic",
        "path": "examples/01_basics/fibonacci_base.agam"
    },
    {
        "name": "Quicksort",
        "category": "Array & Sorting",
        "path": "examples/01_basics/02_quicksort_base.agam"
    },
    {
        "name": "Prime Sieve",
        "category": "Number Theory",
        "path": "examples/01_basics/03_prime_sieve_base.agam"
    },
    {
        "name": "Binary Search",
        "category": "Algorithms",
        "path": "benchmarks/suites/01_algorithms/binary_search.agam"
    },
    {
        "name": "Monte Carlo Pi",
        "category": "Numerical Computation",
        "path": "benchmarks/suites/02_numerical_computation/monte_carlo_pi.agam"
    },
    {
        "name": "RLE Compression",
        "category": "Compression Kernel",
        "path": "benchmarks/suites/04_compression_kernels/rle_codec.agam"
    },
    {
        "name": "CRC32 Checksum",
        "category": "Cryptography Kernel",
        "path": "benchmarks/suites/07_cryptography_kernels/crc32_checksum.agam"
    }
]

def run_local(cmd):
    start = time.perf_counter()
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        dur = (time.perf_counter() - start) * 1000.0
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "duration_ms": round(dur, 2)
        }
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e), "duration_ms": 0}

def try_connect_remote():
    """Fast fail-soft connection check (2s timeout). Returns client or None."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(REMOTE_HOST, username=REMOTE_USER, password=REMOTE_PASS, timeout=2.0)
        # Test a quick ping command
        stdin, stdout, stderr = client.exec_command('whoami', timeout=2.0)
        stdin.close()
        stdout.channel.recv_exit_status()
        return client
    except Exception:
        return None

def run_remote_silent(client, rel_path, mode="run"):
    """
    Executes agamc remotely with BelowNormal priority and no new window.
    Zero disruption to primary user on Dell.
    """
    start = time.perf_counter()
    remote_rel = rel_path.replace('/', '\\')
    ps_cmd = (
        f'[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = "BelowNormal"; '
        f'Set-Location "{REMOTE_ROOT}"; '
        f'.\\agamc.exe {mode} {remote_rel}'
    )
    try:
        stdin, stdout, stderr = client.exec_command(f'powershell -NoProfile -Command "{ps_cmd}"', timeout=30)
        stdin.close()
        code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        dur = (time.perf_counter() - start) * 1000.0
        return {
            "exit_code": code,
            "stdout": out,
            "stderr": err,
            "duration_ms": round(dur, 2)
        }
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e), "duration_ms": 0}

def main():
    print("=" * 70)
    print("AGAM DUAL-NODE COMPILATION & BENCHMARK MATRIX")
    print(f"Host: AMD Ryzen 7 7840HS (Zen 4, 8C/16T)")
    print(f"Remote Target: Intel Core i5-10310U (Comet Lake, 4C/8T) @ {REMOTE_HOST}")
    print("=" * 70)

    print(f"Checking Dell node connectivity (timeout: 2.0s)...", end="", flush=True)
    client = try_connect_remote()
    if client:
        print(" [ONLINE] (Zero-disruption mode engaged)")
    else:
        print(" [OFFLINE] (Fail-soft: proceeding with local verification only)")

    results = []

    for tc in TEST_CASES:
        rel_path = tc["path"]
        name = tc["name"]
        cat = tc["category"]
        print(f"\n---> Running [{cat}] {name} ({rel_path})...")

        # 1. Typecheck
        print("  - Local Typecheck...", end="", flush=True)
        local_check = run_local([LOCAL_AGAMC, "check", rel_path])
        print(f" {local_check['duration_ms']}ms (code {local_check['exit_code']})")

        remote_check = None
        if client:
            print("  - Remote Intel Typecheck (low-priority)...", end="", flush=True)
            remote_check = run_remote_silent(client, rel_path, mode="check")
            print(f" {remote_check['duration_ms']}ms (code {remote_check['exit_code']})")

        # 2. JIT Execution
        print("  - Local JIT Run...", end="", flush=True)
        local_run = run_local([LOCAL_AGAMC, "run", rel_path])
        print(f" {local_run['duration_ms']}ms (code {local_run['exit_code']})")

        remote_run = None
        parity = None
        if client:
            print("  - Remote Intel JIT Run (low-priority)...", end="", flush=True)
            remote_run = run_remote_silent(client, rel_path, mode="run")
            print(f" {remote_run['duration_ms']}ms (code {remote_run['exit_code']})")
            parity = (local_run['stdout'] == remote_run['stdout']) and (local_run['exit_code'] == remote_run['exit_code'] == 0)
            print(f"  * PARITY: {'MATCH (OK)' if parity else 'MISMATCH / ERROR'}")

        results.append({
            "name": name,
            "category": cat,
            "path": rel_path,
            "local_check_ms": local_check['duration_ms'],
            "remote_check_ms": remote_check['duration_ms'] if remote_check else None,
            "local_run_ms": local_run['duration_ms'],
            "remote_run_ms": remote_run['duration_ms'] if remote_run else None,
            "local_stdout": local_run['stdout'],
            "remote_stdout": remote_run['stdout'] if remote_run else None,
            "parity": parity
        })

    if client:
        # Final cleanup: ensure temporary files or caches stay lean
        try:
            stdin, stdout, stderr = client.exec_command(f'powershell -NoProfile -Command "Get-ChildItem -Path {REMOTE_ROOT} -Filter *.tmp | Remove-Item -Force"')
            stdin.close()
            stdout.channel.recv_exit_status()
        except Exception:
            pass
        client.close()

    out_file = "benchmarks/results/remote_intel_node_matrix.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("SUMMARY RESULTS TABLE")
    print("=" * 70)
    remote_col = "Remote (Intel)" if client else "Remote (Offline)"
    print(f"{'Benchmark':<24} | {'Local (AMD)':<12} | {remote_col:<16} | {'Parity':<8}")
    print("-" * 70)
    for r in results:
        p_str = "PASS" if r['parity'] else ("SKIP" if r['parity'] is None else "FAIL")
        rem_ms = f"{r['remote_run_ms']:>10.1f} ms" if r['remote_run_ms'] is not None else "     N/A     "
        print(f"{r['name']:<24} | {r['local_run_ms']:>8.1f} ms  | {rem_ms} | {p_str:<8}")
    print("=" * 70)
    print(f"Results saved to {out_file}")

if __name__ == '__main__':
    main()
