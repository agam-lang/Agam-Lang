# Agam Language & Compiler: Core Audit, Discrepancies & Roadmap

> **Author**: Lead Language Designer & Systems Architect  
> **Date**: 2026-09-05  
> **Status**: Mandatory Reference for All Contributors & AI Agents (Gemini, Claude, Codex)  

---

## 1. Executive Summary: The "Too Basic" Discrepancies

A systematic empirical audit comparing the **Web Playground**, the **Cranelift JIT Engine (`agamc run`)**, and the **LLVM AOT Backend (`agamc build --backend llvm`)** surfaced critical discrepancies in foundational language constructs.

While the compiler boasts advanced architectural features (SSA MIR optimization, CUDA PTX GPU emission, algebraic effects, SMT contract verification), several basic operations (range iteration, string concatenation, array stores, and pattern destructuring) diverged across backends or crashed the runtime.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 COMPILATION TARGETS                                    │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ Web Browser Playground   │ Cranelift JIT (agamc run)   │ LLVM AOT (agamc build)        │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ JavaScript AST Evaluator │ In-Memory Native JIT        │ Optimizing LLVM IR (.ll)      │
│ Uses JS array polyfills  │ Zero-dependency execution   │ Emits vectorization & LTO     │
│ Diverged from native!    │ Fast, but lowering gaps!    │ Full features, requires Clang │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

---

## 2. Forensic Audit Findings: The 5 Core Gaps

### GAP-01: Range Iteration & Method Dispatch (`(0..10).reduce(...)`)
* **The Illusion**: The Web Playground used JavaScript array methods to make `(0..10).reduce(0, |acc, x| acc + x)` appear functional.
* **The Reality**:
  * **Cranelift JIT**: Fails with `error: unsupported JIT call target 'reduce'` (method call dispatch on range objects is not lowered).
  * **LLVM AOT**: Lowers through HIR/MIR, extracts lambda `__lambda_6`, but fails in LLVM emission with `error: load from undeclared local '__lambda_6'`.
* **Root Cause**: Range method chains (`.map`, `.filter`, `.reduce`) are not desugared during frontend HIR lowering into canonical counting loops.
* **Verified Working Equivalent**:
  ```agam
  @lang.advance
  fn main() -> i32 {
      let mut sum = 0;
      let mut i = 0;
      while i < 10 {
          sum = sum + i;
          i = i + 1;
      }
      print_int(sum); // Output: 45
      0
  }
  ```

---

### GAP-02: String Concatenation Pointer Arithmetic in JIT
* **The Illusion**: String addition `let full = greeting + name;` is standard in modern languages.
* **The Reality**:
  * **LLVM AOT**: Works properly. Generates `call i8* @agam_str_concat(i8*, i8*)`.
  * **Cranelift JIT**: **Crashes the process** with `thread 'main' has overflowed its stack`.
* **Root Cause**: In `agam_jit/src/lib.rs` (lines 2731–2736), `MirBinOp::Add` on strings executes raw `builder.ins().iadd(left, right)`. Because strings are pointers in memory, it performs integer arithmetic on two memory addresses, producing a corrupted pointer that crashes dereference routines.
* **Verified Working Equivalent**:
  ```agam
  // Print multi-argument values sequentially without string addition:
  println("Hello, ", name);
  ```

---

### GAP-03: Array Literal Construction & Store in JIT
* **The Illusion**: `let arr = [10, 20, 30]; print_int(arr[1]);` is a basic test case.
* **The Reality**:
  * **LLVM AOT**: Works properly. Lowers via `getelementptr inbounds` and stores elements in sequence.
  * **Cranelift JIT**: Fails with `error: indexed aggregate stores are not yet supported by the Cranelift JIT slice`.
* **Root Cause**: Stage 1 implemented `Op::GetIndex` and `Op::StoreIndex` in `agam_codegen::llvm_emitter`, but never ported the store slice to `agam_jit`.

---

