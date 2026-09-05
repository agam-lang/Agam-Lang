---
name: benchmark-guard
description: "Validate performance claims and optimization passes with before/after benchmarks."
---

# Benchmark Guard

Use this skill when changing performance-sensitive code, MIR optimization passes, or claiming speed improvements.

## Workflow

1. Identify the specific hot path affected (e.g. `agam_mir::opt`, `agam_codegen`, `agam_jit`).
2. Run baseline benchmark before modifying code:
   ```powershell
   python benchmarks/run_benchmarks.py
   ```
3. Apply changes and measure narrow before/after comparison.
4. Reject changes that regress compile time or runtime throughput materially.
5. Record benchmark delta in PR or handoff.

## Focus Areas

- MIR optimization passes (`crates/middle/agam_mir/src/opt/`)
- JIT / LLVM lowering throughput
- Benchmark suites under `benchmarks/suites/`
