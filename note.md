# Agam Language & Compiler: Core Audit, Discrepancies & Roadmap

> **Author**: Lead Language Designer & Systems Architect  
> **Date**: 2026-09-05  
> **Status**: Mandatory Reference for All Contributors & AI Agents (Gemini, Claude, Codex)  

---

## 1. Executive Summary: The "Too Basic" Discrepancies

A systematic empirical audit comparing the **Web Playground**, the **Cranelift JIT Engine (`agamc run`)**, and the **LLVM AOT Backend (`agamc build --backend llvm`)** surfaced critical discrepancies in foundational language constructs.

While the compiler boasts advanced architectural features (SSA MIR optimization, CUDA PTX GPU emission, algebraic effects, SMT contract verification), several basic operations (range iteration, string concatenation, array stores, and pattern destructuring) diverged across backends or crashed the runtime.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 COMPILATION TARGETS                                    │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ Web Browser Playground   │ Cranelift JIT (agamc run)   │ LLVM AOT (agamc build)        │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ JavaScript AST Evaluator │ In-Memory Native JIT        │ Optimizing LLVM IR (.ll)      │
│ Uses JS array polyfills  │ Zero-dependency execution   │ Emits vectorization & LTO     │
│ Diverged from native!    │ Fast, but lowering gaps!    │ Full features, requires Clang │
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

---

## 2. Forensic Audit Findings: The 5 Core Gaps

### GAP-01: Range Iteration & Method Dispatch (`(0..10).reduce(...)`)
* **The Illusion**: The Web Playground used JavaScript array methods to make `(0..10).reduce(0, |acc, x| acc + x)` appear functional.
* **The Reality**:
  * **Cranelift JIT**: Fails with `error: unsupported JIT call target 'reduce'` (method call dispatch on range objects is not lowered).
  * **LLVM AOT**: Lowers through HIR/MIR, extracts lambda `__lambda_6`, but fails in LLVM emission with `error: load from undeclared local '__lambda_6'`.
* **Root Cause**: Range method chains (`.map`, `.filter`, `.reduce`) are not desugared during frontend HIR lowering into canonical counting loops.
* **Verified Working Equivalent**:
  ```agam
  @lang.advance
  fn main() -> i32 {
      let mut sum = 0;
      let mut i = 0;
      while i < 10 {
          sum = sum + i;
          i = i + 1;
      }
      print_int(sum); // Output: 45
      0
  }
  ```

---

### GAP-02: String Concatenation Pointer Arithmetic in JIT
* **The Illusion**: String addition `let full = greeting + name;` is standard in modern languages.
* **The Reality**:
  * **LLVM AOT**: Works properly. Generates `call i8* @agam_str_concat(i8*, i8*)`.
  * **Cranelift JIT**: **Crashes the process** with `thread 'main' has overflowed its stack`.
* **Root Cause**: In `agam_jit/src/lib.rs` (lines 2731–2736), `MirBinOp::Add` on strings executes raw `builder.ins().iadd(left, right)`. Because strings are pointers in memory, it performs integer arithmetic on two memory addresses, producing a corrupted pointer that crashes dereference routines.
* **Verified Working Equivalent**:
  ```agam
  // Print multi-argument values sequentially without string addition:
  println("Hello, ", name);
  ```

---

### GAP-03: Array Literal Construction & Store in JIT
* **The Illusion**: `let arr = [10, 20, 30]; print_int(arr[1]);` is a basic test case.
* **The Reality**:
  * **LLVM AOT**: Works properly. Lowers via `getelementptr inbounds` and stores elements in sequence.
  * **Cranelift JIT**: Fails with `error: indexed aggregate stores are not yet supported by the Cranelift JIT slice`.
* **Root Cause**: Stage 1 implemented `Op::GetIndex` and `Op::StoreIndex` in `agam_codegen::llvm_emitter`, but never ported the store slice to `agam_jit`.

