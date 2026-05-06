# Current Development

## Program Goal

Build Agam into a **world-class compiled language** with Python-level readability, Rust-like safety, native-speed execution, and language-native AI/ML capabilities. Native LLVM remains the first-class production backend for Windows, Linux, and Android.

## Strategic Roadmap

Work is organized into **6 tiers** of descending priority. See `catalog.md` for the full tier map.

| Tier | Theme | Status |
|------|-------|--------|
| **0** | Foundation Completion | **Next up** — credibility-critical |
| **1** | Developer Experience | Planned |
| **2** | Runtime and Concurrency | Requires design decisions |
| **3** | Platform and Ecosystem | Planned |
| **4** | Performance and Optimization | Partial (GPU pipeline active) |
| **5** | AI-Native Differentiation | Planned |
| **6** | Frontier and Long-Horizon | Far future |

## Active Workstreams (Shipped Infrastructure)

| Phase | Status | Focus | Detail |
|-------|--------|-------|--------|
| **15F** | complete | Incremental daemon, background prewarm, parallel compilation | `details/15F.md` |
| **15G** | complete | Premium experience layer (tooling unification) | `details/15G.md` |
| **15H** | partial | Native LLVM SDK distribution and toolchain bundles | `details/15H.md` |
| **16** | complete | Interactive REPL and structured headless execution | `details/16.md` |
| **17A–17E** | complete | Workspace, resolver, lockfile, registry, governance | `details/17A.md`–`details/17E.md` |
| **17F** | partial | Standard library, effects runtime, native I/O | `details/17F.md` |
| **18** | partial | Agent-facing execution tool | `details/18.md` |
| **19** | partial | Wrapper foundation for agent ecosystems | `details/19.md` |
| **20** | complete | Language surface: effect/handler/perform syntax | `details/20.md` |
| **21** | complete | Runtime hardening: OS-level sandbox | `details/21.md` |
| **22** | complete | Omni-targeting directives | `details/22.md` |
| **23** | partial | GPU/NPU integration (@gpu kernel pipeline) | `details/23.md` |

## Next Priority: Tier 0 — Foundation Completion

These phases are **credibility-critical**. Without them, experienced engineers cannot take Agam seriously as a production language.

| Phase | Status | Focus | Detail |
|-------|--------|-------|--------|
| **F1** | open | Formal grammar specification (EBNF/PEG for all syntax modes) | `details/F1.md` |
| **F2** | open | Type system completion (generics, enums, inference, Option/Result) | `details/F2.md` |
| **F3** | open | Object model completion (struct/trait/impl end-to-end) | `details/F3.md` |
| **F4** | open | Module system and visibility (pub/private, qualified imports) | `details/F4.md` |
| **F5** | open | Ergonomics (named args, defaults, destructuring, interpolation) | `details/F5.md` |

## Queued: Tier 1 — Developer Experience

| Phase | Status | Focus | Detail |
|-------|--------|-------|--------|
| **DX1** | open | Elite error messages with recovery and suggestions | `details/DX1.md` |
| **DX2** | open | LSP production quality (completion, hover, go-to-def) | `details/DX2.md` |
| **DX3** | open | Documentation generation (`agamc doc`) | `details/DX3.md` |
| **DX4** | open | Debugger integration (DWARF, CodeView, DAP) | `details/DX4.md` |
| **DX5** | open | Testing framework maturity (`agamc test` full surface) | `details/DX5.md` |
| **GUI5** | open | **Zero-friction visual toolchain** (hot-reload, preview) | `details/GUI5.md` |
| **PKG1** | partial | **Unified "One Tool" build system** (compiler = pkg mgr) | `details/PKG1.md` |

## Queued: Tier 2 — Runtime, Concurrency, and Security

| Phase | Status | Focus | Detail |
|-------|--------|-------|--------|
| **R1** | decided | Memory model decision and implementation | `details/R1.md` |
| **R2** | open | Async and structured concurrency | `details/R2.md` |
| **R3** | open | Networking and I/O stdlib | `details/R3.md` |
| **SEC1** | open | **World-class cybersecurity** (capabilities, crypto, taint, formal proofs) | `details/SEC1.md` |
| **PKG2** | partial | **Immutable reproducibility** (crypto lockfile, hermetic builds) | `details/PKG2.md` |
| **PKG3** | open | **Supply chain fortress** (signing, capability sandbox, SBOM) | `details/PKG3.md` |

## Queued: Tier 3 — Platform and Ecosystem

