#!/usr/bin/env python3
"""Run complete multi-compiler performance benchmark across all workloads in WSL2 Ubuntu."""

import os
import subprocess
import time
from pathlib import Path

ROOT = Path("/mnt/c/Users/ksvik/Projects/Agam-Lang")
WSL_AGAMC = "/home/ksvikash236/target_linux/release/agamc"

WORKLOADS = [
    ("fibonacci", "01_algorithms"),
    ("binary_search", "01_algorithms"),
    ("quicksort", "01_algorithms"),
    ("prime_sieve", "01_algorithms"),
    ("edit_distance", "01_algorithms"),
    ("dot_product", "13_simd_vectorization"),
    ("matrix_multiply", "13_simd_vectorization"),
    ("image_blur", "13_simd_vectorization"),
    ("mandelbrot_set", "13_simd_vectorization"),
    ("nbody_simulation", "13_simd_vectorization"),
    ("liquid_dsp_filter", "02_numerical_computation"),
    ("valkey_kv_store", "03_data_structures"),
    ("ocudu_5g_phy", "06_gpu_compute"),
    ("webp_encode", "08_media_encoding_kernels"),
    ("graphics_magick", "08_media_encoding_kernels"),
    ("flac_audio_encode", "08_media_encoding_kernels"),
    ("video_kvazaar", "08_media_encoding_kernels"),
    ("c_ray_4k", "11_ray_tracing"),
]

def time_binary(bin_path, runs=10):
    timings = []
    # Warmup
    subprocess.run([str(bin_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(runs):
        t0 = time.perf_counter()
        subprocess.run([str(bin_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        timings.append((time.perf_counter() - t0) * 1000.0)
    return min(timings)

def parse_agam_bench(stdout):
    for line in stdout.splitlines():
        if line.startswith("bench "):
            parts = line.split(":")
            if len(parts) >= 2:
                ns_val = parts[1].strip().split()[0]
                return float(ns_val) / 1_000_000.0
    return None

def main():
    print("=" * 115)
    print("COMPLETE 6-COMPILER BENCHMARK MATRIX (MEASURED NATIVELY IN LINUX)")
    print("=" * 115)
    print(f"{'Workload':<20} | {'Agam JIT':<12} | {'Agam AOT':<12} | {'GCC 15 -O3':<12} | {'Clang++ 21':<12} | {'Rustc -O':<12} | {'Python 3.14'}")
    print("-" * 115)

    for name, suite in WORKLOADS:
        src_agm = ROOT / "benchmarks" / "suites" / suite / f"{name}.agam"
        src_cpp = ROOT / "benchmarks" / "suites" / suite / "comparisons" / f"{name}.cpp"
        src_rs = ROOT / "benchmarks" / "suites" / suite / "comparisons" / f"{name}.rs"
        src_py = ROOT / "benchmarks" / "suites" / suite / "comparisons" / f"{name}.py"

        # 1. Agam JIT
        t_jit = None
        if src_agm.exists():
            res = subprocess.run([WSL_AGAMC, "bench", str(src_agm)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                t_jit = parse_agam_bench(res.stdout)

        # 2. Agam LLVM AOT
        t_aot = None
        temp_aot_out = f"/tmp/agam_aot_{name}.out"
        res_build = subprocess.run([WSL_AGAMC, "build", str(src_agm), "--backend", "llvm", "-O", "3", "-o", temp_aot_out], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res_build.returncode == 0:
            t_aot = time_binary(temp_aot_out)

        # 3. GCC 15 -O3
        t_gcc = None
        if src_cpp.exists():
            temp_gcc_out = f"/tmp/gcc_{name}.out"
            res_gcc = subprocess.run(["g++", "-O3", "-std=c++20", str(src_cpp), "-o", temp_gcc_out], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res_gcc.returncode == 0:
                t_gcc = time_binary(temp_gcc_out)

        # 4. Clang++ 21 -O3
        t_clang = None
        if src_cpp.exists():
            temp_clang_out = f"/tmp/clang_{name}.out"
            res_clang = subprocess.run(["clang++", "-O3", "-std=c++20", str(src_cpp), "-o", temp_clang_out], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res_clang.returncode == 0:
                t_clang = time_binary(temp_clang_out)

        # 5. Rustc -O
        t_rust = None
        if src_rs.exists():
            temp_rs_out = f"/tmp/rust_{name}.out"
            res_rs = subprocess.run(["rustc", "-O", str(src_rs), "-o", temp_rs_out], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res_rs.returncode == 0:
                t_rust = time_binary(temp_rs_out)

        # 6. Python 3.14
        t_py = None
        if src_py.exists():
            timings_py = []
            subprocess.run(["python3", str(src_py)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for _ in range(5):
                t0 = time.perf_counter()
                subprocess.run(["python3", str(src_py)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                timings_py.append((time.perf_counter() - t0) * 1000.0)
            t_py = min(timings_py)

        s_jit = f"{t_jit:.2f} ms" if t_jit is not None else "—"
        s_aot = f"{t_aot:.2f} ms" if t_aot is not None else "—"
        s_gcc = f"{t_gcc:.2f} ms" if t_gcc is not None else "—"
        s_clang = f"{t_clang:.2f} ms" if t_clang is not None else "—"
        s_rust = f"{t_rust:.2f} ms" if t_rust is not None else "—"
        s_py = f"{t_py:.2f} ms" if t_py is not None else "—"

        print(f"{name:<20} | {s_jit:<12} | {s_aot:<12} | {s_gcc:<12} | {s_clang:<12} | {s_rust:<12} | {s_py}")

    print("=" * 115)

if __name__ == "__main__":
    main()
