import os
import sys
import time
import json
import subprocess
import paramiko

REMOTE_HOST = "192.168.0.150"
REMOTE_USER = "Main_Guest"
REMOTE_PASS = "56341236"
REMOTE_ROOT = "C:/Users/Main_Guest/Agam-Node"
REMOTE_PYTHON = f"{REMOTE_ROOT}/python/python.exe"
REMOTE_AGAMC = f"{REMOTE_ROOT}/agamc.exe"

LOCAL_ROOT = os.path.abspath(".")
LOCAL_AGAMC = os.path.join(LOCAL_ROOT, "agam", "target", "release", "agamc.exe")
LOCAL_PYTHON = sys.executable

BENCHMARKS = [
    {
        "name": "Recursive Fibonacci (fib 32)",
        "domain": "Stack recursion & branch prediction",
        "py_rel": "benchmarks/suites/01_algorithms/comparisons/fibonacci.py",
        "agam_rel": "benchmarks/suites/01_algorithms/fibonacci.agam",
        "iterations": 3
    },
    {
        "name": "Prime Sieve (limit 25000)",
        "domain": "Tight loop & integer divisibility",
        "py_rel": "benchmarks/suites/01_algorithms/comparisons/prime_sieve.py",
        "agam_rel": "benchmarks/suites/01_algorithms/prime_sieve.agam",
        "iterations": 3
    },
    {
        "name": "Monte Carlo Pi (500k samples)",
        "domain": "Pseudo-random & arithmetic throughput",
        "py_rel": "benchmarks/suites/02_numerical_computation/comparisons/monte_carlo_pi.py",
        "agam_rel": "benchmarks/suites/02_numerical_computation/monte_carlo_pi.agam",
        "iterations": 3
    },
    {
        "name": "Quicksort Partition (10k items)",
        "domain": "Array indexing & memory comparison",
        "py_rel": "benchmarks/suites/01_algorithms/comparisons/quicksort.py",
        "agam_rel": "benchmarks/suites/01_algorithms/quicksort.agam",
        "iterations": 3
    }
]

def run_local(cmd):
    start = time.perf_counter()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
    dur = (time.perf_counter() - start) * 1000.0
    return dur, res.stdout.strip(), res.returncode

def run_remote(client, cmd):
    start = time.perf_counter()
    stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
    stdin.close()
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace").strip()
    dur = (time.perf_counter() - start) * 1000.0
    return dur, out, code

def benchmark_series(fn, runs):
    times = []
    out = ""
    for _ in range(runs):
        dur, o, code = fn()
        times.append(dur)
        out = o
    times.sort()
    return times[0], out # Best / minimum time to eliminate jitter

