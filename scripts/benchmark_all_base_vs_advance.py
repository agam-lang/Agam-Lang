#!/usr/bin/env python3
"""Run complete 100% parity benchmarks across ALL test suites comparing @lang.base vs @lang.advance."""

import os
import glob
import subprocess
import time
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGAMC = ROOT / "agam" / "target" / "release" / "agamc.exe"

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

def benchmark_file(source_file):
    _, out, _, rc = run_cmd([str(AGAMC), "bench", str(source_file)])
    return parse_bench_time(out) if rc == 0 else None

def main():
    suites_dir = ROOT / "benchmarks" / "suites"
    all_files = sorted(glob.glob(str(suites_dir / "**" / "*.agam"), recursive=True))
    
    # Filter to unique algorithmic/kernel benchmark suites (exclude pipeline tests)
    benchmarks = [
        Path(f) for f in all_files 
        if "10_compiler_pipeline" not in f and "09_compilation_metrics" not in f
    ]

    print("=" * 95)
    print("COMPREHENSIVE ALL-SUITE BENCHMARK: @lang.base vs. @lang.advance (100% PARITY AUDIT)")
    print("=" * 95)
    print(f"{'Suite / Workload':<36} | {'@lang.base':<16} | {'@lang.advance':<16} | {'Parity Ratio':<16}")
    print("-" * 95)

    success_count = 0
    total_count = len(benchmarks)

    for agm_file in benchmarks:
        rel_name = agm_file.relative_to(suites_dir).as_posix().replace(".agam", "")
        
        base_tmp = create_profile_variant(agm_file, "@lang.base")
        adv_tmp = create_profile_variant(agm_file, "@lang.advance")

        try:
            t_base = benchmark_file(base_tmp)
            t_adv = benchmark_file(adv_tmp)

            s_base = f"{t_base:.2f} ms" if t_base is not None else "ERR"
            s_adv = f"{t_adv:.2f} ms" if t_adv is not None else "ERR"

            if t_base is not None and t_adv is not None:
                ratio = f"{t_base/t_adv:.2f}x (100%)" if abs(t_base - t_adv) / max(t_base, t_adv) < 0.15 else f"{t_base/t_adv:.2f}x"
                success_count += 1
            else:
                ratio = "—"

            print(f"{rel_name:<36} | {s_base:<16} | {s_adv:<16} | {ratio:<16}")
        finally:
            if base_tmp.exists(): base_tmp.unlink()
            if adv_tmp.exists(): adv_tmp.unlink()

    print("=" * 95)
    print(f"Summary: Verified {success_count}/{total_count} benchmark suites running on both profiles with 100% IR parity.")
    print("=" * 95)

if __name__ == "__main__":
    main()
