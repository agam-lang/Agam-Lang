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

## Micro-Architectural Hardware Profiling (AMD uProf CLI)

When profiling on Zen 4 (Ryzen 7 7840HS), use hardware PMU counters to measure micro-architectural impact:

1. **Bare-Metal PMU Precondition**: Ensure Hyper-V is toggled off (`bcdedit /set hypervisorlaunchtype off` + reboot) so hardware MSRs and IBS are unblocked.
2. **IBS Instruction Sampling**:
   ```powershell
   AMDuProfCLI.exe collect --config ibs --output-dir ./profiles/ibs agamc.exe run benchmarks/suites/13_simd_vectorization/bench.agam
   ```
3. **Core Cache & Locality Analysis**:
   ```powershell
   AMDuProfCLI.exe collect --config assess --output-dir ./profiles/cache agamc.exe run benchmarks/suites/02_numerical_computation/bench.agam
   ```
4. **Generate CSV Report**:
   ```powershell
   AMDuProfCLI.exe report --input-dir ./profiles/ibs/AMDuProf-*.data --output-dir ./profiles/reports/ --format csv
   ```
Consult [`note.md`](../../note.md) §9 for the full OS capability matrix and Hyper-V switching runbook.

