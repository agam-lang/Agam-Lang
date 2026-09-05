#!/usr/bin/env python3
"""Benchmark Agam AOT (LLVM -O3) vs Agam JIT across @lang.base vs @lang.advance."""

import os
import subprocess
import time
import statistics
import tempfile
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
]

def run_cmd(cmd, timeout=30):
    start = time.perf_counter()
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return elapsed_ms, res.stdout.strip(), res.stderr.strip(), res.returncode

def benchmark_jit(source_file):
    cmd = [str(AGAM_BIN), "bench", str(source_file)]
    _, stdout, stderr, rc = run_cmd(cmd)
    if rc != 0:
        return None, f"JIT Error: {stderr}"
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

def benchmark_llvm_aot(source_file, runs=5):
    with tempfile.NamedTemporaryFile(suffix=".ll", delete=False) as f_ll:
        ll_path = Path(f_ll.name)
    
    # 1. Generate LLVM IR via agamc build
    cmd_ll = [str(AGAM_BIN), "build", str(source_file), "--backend", "llvm", "-O", "3", "-o", str(ll_path)]
    _, _, err_ll, rc_ll = run_cmd(cmd_ll)
    if rc_ll != 0 or not ll_path.exists():
        if ll_path.exists(): ll_path.unlink()
        return None, f"LLVM IR gen error: {err_ll}"

    # 2. Compile LLVM IR with clang -O3 in WSL
    wsl_ll = str(ll_path).replace('\\', '/').replace('C:', '/mnt/c').replace('c:', '/mnt/c')
    out_bin = f"/tmp/agam_aot_{os.getpid()}_{int(time.time()*1000)}.out"
    compile_bash = f"clang -O3 '{wsl_ll}' -o {out_bin}"
    _, _, c_err, c_rc = run_cmd(["wsl", "bash", "-c", compile_bash])
    if ll_path.exists():
        ll_path.unlink()
    if c_rc != 0:
        return None, f"Clang compile error: {c_err}"

    # 3. Benchmark standalone AOT executable inside WSL
    timings = []
    for _ in range(runs):
        t, _, _, rc = run_cmd(["wsl", "bash", "-c", out_bin])
        if rc == 0:
            timings.append(t)

    run_cmd(["wsl", "bash", "-c", f"rm -f {out_bin}"])
    return statistics.median(timings) if timings else None, None

def create_profile_variant(orig_file, profile_tag):
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
    print("=" * 105)
    print("AGAM COMPILER BENCHMARK MATRIX: AOT (LLVM -O3) vs. JIT (CRANELIFT) across @lang.base vs @lang.advance")
    print("=" * 105)
    print(f"{'Workload':<20} | {'JIT (@base)':<14} | {'JIT (@advance)':<16} | {'LLVM AOT (@base)':<18} | {'LLVM AOT (@advance)':<20}")
    print("-" * 105)

    for name, suite in WORKLOADS:
        agm_file = ROOT / "benchmarks" / "suites" / suite / f"{name}.agam"
        if not agm_file.exists():
            continue

        base_file = create_profile_variant(agm_file, "@lang.base")
        adv_file = create_profile_variant(agm_file, "@lang.advance")

        try:
            t_jit_base, _ = benchmark_jit(base_file)
            t_jit_adv, _ = benchmark_jit(adv_file)
            t_aot_base, _ = benchmark_llvm_aot(base_file)
            t_aot_adv, _ = benchmark_llvm_aot(adv_file)

            s_jit_base = f"{t_jit_base:.2f} ms" if t_jit_base is not None else "ERR"
            s_jit_adv = f"{t_jit_adv:.2f} ms" if t_jit_adv is not None else "ERR"
            s_aot_base = f"{t_aot_base:.2f} ms" if t_aot_base is not None else "ERR"
            s_aot_adv = f"{t_aot_adv:.2f} ms" if t_aot_adv is not None else "ERR"

            print(f"{name:<20} | {s_jit_base:<14} | {s_jit_adv:<16} | {s_aot_base:<18} | {s_aot_adv:<20}")
        finally:
            if base_file.exists(): base_file.unlink()
            if adv_file.exists(): adv_file.unlink()

    print("=" * 105)

if __name__ == "__main__":
    main()
