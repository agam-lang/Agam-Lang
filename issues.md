# Agam Compiler & Language: Live Problem Ledger & Bug Tracker

> **Mandatory Rule for All AI Agents (Gemini, Claude, Codex) & Contributors**:  
> Whenever you discover a bug, panic, lowering divergence, crash, or parser failure in the Agam compiler or tooling, you **MUST IMMEDIATELY**:
> 1. Assign it to its Priority Grade (`S-Grade`, `A-Grade`, `B-Grade`, `C-Grade`) and increment the problem number for that grade (e.g. `S-Grade: #1`, `S-Grade: #2`, ... `S-Grade: #120`).
> 2. Add an entry to the **Master Index Table** showing whether the problem is **Fixed** (`🟢 Yes`) or **Still Exists** (`🔴 Still Exists` / `🟡 In Progress`).
> 3. Update the **Summary Table** counters (Total Found, Fixed, Still Exists).
> 4. Document the exact symptoms, root cause, and repro snippet in the detailed section below.
> 5. When resolved, mark as `🟢 Yes (Fixed)`, decrement "Still Exists", increment "Fixed", and cite the resolution commit.

---

## 1. Summary Table: Problem Status by Priority

| Priority Grade | Severity & Nature | Total Found | 🟢 Fixed | 🔴 Still Exists (Open) | 🟡 In Progress | Resolution Rate |
|:---:|---|:---:|:---:|:---:|:---:|:---:|
| **S-Grade** | Critical: Crashes, Stack Overflows, Memory Safety, Panics | 2 | 0 | 1 | 1 | 0.0% |
| **A-Grade** | Major: Dual-Backend Parity Divergence, Missing Lowering Gaps | 3 | 0 | 3 | 0 | 0.0% |
| **B-Grade** | Minor: Diagnostics, Parser Recovery, Layout Lexer, Doc Drift | 3 | 0 | 1 | 2 | 0.0% |
| **C-Grade** | Trivial: Ergonomics, Non-blocking Cosmetic Warnings | 0 | 0 | 0 | 0 | - |
| **TOTAL** | **All Compiler Problems Tracked** | **8** | **0** | **5** | **3** | **0.0%** |

---

## 2. Priority Grade Definitions

| Grade | Category | Criteria & Impact | SLA / Invariant |
|:---:|---|---|---|
| **S-Grade** | **Fatal / Blocker** | **Compiler crash**, `STATUS_STACK_OVERFLOW`, memory corruption, SIGSEGV, or panic on user input. | **Zero-Panic Invariant**. Must block releases. |
| **A-Grade** | **Backend Divergence** | **Cranelift JIT $\ne$ LLVM AOT divergence**; missing lowering pass; unsupported core primitive syntax. | **Parity Invariant**. Breaks dual-backend proof. |
| **B-Grade** | **Diagnostics & Layout** | **Missing error recovery tokens**; spurious layout indents; poor diagnostics; doc snippet drift. | Quality & ergonomics. Addressed in active stage. |
| **C-Grade** | **Ergonomics** | Minor cosmetic CLI formatting, warning noise, or doc typos. | Handled opportunistically. |

---

## 3. Master Index Table