### GAP-04: Python-Style Layout Indentation inside Braces (`@lang.base`)
* **The Illusion**: Users should be able to write multiline structs naturally:
  ```agam
  struct Point {
      x: i32,
      y: i32,
  }
  ```
* **The Reality**: Fails in `@lang.base` mode with `error: expected expression, found Indent`.
* **Root Cause**: The layout lexer in `agam_lexer` inserts `Indent`/`Dedent` tokens inside curly braces `{ ... }` unless bracket depth suppression is active.
* **Verified Working Equivalent**:
  ```agam
  // Option A: Specify @lang.advance (systems mode):
  @lang.advance
  struct Point { x: i32, y: i32 }

  // Option B: Format on a single line in base mode:
  struct Point { x: i32, y: i32 }
  ```

---

### GAP-05: Rust-Style `{}` Format Strings vs Multi-Argument Printing
* **The Illusion**: Code examples showed `println("Sum = {}", sum);`.
* **The Reality**: Native Agam does not parse `{}` as format specifiers; it literally prints `"Sum = {}45"`.
* **Verified Working Syntax**:
  ```agam
  println("Sum = ", sum); // Outputs: Sum = 45
  ```

---

## 3. Why Did AI Agents Make These Mistakes?

1. **Hallucinating Syntax Across Languages**: Previous agents working on Agam assumed Rust syntax (`"{}"`, closures `|x| x + 1`) or Python syntax without testing against `agamc.exe`.
2. **False Confidence from Synthetic Web Polyfills**: Agents wrote JS polyfills in `agam-lang.github.io/app.js` and assumed that because the web page printed "45", the native compiler supported the feature.
3. **Horizontal Breadth Over Vertical Verification**: 220 unit tests passed because tests isolated specific crates (e.g. testing parser AST generation without running end-to-end code generation through JIT and LLVM).
4. **Weak Guardrails**: The existing rules did not strictly forbid publishing unverified code.

---

## 4. Immediate Remediation Plan (Core Parity Sprint)

| Gap | Component | Remediation Action |
|---|---|---|
| **GAP-01** | `agam_hir` | Desugar Range method calls (`.reduce`, `.map`) into canonical `while` loops before MIR lowering. |
| **GAP-02** | `agam_jit` | Divert `MirBinOp::Add` for `JitType::Str` to invoke `agam_runtime::export::agam_str_concat`. |
| **GAP-03** | `agam_jit` | Implement `Op::StoreIndex` in `agam_jit` using Cranelift stack slot GEP and stores. |
| **GAP-04** | `agam_lexer` | Suppress `Indent`/`Dedent` emission when bracket nesting counter (`{`, `[`, `(`) is $> 0$. |
| **GAP-05** | `agam_sema` | Wire tuple destructuring patterns (`let (a, b) = ...`) to SSA local bindings. |

---

## 5. Macro Development Roadmap (Stages 0 to 7)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               8-STAGE COMPILER ROADMAP                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Stage 0: Modular Driver & Differential Parity Test Suite (JIT vs LLVM Bitwise Parity)  │
│ Stage 1: Dynamic Memory Buffers & Slices (C-ABI Runtime)                        [DONE] │
│ Stage 2: Dynamic Arbitrary-Field Structs & Tagged Enums (No 8-field limit)      [DONE] │
│ Stage 3: Direct Syscalls & PAL Engine (Zero-libc mmap, IOCP, epoll, raw sockets)[NEXT] │
│ Stage 4: Foreign Function Binding Generator (agam-bindgen parsing C headers)           │
│ Stage 5: SIMD Vector Engine (AVX2, AVX-512, NEON, RVV intrinsic codegen)               │
│ Stage 6: Production Standard Library & Media Codecs (4K Image, FLAC, Async HTTP)       │
│ Stage 7: Self-Hosting Bootstrap & Parity Benchmarks vs C++, Rust, Go, Python           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Micro-Architectural Acceleration: AVX-512 Predication & `-march=znver4`