| Phase | Status | Focus | Detail |
|-------|--------|-------|--------|
| **P1** | open | WASM backend (web playground, edge computing) | `details/P1.md` |
| **P2** | open | Cross-compilation matrix (extends 15H) | `details/P2.md` |
| **P3** | open | Package manager production quality (remote registry) | `details/P3.md` |
| **P4** | open | Web playground and documentation site | `details/P4.md` |
| **FFI1** | open | **Universal FFI** (C/C++/Python/Rust/Java/JS zero-friction interop) | `details/FFI1.md` |
| **GUI1** | open | **Omni-platform native renderer** (Win/Mac/Linux/Web/Android) | `details/GUI1.md` |
| **GUI3** | open | **Modern component ecosystem** (100+ widgets, theme engine) | `details/GUI3.md` |
| **PKG4** | open | **Zero-config foreign build** (drop .c/.py, it works) | `details/PKG4.md` |
| **PKG5** | open | **Decentralized federated registry** (multi-source, mirrors) | `details/PKG5.md` |

## Queued: Tier 4 — Performance and Optimization

| Phase | Status | Focus | Detail |
|-------|--------|-------|--------|
| **O1** | open | Advanced LLVM optimization (PGO, LTO, auto-vectorization) | `details/O1.md` |
| **O2** | open | Compile-time execution (comptime) | `details/O2.md` |
| **O3** | open | Advanced DSA and scientific computing (was Phase 24) | `details/O3.md` |
| **O4** | open | Machine-code control (was Phase 25) | `details/O4.md` |
| **O5** | partial | GPU/NPU completion (finish Phase 23 remaining) | `details/O5.md` |
| **META1** | open | **Metaprogramming and macro system** (DSLs, derive, code generation) | `details/META1.md` |
| **HW1** | open | **Hardware introspection** (cache-aware compilation, auto-acceleration) | `details/HW1.md` |
| **GUI2** | open | **Hardware-accelerated visual engine** (120 FPS GPU rendering) | `details/GUI2.md` |

## Queued: Tier 5 — AI-Native Differentiation

| Phase | Status | Focus | Detail |
|-------|--------|-------|--------|
| **AI1** | open | Autodiff and tensor types (language-native) | `details/AI1.md` |
| **AI2** | open | ML training loop primitives | `details/AI2.md` |
| **AI3** | open | Ecosystem integration (Python interop, ONNX) | `details/AI3.md` |

## Queued: Tier 6 — Frontier

| Phase | Status | Focus | Detail |
|-------|--------|-------|--------|
| **X1** | open | Self-hosting (Agam compiler in Agam) | `details/X1.md` |
| **X2** | open | Formal verification integration | `details/X2.md` |
| **X3** | open | Quantum and ZKP primitives (was Phase 26) | `details/X3.md` |
| **AIC1** | open | **AI-native compiler intelligence** (ML-guided optimization) | `details/AIC1.md` |

## Shipped Infrastructure Progress

### 15H Progress
- ✅ `agamc package sdk`, bundled LLVM layout, release-ready archive/checksum flow
- ⬜ Exercise hosted-runner SDK builds on real GitHub runners
- ⬜ Validate release-uploaded Windows/Linux SDK artifacts end to end

### 17F Progress
- ✅ `agam_std::io` deterministic file/path I/O slice
- ✅ `IoError` with round-trip tests
- ✅ `FileSystem` and `Console` effect definitions with 14 handlers
- ✅ HIR lowering for `Perform`/`HandleWith` nodes
- ✅ C and LLVM backends emit concrete effect dispatch
- ✅ End-to-end integration tests for `perform` compilation
- ⬜ Align broader stdlib with first-party distribution contracts

### 23 Progress
- ✅ `@gpu` kernel config parsing and sema validation
- ✅ `GpuKernelLaunch` MIR op across all backends
- ✅ NVPTX64 IR emitter with CUDA linkage
- ✅ GPU builtins (thread_id, block_id, block_dim, barrier)
- ✅ Indexed buffer reads/writes with NVPTX getelementptr
- ✅ Shared memory (`addrspace(3)`) allocations
- ✅ GPU math builtins → NVVM fast-math intrinsics
- ✅ Host-device transfer APIs (gpu_malloc, gpu_free, memcpy)
- ⬜ Rich memory types (pointer/array lowering in kernels)

## Decision Rules

- Prefer native host LLVM over WSL fallback
- Keep `agamc doctor` and SDK packaging aligned with the readiness contract
- VS Community 2026 is the canonical Windows toolchain inventory
- No macOS/iOS backend claims until native validation hardware exists
- Tier 0 foundation work takes priority over all new feature tiers
- If a phase decision needs more context → open `details/`
