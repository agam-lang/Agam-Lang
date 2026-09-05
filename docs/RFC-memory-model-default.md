# RFC: Should `strict {}` Become Agam's Default Memory Model?

**Status:** Decision record — 2026-09-05  
**Decision:** **Do not make `strict {}` the default yet.** Keep ARC/CoW as the default for `@lang.base` and `@lang.advance`; turn strict ownership into an end-to-end, opt-in feature first. This is a technical conclusion, independent of pricing, marketing, or news.

## 1. Ground-truth maturity assessment

Status keys: 🟢 implemented and exercised by the language pipeline; 🟡 implemented as a component or prototype but not proven end-to-end; ⚪ specified or absent from the executable language path.

| Area | Status | Repository evidence | What works now | What is not yet expressed or proven |
|---|---:|---|---|---|
| Public memory-model contract | 🟢 | `doc/MEMORY_MODEL.md:9-14,25-57` defines ARC/CoW as default and lexical affine `strict` as Tier 2; version is `0.1.0-alpha.1` at `:3-4`. | The intended two-tier contract is unambiguous. | Documentation is not evidence that the parser, SEMA, MIR, and backends honor the contract. |
| `strict` lexical syntax | ⚪ | The lexer reserves `strict` at `agam/crates/core/agam_lexer/src/token.rs:105,381`. A repository search finds **zero** `TokenKind::Strict`/`Strict` references under `agam/crates/core/agam_parser/src` and `agam/crates/core/agam_ast/src` (audit 2026-09-05). | Token recognition only. | No parsed AST block, nesting semantics, diagnostics, or lowering boundary. A source program cannot presently establish strict semantics through the parser. |
| Ownership tracker | 🟡 | `agam/crates/middle/agam_sema/src/ownership.rs` is **492 LOC** with **15 unit tests**. `MemoryMode` defaults to ARC (`:21-30`), ARC treats moves as retains (`:125-131`), and strict records moved/dropped uses (`:132-149`). | Symbol-level move state, mutability, and shared/exclusive-borrow conflict checks exist. | `OwnershipTracker` is referenced only inside its module in `agam_sema`; no parser/SEMA visitor uses it (repository search, 2026-09-05). It is neither CFG-aware nor connected to type/layout-specific moves, closures, calls, return paths, or code generation. |
| Lifetime and loan checker | 🟡 | `agam/crates/middle/agam_sema/src/lifetime.rs` is **497 LOC** with **7 unit tests**. Region constraints propagate scope-depth endpoints at `:114-159`; `BorrowChecker` tracks root-string places and active loans at `:194-382`. | The component rejects simple conflicting mutable loans, moves, and writes during a loan (`:435-496`). | Lifetime identity is lexical depth, not program points; `BorrowChecker` is only exported at `agam/crates/middle/agam_sema/src/lib.rs:45-47`. No CFG/closure/async/trait-object integration, partial-move/drop-tree analysis, or diagnostic path from user syntax is demonstrated. |
| ARC runtime representation | 🟡 | `agam/crates/runtime/agam_runtime/src/arc.rs` is **247 LOC** with **8 unit tests**. Atomic header retain/release is at `:20-72`; `AgamArc<T>` is at `:88-163`. | Atomic counts and an aligned allocation wrapper are implemented. | `AgamArc<T>` has manual `retain`/`release` but no Rust `Clone`/`Drop` implementation in this file; the header can be decremented without a demonstrated allocation teardown path. Its `new_aligned` uses `assert!` and `expect` (`:100-108`), so it is not a production proof for a universal default runtime representation. |
| Source-language adoption | ⚪ | Audit read **108 unique `.agam` files** under `agam/examples/` and `agam/benchmarks/suites/`: **6** `@lang.base`, **101** `@lang.advance`, **1** `@lang.base.dynamic`, and **0** `strict {` occurrences (2026-09-05). | The profiles are exercised by examples and benchmarks. | There is no real-program strict corpus: no migration examples, negative compile tests, or resource/borrow-heavy strict workload. `@lang.advance` must not be equated with strict ownership. |
| Escape analysis / ARC elision | 🟡 | `agam/crates/middle/agam_mir/src/opt/escape.rs` is **405 LOC** with **3 unit tests**; hostile integration coverage adds **4 tests** in `agam/crates/middle/agam_mir/tests/escape_hostile_tests.rs`. The fixed-point lattice is `NoEscape < ArgEscape < GlobalEscape` (`escape.rs:17-20,118-206`). | Conservative classification covers direct return, selected calls, stores, copies, and effects; hostile tests cover recursive return, store-through-container, effects, and non-escaping temporaries. | Despite its name, `analyze_and_mutate_function_escape` only computes summaries; it does not rewrite an allocation, release, retain, or MIR instruction (`escape.rs:81-256`). The "promotion" counts are report entries (`:224-255`), not verified transformations. |
| MIR escape verifier | 🟡 | `agam/crates/middle/agam_mir/src/verifier.rs` is **623 LOC** with **5 unit tests**. `EscapingStackAllocation` exists at `:43-47`; the check only collects `Op::Alloca` and rejects a direct `Return` of that exact value (`:287-307`), with one targeted test at `:492-525`. | Direct `alloca` return is rejected. | It does not trace aliases, aggregate fields, calls, closures, stores, phis, or indirect escapes. It cannot certify a future stack-promotion pass. |

