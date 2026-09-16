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
| **S-Grade** | Critical: Crashes, Stack Overflows, Memory Safety, Panics | 3 | 0 | 2 | 1 | 0.0% |
| **A-Grade** | Major: Dual-Backend Parity Divergence, Missing Lowering Gaps | 6 | 0 | 6 | 0 | 0.0% |
| **B-Grade** | Minor: Diagnostics, Parser Recovery, Layout Lexer, Doc Drift | 6 | 0 | 4 | 2 | 0.0% |
| **C-Grade** | Trivial: Ergonomics, Non-blocking Cosmetic Warnings | 1 | 0 | 1 | 0 | 0.0% |
| **TOTAL** | **All Compiler Problems Tracked** | **16** | **0** | **13** | **3** | **0.0%** |

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
| [`B-Grade: #1`](#b-grade-1-spurious-indentation-inside-braces-in-base-profile) | `agam_lexer` | Layout mode inserts spurious `Indent`/`Dedent` inside curly braces `{ ... }` in base profile | 🔴 **Still Exists** | [Spec 001](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/001-base-mode-type-declarations.md) |
| [`B-Grade: #2`](#b-grade-2-parser-lacks-pratt-panic-mode-error-synchronization) | `agam_parser` | Parser terminates on first syntax error without recovery tokens or `Expr::Error` nodes | 🟡 **In Progress** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`B-Grade: #3`](#b-grade-3-documentation-code-snippet-syntax-drift-across-docs) | `docs/` | ~15 docs have outdated syntax (`Int` vs `i32`, `.to_string()`), failing `doctest_check.py` | 🟡 **In Progress** | [Stage 0](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/active/details/STAGE-00-driver-modularization-and-hardening.md) |
| [`S-Grade: #3`](#s-grade-3-silent-wrong-mode-lexing-with-leading-file-comments) | `agam_lexer` | `detect_mode` skips whitespace only; leading comments cause silent fallback to base mode | 🔴 **Still Exists** | [Spec 003](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/003-manifest-syntax-profile.md) |
| [`A-Grade: #4`](#a-grade-4-no-call-arity-and-argument-type-checking-in-sema) | `agam_sema` | Function call expressions (`ExprKind::Call`) do not check argument count or parameter types | 🔴 **Still Exists** | [Spec 002](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/002-call-arity-checking.md) |
| [`A-Grade: #5`](#a-grade-5-silent-no-op-syscall-in-cranelift-jit) | `agam_jit` | `Op::Syscall` emits `default_value(0)` in JIT while emitting real inline assembly in LLVM AOT | 🔴 **Still Exists** | [Parity Invariant](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/rules/wasm-parity-invariant.md) |
| [`A-Grade: #6`](#a-grade-6-refinement-type-predicates-silently-discarded-in-hir) | `agam_hir` | `{v: i32 | v > 0}` drops predicate with `..` at `lower.rs:1174`, compiling without constraint | 🔴 **Still Exists** | [Spec 008](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/008-refinement-types-reject.md) |
| [`B-Grade: #4`](#b-grade-4-inconsistent-struct-literal-disambiguation-heuristics) | `agam_parser` | Two conflicting heuristics (`looks_like_struct_literal` vs raw `peek_at(1)`) for struct literals | 🔴 **Still Exists** | [Spec 004](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/004-struct-literal-restrictions.md) |
| [`B-Grade: #5`](#b-grade-5-syntax-dialects-unenforced-in-parser) | `agam_parser` | Parser lacks dialect awareness; colon-indent and braces can be mixed freely in any file | 🔴 **Still Exists** | [Spec 006](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/006-dialect-enforcement.md) |
| [`B-Grade: #6`](#b-grade-6-var-and-base-dynamic-are-misleading-no-ops) | `agam_ast` / `agam_lexer` | `var` collapses to untyped `Any`; `@lang.base.dynamic` has identical behavior to static base | 🔴 **Still Exists** | [Spec 007](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/007-remove-var-and-dynamic-profile.md) |
| [`C-Grade: #1`](#c-grade-1-cli-surface-bloat-before-registry-launch) | `agam_driver` | 31+ top-level CLI subcommands with overlapping execution, supply chain, and agent verbs | 🔴 **Still Exists** | [Spec 009](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/009-cli-verb-consolidation.md) |

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

---

### S-Grade: #3: Silent Wrong-Mode Lexing with Leading File Comments
- **Index**: `S-Grade: #3`
- **Component**: `crates/core/agam_lexer/src/lexer.rs:52-71`
- **Fixed?**: 🔴 **Still Exists** (Tracked in [Spec 003](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/003-manifest-syntax-profile.md))
- **Symptoms**: Files starting with license comments or copyright notices (e.g., `// Copyright 2026\n@lang.advance`) are silently lexed in `BaseStatic` mode, triggering spurious `expected expression, found Indent` errors.
- **Root Cause**: `detect_mode` uses `eat_while` that only skips whitespace and BOM, stopping at the first `/` of a comment. It fails all `@lang` prefixes and silently falls back to `BaseStatic`.
- **Fix Strategy**: Lift package syntax mode into `agam.toml` (`[project] syntax = "advance"`). Enforce directive placement to be the first non-comment token or emit `E0140`.

---

### A-Grade: #4: No Call Arity and Argument Type Checking in Sema
- **Index**: `A-Grade: #4`
- **Component**: `crates/middle/agam_sema/src/checker.rs:368-383`
- **Fixed?**: 🔴 **Still Exists** (Tracked in [Spec 002](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/002-call-arity-checking.md))
- **Symptoms**: Calling a function with the wrong number of arguments (e.g., `add(1, 2, 3)` for `fn add(a: i32, b: i32)`) compiles without error.
- **Root Cause**: `ExprKind::Call` handling in `checker.rs` does not compare argument counts or unify argument types against callee parameters; it merely calls `self.infer_expr(callee)` and returns a fresh type variable.
- **Fix Strategy**: Implement call-site arity and argument type validation in `agam_sema`, and explicitly declare builtin `print`/`println` as variadic so legitimate multi-arg printing remains valid.

---

### A-Grade: #5: Silent No-Op Syscall in Cranelift JIT
- **Index**: `A-Grade: #5`
- **Component**: `crates/backends/agam_jit/src/lib.rs`
- **Fixed?**: 🔴 **Still Exists** (Tracked in [WASM Parity Invariant](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/rules/wasm-parity-invariant.md))
- **Symptoms**: Syscall operations emit real inline assembly in LLVM AOT, but return `default_value(0)` as a silent no-op in Cranelift JIT.
- **Root Cause**: Absence of JIT syscall emulation or host trampoline execution.
- **Fix Strategy**: Provide runtime syscall trampolines in `agam_runtime` or explicitly reject unsupported syscalls in JIT rather than silently returning 0.

---

### A-Grade: #6: Refinement Type Predicates Silently Discarded in HIR Lowering
- **Index**: `A-Grade: #6`
- **Component**: `crates/middle/agam_hir/src/lower.rs:1174`
- **Fixed?**: 🔴 **Still Exists** (Tracked in [Spec 008](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/008-refinement-types-reject.md))
- **Symptoms**: Refinement types like `{v: i32 | v > 0}` parse successfully but provide zero verification or runtime assertions.
- **Root Cause**: `lower.rs:1174` matches `TypeExprKind::Refined { base, .. } => self.resolve_type_expr(base)`, silently discarding the predicate AST with `..`.
- **Fix Strategy**: Explicitly reject refinement types with error `E0180` ("refinement types are parsed but not checked") until `agam_smt` solver integration is ready.

---

### B-Grade: #4: Inconsistent Struct-Literal Disambiguation Heuristics
- **Index**: `B-Grade: #4`
- **Component**: `crates/core/agam_parser/src/parser.rs:60-96` & `1238-1253`
- **Fixed?**: 🔴 **Still Exists** (Tracked in [Spec 004](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/004-struct-literal-restrictions.md))
- **Symptoms**: Multiline struct literals work in path expressions via `looks_like_struct_literal` but fail in postfix loops due to fixed lookahead (`peek_at(1) == Identifier`) that does not skip layout tokens.
- **Root Cause**: Two conflicting disambiguation heuristics in different parser positions.
- **Fix Strategy**: Replace ad-hoc lookaheads with Rust-style restriction flags (`NO_STRUCT_LITERAL`) threaded through condition and match-scrutinee positions.

---

### B-Grade: #5: Syntax Dialects Unenforced in Parser
- **Index**: `B-Grade: #5`
- **Component**: `crates/core/agam_parser/src/parser.rs:1164-1178`
- **Fixed?**: 🔴 **Still Exists** (Tracked in [Spec 006](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/006-dialect-enforcement.md))
- **Symptoms**: `@lang.advance` files can use Pythonic colon-indent blocks, and `@lang.base` files can use curly braces, with no diagnostics.
- **Root Cause**: `agam_parser` has no `SyntaxMode` field and accepts both block styles unconditionally in `parse_block`.
- **Fix Strategy**: Pass `SyntaxMode` into the parser and enforce block delimiters (curly braces for advance, colon-indent for base) with `E0160`/`E0161`.

---

### B-Grade: #6: `var` and `@lang.base.dynamic` Are Misleading No-Ops
- **Index**: `B-Grade: #6`
- **Component**: `crates/core/agam_lexer/src/lexer.rs` & `crates/core/agam_ast/src/types.rs`
- **Fixed?**: 🔴 **Still Exists** (Tracked in [Spec 007](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/007-remove-var-and-dynamic-profile.md))
- **Symptoms**: `var` is marketed as a dynamic typing mode but merely lowers to untyped `Any` without dynamic dispatch or runtime tags. `@lang.base.dynamic` has identical behavior to static base.
- **Root Cause**: Dynamic typing was never hooked up to runtime tagging or dispatch.
- **Fix Strategy**: Remove `var` and `@lang.base.dynamic`; make dynamic typing explicit via `let x: Any = ...`.

---

### C-Grade: #1: CLI Surface Bloat Before Registry Launch
- **Index**: `C-Grade: #1`
- **Component**: `crates/tooling/agam_driver/src/cli.rs`
- **Fixed?**: 🔴 **Still Exists** (Tracked in [Spec 009](file:///c:/Users/ksvik/Projects/Agam-Lang/.agent/specs/syntax/009-cli-verb-consolidation.md))
- **Symptoms**: 31+ top-level subcommands clutter `--help` and overlap in scope (`run`/`exec`/`dev`/`daemon`).
- **Root Cause**: Accumulation of experimental and tooling commands without namespace discipline.
- **Fix Strategy**: Consolidate to 13 core verbs and move utility/agent verbs behind `agamc tool <subcommand>` and `agamc registry <subcommand>`.

