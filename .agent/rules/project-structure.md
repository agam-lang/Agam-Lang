# Project Structure & Architecture Rules

> **Mandatory Rule**: All contributors and AI agents must preserve clean crate and repository boundaries.

---

## 1. Single Source of Truth for Documentation & Web
- **Canonical Docs**: Root `docs/` is the sole canonical documentation directory. Subordinate `agam/docs/` or other parallel doc trees are prohibited.
- **Web Portal Repository**: `agam-lang.github.io/` is the official web documentation and compiler interface. It must remain 100% synchronized with the syntax verified in `note.md` and `docs/`.
- **Archive Quarantine Zone (`archive/`)**: Placeholder or ghost repositories (`archive/repos/`) are quarantined and anti-scannable. Agents must NEVER scan, index, or treat files in `archive/` as active project code or rules.

---

## 2. Compiler Crate Boundaries (`agam/crates/`)
- **Core Separation**:
  - `core/`: `agam_ast`, `agam_lexer`, `agam_parser`, `agam_errors` (pure syntax, zero dependencies on codegen).
  - `middle/`: `agam_hir`, `agam_mir`, `agam_sema` (type checking, SSA optimization, ownership).
  - `backends/`: `agam_codegen` (LLVM, C, PTX, WASM), `agam_jit` (Cranelift).
  - `runtime/`: `agam_runtime` (C-ABI allocators, strings, I/O), `agam_std` (standard library).
  - `tooling/`: `agam_driver`, `agam_target`, `agam_session`, `agam_lsp`, `agam_fmt`, `agam_lint`.
- **God-File Prohibition**: No single source file may exceed 2,500 lines of code. Monolithic files like `agam_driver/src/main.rs` must be split into dedicated submodules under `src/commands/`.

---

## 3. Artifact Hygiene & Workspace Integrity
- **Single Agent Authority**: Agent guidance lives exclusively in root `.agent/`. Nested `.agent/` directories (e.g. inside `agam/`) are prohibited.
- **Artifact Hygiene**: PDBs (`*.pdb`), LLVM IR (`*.ll`), intermediate binaries, and temporary files must never be committed or left lingering in workspace root or crate directories.
- **Benchmark & Example Hygiene**: User examples belong in `examples/`, benchmarks in `benchmarks/`.
- Put runnable user examples under `examples/`.
- Root entrypoints (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `agam/AGENTS.md`, `agam/CLAUDE.md`) are lightweight pointers, not competing sources of truth.
