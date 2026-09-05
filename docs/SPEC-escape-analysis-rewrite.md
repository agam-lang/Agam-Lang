# Specification: Escape Analysis That Actually Rewrites MIR

**Status:** Implementation specification; no code change is authorized by this document.  
**Scope:** Make `agam_mir::opt::escape` a conservative, verifiable ARC-elision and stack-promotion transform.  
**Legend:** 🟢 current repository fact; ⚪ proposed type, opcode, invariant, or workflow.

## 0. Ground truth and non-goals

🟢 The preceding audit establishes that the default optimizer invokes escape analysis after DCE (`agam/crates/middle/agam_mir/src/opt/mod.rs:42-55`), but the current implementation only reads MIR through immutable references:

```rust
for block in &func.blocks {
    for instr in &block.instructions {
        match &instr.op { … }
```

`agam/crates/middle/agam_mir/src/opt/escape.rs:100-116`.

🟢 Its claimed promotion is only result construction:

```rust
promoted_locals.push(format!("%{}", alloc.0));
```

`agam/crates/middle/agam_mir/src/opt/escape.rs:211-239`. No `func.blocks`, `block.instructions`, `block.terminator`, or `instr.op` write occurs in `escape.rs:87-240`; the audit is the source of truth: [`AUDIT-optimizer-pipeline-honesty-2026-09-05.md`](AUDIT-optimizer-pipeline-honesty-2026-09-05.md:35).

⚪ This specification does not change source-language ownership defaults, infer user-visible strict ownership, or make speculative partial-path promotion. It only optimizes explicit ARC operations in MIR after proving their allocation value cannot escape on **any** reachable path.

## 1. Exact MIR-level rewrite semantics

### 1.1 Current MIR boundary

🟢 `MirFunction` contains only `params`, `return_ty`, `blocks`, `entry`, target, and GPU configuration (`agam/crates/middle/agam_mir/src/ir.rs:18-39`); `BasicBlock` contains `instructions: Vec<Instruction>` and `terminator` (`ir.rs:52-57`); `Instruction` contains `result`, `ty`, and `op` (`ir.rs:60-68`).

🟢 The only allocation-like opcode is already documented as a **stack allocation**:

```rust
/// Allocate a local variable (stack allocation).
Alloca { name: String, ty: TypeId },
```

`agam/crates/middle/agam_mir/src/ir.rs:108-109`. `StructConstruct` and `EnumConstruct` describe value construction, not allocation ownership (`ir.rs:181-201`). There is no MIR retain or release opcode. Therefore no existing opcode can honestly be rewritten from “heap alloca” to “stack alloca.”

🟢 This agrees with current emitters: the C emitter handles `Op::Alloca` as a local initialized variable (`agam/crates/backends/agam_codegen/src/c_emitter.rs:920-936`), while the LLVM emitter emits LLVM `alloca` (`agam/crates/backends/agam_codegen/src/llvm_emitter.rs:2537-2552`).

### 1.2 Proposed ownership-normalized MIR

⚪ Add the following variants to `Op` in `agam/crates/middle/agam_mir/src/ir.rs`; retain existing `Alloca` unchanged as a stack-local operation.

```rust
/// ⚪ Proposed: ARC-managed heap allocation. `result` is the sole initial owner.
ArcAlloc { name: String, ty: TypeId },

/// ⚪ Proposed: creates one additional ARC ownership token for `value`.
/// `Instruction::result` is the owned alias.
ArcRetain { value: ValueId },

/// ⚪ Proposed: consumes one ownership token for `value`; instruction result is Unit.
ArcRelease { value: ValueId },

/// ⚪ Proposed: runs the non-ARC destructor for a promoted stack object.
/// Omitted for trivially droppable types; instruction result is Unit.
StackDrop { value: ValueId },
```

⚪ Add `AllocationClass` only to analysis output, not to `MirFunction` or `BasicBlock`:

```rust
enum AllocationClass { ArcHeap, Stack, Unknown }
```

