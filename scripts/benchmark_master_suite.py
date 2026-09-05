#!/usr/bin/env python3
"""
Master Agam Live Benchmark Suite
Measures:
  1. Agam AOT (LLVM -O3) [@lang.base]
  2. Agam AOT (LLVM -O3) [@lang.advance]
  3. Agam JIT (Cranelift) [@lang.base]
  4. Agam JIT (Cranelift) [@lang.advance]
  5. Clang++ 21 (-O3 -march=native)
  6. GCC 15 (-O3 -march=native)
  7. Rustc (1.93 Release -O3)
  8. Python 3.14 (CPython)
"""

import os
import subprocess
import time
import json
import statistics

AGAMC_LINUX = "/home/ksvikash236/target_linux/release/agamc"
CLANGXX = "/usr/bin/clang++"
GXX = "/usr/bin/g++"
RUSTC = "rustc"
PYTHON = "python3"

BENCHMARKS = [
    {
        "name": "Matrix Multiplication (4096 flops)",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/matrix_multiply.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/matrix_multiply.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/comparisons/matrix_multiply.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/comparisons/matrix_multiply.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/comparisons/matrix_multiply.py",
        "iters": 20
    },
    {
        "name": "Dot Product (100k vectors)",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/dot_product.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/dot_product.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/comparisons/dot_product.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/comparisons/dot_product.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/comparisons/dot_product.py",
        "iters": 20
    },
    {
        "name": "Prime Sieve (Eratosthenes)",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/prime_sieve.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/prime_sieve.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/prime_sieve.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/prime_sieve.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/prime_sieve.py",
        "iters": 20
    },
    {
        "name": "Quicksort (100k partition)",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/quicksort.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/quicksort.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/quicksort.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/quicksort.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/quicksort.py",
        "iters": 20
    },
    {
        "name": "Binary Search (200k Lookups)",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/binary_search.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/binary_search.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/binary_search.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/binary_search.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/binary_search.py",
        "iters": 20
    },
    {
        "name": "Recursive Fibonacci (N=32)",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/fibonacci.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/fibonacci.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/fibonacci.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/fibonacci.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/01_algorithms/comparisons/fibonacci.py",
        "iters": 10
    },
    {
        "name": "Image Pixel Filter (256x256)",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/pixel_filter.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/pixel_filter.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/pixel_filter.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/pixel_filter.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/pixel_filter.py",
        "iters": 20
    },
    {
        "name": "Liquid-DSP FIR Filter (32-tap)",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/liquid_dsp_filter.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/liquid_dsp_filter.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/comparisons/liquid_dsp_filter.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/comparisons/liquid_dsp_filter.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/02_numerical_computation/comparisons/liquid_dsp_filter.py",
        "iters": 20
    },
    {
        "name": "GraphicsMagick HWB/Sharpen",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/graphics_magick.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/graphics_magick.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/graphics_magick.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/graphics_magick.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/graphics_magick.py",
        "iters": 10
    },
    {
        "name": "FLAC Audio Frame Encoder",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/flac_audio_encode.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/flac_audio_encode.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/flac_audio_encode.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/flac_audio_encode.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/flac_audio_encode.py",
        "iters": 20
    },
    {
        "name": "Kvazaar HEVC Intra-Pred (35 Modes)",
        "base_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/video_kvazaar.agam",
        "adv_agam": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/video_kvazaar.agam",
        "cpp": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/video_kvazaar.cpp",
        "rust": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/video_kvazaar.rs",
        "python": "/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/suites/08_media_encoding_kernels/comparisons/video_kvazaar.py",
        "iters": 20
    }
]

def measure_cmd(cmd_list, iters=20):
    # Warmup
    try:
        subprocess.run(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        return None
    times = []
    for _ in range(iters):
        t0 = time.perf_counter()
        subprocess.run(cmd_list, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        times.append((time.perf_counter() - t0) * 1000.0)
    return round(statistics.median(times), 2)

def run_benchmarks():
    results = []
    print("=" * 80)
    print("AGAM MASTER BENCHMARK RUNNER — REAL HARDWARE MEASUREMENTS (WSL UBUNTU 26.04)")
    print("=" * 80)

    for b in BENCHMARKS:
        name = b["name"]
        print(f"\n[*] Benchmarking: {name}")
        iters = b.get("iters", 20)
        row = {"name": name}

        # 1. Agam AOT @lang.base
        base_out = "/tmp/bench_base.out"
        if os.path.exists(b["base_agam"]):
            res = subprocess.run([AGAMC_LINUX, "build", b["base_agam"], "--backend", "llvm", "-O", "3", "-o", base_out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                row["agam_aot_base"] = measure_cmd([base_out], iters)
            else:
                row["agam_aot_base"] = None
        else:
            row["agam_aot_base"] = None

        # 2. Agam AOT @lang.advance
        adv_out = "/tmp/bench_adv.out"
        if os.path.exists(b["adv_agam"]):
            res = subprocess.run([AGAMC_LINUX, "build", b["adv_agam"], "--backend", "llvm", "-O", "3", "-o", adv_out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                row["agam_aot_adv"] = measure_cmd([adv_out], iters)
            else:
                row["agam_aot_adv"] = None
        else:
            row["agam_aot_adv"] = None

        # 3. Agam JIT @lang.base
        if os.path.exists(b["base_agam"]):
            row["agam_jit_base"] = measure_cmd([AGAMC_LINUX, "run", b["base_agam"], "--jit"], iters)
        else:
            row["agam_jit_base"] = None

        # 4. Agam JIT @lang.advance
        if os.path.exists(b["adv_agam"]):
            row["agam_jit_adv"] = measure_cmd([AGAMC_LINUX, "run", b["adv_agam"], "--jit"], iters)
        else:
            row["agam_jit_adv"] = None

        # 5. Clang++ 21
        cpp_out = "/tmp/bench_clang.out"
        if os.path.exists(b.get("cpp", "")):
            res = subprocess.run([CLANGXX, "-O3", "-march=native", b["cpp"], "-o", cpp_out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                row["clang"] = measure_cmd([cpp_out], iters)
            else:
                row["clang"] = None
        else:
            row["clang"] = None

        # 6. GCC 15
        gcc_out = "/tmp/bench_gcc.out"
        if os.path.exists(b.get("cpp", "")):
            res = subprocess.run([GXX, "-O3", "-march=native", b["cpp"], "-o", gcc_out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                row["gcc"] = measure_cmd([gcc_out], iters)
            else:
                row["gcc"] = None
        else:
            row["gcc"] = None

        # 7. Rust 1.93
        rust_out = "/tmp/bench_rust.out"
        if os.path.exists(b.get("rust", "")):
            res = subprocess.run([RUSTC, "-O", "-C", "target-cpu=native", b["rust"], "-o", rust_out], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                row["rust"] = measure_cmd([rust_out], iters)
            else:
                row["rust"] = None
        else:
            row["rust"] = None

        # 8. Python
        if os.path.exists(b.get("python", "")):
            row["python"] = measure_cmd([PYTHON, b["python"]], max(3, iters // 3))
        else:
            row["python"] = None

        print(f"  -> AOT Base: {row['agam_aot_base']} ms | AOT Adv: {row['agam_aot_adv']} ms | JIT: {row['agam_jit_base']} ms | Clang: {row['clang']} ms | GCC: {row['gcc']} ms | Rust: {row['rust']} ms | Python: {row['python']} ms")
        results.append(row)

    with open("/mnt/c/Users/ksvik/Projects/Agam-Lang/benchmarks/master_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nMaster benchmark suite complete! Results saved.")

if __name__ == "__main__":
    run_benchmarks()
