#!/usr/bin/env python3
"""
Raw, Unscaled, 100% Direct Execution Measurement:
Zero multipliers. Zero synthetic formulas.
Measures the exact wall-clock milliseconds to execute each compiled native binary on this laptop.
"""

import subprocess
import time
from pathlib import Path

ROOT = Path("/mnt/c/Users/ksvik/Projects/Agam-Lang")
AGAMC = Path("/home/ksvikash236/target_linux/release/agamc")

def measure_raw(name, bin_path, iters=10):
    durations = []
    # Warmup
    subprocess.run([str(bin_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for _ in range(iters):
        t0 = time.perf_counter()
        res = subprocess.run([str(bin_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        t1 = time.perf_counter()
        if res.returncode != 0:
            print(f"FAILED: {bin_path}")
            return
        durations.append((t1 - t0) * 1000.0) # Raw milliseconds
    
    avg_ms = sum(durations) / len(durations)
    min_ms = min(durations)
    max_ms = max(durations)
    return avg_ms, min_ms, max_ms, res.stdout.decode().strip()

def run_raw_suite():
    print("=" * 90)
    print("RAW UNTOUCHED WALL-CLOCK EXECUTION BENCHMARK (ZERO MULTIPLIERS)")
    print("Measurements in Milliseconds (ms) across 10 iterations on your CPU")
    print("=" * 90)

    suites = [
        ("FLAC Audio Kernel", "benchmarks/suites/08_media_encoding_kernels/real_flac_encoder.agam", "benchmarks/suites/08_media_encoding_kernels/comparisons/flac_audio_encode.cpp", "benchmarks/suites/08_media_encoding_kernels/comparisons/flac_audio_encode.rs"),
        ("Liquid-DSP Filter", "benchmarks/suites/02_numerical_computation/liquid_dsp_filter.agam", "benchmarks/suites/02_numerical_computation/comparisons/liquid_dsp_filter.cpp", "benchmarks/suites/02_numerical_computation/comparisons/liquid_dsp_filter.rs"),
        ("WebP Predictor", "benchmarks/suites/08_media_encoding_kernels/webp_encode.agam", "benchmarks/suites/08_media_encoding_kernels/comparisons/webp_encode.cpp", "benchmarks/suites/08_media_encoding_kernels/comparisons/webp_encode.rs"),
        ("GraphicsMagick HWB", "benchmarks/suites/08_media_encoding_kernels/real_image_processor.agam", "benchmarks/suites/08_media_encoding_kernels/comparisons/graphics_magick.cpp", "benchmarks/suites/08_media_encoding_kernels/comparisons/graphics_magick.rs"),
        ("Kvazaar Intra-Pred", "benchmarks/suites/08_media_encoding_kernels/video_kvazaar.agam", "benchmarks/suites/08_media_encoding_kernels/comparisons/video_kvazaar.cpp", "benchmarks/suites/08_media_encoding_kernels/comparisons/video_kvazaar.rs"),
    ]

    for title, agam_p, cpp_p, rs_p in suites:
        print(f"\n--- {title} ---")
        
        # 1. Agam LLVM AOT
        agam_out = f"/tmp/{title.lower().replace(' ', '_')}_agam.out"
        subprocess.run([str(AGAMC), "build", str(ROOT / agam_p), "--backend", "llvm", "-O", "3", "-o", agam_out], check=True, stdout=subprocess.DEVNULL)
        avg_a, min_a, max_a, out_a = measure_raw("Agam LLVM", agam_out)

        # 2. Clang++ 21
        clang_out = f"/tmp/{title.lower().replace(' ', '_')}_clang.out"
        subprocess.run(["clang++", "-O3", "-march=native", str(ROOT / cpp_p), "-o", clang_out], check=True)
        avg_c, min_c, max_c, out_c = measure_raw("Clang++ 21", clang_out)

        # 3. GCC 15
        gcc_out = f"/tmp/{title.lower().replace(' ', '_')}_gcc.out"
        subprocess.run(["g++", "-O3", "-march=native", str(ROOT / cpp_p), "-o", gcc_out], check=True)
        avg_g, min_g, max_g, out_g = measure_raw("GCC 15", gcc_out)

        # 4. Rustc 1.93
        rust_out = f"/tmp/{title.lower().replace(' ', '_')}_rust.out"
        subprocess.run(["rustc", "-C", "opt-level=3", "-C", "target-cpu=native", str(ROOT / rs_p), "-o", rust_out], check=True)
        avg_r, min_r, max_r, out_r = measure_raw("Rust 1.93", rust_out)

        print(f"  [Agam LLVM -O3] Avg: {avg_a:6.2f} ms | Min: {min_a:6.2f} ms | Max: {max_a:6.2f} ms | Stdout: {out_a}")
        print(f"  [Clang++ 21 -O3] Avg: {avg_c:6.2f} ms | Min: {min_c:6.2f} ms | Max: {max_c:6.2f} ms | Stdout: {out_c}")
        print(f"  [GCC 15 -O3]     Avg: {avg_g:6.2f} ms | Min: {min_g:6.2f} ms | Max: {max_g:6.2f} ms | Stdout: {out_g}")
        print(f"  [Rust 1.93 -O3]  Avg: {avg_r:6.2f} ms | Min: {min_r:6.2f} ms | Max: {max_r:6.2f} ms | Stdout: {out_r}")

    print("\n" + "=" * 90)

if __name__ == "__main__":
    run_raw_suite()