This keeps the IR rewrite explicit and serializable in the existing `Instruction { result, ty, op }` shape, rather than adding mutable side tables to `MirFunction`.

⚪ Before escape analysis, a normalization/lowering boundary must materialize every ARC-managed aggregate allocation as exactly one `ArcAlloc` and each ownership-token operation as `ArcRetain`/`ArcRelease`. It must not classify `Alloca`, `StructConstruct`, or `EnumConstruct` as heap allocations merely by opcode name. The existing classifier does exactly that for `Alloca`, struct, and enum construction (`escape.rs:100-113`); this is replaced by the normalized ownership operations.

### 1.3 Eligibility and atomic rewrite

⚪ An `ArcAlloc` value `a` is `NoEscape` only if a monotone whole-function dataflow proof finds no path from `a` (or an alias/projection/aggregate containing it) to:

- `Terminator::Return`; current returns are values (`ir.rs:262-268`);
- an unknown, capturing, impure, external, indirect, recursive-unknown, effect, or coroutine boundary;
- a store through an externally reachable object;
- a closure/handler environment or global/static sink; or
- a phi/aggregate alias that reaches any listed sink.

⚪ `NoEscape` is a whole-all-paths fact. If any feasible path escapes, classify `GlobalEscape` and leave all ARC operations unchanged. No per-branch stack promotion is permitted in the first implementation.

⚪ Given a verified `NoEscape` allocation, rewrite a function atomically as follows:

| Precondition | Rewrite | Required postcondition |
|---|---|---|
| `a = ArcAlloc { name, ty }` and all aliases remain intraprocedural | Replace only `op` with `Alloca { name, ty }`, preserving `result` and `ty`. | All users retain the same `ValueId`; the allocation is stack-backed. |
| `r = ArcRetain { value: v }`, where `v` belongs to `a`’s alias set | Replace `r` with `Copy(v)` only when SSA ownership bookkeeping proves the result is used as the same non-owning intra-function alias; otherwise decline promotion. | No runtime retain remains; value use and dominance remain valid. |
| `u = ArcRelease { value: v }`, where `v` belongs to `a`’s alias set | Remove the release instruction. If `ty` needs destruction, insert one `StackDrop { value: a }` on the unique post-dominating cleanup edge. | Exactly one non-ARC destructor runs on every normal exit; no ARC release remains. |
| Mixed/ambiguous alias or partial escape | Do not rewrite any operation belonging to `a`. | Existing ARC semantics are preserved. |

⚪ The rewrite must build a replacement `Vec<Instruction>` and assign it to each affected `block.instructions`, following the proven pattern used by inlining:

```rust
let original = std::mem::take(&mut block.instructions);
…
block.instructions = rewritten;
```

`agam/crates/middle/agam_mir/src/opt/inline.rs:21-42`. The pass returns `changed = true` only after at least one such assignment changes MIR; summary counts are derived from the diff, never used as a proxy for one.

⚪ All three code generators must reject unlowered proposed ARC opcodes or lower them explicitly. This is mandatory because current backend operation matches enumerate `Op::Alloca` directly (C: `c_emitter.rs:920-936`; LLVM: `llvm_emitter.rs:2537-2552`; GPU: `gpu_emitter.rs:796-803`).

## 2. Interprocedural purity and capture summaries

🟢 `CalleePurityInfo` is currently only `HashSet<String>` (`agam/crates/middle/agam_mir/src/opt/escape.rs:24-28`) and the fixed-point pipeline passes `CalleePurityInfo::default()` (`opt/mod.rs:51-52`). The call rule consequently uses the empty set and treats a call argument as `GlobalEscape` unless the name is in that set (`escape.rs:142-157`).

⚪ Replace it with a serializable per-function summary keyed by a stable function identity and MIR fingerprint:

```rust
struct FunctionEffectSummary {
    function: FunctionKey,
    mir_fingerprint: [u8; 32],
    param_capture: Vec<CaptureKind>, // NoCapture | MayCapture | Escapes
    returns_alias_of: Option<usize>,
    may_allocate: bool,
    may_write_external: bool,
    may_perform_effect: bool,
    is_external: bool,
}

enum CaptureKind { NoCapture, MayCapture, Escapes }
```

