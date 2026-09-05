# Agam Compiler & Language: Live Problem Ledger & Bug Tracker

> **Mandatory Rule for All AI Agents (Gemini, Claude, Codex) & Contributors**:  
> Whenever you discover a bug, panic, lowering divergence, crash, or parser failure in the Agam compiler or tooling, you **MUST IMMEDIATELY**:
> 1. Assign a priority score and grade (e.g. S-Grade: 120 for crashes).
> 2. Add an entry to the **Master Index Table**.
> 3. Update the **Summary Table** counters.
> 4. Document the symptoms, root cause, and repro snippet in the detailed section below.
> 5. When resolved, mark as `🟢 FIXED`, update the fix counter, and cite the resolution commit or spec.

---

## 1. Summary Table

| Severity Category | Priority Score | Total Logged | 🟢 Fixed | 🟡 In Progress | 🔴 Open | Resolution Rate |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **S-Grade (Blocker / Crash / Corruption)** | **100 – 120** | 2 | 0 | 1 | 1 | 0.0% |
| **A-Grade (Major / Parity / Lowering Gap)** | **70 – 99** | 3 | 0 | 0 | 3 | 0.0% |
| **B-Grade (Minor / Diagnostics / Lexer)** | **40 – 69** | 3 | 0 | 2 | 1 | 0.0% |
| **C-Grade (Ergonomics / Documentation)** | **10 – 39** | 0 | 0 | 0 | 0 | 0.0% |
| **TOTAL** | **10 – 120** | **8** | **0** | **3** | **5** | **0.0%** |

---

## 2. Priority Scoring Rubric

| Grade | Score Range | Definition & Criteria | SLA / Invariant |
|:---:|:---:|---|---|
| **S-Grade** | **100 – 120** | **Compiler crash**, `STATUS_STACK_OVERFLOW`, SIGSEGV, memory corruption, unsound codegen, or panic on user input. | **Zero-Panic Invariant**. Must block release. |
| **A-Grade** | **70 – 99** | **Cross-backend divergence** between JIT and LLVM AOT; missing lowering pass; unsupported core primitive syntax. | **Parity Invariant**. Breaks dual-backend proof. |
| **B-Grade** | **40 – 69** | **Diagnostic quality**; missing error recovery; spurious layout indent tokens; missing compiler warnings; documentation drift. | Quality & ergonomics. Addressed in active stage. |
| **C-Grade** | **10 – 39** | Minor cosmetic CLI formatting, warning noise, or non-blocking documentation typos. | Handled opportunistically. |

---

## 3. Master Index Table