| Index (Priority: Number) | Component / Crate | Problem Summary | Fixed? | Stage Reference |
|:---|---|---|:---:|:---|
| [`S-Grade: #1`](#s-grade-1-msvc-dev-debug-stack-frame-overflow-in-monolithic-fn-main) | `agam_driver` | MSVC `dev` debug stack frame overflow in 16.7K-line monolithic `main.rs` | 🟡 **In Progress** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`S-Grade: #2`](#s-grade-2-string-concatenation-pointer-arithmetic-crash-in-jit) | `agam_jit` | String concatenation uses raw pointer integer addition (`iadd`), crashing process | 🔴 **Still Exists** | [Stage 0 / 1](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`A-Grade: #1`](#a-grade-1-range-method-dispatch-reduce-not-desugared-in-hir) | `agam_hir` / `agam_sema` | Range method chains (`(0..10).reduce(...)`) fail in JIT and emit undeclared locals in LLVM | 🔴 **Still Exists** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`A-Grade: #2`](#a-grade-2-missing-cranelift-jit-indexed-aggregate-store-slice) | `agam_jit` | Indexed aggregate stores (`arr[i] = val`) supported in LLVM but missing in Cranelift JIT | 🔴 **Still Exists** | [Stage 0 / 1](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`A-Grade: #3`](#a-grade-3-tuple-destructuring-variable-binding-unlowered-in-sema) | `agam_sema` | Tuple destructuring bindings (`let (a, b) = pair;`) unhandled during semantic resolution | 🔴 **Still Exists** | [Stage 0 / 2](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`B-Grade: #1`](#b-grade-1-spurious-indentation-inside-braces-in-base-profile) | `agam_lexer` | Layout mode inserts spurious `Indent`/`Dedent` inside curly braces `{ ... }` in base profile | 🔴 **Still Exists** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`B-Grade: #2`](#b-grade-2-parser-lacks-pratt-panic-mode-error-synchronization) | `agam_parser` | Parser terminates on first syntax error without recovery tokens or `Expr::Error` nodes | 🟡 **In Progress** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`B-Grade: #3`](#b-grade-3-documentation-code-snippet-syntax-drift-across-docs) | `docs/` | ~15 docs have outdated syntax (`Int` vs `i32`, `.to_string()`), failing `doctest_check.py` | 🟡 **In Progress** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |

---

## 4. Detailed Problem Records

### S-Grade: #1: MSVC `dev` Debug Stack Frame Overflow in Monolithic `fn main()`
- **Index**: `S-Grade: #1`
- **Component**: `crates/tooling/agam_driver/src/main.rs`
- **Fixed?**: 🟡 **In Progress** (Tracked in Stage 0)
- **Symptoms**: Running `agamc` built under debug mode (`target/debug/agamc.exe`) on Windows crashes immediately with `0xc00000fd (STATUS_STACK_OVERFLOW)`.
- **Root Cause**: Monolithic 16,768-line `main.rs` contains all CLI command matches inside a single stack frame. MSVC debug codegen sums all local variables across all branches without stack slot coloring, exceeding the default Windows 1MB thread stack.
- **Fix Strategy**: Modularize `main.rs` into `src/commands/` submodules (`build.rs`, `run.rs`, `daemon.rs`, `doctor.rs`) and extract `agam_target` and `agam_session`. Target size: $< 1,500$ lines.

---

### S-Grade: #2: String Concatenation Pointer Arithmetic Crash in JIT
- **Index**: `S-Grade: #2`
- **Component**: `crates/backends/agam_jit/src/lib.rs:2731-2736`
- **Fixed?**: 🔴 **Still Exists** (Tracked in Stage 0 / 1)
- **Symptoms**: Evaluating string concatenation (`let s = "a" + "b";`) in Cranelift JIT causes a thread stack overflow / segmentation fault.
- **Root Cause**: `MirBinOp::Add` on string pointers emits raw `builder.ins().iadd(left, right)`, performing integer addition on memory addresses instead of calling `agam_str_concat`.
- **Fix Strategy**: Intercept string binary addition in JIT lowering and emit a call to `agam_runtime`'s `agam_str_concat(i8*, i8*) -> i8*`.

---

### A-Grade: #1: Range Method Dispatch (`.reduce()`) Not Desugared in HIR
- **Index**: `A-Grade: #1`
- **Component**: `crates/middle/agam_hir` & `crates/backends/agam_codegen`
- **Fixed?**: 🔴 **Still Exists** (Tracked in Stage 0)
- **Symptoms**: Calling `(0..10).reduce(...)` fails in JIT (`unsupported JIT call target 'reduce'`) and fails in LLVM (`load from undeclared local '__lambda_6'`).
- **Root Cause**: Method calls on Range instances are not desugared into canonical loop constructs during HIR lowering.
- **Fix Strategy**: Implement HIR desugaring for Range method pipelines (`.map`, `.filter`, `.reduce`) into canonical counting loops.

---

### A-Grade: #2: Missing Cranelift JIT Indexed Aggregate Store Slice
- **Index**: `A-Grade: #2`
- **Component**: `crates/backends/agam_jit/src/lib.rs`
- **Fixed?**: 🔴 **Still Exists** (Tracked in Stage 0 / 1)
- **Symptoms**: `arr[i] = val` works in LLVM AOT, but fails in Cranelift JIT with `error: indexed aggregate stores are not yet supported by the Cranelift JIT slice`.
- **Root Cause**: `Op::StoreIndex` was implemented for LLVM codegen in Stage 1, but the Cranelift lower path was left unimplemented.
- **Fix Strategy**: Implement `Op::StoreIndex` in Cranelift JIT by computing element offset via pointer arithmetic and emitting `builder.ins().store(...)`.

---

### A-Grade: #3: Tuple Destructuring Variable Binding Unlowered in Sema
- **Index**: `A-Grade: #3`
- **Component**: `crates/middle/agam_sema/src/resolver.rs`
- **Fixed?**: 🔴 **Still Exists** (Tracked in Stage 0 / 2)
- **Symptoms**: `let (x, y) = get_pair();` fails with unresolved symbol errors during semantic analysis.
- **Root Cause**: AST parser recognizes tuple patterns, but semantic resolver treats the pattern as a single identifier.
- **Fix Strategy**: Extend pattern matching and let-binding resolution in `agam_sema` to unpack tuple elements into individual local bindings.

---

### B-Grade: #1: Spurious Indentation Inside Braces in Base Profile
- **Index**: `B-Grade: #1`
- **Component**: `crates/core/agam_lexer/src/layout.rs`
- **Fixed?**: 🔴 **Still Exists** (Tracked in Stage 0)
- **Symptoms**: Multiline struct or block definitions inside curly braces `{ ... }` fail in `@lang.base` mode with `error: expected expression, found Indent`.
- **Root Cause**: Layout-sensitive lexer does not suppress `Indent`/`Dedent` token emission when inside explicit curly braces `{ ... }`.
- **Fix Strategy**: Track brace/bracket nesting depth in the lexer; when depth $> 0$, suppress layout indentation tokens.

---

### B-Grade: #2: Parser Lacks Pratt Panic-Mode Error Synchronization
- **Index**: `B-Grade: #2`
- **Component**: `crates/core/agam_parser/src/parser.rs`
- **Fixed?**: 🟡 **In Progress** (Tracked in Stage 0 Section 2.4)
- **Symptoms**: The parser immediately halts upon encountering the first syntax error, preventing IDEs and CLI from reporting multiple diagnostics.
- **Root Cause**: Absence of token synchronization loops (skipping to `;`, `}`, `fn`, `let`) and missing error AST placeholder nodes.
- **Fix Strategy**: Introduce Pratt error recovery tokens and `ast::Expr::Error` recovery nodes as specified in Stage 0 Section 2.4.

---

### B-Grade: #3: Documentation Code Snippet Syntax Drift Across `docs/`
- **Index**: `B-Grade: #3`
- **Component**: `docs/`
- **Fixed?**: 🟡 **In Progress** (Tracked in Stage 0 Section 2.8)
- **Symptoms**: `python scripts/doctest_check.py` fails on ~15 documentation chapters due to outdated syntax (e.g. `Int` instead of `i32`, unsupported `.to_string()`, invalid enum match arrows).
- **Root Cause**: Documentation chapters written before syntax stabilization drift from verified compiler reality.
- **Fix Strategy**: Remediate all documentation code fences to adhere to verified syntax in `note.md`; integrate into CI.
