# Phase Catalog

The complete roadmap for Agam — organized into **strategic tiers**. Agam's design is built on **22 foundational pillars** that together make it the world's most complete omni-language.

## The 22 Pillars of Agam

| # | Pillar | Phases |
|---|--------|--------|
| 1 | **Performance** — Zero-overhead abstractions, LLVM, predictable memory | R1, O1–O5 |
| 2 | **Syntax** — Progressive complexity, multi-paradigm, metaprogramming | F5, META1 |
| 3 | **Math & AI** — First-class tensors, native vectorization, auto-acceleration | AI1–AI3 |
| 4 | **Security** — Provable safety, capability security, formal verification | SEC1, X2 |
| 5 | **Concurrency** — Fearless parallelism, data race prevention | R2, R1 |
| 6 | **Interoperability** — Universal FFI: C/C++/Python/Rust/Java/JS | FFI1 |
| 7 | **Tooling** — One-binary, zero-config: compiler+pkg+fmt+lint+LSP+test | DX1–DX5, P3 |
| 8 | **Adaptive Compilation** — REPL+JIT prototyping, AOT production | Phase 16 ✅, O2 |
| 9 | **Hardware Introspection** — Deep silicon access, cache-aware compilation | HW1 |
| 10 | **AI Compiler** — Semantic errors, ML-guided optimization | AIC1, DX1 |
| 11 | **Error & State** — Deterministic resilience, Result/Option, immutable-first | F2, DX1 |
| 12 | **Multi-Target** — WASM native, cross-compilation via `--target` | P1, P2 |
| 13 | **Omni-Platform Renderer** — Single codebase → native UI everywhere | GUI1 |
| 14 | **Hardware-Accelerated Visuals** — GPU-native 120 FPS rendering | GUI2 |
| 15 | **Modern Component Ecosystem** — 100+ widgets, themes | GUI3 |
| 16 | **Declarative & Reactive Syntax** — @ui DSL, auto state-driven updates | GUI4 |
| 17 | **Zero-Friction Visual Toolchain** — Hot-reload, preview, architect | GUI5 |
| 18 | **One Tool** — Compiler IS the pkg manager, test runner, everything | PKG1 |
| 19 | **Immutable Reproducibility** — Cryptographic lockfile, hermetic builds | PKG2 |
| 20 | **Supply Chain Fortress** — Signed packages, capability sandbox, SBOM | PKG3 |
| 21 | **Zero-Config Foreign Build** — Drop .c/.py/.rs in, it just works | PKG4 |
| 22 | **Decentralized Registry** — Federated, mirrored, no single point of failure | PKG5 |

## Tier Structure

| Tier | Theme | Why This Order |
|------|-------|---------------|
| **Legacy** | Foundation already shipped | Shipped infrastructure |
| **0** | Foundation Completion | Table stakes for serious language |
| **1** | Developer Experience Excellence | Errors, tooling, **visual toolchain**, **one-tool** drive adoption |
| **2** | Runtime, Concurrency, Security & **Reproducibility** | Memory, async, **supply chain**, **hermetic builds** |
| **3** | Platform, Ecosystem, **GUI** & **Build Integration** | WASM, FFI, **native rendering**, **foreign build**, **federated registry** |
| **4** | Performance & Optimization | Codegen, comptime, **GPU rendering**, hardware introspection |
| **5** | AI-Native Differentiation | Autodiff, tensors, ML |
| **6** | Frontier | Self-hosting, verification, AI compiler |

---

## Legacy Foundation (Phases 0–23)

1. `Phase 0`: partial — roadmap/design
2. `Phase 1`: partial → F1
3. `Phase 2`–`14`: complete
4. `Phase 15A`–`15G`: complete | `15H`: partial → P2
5. `Phase 16`: complete — REPL, JIT, headless (**Pillar 8**)
6. `Phase 17A`–`17E`: complete | `17F`: partial → R3
7. `Phase 18`: partial | `Phase 19`: partial → AI3
8. `Phase 20`: complete — effects | `Phase 21`: complete — sandbox
9. `Phase 22`: complete — omni-targeting | `Phase 23`: partial → O5

---

## Tier 0: Foundation Completion

> Pillars: 2, 11, **16**

| # | Phase | Focus | Detail |
|---|-------|-------|--------|
| 14 | `F1` | Formal Grammar Specification | `details/F1.md` |
| 15 | `F2` | Type System (generics, enums, Result/Option, **immutable-first**) | `details/F2.md` |
| 16 | `F3` | Object Model (struct/trait/impl) | `details/F3.md` |
| 17 | `F4` | Module System and Visibility | `details/F4.md` |
| 18 | `F5` | Ergonomics (named args, closures, destructuring) | `details/F5.md` |
| 19 | `GUI4` | **Declarative & Reactive UI Syntax** | `details/GUI4.md` |

---

## Tier 1: Developer Experience Excellence

> Pillars: 7, 10, 11, **17**, **18**

