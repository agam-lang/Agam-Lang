# Compiler Backend Parity Gaps & Core Hardening Audit

**Status**: Active Tracking  
**Audited Targets**: Web Browser Compiler, Cranelift JIT (`agamc run`), LLVM AOT (`agamc build --backend llvm`)  
**Audit Date**: 2026-09-05  

---

## 1. Executive Summary

A comprehensive empirical audit of language constructs across Agam's execution targets revealed that while advanced features (SSA MIR optimization, GPU PTX generation, effect systems, and algebraic handlers) are functional, several fundamental language operations suffer from cross-backend divergence or missing lowering passes.

This document serves as the formal tracking ledger for closing these core gaps.

---

## 2. Identified Deficiencies & Root Cause Analysis

### GAP-01: Range Iterator Method Dispatch (`(start..end).reduce(...)`)
- **Observed Behavior**:
  - Web: Evaluated via JS Array prototype polyfill.
  - Cranelift JIT: Fails with `error: unsupported JIT call target 'reduce'`.
  - LLVM AOT: Fails with `error: load from undeclared local '__lambda_6' in LLVM emitter`.
- **Root Cause**: Method calls on Range expressions are not desugared during HIR lowering into canonical counting loops. Instead, they reach the backend as unresolved function symbols, and closure lambda lifting creates orphaned SSA symbols not registered in the target module's symbol table.
- **Remedy**: Implement AST/HIR desugaring in `agam_hir` for Range method chains (`.map`, `.filter`, `.reduce`) into canonical `while` loops before MIR lowering.

### GAP-02: String Concatenation Pointer Arithmetic in JIT
- **Observed Behavior**:
  - LLVM AOT: Correctly calls `declare i8* @agam_str_concat(i8*, i8*)`.
  - Cranelift JIT: Crashes with `thread 'main' has overflowed its stack`.
- **Root Cause**: In `agam_jit/src/lib.rs` (lines 2731–2736), `MirBinOp::Add` on strings executes `builder.ins().iadd(left, right)`. Because string values are pointers, this performs integer addition of raw memory addresses, creating invalid pointers that loop endlessly when read.
- **Remedy**: Update `agam_jit`'s `MirBinOp::Add` handler to import and invoke `agam_runtime::export::agam_str_concat` whenever either operand is `JitType::Str`.

### GAP-03: Array Literal Construction & Store in JIT
- **Observed Behavior**:
  - LLVM AOT: Successfully lowers fixed array literals via `getelementptr inbounds` + `store`.
  - Cranelift JIT: Fails with `error: indexed aggregate stores are not yet supported by the Cranelift JIT slice`.
- **Root Cause**: Stage 1 implemented `Op::GetIndex` and `Op::StoreIndex` in `agam_codegen::llvm_emitter`, but `agam_jit` was never updated to implement aggregate array stores.
- **Remedy**: Port `Op::StoreIndex` lowering into `agam_jit` using Cranelift stack slot GEP and store instructions.

### GAP-04: Indentation Layout in Struct Declarations (`@lang.base`)
- **Observed Behavior**:
  - Multi-line struct definitions with field indentations fail in `@lang.base` mode with `error: expected expression, found Indent`.
  - Adding `@lang.advance` or formatting struct on a single line bypasses the error.
- **Root Cause**: The Python-style layout lexer in `agam_lexer` inserts `Indent` and `Dedent` tokens inside curly braces `{ ... }` unless suppressed by bracket nesting counters.
- **Remedy**: Ensure the lexer suppresses indentation token emission when bracket nesting depth (`{`, `[`, `(`) is greater than zero.

### GAP-05: Tuple Destructuring Semantic Lowering
- **Observed Behavior**:
  - `let (a, b) = get_pair();` parses without syntax errors, but fails semantic analysis with `error[E3001]: undeclared identifier 'a'`.
- **Root Cause**: The parser accepts tuple patterns in `let` bindings, but `agam_sema` does not yet unpack tuple elements into individual SSA local variables.
- **Remedy**: Implement pattern unpacking in `agam_sema` binding resolution.

---

## 3. Action Plan for Parity Hardening

1. **Sprint A (JIT Hardening)**: Fix GAP-02 (String Concat) and GAP-03 (Array Stores) in `agam_jit`.
2. **Sprint B (Frontend Desugaring)**: Fix GAP-01 (Range desugaring to loops) and GAP-04 (Brace indentation nesting suppression).
3. **Sprint C (Pattern Lowering)**: Fix GAP-05 (Tuple destructuring) in `agam_sema`.
4. **Differential Parity Runner**: Wire these cases into `agam_test::differential` as mandatory gating tests in Stage 0.