### 6.1 Architectural Principle: Eliminating Branch Misprediction via Mask Registers
In branchy numerical and data-filtering inner loops:
```agam
for x in dataset {
    if x > threshold {
        sum = sum + x;
    }
}
```
Traditional scalar compilation relies on speculative hardware branch predictors (`jle`/`jg`). When data is random or conditions are unpredictable (e.g. 50% branch rate), CPUs suffer severe branch misprediction stalls (15–20 clock cycles per stall).

Targeting modern microarchitectures—specifically **AMD Zen 4 / Zen 5 (`znver4` / `znver5`)** and **Intel AVX-512**—allows compilers to replace conditional branch control flow with **vector mask registers (`k0`–`k7`)**:
* **Vector Comparisons (`vcmpps`)**: Evaluate condition masks across 8 (`<8 x float>`) or 16 (`<16 x float>`) lanes simultaneously into a 64-bit opmask register.
* **Predicated Execution**: Arithmetic instructions execute conditionally per lane via `{k1}` masking without branching.
* **Zen 4 Zero-Throttling Advantage**: Unlike early Intel architectures (Skylake-X) that incurred thermal downclocking (frequency drop) when executing 512-bit instructions, AMD Zen 4 implements double-pumped 256-bit ALUs without any frequency penalty.
* **Loop Tail Predication**: Slices with lengths not divisible by vector width are handled via masked loads/stores instead of scalar epilogue loops.

### 6.2 Current Agam Compiler State
1. **LLVM AOT Backend**: Indirectly available when compiling with `--fast` on a Zen 4/5 host because `build.rs` passes `-march=native -mtune=native` to `clang`. LLVM's loop vectorizer auto-detects host vector masks.
2. **Missing CLI Capabilities**: `agamc` lacks `--target-cpu <cpu>` and `-march` flags, preventing cross-compilation or targeted deployment to `znver4`.
3. **Constrained Codegen Defaults**: `LlvmOptConfig` in `agam_codegen::llvm_opt` defaults to `preferred_vector_width = 256` and `+avx2`, omitting AVX-512 feature flags (`+avx512f`, `+avx512vl`, `+avx512bw`, `+avx512dq`).
4. **Cranelift JIT**: Cranelift JIT does not support AVX-512 mask predication; fallback paths are necessary to preserve the **Dual-Backend Parity Invariant**.

### 6.3 Implementation Plan
* **Stage 0 / Tooling**:
  * Add `--target-cpu` (e.g., `agamc build --target-cpu znver4`) and `--target-features` to the CLI driver.
  * Update `LlvmOptConfig` to set `preferred_vector_width = 512` when targeting `znver4`, `znver5`, or AVX-512 targets, and inject `-mllvm -prefer-predicate-over-epilogue=predicate-else-scalar-epilogue`.
* **Stage 5 (SIMD Engine)**:
  * Expose first-class vector mask types and conditional operations in HIR/MIR (`Op::VecMaskCompare`, `Op::VecMaskedLoad`, `Op::VecMaskedStore`).
  * Lower to LLVM intrinsics (`llvm.masked.load`, `llvm.masked.store`, vector `select`) with automatic scalar/AVX2 fallbacks for Cranelift JIT parity.

---

## 7. Advanced Micro-Architectural Compiler Co-Design & Hardware Test Matrix

### 7.1 High-Impact Silicon Techniques for Future Compiler Stages

