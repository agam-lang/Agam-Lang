#!/usr/bin/env python3
"""Comprehensive Benchmark: Windows 11 vs. WSL Ubuntu across @lang.base vs @lang.advance."""

import os
import subprocess
import time
import statistics
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIN_AGAMC = ROOT / "agam" / "target" / "release" / "agamc.exe"
WSL_AGAMC = "/home/ksvikash236/target_linux/release/agamc"

WORKLOADS = [
    ("fibonacci", "01_algorithms"),
    ("quicksort", "01_algorithms"),
    ("prime_sieve", "01_algorithms"),
    ("binary_search", "01_algorithms"),
    ("edit_distance", "01_algorithms"),
    ("dot_product", "13_simd_vectorization"),
    ("matrix_multiply", "13_simd_vectorization"),
    ("mandelbrot_set", "13_simd_vectorization"),
    ("nbody_simulation", "13_simd_vectorization"),
    ("image_blur", "13_simd_vectorization"),
]

def run_cmd(cmd, timeout=30):
    start = time.perf_counter()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, res.stdout.strip(), res.stderr.strip(), res.returncode

def parse_bench_time(stdout):
    bench_lines = [l for l in stdout.splitlines() if l.startswith("bench ")]
    if not bench_lines:
        return None
    parts = bench_lines[-1].split(":")
    if len(parts) >= 2:
        ns_str = parts[1].strip().split()[0]
        try:
            return float(ns_str) / 1_000_000.0
        except Exception:
            return None
    return None

def benchmark_win_jit(file_path):
    _, out, _, rc = run_cmd([str(WIN_AGAMC), "bench", str(file_path)])
    return parse_bench_time(out) if rc == 0 else None

def benchmark_wsl_jit(file_path):
    wsl_file = str(file_path).replace('\\', '/').replace('C:', '/mnt/c').replace('c:', '/mnt/c')
    cmd = ["wsl", WSL_AGAMC, "bench", wsl_file]
    _, out, _, rc = run_cmd(cmd)
    return parse_bench_time(out) if rc == 0 else None

def create_profile_temp(orig_file, profile_tag):
    content = orig_file.read_text(encoding="utf-8")
    lines = content.splitlines()
    if lines and lines[0].startswith("@lang."):
        lines[0] = profile_tag
    else:
        lines.insert(0, profile_tag)
    
    tmp = tempfile.NamedTemporaryFile(suffix=".agam", delete=False, mode="w", encoding="utf-8")
    tmp.write("\n".join(lines))
    tmp.close()
    return Path(tmp.name)

def main():
    print("=" * 115)
    print("LIVE REAL-TIME BENCHMARKS: WINDOWS 11 vs. WSL UBUNTU across @lang.base vs. @lang.advance")
    print("=" * 115)
    print(f"{'Workload':<18} | {'Win11 (@base)':<15} | {'Win11 (@adv)':<15} | {'WSL2 (@base)':<15} | {'WSL2 (@adv)':<15} | {'Win vs WSL'}")
    print("-" * 115)

    for name, suite in WORKLOADS:
        agm_file = ROOT / "benchmarks" / "suites" / suite / f"{name}.agam"
        if not agm_file.exists():
            continue

        base_tmp = create_profile_temp(agm_file, "@lang.base")
        adv_tmp = create_profile_temp(agm_file, "@lang.advance")

        try:
            t_win_base = benchmark_win_jit(base_tmp)
            t_win_adv = benchmark_win_jit(adv_tmp)
            t_wsl_base = benchmark_wsl_jit(base_tmp)
            t_wsl_adv = benchmark_wsl_jit(adv_tmp)

            s_wb = f"{t_win_base:.2f} ms" if t_win_base is not None else "ERR"
            s_wa = f"{t_win_adv:.2f} ms" if t_win_adv is not None else "ERR"
            s_lb = f"{t_wsl_base:.2f} ms" if t_wsl_base is not None else "ERR"
            s_la = f"{t_wsl_adv:.2f} ms" if t_wsl_adv is not None else "ERR"

            ratio = f"{t_win_adv/t_wsl_adv:.2f}x" if (t_win_adv and t_wsl_adv) else "—"

            print(f"{name:<18} | {s_wb:<15} | {s_wa:<15} | {s_lb:<15} | {s_la:<15} | {ratio}")
        finally:
            if base_tmp.exists(): base_tmp.unlink()
            if adv_tmp.exists(): adv_tmp.unlink()

    print("=" * 115)

if __name__ == "__main__":
    main()
