# Truth-First Documentation

## The Rule
Every code snippet in `docs/`, `README.md`, or `agam-lang.github.io` MUST be copy-pasteable and empirically verified against the native compiler `agamc.exe`.

## Enforcement
1. Before adding or committing any Agam snippet to documentation, test it:
   ```powershell
   agamc run snippet.agam
   agamc build --backend llvm snippet.agam
   ```
2. If a snippet demonstrates a feature that currently works on only one backend, explicitly tag it:
   - `<!-- BACKEND: llvm-only -->`
   - `<!-- BACKEND: jit-only -->`
3. Never copy speculative syntax from Rust or Python into docs without execution proof.
4. When fixing or changing compiler semantics, update all documentation and examples referencing that syntax in the same commit.
5. Use the `doctest-guard` skill (`python scripts/doctest_check.py`) to validate all markdown code fences across `docs/`.