| Technique & Instructions | Microarchitecture Target | Hardware Bottleneck Bypassed | Compiler Emission Strategy & Agam Application |
|---|---|---|---|
| **APX Branchless Compare**<br>`CCMP`, `CTEST`, `{nf}` | Intel Arrow Lake / Granite Rapids | Multi-branch cascading & false flag WAW register dependencies | Perform wide-scope if-conversion on `if (a && b && c)`; suppress `EFLAGS` updates via `{nf}` prefix. Speeds up pattern match guards in `agam_sema`. |
| **First-Faulting Loads**<br>`LDFF1B`, `FFR` register | ARMv9 (Neoverse V2, Apple M-series) | Memory page-fault `SIGSEGV` when speculatively loading variable-length strings | Suppress faults when speculative vector reads cross page boundaries; read `FFR` mask for valid bytes. Enables zero-overhead vectorized string & JSON scanning in `std.re`. |
| **Conflict Detection**<br>`VPCONFLICTD/Q` | AVX-512CD / AMD Zen 4 | Loop-carried dependencies & write-after-write hazards in histogram updates (`hist[arr[i]]++`) | Vectorize histogram accumulation loops: detect conflicts in 1 cycle, update conflict-free lanes via masked scatter-add, resolve remainder. Powers Stage 6 columnar analytics. |
| **Non-Temporal Stores**<br>`movntdq`, `vmovntps`, `DC ZVA` | All modern x86-64 & ARMv8+ | Write-allocate penalty: CPU reads 64B cache line from RAM before writing, wasting 50% memory bandwidth | Emit streaming stores for allocations $> \text{L3 cache size}$, writing directly to Write-Combining buffers to double memory write throughput in Stage 1 & Stage 6. |
| **Subnormal Hardware Trap Flush**<br>`MXCSR: FTZ + DAZ` | All x86-64 SSE/AVX | 150-cycle microcode assist exception on subnormal floating-point numbers ($< 10^{-38}$) | Initialize `FTZ` (Flush-To-Zero) and `DAZ` (Denormals-Are-Zero) at thread startup in `@lang.advance` systems mode. Prevents 100x slowdowns in audio DSP & physics. |
| **Hardware Spinlock Backoff**<br>`PAUSE`, `UMWAIT`, `TPAUSE` | Modern x86-64 (Zen 4, Alder Lake+) | Memory bus contention & speculative pipeline flushes on lock-free spin-loops | Emit scaled `PAUSE` instructions (~65–140 cycles) and user-mode `UMWAIT` in Stage 3 async PAL ring buffers and worker thread wait loops. |

---

### 7.2 Empirically Verified Hardware Test Matrix & Lab Setup

The developer environment provides a multi-tier testing and benchmarking laboratory:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                HARDWARE TESTING MATRIX                                 │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ Laptop 1 (Local Host)    │ Laptop 2 (Control Baseline) │ GitHub CI/CD (Matrix Fleet)   │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ AMD Ryzen 7 7840HS       │ Intel Core i5-10310U        │ Azure VMs + ARM Runners       │
│ Zen 4 (znver4), 8C/16T   │ Comet Lake (14nm), 4C/8T    │ ubuntu-latest, macos-14 (M3)  │
│ Full AVX-512, k0-k7, CD  │ Baseline AVX2 / FMA3 only   │ ubuntu-24.04-arm64 (NEON)     │
│ Zero-throttle double-ALU │ Strict No-AVX-512 control   │ Intel SDE (APX) & QEMU (SVE)  │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

#### 1. Laptop 1: AMD Ryzen 7 7840HS (AMD Zen 4 — `znver4`)
* **Verified Silicon State**: Live host probing verified support for `AVX512F`, `AVX512VL`, `AVX512BW`, `AVX512DQ`, `AVX512CD`, `AVX512VNNI`, `AVX512BF16`, and 32 512-bit registers (`%zmm0`–`%zmm31`).
* **Verified Codegen**: Live compilation via WSL Clang (`-march=znver4`) confirmed hardware opmask predication:
  ```assembly
  vcmpltps    %zmm6, %zmm1, %k1           ; 16-lane condition mask into %k1
  vaddps      %zmm6, %zmm2, %zmm2{%k1}    ; Branchless predicated add (0 mispredicts)
  ```
* **Assigned Test Scope**: AVX-512 predication benchmarks, `VPCONFLICT` histogram vectorization, non-temporal streaming writes, and Zen 4 macro-fusion verification.

#### 2. Laptop 2: Intel Core i5-10310U (Intel Comet Lake)
* **Silicon Role**: Control machine representing the standard enterprise AVX2 baseline without AVX-512 or mask registers.
* **Assigned Test Scope**: A/B baseline speedup benchmarks ($T_{\text{baseline}} / T_{\text{znver4}}$), subnormal trap demonstration (measuring the 100x penalty without FTZ), and `PAUSE` latency differences.

