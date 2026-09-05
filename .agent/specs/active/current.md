# Current Development Roadmap

## Program Goal
Production-grade native systems compiler delivering bare-metal execution performance, transparent benchmarks, zero-panic resilience, and unified multi-target compilation (Windows, Linux, macOS, Android).

---

## Active Execution Stages

| Stage | Focus Area | Status | Spec File |
|:---|:---|:---:|:---|
| **Stage 0** | **Crate Decoupling, Inverted Driver Modularization & Zero-Panic** | 🔄 **ACTIVE** | [`details/STAGE-00-driver-modularization-and-hardening.md`](details/STAGE-00-driver-modularization-and-hardening.md) |
| **Stage 1** | **Dynamic Memory Buffers, Array/Slice Indexing & Native FFI Runtime ABI** | ✅ **VERIFIED** | [`details/STAGE-01-dynamic-buffers-ffi.md`](details/STAGE-01-dynamic-buffers-ffi.md) |
| **Stage 2** | **Arbitrary-Field Dynamic Structs & Enums** | ✅ **VERIFIED** | [`details/STAGE-02-dynamic-structs-enums.md`](details/STAGE-02-dynamic-structs-enums.md) |
| **Stage 3** | **Direct System Call & OS Subsystem Engine (mmap, IOCP, epoll, Sockets)** | 🚀 **READY / NEXT** | [`details/STAGE-03-direct-syscalls-pal.md`](details/STAGE-03-direct-syscalls-pal.md) |
| **Stage 4** | **C-ABI Foreign Function Binding Generator (`agam-bindgen`)** | 📋 **PLANNED** | [`details/STAGE-04-foreign-bindgen.md`](details/STAGE-04-foreign-bindgen.md) |
| **Stage 5** | **High-Performance SIMD Vector Engine (AVX2, AVX-512, NEON, RVV)** | 📋 **PLANNED** | [`details/STAGE-05-simd-vector-engine.md`](details/STAGE-05-simd-vector-engine.md) |
| **Stage 6** | **Production Standard Library & Media Codecs (4K Image, FLAC, Async HTTP)** | 📋 **PLANNED** | [`details/STAGE-06-stdlib-media-codecs.md`](details/STAGE-06-stdlib-media-codecs.md) |
| **Stage 7** | **Self-Hosting Bootstrap & 1:1 Benchmark Verification** | 📋 **PLANNED** | [`details/STAGE-07-self-hosting-bootstrap.md`](details/STAGE-07-self-hosting-bootstrap.md) |

---

## Verification & Health Status

| Pillar | Status | Metric |
|:---|:---:|:---|
| **Workspace Test Suite** | 🟢 | **220 / 220 Passed** across all 27 crates |
| **Clippy Lint Rules** | 🟢 | **0 warnings** under `cargo clippy --all-targets -- -D warnings` |
| **Code Formatting** | 🟢 | **100% compliant** with `cargo fmt --all -- --check` |
| **Example Programs** | 🟢 | 8/8 runnable examples verified in `examples/01_basics/` |

---

## Influencing Audits & Architectural RFCs
The active execution stages are directly bounded and informed by the ground-truth audits and RFCs in `docs/`:
- [AUDIT-optimizer-pipeline-honesty-2026-09-05.md](file:///c:/Users/ksvik/Projects/Agam-Lang/docs/AUDIT-optimizer-pipeline-honesty-2026-09-05.md): Rigorous MIR pass audit proving escape analysis is currently analysis-only (no mutation). Directly influences Stage 0 optimization verification and Stage 1 memory semantics.
- [SPEC-escape-analysis-rewrite.md](file:///c:/Users/ksvik/Projects/Agam-Lang/docs/SPEC-escape-analysis-rewrite.md): Concrete rewrite specification to turn escape analysis into real stack-promotion MIR transformations.
- [RFC-memory-model-default.md](file:///c:/Users/ksvik/Projects/Agam-Lang/docs/RFC-memory-model-default.md): Canonical memory semantics governing Stage 1 dynamic buffers and Stage 2 dynamic structs/enums.
- [AUDIT-gui-shipment-2026-08-29.md](file:///c:/Users/ksvik/Projects/Agam-Lang/docs/AUDIT-gui-shipment-2026-08-29.md) & [RFC-gui-engine.md](file:///c:/Users/ksvik/Projects/Agam-Lang/docs/RFC-gui-engine.md): GUI engine requirements and shipping criteria.
- [WEEKLY-REVIEW-2026-08-29.md](file:///c:/Users/ksvik/Projects/Agam-Lang/docs/WEEKLY-REVIEW-2026-08-29.md): Review notes on compiler progress and milestones.

---

## Past Completed Foundations
All 78 foundational Phase specifications (T0–T6) have been archived under [`.agent/specs/archive/tier_fundamentals/`](../archive/tier_fundamentals/) with index tracking in [`.agent/specs/archive/INDEX.md`](../archive/INDEX.md).
