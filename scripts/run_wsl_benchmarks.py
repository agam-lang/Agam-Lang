#!/usr/bin/env python3
"""Run real-time benchmarks in WSL Ubuntu comparing Clang++ -O3, GCC -O3, Rust -O, and Agam JIT."""

import os
import subprocess
import time
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGAM_BIN = ROOT / "agam" / "target" / "release" / "agamc.exe"

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
    ("fft", "02_numerical_computation"),
    ("monte_carlo_pi", "02_numerical_computation"),
    ("polynomial_eval", "02_numerical_computation"),
    ("btree_operations", "03_data_structures"),
    ("hashmap_operations", "03_data_structures"),
    ("audio_lpc", "08_media_encoding_kernels"),
    ("pixel_filter", "08_media_encoding_kernels"),
    ("ray_sphere_intersect", "11_ray_tracing"),
    ("zbuffer_rasterize", "11_ray_tracing"),
]

def run_cmd(cmd, timeout=30):
    start = time.perf_counter()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, res.stdout.strip(), res.stderr.strip(), res.returncode

def benchmark_wsl_compiler(compiler_cmd, cpp_file, runs=5):
    # Convert windows path to wsl path
    wsl_path = str(cpp_file).replace('\\', '/').replace('C:', '/mnt/c').replace('c:', '/mnt/c')
    
    # 1. Compile in WSL
    bin_name = f"/tmp/bench_{compiler_cmd}.out"
    compile_bash = f"{compiler_cmd} -O3 -std=c++20 '{wsl_path}' -o {bin_name}"
    c_time, _, c_err, c_rc = run_cmd(["wsl", "bash", "-c", compile_bash])
    if c_rc != 0:
        return None, f"Compile error: {c_err}"
        
    # 2. Run in WSL
    timings = []
    for _ in range(runs):
        t, out, _, rc = run_cmd(["wsl", "bash", "-c", bin_name])
        if rc == 0:
            timings.append(t)
            
    run_cmd(["wsl", "bash", "-c", f"rm -f {bin_name}"])
    return statistics.median(timings) if timings else None, None

def benchmark_agam(agm_file):
    cmd = [str(AGAM_BIN), "bench", str(agm_file)]
    _, stdout, stderr, rc = run_cmd(cmd)
    if rc != 0:
        return None, f"Agam error: {stderr}"
    
    bench_lines = [l for l in stdout.splitlines() if l.startswith("bench ")]
    if not bench_lines:
        return None, "No bench output"
    
    parts = bench_lines[-1].split(":")
    if len(parts) >= 2:
        ns_str = parts[1].strip().split()[0]
        try:
            return float(ns_str) / 1_000_000.0, None
        except Exception as e:
            return None, str(e)
    return None, "Parse failed"

def main():
    print("=" * 100)
    print("LIVE REAL-TIME BENCHMARKS: AGAM vs. CLANG++ 21 (-O3) vs. GCC 15 (-O3) in WSL UBUNTU")
    print("=" * 100)
    print(f"{'Workload':<22} | {'Agam JIT':<12} | {'Clang++ -O3':<14} | {'GCC -O3':<14} | {'Agam vs Clang':<14}")
    print("-" * 100)

    for name, suite in WORKLOADS:
        agm_file = ROOT / "benchmarks" / "suites" / suite / f"{name}.agam"
        cpp_file = ROOT / "benchmarks" / "suites" / suite / "comparisons" / f"{name}.cpp"

        t_agam, err_ag = benchmark_agam(agm_file) if agm_file.exists() else (None, "Missing")
        t_clang, err_cl = benchmark_wsl_compiler("clang++", cpp_file) if cpp_file.exists() else (None, "Missing")
        t_gcc, err_gc = benchmark_wsl_compiler("g++", cpp_file) if cpp_file.exists() else (None, "Missing")

        s_agam = f"{t_agam:.2f} ms" if t_agam is not None else "ERR"
        s_clang = f"{t_clang:.2f} ms" if t_clang is not None else "ERR"
        s_gcc = f"{t_gcc:.2f} ms" if t_gcc is not None else "ERR"

        vs_clang = f"{t_clang/t_agam:.2f}x" if (t_agam and t_clang and t_agam > 0) else "—"

        print(f"{name:<22} | {s_agam:<12} | {s_clang:<14} | {s_gcc:<14} | {vs_clang:<14}")

    print("=" * 100)

if __name__ == "__main__":
    main()