### Strict-mode cases that are currently unexpressible or unproven

| Category | Status | Evidence and consequence |
|---|---:|---|
| `strict { ... }` source block | ⚪ | Lexer token only; no parser/AST consumer. No source-level accept/reject test can exist until the syntax is lowered. |
| Function signature ownership, borrowed returns, and generic bounds | ⚪ | `LifetimeAnalyzer::elide_function` is an isolated helper (`lifetime.rs:161-171`); no parser/SEMA call site consumes it. |
| Control-flow joins and non-lexical loan end | ⚪ | Loans expire only through explicit `expire_lifetime` (`lifetime.rs:379-381`); no MIR CFG/program-point linkage is present. |
| Partial moves, destructors, self-referential values, closures, async/coroutines, trait objects, and FFI | ⚪ | `OwnershipTracker` uses a single state per `SymbolId` (`ownership.rs:72-85`) and `BorrowChecker` marks a whole root moved (`lifetime.rs:326-350`); neither is integrated with lowering or backend ABI. |
| Strict/ARC boundary crossing and CoW semantics | ⚪ | The specification promises ARC bypass in strict (`doc/MEMORY_MODEL.md:51-57`), but no parsed boundary or MIR ownership operation represents the transition. |

## 2. Consequences of a default flip now

| Surface | Current ARC-oriented assumption | Effect of making strict default today | Required before a safe flip |
|---|---|---|---|
| Standard library | `agam_std` exposes shared/threaded constructs such as `Arc` use in `agam/crates/runtime/agam_std/src/sync.rs:10,81-84,195` and allocation/cloning-heavy tensor/ndarray values (for example `agam_std/src/tensor.rs:127-180,217-281`; `agam_std/src/ndarray.rs:116-162`). | Callers would need explicit ownership transfer or borrowing rules without source syntax or a type/lowering implementation to state them. A blanket default change would be semantics-breaking, not an optimization. | Define language-level owned/shared/borrowed ABI forms; port collections and tensors; establish CoW-to-owned conversion rules and compile/runtime tests. |
| Runtime actor system | Actors use `std::sync::mpsc::{Sender, Receiver}`, `Arc`, `Mutex`, and `RwLock` (`agam/crates/runtime/agam_runtime/src/actor.rs:12-17`); `ActorRef` holds `Sender` plus `Arc<AtomicBool>` (`:153-177`), and `ActorSystem` owns `Arc<ActorSystemInner>` (`:345-349`). | Actor handles intentionally clone/share across threads. A strict-by-default language must have explicit shared handle semantics, `Send` boundaries, and ownership transfer into mailboxes. Otherwise actor APIs either become unusable or silently reintroduce ARC. | Specify and test `Send`/shareable handle rules, mailbox transfer, supervision, cancellation, and drop behavior at the language/FFI boundary. |
| Reactive GUI prototype | `agam_ui` is a Rust prototype using `Rc<RefCell<T>>`, cloneable signals, callbacks, and `thread_local!` queues (`agam/crates/experiments/agam_ui/src/reactive.rs:3-22,80-124`). | This graph relies on shared aliasing and interior mutation. It is neither transferable to strict ownership nor thread-safe by construction. | Retain ARC/shared reactive nodes as an explicit library capability, or design a distinct owned-event model. Do not make its current representation implicit language behavior. |
| Existing language profiles | The documented default is ARC for base and unmarked advance (`doc/MEMORY_MODEL.md:25-43`); existing corpus has no strict blocks. | Flipping `@lang.advance` would change the meaning of **101** checked advance samples without a migration corpus. Flipping base would directly violate the stated ergonomic profile. | Preserve compatibility using profile-controlled defaults and source-to-source migration diagnostics before changing any default. |

## 3. Migration options and recommendation

| Option | Compatibility with alpha users | Technical risk | Recommendation |
|---|---:|---:|---|
| A. Flip every profile immediately | Low | Very high: parser and SEMA cannot enforce the promised rules; ARC-dependent libraries have no boundary contract. | Reject. |
| B. Keep `@lang.base` ARC; make unmarked `@lang.advance` strict | Medium/low | High: **101/108** checked programs are advance, none uses strict, and `@lang.advance` currently denotes syntax/profile rather than established ownership. | Reject for now. |
| C. Keep present defaults; deliver real opt-in `strict {}` | High | Contained: new diagnostics are limited to explicit regions. | **Adopt now.** This respects pre-1.0 experimentation while avoiding a silent semantic rewrite. |
| D. Add a future explicit preview profile (for example, a documented strict-default edition) after C is complete | High | Manageable if it has a separate compatibility contract and migration lint. | Conditional follow-on, not a current change. |

**Recommendation:** choose C. In an alpha language, compatibility is not immutable, but a breaking default needs a working semantic implementation, migration diagnostics, and real-program validation—not only a stated future direction. Preserve `@lang.base` as ARC/CoW ergonomics and `@lang.advance` as its current syntax/profile boundary until a separately versioned strict-default preview can be measured.