#### 3. GitHub CI/CD Automated Test Fleet
* **Multi-OS Parity**: Automated matrix builds across Linux, Windows, and macOS.
* **Apple Silicon & ARM64**: Native execution on `macos-14` (M-series) and `ubuntu-24.04-arm64` for ARM NEON validation.
* **Emulated Verification**:
  * **Intel APX**: Run `intel-sde -apx -- ./test_binary` on Linux runners to verify `CCMP`/`CTEST` code generation ahead of consumer hardware availability.
  * **ARM SVE/SVE2**: Run `qemu-aarch64 -cpu max` to verify `LDFF1` first-faulting vector string scanners.

---

## 8. Strategic AI & NPU Architecture: Bypassing ONNX vs. Pragmatic Acceleration

### 8.1 The "Bypassing ONNX" Dilemma (MLIR-AIE & IREE)
* **Value & Impact**: Academic / High Systems Engineering Prestige.
* **The Reality**: Stepping off the supported AMD Ryzen AI SDK path into experimental compiler territory requires writing custom MLIR dialects, manually routing spatial AIE-ML tile DMAs and switch matrices, and compiling directly to FPGA-derived `.xclbin` bitstreams. Driver/firmware updates can break the toolchain overnight.
* **Time to Build**: 6 to 10+ weeks.
* **Daily Utility Score**: **4.0 / 10** (High resume value for compiler engineering roles, but very low ROI for shipping an everyday desktop systems language).

### 8.2 The Silicon Reality on the Ryzen 7 7840HS: The "NPU Paradox"
On modern mobile APUs, the dedicated NPU is architected for low-power (5W) continuous background tasks (e.g. Windows Studio Effects), making it the weakest accelerator on the system while having the most brittle compiler toolchain:

| Silicon Component | Compute Throughput | Native Target Model | Toolchain Stability | Engineering Effort |
|---|---|---|---|:---:|
| **NVIDIA RTX 3050 Laptop GPU** | **~36–40 TFLOPS (FP16)**<br>**~70+ TOPS (INT8)** | Native CUDA / NVPTX (already in `agam_codegen`) | 🟢 Rock solid (Decades of mature drivers) | Moderate |
| **AMD Zen 4 CPU (8C/16T, AVX-512)** | **~20–25 TOPS (INT8 VNNI)**<br>**~1.5 TFLOPS (FP32)** | Native AVX-512 / LLVM (`-march=znver4`) | 🟢 Zero external drivers (Bare-metal) | Low |
| **AMD Radeon 780M (RDNA3 iGPU)** | **~17 TFLOPS (FP16)** | DirectML, Vulkan Kompute, ROCm | 🟡 Stable (Standard graphics driver) | Moderate |
| **AMD XDNA 1 NPU (Phoenix AIE-ML)** | **10 TOPS (INT8 only)** | Spatial AIE Tiles $\rightarrow$ XRT $\rightarrow$ `.xclbin` | 🔴 High fragility (Firmware/driver ABI drift) | Extreme (6–10+ weeks) |

### 8.3 Agam 3-Tier AI/Tensor Implementation Strategy

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              AGAM TENSOR & AI ROADMAP                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Tier 1 (10/10 Utility): Stage 4 C-ABI FFI -> ONNX Runtime / DirectML C-API    [1 Week] │
│ Tier 2 (9/10 Utility):  Stage 5 Native AVX-512 VNNI + NVIDIA CUDA PTX        [Planned] │
│ Tier 3 (4/10 Academic): Experimental MLIR-AIE Dialect Sandbox             [Non-Block] │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Tier 1: Pragmatic Production FFI (10/10 Daily Utility — 1 Week)**:
   * Implement C-ABI bindings in Stage 4 (`agam-bindgen`) to the **ONNX Runtime C API** and **DirectML C API**.
   * Automatically inherits AMD's official `VitisAI` Execution Provider (leveraging the 7840HS NPU safely), DirectML (targeting the 780M iGPU), and TensorRT (targeting the RTX 3050) with zero custom tile routing or driver fragility.