---

### GAP-04: Python-Style Layout Indentation inside Braces (`@lang.base`)
* **The Illusion**: Users should be able to write multiline structs naturally:
  ```agam
  struct Point {
      x: i32,
      y: i32,
  }
  ```
* **The Reality**: Fails in `@lang.base` mode with `error: expected expression, found Indent`.
* **Root Cause**: The layout lexer in `agam_lexer` inserts `Indent`/`Dedent` tokens inside curly braces `{ ... }` unless bracket depth suppression is active.
* **Verified Working Equivalent**:
  ```agam
  // Option A: Specify @lang.advance (systems mode):
  @lang.advance
  struct Point { x: i32, y: i32 }

  // Option B: Format on a single line in base mode:
  struct Point { x: i32, y: i32 }
  ```

---

### GAP-05: Rust-Style `{}` Format Strings vs Multi-Argument Printing
* **The Illusion**: Code examples showed `println("Sum = {}", sum);`.
* **The Reality**: Native Agam does not parse `{}` as format specifiers; it literally prints `"Sum = {}45"`.
* **Verified Working Syntax**:
  ```agam
  println("Sum = ", sum); // Outputs: Sum = 45
  ```

---

## 3. Why Did AI Agents Make These Mistakes?

1. **Hallucinating Syntax Across Languages**: Previous agents working on Agam assumed Rust syntax (`"{}"`, closures `|x| x + 1`) or Python syntax without testing against `agamc.exe`.
2. **False Confidence from Synthetic Web Polyfills**: Agents wrote JS polyfills in `agam-lang.github.io/app.js` and assumed that because the web page printed "45", the native compiler supported the feature.
3. **Horizontal Breadth Over Vertical Verification**: 220 unit tests passed because tests isolated specific crates (e.g. testing parser AST generation without running end-to-end code generation through JIT and LLVM).
4. **Weak Guardrails**: The existing rules did not strictly forbid publishing unverified code.

---

## 4. Immediate Remediation Plan (Core Parity Sprint)

| Gap | Component | Remediation Action |
|---|---|---|
| **GAP-01** | `agam_hir` | Desugar Range method calls (`.reduce`, `.map`) into canonical `while` loops before MIR lowering. |
| **GAP-02** | `agam_jit` | Divert `MirBinOp::Add` for `JitType::Str` to invoke `agam_runtime::export::agam_str_concat`. |
| **GAP-03** | `agam_jit` | Implement `Op::StoreIndex` in `agam_jit` using Cranelift stack slot GEP and stores. |
| **GAP-04** | `agam_lexer` | Suppress `Indent`/`Dedent` emission when bracket nesting counter (`{`, `[`, `(`) is $> 0$. |
| **GAP-05** | `agam_sema` | Wire tuple destructuring patterns (`let (a, b) = ...`) to SSA local bindings. |

---

## 5. Macro Development Roadmap (Stages 0 to 7)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               8-STAGE COMPILER ROADMAP                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Stage 0: Modular Driver & Differential Parity Test Suite (JIT vs LLVM Bitwise Parity)  │
│ Stage 1: Dynamic Memory Buffers & Slices (C-ABI Runtime)                        [DONE] │
│ Stage 2: Dynamic Arbitrary-Field Structs & Tagged Enums (No 8-field limit)      [DONE] │
│ Stage 3: Direct Syscalls & PAL Engine (Zero-libc mmap, IOCP, epoll, raw sockets)[NEXT] │
│ Stage 4: Foreign Function Binding Generator (agam-bindgen parsing C headers)           │
│ Stage 5: SIMD Vector Engine (AVX2, AVX-512, NEON, RVV intrinsic codegen)               │
│ Stage 6: Production Standard Library & Media Codecs (4K Image, FLAC, Async HTTP)       │
│ Stage 7: Self-Hosting Bootstrap & Parity Benchmarks vs C++, Rust, Go, Python           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```
