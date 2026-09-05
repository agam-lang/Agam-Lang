#!/usr/bin/env python3
"""Run real-time benchmarks directly INSIDE WSL Linux measuring Clang++ -O3 vs GCC -O3 vs Python 3."""

import os
import subprocess
import time
import statistics
from pathlib import Path

ROOT = Path("/mnt/c/Users/ksvik/Projects/Agam-Lang")

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

def benchmark_native_compiler(compiler_bin, cpp_file, runs=5):
    out_bin = f"/tmp/bench_{compiler_bin}.out"
    if os.path.exists(out_bin):
        os.remove(out_bin)
        
    compile_cmd = [compiler_bin, "-O3", "-std=c++20", str(cpp_file), "-o", out_bin]
    _, _, c_err, c_rc = run_cmd(compile_cmd)
    if c_rc != 0:
        return None, f"Compile error: {c_err}"
        
    timings = []
    for _ in range(runs):
        t, _, _, rc = run_cmd([out_bin])
        if rc == 0:
            timings.append(t)
            
    if os.path.exists(out_bin):
        os.remove(out_bin)
    return statistics.median(timings) if timings else None, None

def main():
    print("=" * 100)
    print("DIRECT INSIDE WSL UBUNTU: CLANG++ 21 (-O3) vs. GCC 15 (-O3) (ZERO VM BRIDGE OVERHEAD)")
    print("=" * 100)
    print(f"{'Workload':<24} | {'Clang++ -O3':<16} | {'GCC -O3':<16} | {'Clang vs GCC':<16}")
    print("-" * 100)

    for name, suite in WORKLOADS:
        cpp_file = ROOT / "benchmarks" / "suites" / suite / "comparisons" / f"{name}.cpp"

        t_clang, err_cl = benchmark_native_compiler("clang++", cpp_file) if cpp_file.exists() else (None, "Missing")
        t_gcc, err_gc = benchmark_native_compiler("g++", cpp_file) if cpp_file.exists() else (None, "Missing")

        s_clang = f"{t_clang:.2f} ms" if t_clang is not None else ("ERR" if err_cl else "N/A")
        s_gcc = f"{t_gcc:.2f} ms" if t_gcc is not None else ("ERR" if err_gc else "N/A")

        vs = f"{t_gcc/t_clang:.2f}x" if (t_clang and t_gcc and t_clang > 0) else "—"

        print(f"{name:<24} | {s_clang:<16} | {s_gcc:<16} | {vs:<16}")

    print("=" * 100)

if __name__ == "__main__":
    main()