## 4. Is a smarter compiler the better near-term answer?

**Partly yes, but only after the current analysis becomes a transforming and verified pass.** Escape analysis can remove ARC work for non-escaping values without forcing every program to express ownership. This is the right direction for the default profile because it preserves ergonomics while targeting the costly cases.

| Current escape pipeline fact | Status | Implication |
|---|---:|---|
| The default optimizer invokes escape analysis each fixed-point iteration (`agam/crates/middle/agam_mir/src/opt/mod.rs:24-57`). | 🟢 | Analysis is on the pipeline path. |
| `CalleePurityInfo::default()` is passed by the default optimizer (`opt/mod.rs:44-45`), while unknown callees become `GlobalEscape` (`escape.rs:142-156`). | 🟡 | Conservative correctness is favored, but without populated purity summaries most calls will not benefit. |
| Allocation discovery uses `Alloca`, struct/enum construction, and name heuristics such as `AlignedBuffer::`, `Tensor::`, or `alloc` (`escape.rs:101-113`). | 🟡 | Heuristics are useful as a prototype but are not a type/effect-based allocation model. |
| Results increase `total_promoted` and `total_arc_elided` merely from summary length (`escape.rs:64-70`), and no MIR instruction is changed in the analysis body (`:81-256`). | ⚪ | No generated code has been proven faster or less allocating. Counters must not be treated as an optimization result. |
| The verifier checks only `return alloca` (`verifier.rs:287-307`). | 🟡 | A transformation pass needs transitive escape verification plus negative tests before it may stack-promote or elide releases. |

**Near-term design direction:** retain ARC as the semantic fallback; add typed ownership/alias annotations in MIR; compute interprocedural summaries by SCC; then rewrite only when every path proves no escape and an ownership-aware verifier accepts the rewrite. Count transformed IR operations and benchmark emitted code, not summaries. This competes on allocation overhead without requiring a premature language-wide ownership tax.

## 5. Decision, readiness gates, and revisit point

### Verdict

**Do not default-flip now.** The language has a documented two-tier model and useful ownership/loan/escape components, but strict ownership is not parseable or integrated end-to-end. The safer performance strategy is: implement strict as an opt-in language feature, make ARC elision real and verified, then use measured evidence to decide whether a strict-default preview is warranted.

### Falsifiable readiness gates

Reopen this decision after **six months of completed implementation evidence**, or earlier only when all gates below pass in CI for two consecutive releases:

| Gate | Pass criterion |
|---|---|
| End-to-end strict semantics | Parser → AST → SEMA → HIR → MIR → both codegen paths carry a strict ownership boundary; compile-pass and compile-fail suites cover moves, borrows, reborrows, branches, loops, returns, closures, async/coroutines, trait/dynamic calls, destructors, and FFI. |
| Semantics soundness | Ownership checking is program-point/CFG based, handles projection/partial moves and drop elaboration, and has differential/fuzz tests with no accepted known-unsound case. |
| ARC boundary contract | Explicit shared/owned/borrowed conversions, CoW mutation behavior, actor/mailbox transfer, and GUI/reactive sharing each have API contracts and integration tests. |
| Escape optimization reality | Escape pass rewrites MIR; verifier follows aliases/aggregates/phis/calls; hostile suite grows beyond the current **4** tests; emitted-code tests prove retains/releases or heap allocations were removed only when legal. |
| Workload evidence | A strict corpus exists: port representative examples and benchmarks, including real aggregate, actor, tensor, and reactive patterns. Publish compile success, diagnostics, allocation count, binary size, and runtime results against ARC mode. |
| Default-change migration | A preview profile has automated migration diagnostics and a documented compatibility story for `@lang.base` and existing `@lang.advance` code. |

## 6. Positioning after the technical conclusion

The defensible position today is **"deterministic ARC/CoW by default, with a path to verified affine regions and compiler-driven ARC elision."** It should not claim zero-cost strict ownership as the normal language default until the gates above are met. Any external claim about memory pricing or industry preference is a market signal, not a readiness criterion and does not alter this decision.

## 7. Open questions

1. What is the source-level spelling and type rule for owned, shared, borrowed, and weak values at an ARC/strict boundary?
2. Is `@lang.advance` a syntax profile only, or should a future edition make it an ownership profile? If so, what exact compatibility guarantees apply?
3. What MIR operations represent retain, release, CoW uniqueness checks, allocation, and destruction so escape analysis can transform and verify them?
4. Which calls may receive a non-escaping borrowed argument, and how will purity/capture summaries be inferred, declared, cached, and invalidated across packages?
5. What semantics govern actor messages: move into mailbox, clone/share, borrowed send prohibition, and remote serialization?
6. Does the reactive GUI model remain explicitly `Rc`/single-threaded, move to `Arc`/synchronization, or gain a separate owned event-graph representation?
7. What allocator and destructor model makes scoped arenas from `doc/MEMORY_MODEL.md:60-66` compatible with strict drops, FFI, and escape promotion?
