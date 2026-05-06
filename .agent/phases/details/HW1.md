# Phase HW1 — Hardware Introspection and Cache-Aware Compilation

**Status:** open
**Tier:** 4 (Performance and Optimization Depth)

## Vision

Give Agam unparalleled awareness of the hardware it runs on. The compiler should automatically organize data structures for cache efficiency, detect available accelerators, and route workloads to the optimal hardware — without the developer writing platform-specific code.

## Deliverables

### Hardware Detection and Telemetry
- [ ] `agam_std::hw::cpu()` — core count, cache sizes, SIMD capabilities, frequency
- [ ] `agam_std::hw::gpu()` — VRAM, compute units, driver version (extends existing `hwinfo`)
- [ ] `agam_std::hw::npu()` — neural processor detection and capability query
- [ ] `agam_std::hw::memory()` — total RAM, NUMA topology, page sizes
- [ ] Safe interfaces — no raw C bindings needed

### Cache-Oblivious Compilation
- [ ] Compiler auto-arranges struct fields for optimal cache line packing
- [ ] `#[align(64)]` for cache-line-aligned types (already in AST attributes)
- [ ] Array-of-Structs → Struct-of-Arrays automatic transformation for hot loops
- [ ] Loop tiling dimensions auto-tuned to L1/L2/L3 cache sizes
- [ ] `@cache_friendly` annotation triggers aggressive data layout optimization

### Hardware-Agnostic Acceleration
- [ ] `@accelerate` annotation on functions: compiler picks CPU/GPU/NPU automatically
- [ ] Runtime hardware probe → dispatch to optimal implementation
- [ ] Fallback chain: GPU → NPU → SIMD → scalar
- [ ] No CUDA/OpenCL code needed — compiler handles device dispatch

### Direct Telemetry Hooks
- [ ] `agam_std::hw::perf_counter()` — hardware performance counter access
- [ ] `agam_std::hw::cache_misses()` — L1/L2/L3 miss counters
- [ ] `agam_std::hw::branch_mispredicts()` — branch prediction counters
- [ ] Safe wrappers around platform perf APIs (Intel PMU, ARM PMU)

### SIMD Auto-Dispatch
- [ ] Compiler detects SSE4, AVX2, AVX-512, NEON at build time
- [ ] Multi-versioned functions: one binary contains all SIMD variants
- [ ] Runtime CPUID dispatch to best available version
- [ ] Extends existing `agam_runtime::simd` module

## Responsible Crates

- `agam_runtime` — hardware detection (extends existing `hwinfo.rs`)
- `agam_codegen` — cache-aware data layout, SIMD multi-versioning
- `agam_mir` — AoS→SoA transform, loop tiling auto-tuning
- `agam_std` — hardware API surface

## Dependencies

- Phase O1 (LLVM optimization) — loop tiling, vectorization
- Phase O5 (GPU) — GPU dispatch for `@accelerate`