⚪ **Computation algorithm.** Build a direct call graph from `Op::Call { callee, args }` (`ir.rs:93`), treating unresolvable names, external/FFI calls, effect performs, and indirect-call encodings as external. Condense the graph into SCCs. Analyze SCCs in reverse topological order; initialize every member of a recursive SCC as maximally conservative (`MayCapture`, effects/writes/allocate true), then iterate transfer functions to a fixed point. A caller can use `NoCapture` for argument `i` only if every reachable callee summary proves it and the function itself has no local capture/store/return route for that parameter. Hitting fuel or an unknown callee yields the conservative summary, not an error or optimistic result.

⚪ **Storage and invalidation.** Persist summaries as a new analysis artifact keyed by `(function identity, MIR fingerprint, transitive callee-summary fingerprints, analysis schema version, target/profile)`. The current repo-local cache key already includes `source_hash`, `semantic_hash`, `backend`, `opt_level`, and `feature_signature` (`agam/crates/runtime/agam_runtime/src/cache.rs:18-29`) but exposes only binary/IR/package/profile artifact kinds (`cache.rs:33-50`); add a ⚪ `EscapeSummary` artifact kind and schema version. On changed MIR or changed callee-summary fingerprint, invalidate that function and every reverse-call-graph dependent; unrelated SCCs remain reusable. A cache miss or deserialization/schema failure recomputes conservatively.

## 3. Retain/release/drop elision

🟢 Current MIR cannot identify a specific retain/release because it has no ARC opcodes (`ir.rs:71-201`); the runtime only provides methods `ArcHeader::retain` and `ArcHeader::release` (`agam/crates/runtime/agam_runtime/src/arc.rs:37-52`) and `AgamArc::retain`/`release` (`arc.rs:153-160`).

⚪ Build an `OwnershipTokenGraph` per normalized function:

1. Seed each `ArcAlloc` with token root `a`.
2. Propagate roots through `Copy`, `ArcRetain`, `Phi`, `StructConstruct`, `EnumConstruct`, `GetField`, `GetIndex`, and local stores/loads using a worklist to a fixed point.
3. Record each `ArcRelease` against the root set of its operand; require an exact single root for elision. Any unknown/multiple root is a non-eligible allocation.
4. For each promoted root, prove token balance along every normal CFG exit. Insert a `StackDrop` only when the type’s destructor classification says it is required; otherwise remove releases. Cleanup-edge placement is computed from post-dominators, not source order.
5. Retain the original ARC allocation and all its operations whenever balance, alias provenance, or destructor placement is not proven.

⚪ A value that escapes on only one branch is **not partially promoted**: join `NoEscape` with `ArgEscape`/`GlobalEscape` using the current ordered lattice intent (`EscapeState` is ordered `NoEscape < ArgEscape < GlobalEscape` at `escape.rs:17-21`) and retain ARC for the root on every path. Path cloning/sinking may be designed only after the whole-all-paths version is verifier-proven.

## 4. Required verifier extension

🟢 The verifier currently collects direct `Op::Alloca` results and rejects only `Terminator::Return` of the exact same `ValueId` (`agam/crates/middle/agam_mir/src/verifier.rs:287-307`). Its use enumerator already knows `Call`, `StoreIndex`, `Phi`, effects, enum payloads, and struct fields (`verifier.rs:332-375`), but it does not use that information to trace stack provenance.

⚪ Add `verify_stack_provenance(func)` after SSA/dominance verification with these required invariants:

