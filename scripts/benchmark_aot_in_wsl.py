#!/usr/bin/env python3
"""Comprehensive in-Linux benchmark comparing Agam AOT vs JIT across @lang.base and @lang.advance vs Clang++ 21 vs GCC 15 vs Rustc vs CPython."""

import os
import re
import subprocess
import time
import statistics
from pathlib import Path

ROOT = Path("/mnt/c/Users/ksvik/Projects/Agam-Lang")
AGAMC_BIN = "/home/ksvikash236/target_linux/release/agamc"

WORKLOADS = [
    ("dot_product", "13_simd_vectorization", 10),
    ("binary_search", "01_algorithms", 10),
    ("quicksort", "01_algorithms", 10),
    ("prime_sieve", "01_algorithms", 10),
    ("matrix_multiply", "02_numerical_computation", 7),
    ("image_blur", "13_simd_vectorization", 7),
    ("fibonacci", "01_algorithms", 7),
    ("webp_encode", "08_media_encoding_kernels", 10),
    ("video_kvazaar", "08_media_encoding_kernels", 10),
    ("c_ray_4k", "11_ray_tracing", 10),
    ("liquid_dsp_filter", "02_numerical_computation", 10),
]

def run_cmd(cmd, cwd=None):
    t0 = time.perf_counter()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return elapsed_ms, res.stdout.strip(), res.stderr.strip(), res.returncode

def get_jit_bench_ms(agam_path):
    _, stdout, _, rc = run_cmd([AGAMC_BIN, "bench", str(agam_path)])
    if rc != 0:
        return None
    m = re.search(r"median:\s*([0-9\.]+)\s*ns", stdout)
    if m:
        return float(m.group(1)) / 1_000_000.0
    m = re.search(r":\s*([0-9\.]+)\s*ns/iter", stdout)
    if m:
        return float(m.group(1)) / 1_000_000.0
    return None

def is_executable(path):
    return os.path.exists(path) and os.access(path, os.X_OK) and not os.path.isdir(path)

def main():
    print("=" * 140)
    print("LIVE HIGH-PERFORMANCE BENCHMARK MATRIX: AGAM (AOT vs JIT / BASE vs ADVANCE) vs CLANG++ vs GCC vs RUST vs PYTHON")
    print("=" * 140)
    header = f"{'Workload':<18} | {'Agam AOT(Adv)':<14} | {'Agam AOT(Base)':<14} | {'Agam JIT (Kernel)':<18} | {'Clang++ 21':<11} | {'GCC 15':<10} | {'Rustc':<10} | {'CPython':<10}"
    print(header)
    print("-" * 140)

    for name, suite, iters in WORKLOADS:
        agam_src = ROOT / "benchmarks" / "suites" / suite / f"{name}.agam"
        cpp_src = ROOT / "benchmarks" / "suites" / suite / "comparisons" / f"{name}.cpp"
        rs_src = ROOT / "benchmarks" / "suites" / suite / "comparisons" / f"{name}.rs"
        py_src = ROOT / "benchmarks" / "suites" / suite / "comparisons" / f"{name}.py"

        if not agam_src.exists():
            continue

        # 1. Agam AOT (Advance / standard)
        aot_adv_bin = f"/tmp/agam_aot_adv_{name}"
        if os.path.exists(aot_adv_bin):
            os.remove(aot_adv_bin)
        run_cmd([AGAMC_BIN, "build", str(agam_src), "-o", aot_adv_bin, "-O", "3"])
        if os.path.exists(aot_adv_bin):
            os.chmod(aot_adv_bin, 0o755)

        # 2. Agam AOT (Base profile)
        with open(agam_src, "r") as f:
            src_code = f.read()
        base_src_path = f"/tmp/{name}_base.agam"
        with open(base_src_path, "w") as f:
            f.write("@lang.base\n" + src_code)
        aot_base_bin = f"/tmp/agam_aot_base_{name}"
        if os.path.exists(aot_base_bin):
            os.remove(aot_base_bin)
        run_cmd([AGAMC_BIN, "build", base_src_path, "-o", aot_base_bin, "-O", "3"])
        if os.path.exists(aot_base_bin):
            os.chmod(aot_base_bin, 0o755)

        # 3. JIT in-memory kernel time
        jit_ms = get_jit_bench_ms(agam_src)

        # 4. Clang++ 21
        clang_bin = f"/tmp/clang_{name}.out"
        if cpp_src.exists():
            subprocess.run(["clang++", "-O3", "-std=c++20", str(cpp_src), "-o", clang_bin], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(clang_bin): os.chmod(clang_bin, 0o755)

        # 5. GCC 15
        gcc_bin = f"/tmp/gcc_{name}.out"
        if cpp_src.exists():
            subprocess.run(["g++", "-O3", "-std=c++20", str(cpp_src), "-o", gcc_bin], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(gcc_bin): os.chmod(gcc_bin, 0o755)

        # 6. Rustc
        rs_bin = f"/tmp/rs_{name}.out"
        if rs_src.exists():
            subprocess.run(["rustc", "-O", str(rs_src), "-o", rs_bin], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(rs_bin): os.chmod(rs_bin, 0o755)

        # --- Measure Executables ---
        t_aot_adv = []
        if is_executable(aot_adv_bin):
            for _ in range(iters):
                t, _, _, rc = run_cmd([aot_adv_bin])
                if rc == 0: t_aot_adv.append(t)

        t_aot_base = []
        if is_executable(aot_base_bin):
            for _ in range(iters):
                t, _, _, rc = run_cmd([aot_base_bin])
                if rc == 0: t_aot_base.append(t)

        t_clang = []
        if is_executable(clang_bin):
            for _ in range(iters):
                t, _, _, rc = run_cmd([clang_bin])
                if rc == 0: t_clang.append(t)

        t_gcc = []
        if is_executable(gcc_bin):
            for _ in range(iters):
                t, _, _, rc = run_cmd([gcc_bin])
                if rc == 0: t_gcc.append(t)

        t_rs = []
        if is_executable(rs_bin):
            for _ in range(iters):
                t, _, _, rc = run_cmd([rs_bin])
                if rc == 0: t_rs.append(t)

        t_py = []
        if py_src.exists():
            for _ in range(max(3, iters // 2)):
                t, _, _, rc = run_cmd(["python3", str(py_src)])
                if rc == 0: t_py.append(t)

        def fmt(lst):
            return f"{statistics.median(lst):.2f} ms" if lst else "—"

        s_aot_adv = fmt(t_aot_adv)
        s_aot_base = fmt(t_aot_base)
        s_jit = f"{jit_ms:.2f} ms" if jit_ms is not None else "—"
        s_clang = fmt(t_clang)
        s_gcc = fmt(t_gcc)
        s_rs = fmt(t_rs)
        s_py = fmt(t_py)

        print(f"{name:<18} | {s_aot_adv:<14} | {s_aot_base:<14} | {s_jit:<18} | {s_clang:<11} | {s_gcc:<10} | {s_rs:<10} | {s_py:<10}")

    print("=" * 140)

if __name__ == "__main__":
    main()