2. **Tier 2: Native Bare-Metal Compute (9/10 Daily Utility — Stage 5)**:
   * Lower `TensorOp::MatMul` in `agam_mir::dialect` directly to AVX-512 VNNI (`vpdpbusd`) for CPU inference and CUDA PTX for RTX 3050 dGPU inference. Delivers $2\times$ to $7\times$ higher real-world compute throughput than the NPU with zero external dependencies.
3. **Tier 3: Academic MLIR-AIE Sandbox (4/10 Daily Utility — Experimental)**:
   * Keep `agam_mir::dialect` extensible, but isolate any spatial AIE tile routing experiments in a separate tooling crate (`agam_aie`), strictly preventing experimental FPGA/NPU toolchains from blocking the compiler core.

---

## 9. AMD uProf Micro-Architectural Profiling & CLI Runbook

### 9.1 Hardware Target & Developer Purpose
* **Target CPU**: AMD Ryzen 7 7840HS (Zen 4 Phoenix, Family 25 / 0x19, Model 117 / 0x75, Stepping 2).
* **Tool**: AMD uProf (GUI & CLI `AMDuProfCLI.exe`).
* **Developer Purpose for Agam Compiler**:
  * **Instruction-Based Sampling (IBS)**: Precise instruction execution sampling with hardware tagging (IBS Fetch & IBS Op) to identify branch penalties, store-to-load forwarding stalls, and retirement latencies without shadow instrumentation drift.
  * **Cache Locality & Hierarchy**: Detailed attribution of L1 Data, L2 Data, and L3 Core Complex Die (CCD) cache misses across Agam runtime allocations, array slicing, and tensor indexing.
  * **SIMD & Loop Vectorization Efficiency**: Quantifying vector register pressure, AVX-512 256-bit vs 512-bit instruction issue rates, and execution pipe saturation (Pipe 0/1/2/3).
  * **Branch Prediction Analysis**: Tracking branch misprediction hotspots in Pratt parsing loops, match dispatch tables, and lexer token synchronization.

### 9.2 OS Capability Matrix: Windows 11 vs. Bare-Metal Linux vs. WSL2

| Metric / Capability | Bare-Metal Windows 11 (HP Laptop 1) | Bare-Metal Linux (Ubuntu 24.04+) | WSL2 (Virtual Machine Platform) |
|---|:---:|:---:|:---:|
| **Hardware Core PMU Counters** (Cycles, IPC, Ret. Inst) | 🟢 **Full Native Support** | 🟢 **Full Native Support** | 🔴 **Blocked** (No MSR access) |
| **IBS (Instruction-Based Sampling)** | 🟢 **Full Native Support** | 🟢 **Full Native Support** | 🔴 **Blocked** (Virtual Hyper-V CPU) |
| **L1/L2/L3 Cache Miss Profiling** | 🟢 **Full Native Support** | 🟢 **Full Native Support** | 🔴 **Blocked** |
| **Branch Misprediction Analysis** | 🟢 **Full Native Support** | 🟢 **Full Native Support** | 🔴 **Blocked** |
| **Energy & Package Power (RAPL)** | 🟢 **Full Native Support** | 🟢 **Full Native Support** | 🔴 **Blocked** |
| **Assembly & Source Hotspot Attribution** | 🟢 **Full Native Support** | 🟢 **Full Native Support** | 🟡 Degraded (Timer-only) |
| **ROCm / GPU Profiling** | 🟡 Direct3D/DirectML Only | 🟢 Full ROCm Profiling | 🔴 Blocked |
| **ftrace / OS Thread Scheduling** | 🟡 ETW (Event Tracing) | 🟢 Full ftrace / perf | 🟡 Guest-only ftrace |

> **Key Architectural Takeaway**: Bare-metal Windows 11 natively supports 100% of all required compiler micro-architectural counters (IBS, IPC, L1-L3 cache, branch mispredictions, and power). Linux is only required if profiling ROCm GPU compute or kernel-level ftrace schedulers.

