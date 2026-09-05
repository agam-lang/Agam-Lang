# Language & Compiler Guardrails

> **Mandatory Rule**: All AI agents (Gemini, Claude, Codex, Antigravity) and contributors MUST adhere to these guardrails. Zero exceptions.

---

## 1. The Dual-Backend Verification Invariant (CRITICAL)

**NEVER write, document, demo, or commit any Agam code snippet unless it has been empirically verified by executing `agamc.exe`:**
```powershell
# Must execute cleanly on Cranelift JIT:
.\agam\target\release\agamc.exe run path/to/file.agam

# Must lower cleanly on LLVM AOT:
.\agam\target\release\agamc.exe build --backend llvm path/to/file.agam
```
- **Prohibition on Speculative Syntax**: Do NOT assume a feature works because it exists in Rust, Python, or C++.
- **Prohibition on Synthetic Web Polyfills**: The web playground and documentation must NEVER simulate features in JavaScript (e.g. fake `.reduce()` or regex `{}` string formatters) that fail on the native compiler `agamc.exe`.

---

## 2. Syntax Truth Table & Hallucination Defense

| Prohibited Assumption / Hallucination | Why It Is Prohibited | Mandatory Verified Syntax |
| :--- | :--- | :--- |
| `println("Val = {}", v)` | Agam does NOT format Rust-style `{}` placeholders in native printing; it literally prints `{}`. | `println("Val = ", v)` or `print_int(v)` |
| `(0..10).reduce(...)` / `.map(...)` | Higher-order iterator method dispatch on Range expressions is not unified across JIT/LLVM yet. | Use canonical imperative loops: `while i < 10 { ... }` |
| `let s = str1 + str2;` (in JIT) | Cranelift JIT currently maps string `+` to integer address addition (`iadd`), triggering a stack overflow. | Pass multiple arguments to `println(str1, str2)` or use LLVM backend. |
| `let arr = [1, 2, 3]; arr[0] = 5;` (in JIT) | Cranelift JIT slice lacks `Op::StoreIndex` lowering. | Fixed arrays are currently supported in LLVM AOT; use scalar variables in JIT. |
| Multi-line braced struct in `@lang.base` | The Python-style layout lexer injects `Indent` inside `{}`. | Use `@lang.advance` for brace syntax, or write single-line structs in `@lang.base`. |
| `let (a, b) = tuple;` | The parser accepts tuple patterns, but `agam_sema` has not wired destructuring bindings to SSA locals. | Assign tuple to a scalar and access elements directly. |

---

## 3. Profile Boundary Rules

Agam supports two explicit profiles:
1. **`@lang.base` (Python Simplicity)**:
   - Indentation-sensitive layout (tabs/spaces define blocks with `:`).
   - Untyped or optionally typed signatures: `fn add(a, b): return a + b`.
   - Never nest multiline curly braces `{}` inside `@lang.base` files.
2. **`@lang.advance` (Systems Control)**:
   - Explicit braces `{}` and semicolons `;`.
   - Strict static typing with explicit return types: `fn main() -> i32 { return 0; }`.
   - Direct memory layouts, aggregate structs, and manual hardware control.

---

## 4. Differential Parity Rule

Every compiler pass and standard library feature must maintain bitwise parity between:
1. **Cranelift JIT (`agam_jit`)** — for instant REPL and development runs (`agamc run`).
2. **LLVM AOT (`agam_codegen`)** — for release builds, vectorization, and LTO (`agamc build`).
If a feature only works on one backend, it must be explicitly flagged with a structured compiler warning, not silently miscompiled.