| ID | Priority | Grade | Crate / Layer | Problem Summary | Status | Stage Link |
|:---|:---:|:---:|---|---|:---:|:---|
| [`ISSUE-001`](#issue-001-msvc-dev-debug-stack-frame-overflow-in-monolithic-fn-main) | **120** | **S-Grade** | `agam_driver` | MSVC `dev` debug stack frame overflow in 16.7K-line monolithic `main.rs` | 🟡 **IN PROGRESS** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`ISSUE-002`](#issue-002-string-concatenation-pointer-arithmetic-crash-in-jit) | **115** | **S-Grade** | `agam_jit` | String concatenation uses raw pointer integer addition (`iadd`), crashing the runtime | 🔴 **OPEN** | [Stage 0 / 1](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`ISSUE-003`](#issue-003-range-method-dispatch-reduce-not-desugared-in-hir) | **95** | **A-Grade** | `agam_hir` / `agam_sema` | Range method chains (`(0..10).reduce(...)`) fail in JIT and emit undeclared locals in LLVM | 🔴 **OPEN** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`ISSUE-004`](#issue-004-missing-cranelift-jit-indexed-aggregate-store-slice) | **90** | **A-Grade** | `agam_jit` | Indexed aggregate stores (`arr[i] = val`) supported in LLVM but missing in Cranelift JIT | 🔴 **OPEN** | [Stage 0 / 1](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`ISSUE-005`](#issue-005-tuple-destructuring-variable-binding-unlowered-in-sema) | **85** | **A-Grade** | `agam_sema` | Tuple destructuring bindings (`let (a, b) = pair;`) unhandled during semantic resolution | 🔴 **OPEN** | [Stage 0 / 2](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`ISSUE-006`](#issue-006-spurious-indentation-inside-braces-in-base-profile) | **65** | **B-Grade** | `agam_lexer` | Layout mode inserts spurious `Indent`/`Dedent` inside curly braces `{ ... }` in base profile | 🔴 **OPEN** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`ISSUE-007`](#issue-007-parser-lacks-pratt-panic-mode-error-synchronization) | **60** | **B-Grade** | `agam_parser` | Parser terminates on first syntax error without recovery tokens or `Expr::Error` nodes | 🟡 **IN PROGRESS** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`ISSUE-008`](#issue-008-documentation-code-snippet-syntax-drift-across-docs) | **50** | **B-Grade** | `docs/` | ~15 docs have outdated syntax (`Int` vs `i32`, `.to_string()`), failing `doctest_check.py` | 🟡 **IN PROGRESS** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |

---

## 4. Detailed Problem Records

### ISSUE-001: MSVC `dev` Debug Stack Frame Overflow in Monolithic `fn main()`
- **Priority**: `120 (S-Grade: Blocker / Crash)`
- **Component**: `crates/tooling/agam_driver/src/main.rs`
- **Symptoms**: Running `agamc` built under debug mode (`target/debug/agamc.exe`) on Windows crashes immediately with `0xc00000fd (STATUS_STACK_OVERFLOW)`.
- **Root Cause**: Monolithic 16,768-line `main.rs` contains all CLI command matches inside a single stack frame. MSVC debug codegen sums all local variables across all branches without stack slot coloring, exceeding the default Windows 1MB thread stack.
- **Fix Strategy**: Modularize `main.rs` into `src/commands/` submodules (`build.rs`, `run.rs`, `daemon.rs`, `doctor.rs`) and extract `agam_target` and `agam_session`. Target size: $< 1,500$ lines.
- **Status**: 🟡 **IN PROGRESS** (Tracked in Stage 0).

---

### ISSUE-002: String Concatenation Pointer Arithmetic Crash in JIT
- **Priority**: `115 (S-Grade: Critical / Memory Corruption)`
- **Component**: `crates/backends/agam_jit/src/lib.rs:2731-2736`
- **Symptoms**: Evaluating string concatenation (`let s = "a" + "b";`) in Cranelift JIT causes a thread stack overflow / segmentation fault.
- **Root Cause**: `MirBinOp::Add` on string pointers emits raw `builder.ins().iadd(left, right)`, performing integer addition on memory addresses instead of calling `agam_str_concat`.
- **Fix Strategy**: Intercept string binary addition in JIT lowering and emit a call to `agam_runtime`'s `agam_str_concat(i8*, i8*) -> i8*`.
- **Status**: 🔴 **OPEN** (Tracked in Stage 0 / 1).

---

### ISSUE-003: Range Method Dispatch (`.reduce()`) Not Desugared in HIR
- **Priority**: `95 (A-Grade: Major / Broken Syntax)`
- **Component**: `crates/middle/agam_hir` & `crates/backends/agam_codegen`
- **Symptoms**: Calling `(0..10).reduce(...)` fails in JIT (`unsupported JIT call target 'reduce'`) and fails in LLVM (`load from undeclared local '__lambda_6'`).
- **Root Cause**: Method calls on Range instances are not desugared into canonical loop constructs during HIR lowering.
- **Fix Strategy**: Implement HIR desugaring for Range method pipelines (`.map`, `.filter`, `.reduce`) into canonical counting loops.
- **Status**: 🔴 **OPEN** (Tracked in Stage 0).

---

### ISSUE-004: Missing Cranelift JIT Indexed Aggregate Store Slice
- **Priority**: `90 (A-Grade: Major / Backend Divergence)`
- **Component**: `crates/backends/agam_jit/src/lib.rs`
- **Symptoms**: `arr[i] = val` works in LLVM AOT, but fails in Cranelift JIT with `error: indexed aggregate stores are not yet supported by the Cranelift JIT slice`.
- **Root Cause**: `Op::StoreIndex` was implemented for LLVM codegen in Stage 1, but the Cranelift lower path was left unimplemented.
- **Fix Strategy**: Implement `Op::StoreIndex` in Cranelift JIT by computing element offset via pointer arithmetic and emitting `builder.ins().store(...)`.
- **Status**: 🔴 **OPEN** (Tracked in Stage 0 / 1).

---

### ISSUE-005: Tuple Destructuring Variable Binding Unlowered in Sema
- **Priority**: `85 (A-Grade: Major / Language Feature Gap)`
- **Component**: `crates/middle/agam_sema/src/resolver.rs`
- **Symptoms**: `let (x, y) = get_pair();` fails with unresolved symbol errors during semantic analysis.
- **Root Cause**: AST parser recognizes tuple patterns, but semantic resolver treats the pattern as a single identifier.
- **Fix Strategy**: Extend pattern matching and let-binding resolution in `agam_sema` to unpack tuple elements into individual local bindings.
- **Status**: 🔴 **OPEN** (Tracked in Stage 0 / 2).

---

### ISSUE-006: Spurious Indentation Inside Braces in Base Profile
- **Priority**: `65 (B-Grade: Minor / Lexer Layout Issue)`
- **Component**: `crates/core/agam_lexer/src/layout.rs`
- **Symptoms**: Multiline struct or block definitions inside curly braces `{ ... }` fail in `@lang.base` mode with `error: expected expression, found Indent`.
- **Root Cause**: Layout-sensitive lexer does not suppress `Indent`/`Dedent` token emission when inside explicit curly braces `{ ... }`.
- **Fix Strategy**: Track brace/bracket nesting depth in the lexer; when depth $> 0$, suppress layout indentation tokens.
- **Status**: 🔴 **OPEN** (Tracked in Stage 0).

---

### ISSUE-007: Parser Lacks Pratt Panic-Mode Error Synchronization
- **Priority**: `60 (B-Grade: Minor / Diagnostics & Resilience)`
- **Component**: `crates/core/agam_parser/src/parser.rs`
- **Symptoms**: The parser immediately halts upon encountering the first syntax error, preventing IDEs and CLI from reporting multiple diagnostics.
- **Root Cause**: Absence of token synchronization loops (skipping to `;`, `}`, `fn`, `let`) and missing error AST placeholder nodes.
- **Fix Strategy**: Introduce Pratt error recovery tokens and `ast::Expr::Error` recovery nodes as specified in Stage 0 Section 2.4.
- **Status**: 🟡 **IN PROGRESS** (Tracked in Stage 0).

---

### ISSUE-008: Documentation Code Snippet Syntax Drift Across `docs/`
- **Priority**: `50 (B-Grade: Minor / Doc Quality)`
- **Component**: `docs/`
- **Symptoms**: `python scripts/doctest_check.py` fails on ~15 documentation chapters due to outdated syntax (e.g. `Int` instead of `i32`, unsupported `.to_string()`, invalid enum match arrows).
- **Root Cause**: Documentation chapters written before syntax stabilization drift from verified compiler reality.
- **Fix Strategy**: Remediate all documentation code fences to adhere to verified syntax in `note.md`; integrate into CI.
- **Status**: 🟡 **IN PROGRESS** (Tracked in Stage 0 Section 2.8).