| Invariant | Required check |
|---|---|
| Alias closure | Fixed-point provenance map from each `Alloca`/promoted allocation across `Copy`, phi entries, loads/stores, field/index projection, enum/struct construction and extraction. |
| Return | Reject return of any value whose provenance contains stack root, not only the direct alloca result. |
| Aggregate escape | Reject stack root stored into an aggregate that escapes, or aggregate/field/projection passed, returned, or written to external storage. |
| Calls and closures | Reject passing stack provenance to a parameter unless its resolved summary marks that parameter `NoCapture`; reject effects, `HandleWith`, external/unknown calls, coroutine/task creation, dynamic dispatch, and FFI until each has a verified non-capture contract. |
| Phi and CFG | Propagate provenance through every phi predecessor; reject inconsistent root/lifetime use and verify a promoted allocation dominates every use. |
| Releases/drops | For a promoted root, reject any remaining `ArcRetain`/`ArcRelease` in its alias set; require exactly one reachable `StackDrop` for non-trivial destruction on every normal exit and none after move/drop. |
| Backend boundary | Reject proposed `ArcAlloc`/retain/release opcodes reaching a backend path not explicitly capable of lowering them. |

⚪ Add diagnostic variants carrying allocation `ValueId`, root block, sink block/instruction, provenance chain, and summary decision. This replaces the present one-string `EscapingStackAllocation` payload (`verifier.rs:43-47`) with actionable proof evidence while preserving that existing diagnostic for direct returns.

## 5. Rewrite-specific hostile test plan

🟢 `escape_hostile_tests.rs` currently has **4** tests (`agam/crates/middle/agam_mir/tests/escape_hostile_tests.rs:15-336`), and they assert promotion counters/summaries and verifier success, not post-pass MIR changes. The current unit suite likewise asserts `promotion.total_promoted` (`escape.rs:291-300`).

⚪ Add the following direct-MIR tests. Each test snapshots `MirFunction` before the pass, runs the pass, verifies the post-MIR, and asserts exact opcode/block differences—not summary counters.

| Test | Mandatory post-pass assertion |
|---|---|
| Local ARC allocation | `ArcAlloc` is absent; same `ValueId` now has `Alloca`; all matching `ArcRetain`/`ArcRelease` are absent; no unrelated instruction changes. |
| Non-trivial local drop | `ArcRelease` is absent and exactly one `StackDrop { value: root }` exists on the computed cleanup edge. |
| Return through copy | `ArcAlloc` and release remain unchanged when `Copy(root)` is returned. |
| Return through phi | Allocation remains ARC when any phi input reaches return. |
| Aggregate field escape | Allocation remains ARC when inserted into a struct/enum then returned or stored through an external object. |
| Pure non-capturing call | Allocation promotes only with a computed `NoCapture` parameter summary; assert the callee call remains and ARC ops disappear. |
| Unknown/recursive/effect/handler call | Allocation remains ARC; assert no `Alloca` replacement occurs. |
| Branch-local apparent non-escape | One branch release plus another branch return/store leaves allocation ARC globally. |
| Loop and multiple releases | Either exact legal cleanup is produced or no rewrite occurs; assert verifier catches deliberately corrupted balance. |
| Negative verifier corpus | Hand-construct aliases through copy, phi, struct/enum payload, index store, call, and handler; each produces the new provenance diagnostic. |

⚪ Add one property/fuzz harness that generates bounded MIR ownership graphs, runs analysis/rewrite/verifier, and compares observable interpreter/backend output before and after. Any generated program that verifies after rewrite but has changed output is a failure.

## 6. Benchmark validation plan

🟢 The benchmark methodology already requires two warmups, seven measured runs, median wall-clock time, baseline comparisons, and a 5% regression threshold (`agam/benchmarks/METHODOLOGY.md:17-34,91-99`). The harness records wall time, stdout hashes, compile data, peak RSS, and artifact size (`agam/benchmarks/infrastructure/benchmark_harness.py:113-207`; `memory_profiler.py:24-75`).

🟢 The named memory suite is not yet an allocation proof: `memory_allocation.agam`, `garbage_collection.agam`, and `arc_contention.agam` are each 21-line scalar-loop programs whose bodies manipulate `i64` values only (`agam/benchmarks/benchmarks/04_memory_intensive/memory_allocation.agam:3-17`; `garbage_collection.agam:3-17`; `arc_contention.agam:3-17`). They cannot validate ARC-elision generated code today. The tensor/media/ray suite paths are computational workload candidates, but their existing `.agam` sources also must be checked for normalized ARC operations before being claimed as allocation-heavy.