| # | Phase | Focus | Detail |
|---|-------|-------|--------|
| 20 | `DX1` | Elite Error Messages (recovery, suggestions) | `details/DX1.md` |
| 21 | `DX2` | LSP Production Quality | `details/DX2.md` |
| 22 | `DX3` | Documentation Generation | `details/DX3.md` |
| 23 | `DX4` | Debugger Integration (DWARF, DAP) | `details/DX4.md` |
| 24 | `DX5` | Testing Framework Maturity | `details/DX5.md` |
| 25 | `GUI5` | **Zero-Friction Visual Toolchain** | `details/GUI5.md` |
| 26 | `PKG1` | **Unified "One Tool" Build System** (compiler = pkg mgr) | `details/PKG1.md` |

---

## Tier 2: Runtime, Concurrency, Security & Reproducibility

> Pillars: 1, 4, 5, **19**, **20**

| # | Phase | Focus | Detail |
|---|-------|-------|--------|
| 27 | `R1` | Memory Model Decision and Implementation | `details/R1.md` |
| 28 | `R2` | Async and Structured Concurrency | `details/R2.md` |
| 29 | `R3` | Networking and I/O Stdlib | `details/R3.md` |
| 30 | `SEC1` | **World-Class Cybersecurity** | `details/SEC1.md` |
| 31 | `PKG2` | **Immutable Reproducibility** (crypto lockfile, hermetic builds) | `details/PKG2.md` |
| 32 | `PKG3` | **Supply Chain Fortress** (signing, capability sandbox, SBOM) | `details/PKG3.md` |

---

## Tier 3: Platform, Ecosystem, GUI & Build Integration

> Pillars: 6, 12, **13**, **15**, **21**, **22**

| # | Phase | Focus | Detail |
|---|-------|-------|--------|
| 33 | `P1` | WASM Backend | `details/P1.md` |
| 34 | `P2` | Cross-Compilation Matrix | `details/P2.md` |
| 35 | `P3` | Package Manager Production Quality | `details/P3.md` |
| 36 | `P4` | Web Playground and Documentation Site | `details/P4.md` |
| 37 | `FFI1` | **Universal FFI** (C/C++/Python/Rust/Java/JS) | `details/FFI1.md` |
| 38 | `GUI1` | **Omni-Platform Native Renderer** | `details/GUI1.md` |
| 39 | `GUI3` | **Modern Component Ecosystem** | `details/GUI3.md` |
| 40 | `PKG4` | **Zero-Config Foreign Build** (drop .c/.py, it works) | `details/PKG4.md` |
| 41 | `PKG5` | **Decentralized Federated Registry** | `details/PKG5.md` |

---

## Tier 4: Performance & Optimization

> Pillars: 1, 2, 9, **14**

| # | Phase | Focus | Detail |
|---|-------|-------|--------|
| 42 | `O1` | Advanced LLVM Optimization (PGO, LTO) | `details/O1.md` |
| 43 | `O2` | Compile-Time Execution (comptime) | `details/O2.md` |
| 44 | `O3` | Advanced DSA and Scientific Computing | `details/O3.md` |
| 45 | `O4` | Machine-Code Control (inline asm) | `details/O4.md` |
| 46 | `O5` | GPU/NPU Completion | `details/O5.md` |
| 47 | `META1` | **Metaprogramming and Macro System** | `details/META1.md` |
| 48 | `HW1` | **Hardware Introspection** | `details/HW1.md` |
| 49 | `GUI2` | **Hardware-Accelerated Visual Engine** (120 FPS GPU) | `details/GUI2.md` |

---

## Tier 5: AI-Native Differentiation

> Pillar: 3

| # | Phase | Focus | Detail |
|---|-------|-------|--------|
| 50 | `AI1` | Autodiff and Tensor Types | `details/AI1.md` |
| 51 | `AI2` | ML Training Loop Primitives | `details/AI2.md` |
| 52 | `AI3` | Ecosystem Integration (Python, ONNX) | `details/AI3.md` |

---

## Tier 6: Frontier

> Pillars: 4, 10

| # | Phase | Focus | Detail |
|---|-------|-------|--------|
| 53 | `X1` | Self-Hosting | `details/X1.md` |
| 54 | `X2` | Formal Verification | `details/X2.md` |
| 55 | `X3` | Quantum and ZKP Primitives | `details/X3.md` |
| 56 | `AIC1` | **AI-Native Compiler Intelligence** | `details/AIC1.md` |

---

## Where To Dive Deeper

| Category | Files |
|----------|-------|
| Legacy | `details/foundation-00-05.md` through `details/23.md` |
| Tier 0 | `details/F1.md`–`F5.md`, `details/GUI4.md` |
| Tier 1 | `details/DX1.md`–`DX5.md`, `details/GUI5.md`, **`details/PKG1.md`** |
| Tier 2 | `details/R1.md`–`R3.md`, `details/SEC1.md`, **`details/PKG2.md`**, **`details/PKG3.md`** |
| Tier 3 | `details/P1.md`–`P4.md`, `details/FFI1.md`, `details/GUI1.md`, `details/GUI3.md`, **`details/PKG4.md`**, **`details/PKG5.md`** |
| Tier 4 | `details/O1.md`–`O5.md`, `details/META1.md`, `details/HW1.md`, `details/GUI2.md` |
| Tier 5 | `details/AI1.md`–`AI3.md` |
| Tier 6 | `details/X1.md`–`X3.md`, `details/AIC1.md` |
| Architecture | `docs/architecture/compiler-architecture.md`, `docs/architecture/gui-architecture.md` |
| Strategy | `next.md` |