def main():
    print("=" * 80)
    print("EMPIRICAL CPU PERFORMANCE COMPARISON: AMD RYZEN 7 vs INTEL CORE i5")
    print(f"Host CPU   : AMD Ryzen 7 7840HS (Zen 4, 8C/16T, 16MB L3, up to 5.1 GHz)")
    print(f"Remote CPU : Intel Core i5-10310U (Comet Lake, 4C/8T, 6MB L3, up to 4.4 GHz)")
    print("=" * 80)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key_file = os.path.expanduser("~/.ssh/id_ed25519")
    print("Connecting to Intel Dell node...", end="", flush=True)
    client.connect(
        REMOTE_HOST,
        username=REMOTE_USER,
        key_filename=key_file,
        allow_agent=False,
        look_for_keys=False,
        timeout=5.0
    )
    print(" [CONNECTED]\n")

    report = []

    for b in BENCHMARKS:
        name = b["name"]
        runs = b["iterations"]
        py_rel = b["py_rel"]
        agam_rel = b["agam_rel"]

        print(f"---> Benchmarking: {name} (Domain: {b['domain']})")

        # 1. Python on AMD (Local)
        py_amd_time, py_amd_out = benchmark_series(
            lambda: run_local([LOCAL_PYTHON, py_rel]), runs
        )
        print(f"  * Python on AMD Ryzen : {py_amd_time:>8.1f} ms  (out: {py_amd_out})")

        # 2. Python on Intel (Remote)
        remote_py_cmd = f'powershell -NoProfile -Command "[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = \\\"BelowNormal\\\"; & {REMOTE_PYTHON} {REMOTE_ROOT}/{py_rel}"'
        py_intel_time, py_intel_out = benchmark_series(
            lambda: run_remote(client, remote_py_cmd), runs
        )
        print(f"  * Python on Intel i5  : {py_intel_time:>8.1f} ms  (out: {py_intel_out})")

        # 3. Agam on AMD (Local)
        agam_amd_time, agam_amd_out = benchmark_series(
            lambda: run_local([LOCAL_AGAMC, "run", agam_rel]), runs
        )
        print(f"  * Agam on AMD Ryzen   : {agam_amd_time:>8.1f} ms  (out: {agam_amd_out})")

        # 4. Agam on Intel (Remote)
        remote_agam_rel = agam_rel.replace('/', '\\')
        remote_agam_cmd = f'powershell -NoProfile -Command "[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = \\\"BelowNormal\\\"; Set-Location {REMOTE_ROOT}; .\\agamc.exe run {remote_agam_rel}"'
        agam_intel_time, agam_intel_out = benchmark_series(
            lambda: run_remote(client, remote_agam_cmd), runs
        )
        print(f"  * Agam on Intel i5    : {agam_intel_time:>8.1f} ms  (out: {agam_intel_out})")

        # Parity check
        py_parity = (py_amd_out == py_intel_out)
        agam_parity = (agam_amd_out == agam_intel_out)

        # Ratios
        py_speedup_amd_vs_intel = py_intel_time / py_amd_time if py_amd_time > 0 else 0
        agam_speedup_amd_vs_intel = agam_intel_time / agam_amd_time if agam_amd_time > 0 else 0
        agam_vs_py_amd = py_amd_time / agam_amd_time if agam_amd_time > 0 else 0
        agam_vs_py_intel = py_intel_time / agam_intel_time if agam_intel_time > 0 else 0

        print(f"  -> AMD Advantage in Python : {py_speedup_amd_vs_intel:.2f}x faster than Intel")
        print(f"  -> AMD Advantage in Agam   : {agam_speedup_amd_vs_intel:.2f}x faster than Intel")
        print(f"  -> Agam vs Python on AMD   : {agam_vs_py_amd:.2f}x faster than Python")
        print(f"  -> Agam vs Python on Intel : {agam_vs_py_intel:.2f}x faster than Python\n")

        report.append({
            "name": name,
            "py_amd_ms": round(py_amd_time, 1),
            "py_intel_ms": round(py_intel_time, 1),
            "py_amd_speedup": round(py_speedup_amd_vs_intel, 2),
            "agam_amd_ms": round(agam_amd_time, 1),
            "agam_intel_ms": round(agam_intel_time, 1),
            "agam_amd_speedup": round(agam_speedup_amd_vs_intel, 2),
            "agam_vs_py_amd": round(agam_vs_py_amd, 2),
            "agam_vs_py_intel": round(agam_vs_py_intel, 2)
        })

    client.close()

    out_file = "benchmarks/results/cpu_perf_comparison_amd_vs_intel.json"
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    print("=" * 80)
    print("FINAL CPU PERFORMANCE MATRIX SUMMARY")
    print("=" * 80)
    print(f"{'Benchmark':<30} | {'Py (AMD)':<9} | {'Py (Intel)':<10} | {'Py Diff':<8} | {'Agam(AMD)':<9} | {'Agam(Intel)':<11} | {'Agam Diff':<9}")
    print("-" * 80)
    for r in report:
        print(f"{r['name']:<30} | {r['py_amd_ms']:>6.1f} ms | {r['py_intel_ms']:>7.1f} ms  | {r['py_amd_speedup']:>5.2f}x  | {r['agam_amd_ms']:>6.1f} ms | {r['agam_intel_ms']:>8.1f} ms   | {r['agam_amd_speedup']:>6.2f}x")
    print("=" * 80)
    print(f"Detailed JSON results saved to: {out_file}")

if __name__ == '__main__':
    main()
