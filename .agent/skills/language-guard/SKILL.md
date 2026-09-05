---
name: language-guard
description: Prevent Python/Rust syntax assumptions; ground code in verified Agam syntax via scripts/prove.py.
---

# Language Guard

Use this skill whenever syntax, parser, examples, or code-generation expectations could drift toward Python or Rust assumptions.

## Workflow

1. Read `note.md` and `.agent/rules/language-guardrails.md`.
2. Run `python scripts/prove.py` to inspect the canonical 100% verified syntax.
3. Inspect working examples under `examples/01_basics/*.agam` and `benchmarks/suites/`.
4. Base syntax decisions on repo reality, not on generic language priors:
   - **No Rust formatting**: Use `println("text = ", val)` (comma separation).
   - **No unlowered range methods**: Use `while i < n { ... }`.
   - **No JIT string add**: Avoid `str + str` in JIT; pass multiple arguments to `println`.
5. Keep ML, tensor, dataframe, and effect features grounded in Agam's own compiler/runtime model.
6. Verify any new `.agam` file with both `agamc run` and `agamc build --backend llvm`.

## Authoritative Sources

- `note.md` (Syntax Truth Table & Core Gaps)
- `scripts/prove.py` (Automated Dual-Backend Proof Harness)
- `examples/01_basics/*.agam` (8 verified runnable programs)
- `agam/crates/core/agam_parser` & `agam/crates/middle/agam_sema`
