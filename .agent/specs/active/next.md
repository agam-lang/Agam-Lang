# Next Implementation Order

Use this document as the canonical answer to **"what should Agam compiler engineers build next?"**

---

## 🎯 Immediate Priority Queue

0. **Syntax & Tooling Redesign Track (`PRE-000` & Specs 001–010)** 📐
   - **Why**: Fixes core compiler/syntax contradictions: multi-line base-mode structs fail, no call arity checking exists in sema, license comments cause silent base-mode default, and dialects are unenforced.
   - **Authority & Index**: [`.agent/specs/syntax/000-INDEX.md`](../syntax/000-INDEX.md)
   - **Hard Precondition**: `PRE-000` (byte-for-byte stdout dual-backend differential execution harness in `agam_test/src/differential.rs`).
   - **Top 3 Immediate Specs**:
     - `001`: Base-Mode Type Declarations (fixes B-Grade #1 / ASYM-1)
     - `002`: Call Arity and Argument Checking (fixes missing sema arity check)
     - `003`: Manifest Syntax Profile & Strict Directive Placement (fixes S-Grade #3)

1. **Stage 4: C-ABI Foreign Binding Generator (`agam-bindgen`)** 🚀
   - **Why**: Enables zero-overhead linkage to native system libraries (`libc`, `libm`, `libz`, `libpng`, `libflac`).
   - **Key Deliverables**:
     - Automated C header parser & Agam extern generator.
     - Zero-cost C-ABI struct/union memory layout mapping.
     - Integration with `agam_ffi` runtime loader.
   - **Detail Spec**: [`details/STAGE-04-foreign-bindgen.md`](details/STAGE-04-foreign-bindgen.md)

2. **Stage 0: Crate Decoupling, Driver Modularization & Quality Hardening (Active Track)** 🔄
   - **Why**: Fixes Windows MSVC debug stack frame overflow by decomposing the 16.7K-line god-file `agam_driver/src/main.rs`, eliminates unwrap panics, and aligns documentation truth.
   - **Key Deliverables**:
     - **Driver Split**: Extract `crates/tooling/agam_target` (MSVC/LLVM/Android toolchains) and `crates/tooling/agam_session` (headless workers); split `main.rs` into `src/commands/`.
     - **Panic Ratchet**: Ratchet down 1,399 unwrap/expect/panic instances across core passes.
     - **Pratt Parser Recovery**: Token synchronization tokens (`;`, `}`, `fn`, `let`) and `ast::Expr::Error` nodes.
     - **Doctest Alignment**: Remediate syntax drift across `docs/` so all snippets pass `python scripts/doctest_check.py`.
   - **Detail Spec**: [`details/STAGE-00-driver-modularization-and-hardening.md`](details/STAGE-00-driver-modularization-and-hardening.md)

3. **Stage 5: High-Performance SIMD Vector Engine** 📋
   - **Why**: First-class vector types (`vec8f32`, `vec16u8`) with AVX2/AVX-512/NEON/RVV hardware acceleration.
   - **Detail Spec**: [`details/STAGE-05-simd-vector-engine.md`](details/STAGE-05-simd-vector-engine.md)

5. **Stage 6: Production Standard Library & Media Codecs** 📋
   - **Why**: Production 4K image convolution kernels, 24-bit FLAC audio encoding, and async HTTP/1.1 & HTTP/2.
   - **Detail Spec**: [`details/STAGE-06-stdlib-media-codecs.md`](details/STAGE-06-stdlib-media-codecs.md)

6. **Stage 7: Self-Hosting Bootstrap & 1:1 Benchmark Verification** 📋
   - **Why**: Stage 0 $\rightarrow$ Stage 1 $\rightarrow$ Stage 2 self-hosting proof and transparent benchmarks vs C++ (`clang++ -O3`) and Rust (`release`).
   - **Detail Spec**: [`details/STAGE-07-self-hosting-bootstrap.md`](details/STAGE-07-self-hosting-bootstrap.md)

---

## ⛔ Anti-Priorities (Do Not Build Ahead of Fundamentals)
- Synthetic micro-benchmarks that test simple arithmetic loops without memory allocations.
- Complex speculative type theories that add complexity before the C-ABI FFI and direct syscall layers are solid.
- Windows-only or Linux-only shortcuts that break cross-platform compilation.
