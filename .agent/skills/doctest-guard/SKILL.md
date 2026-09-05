---
name: doctest-guard
description: "Verify that all Agam code snippets in docs/ and README.md compile and execute without drift."
---

# Doctest Guard

**Purpose**: Eliminates documentation drift by treating documentation examples as an executable test suite against `agamc.exe`.

## When to Run
- Before committing any changes to markdown documentation (`docs/`, `README.md`).
- After refactoring language syntax, parser rules, or standard library APIs.
- Whenever running `/doctest` in chat.

## Usage

Run the automated doctest extraction and validation runner:
```powershell
python scripts/doctest_check.py
```

## Directives in Documentation
To annotate snippets in Markdown:
- `<!-- SKIP-DOCTEST -->`: For incomplete code fragments or conceptual pseudocode.
- `<!-- BACKEND: llvm-only -->`: For features supported on LLVM AOT only.
- `<!-- BACKEND: jit-only -->`: For features supported on Cranelift JIT only.

Place the directive immediately preceding the ` ```agam ` code block.