### 9.3 Hyper-V / WSL2 PMU Virtualization Conflict & Root Cause
When WSL2, Windows Sandbox, or "Virtual Machine Platform" is active, Windows loads the **Hyper-V Hypervisor** beneath the host operating system (`hypervisorlaunchtype = auto`).

* **Root Cause**:
  1. The Hyper-V root partition intercepts access to the AMD Zen 4 Performance Monitoring Unit (PMU) Model-Specific Registers (MSRs: `MSR0000_0200`–`MSR0000_020B`, and IBS MSRs `MSRC001_1030`–`MSRC001_103B`).
  2. Hyper-V does not expose virtual PMU (vPMC) MSR passthrough to the host driver without enterprise virtualization profiles.
  3. Consequently, AMD uProf detects that MSR programming is trapped and triggers the warning:
     > *"WSL2 is enabled, which enables 'Virtual Machine Platform'. Only Timer-based profiling available."*
  4. In this state, hardware events (IBS, cache misses, branch penalties) cannot be measured; uProf degrades strictly into statistical timer-based sampling (coarse call-stack sampling with zero CPU pipeline insight). Furthermore, forcing vPMC in nested hypervisors (e.g. VMware Workstation) triggers known fatal driver crashes (VMware KB 81623).

### 9.4 Operational Switching Runbook

Agam compiler profiling requires full hardware PMU counters. Follow this simple zero-risk switching runbook:

#### Mode A: 100% Bare-Metal Profiling (Unlock Full IBS, Cache & PMU)
When running micro-architectural benchmark sweeps, SIMD optimization proofs, or deep profiling:
```cmd
:: Run elevated in Windows Administrator Command Prompt or PowerShell:
bcdedit /set hypervisorlaunchtype off
```
* **Action**: Restart Windows.
* **Result**: Hyper-V is disabled. Windows runs bare-metal on the Zen 4 silicon. Full IBS, IPC, branch prediction, and L1/L2/L3 cache counters are **100% unlocked** in AMD uProf GUI and CLI.
* *(Note: WSL2 will temporarily not launch in this mode).*

#### Mode B: Restore WSL2 & Virtualization
When development requires WSL2 (e.g., Linux Clang AOT cross-builds, Miniconda Linux sandbox):
```cmd
:: Run elevated in Windows Administrator Command Prompt or PowerShell:
bcdedit /set hypervisorlaunchtype auto
```
* **Action**: Restart Windows.
* **Result**: Hyper-V and Virtual Machine Platform are restored. WSL2, Docker Desktop, Windows Sandbox, and VMware VMs operate normally.

### 9.5 Automated CLI Profiling Runbook (`AMDuProfCLI`)
AMD uProf includes a scriptable command-line interface (`AMDuProfCLI.exe`) that can be driven automatically by Agam's benchmark harness (`scripts/benchmark_guard.py`):

```powershell
# 1. Profile Core Performance (IPC, Cycles, Retired Instructions, Branch Mispredictions)
AMDuProfCLI.exe collect --config tbp --output-dir ./profiles/tbp agamc.exe run benchmarks/suites/13_simd_vectorization/bench.agam

# 2. Instruction-Based Sampling (IBS) Execution Profiling (Hardware tagged operations)
AMDuProfCLI.exe collect --config ibs --output-dir ./profiles/ibs agamc.exe run benchmarks/suites/13_simd_vectorization/bench.agam

# 3. Cache Miss & Memory Locality Profiling (L1-D, L2, L3 Data Misses)
AMDuProfCLI.exe collect --config assess --output-dir ./profiles/cache agamc.exe run benchmarks/suites/02_numerical_computation/bench.agam

# 4. Generate Machine-Readable Translation Report (CSV)
AMDuProfCLI.exe report --input-dir ./profiles/ibs/AMDuProf-*.data --output-dir ./profiles/reports/ --format csv
```
This enables zero-overhead, reproducible hardware counter regression testing inside Agam's CI and benchmarking infrastructure.