⚪ Add two benchmark fixtures to the existing `04_memory_intensive` suite after normalized ARC lowering exists: (a) repeated non-escaping aggregate construction and local field use, and (b) the same operation returned/stored to force escape. The fixtures must share input, output checksum, backend, optimization level, and target with only escape behavior differing.

⚪ **Proof protocol:**

1. Build an ARC-forced baseline and an escape-rewrite build from identical source/MIR; record generated MIR and emitted C/LLVM IR artifacts.
2. Add a debug-only runtime counter incremented exactly in `ArcAlloc`, `ArcRetain`, and `ArcRelease` lowering, emitted in the benchmark JSON beside the existing result fields. It is not a timing substitute.
3. For the non-escaping fixture, require equal stdout hash/return code, **zero** ARC allocation/retain/release counter events after rewrite, a strictly smaller emitted ARC-operation count in MIR, and no verifier error. For the forced-escape control, require nonzero ARC events and no promotion.
4. Run the existing harness protocol (2 warmups, 7 measured runs) for C/LLVM and JIT where supported; publish median wall time, peak RSS, artifact size, compile time, counter totals, and raw outputs. RSS and binary size are secondary evidence; ARC counters plus emitted-MIR diff establish causality.
5. Claim “faster” only if the same-host median improves by at least 5% with coefficient of variation no greater than the methodology’s 10% warning threshold; claim “allocates less” only if the debug counter is reduced as specified. Otherwise report correctness-only or no measurable win.

## 7. Phased implementation breakdown

🟢 The project’s milestone convention is one roughly week-long daily-cadence phase with shippable acceptance criteria (`doc/RFC-gui-engine.md:87-101`). The following phases use Gemini for daily implementation slices and Claude for the end-of-week evidence review; neither reviewer accepts status prose in place of MIR diffs and test output.

| Phase | Daily-cadence Gemini scope | Weekly Claude review checkpoint / shippable acceptance criteria |
|---|---|---|
| **1 — Ownership-normalized MIR** | Add the ⚪ ARC opcodes, update all MIR serialization/matches and codegen rejection/lowering boundaries, and produce direct IR construction tests. | Every backend either handles or explicitly rejects each proposed opcode; existing `Alloca` behavior remains unchanged; direct tests assert opcode serialization and an ARC lowering shape. |
| **2 — Intraprocedural proof and rewrite** | Implement root/alias/token graph, whole-all-paths `NoEscape`, instruction-list replacement, and conservative no-rewrite fallbacks. | Post-MIR tests prove `ArcAlloc → Alloca` and retain/release removal; any return/store/call ambiguity preserves ARC; no summary counter is accepted as evidence. |
| **3 — Verifier and hostile corpus** | Implement provenance verifier and all direct/aggregate/phi/call/handler hostile tests. | Corrupted promoted MIR is rejected with provenance diagnostics; every promoted fixture verifies; suite contains the specified post-MIR assertions. |
| **4 — Interprocedural summaries and cache** | Implement call graph, SCC fixed point, conservative external handling, sidecar summaries, fingerprints, and reverse-dependency invalidation. | Pure no-capture case promotes; recursive/unknown/effect cases do not; changing a callee invalidates dependents while an unrelated function retains its cached summary. |
| **5 — Measurement and release gate** | Add fixtures, debug counters, artifact capture, baseline/rewrite benchmark runs, and result reporting. | Reproducible raw data satisfies the proof protocol; claims are limited to observed counter/runtime/memory/artifact deltas; forced-escape control demonstrates no unsound promotion. |

## 8. Acceptance decision

⚪ The pass may be described as “stack promotion” or “ARC elision” only after Phase 3 proves actual MIR writes and verifier certification, and Phase 5 supplies generated-code evidence. Before then, it remains an escape-analysis report, regardless of summary field names such as `total_promoted` or `total_arc_elided` (`agam/crates/middle/agam_mir/src/opt/escape.rs:48-51`).
