# Agam-Lang Organization — Agent Instructions

> **Compiler Core**: `agam/CLAUDE.md`. **Root Workspace**: Cross-repo coordination.
> **Backend Parity & Verified Syntax**: Read `note.md` before writing or documenting Agam code.
> **Live Problem Ledger**: Read and update `issues.md` whenever any compiler defect, crash, or gap is discovered.

## 🤖 Unified Multi-AI Workflow
Continuous session across Gemini, Claude, Codex. Rotate models freely.
1. **Handoff**: Continue exactly where previous agent stopped. Track state in `task.md`.
2. **Dual-Backend Verification**: Never commit or document Agam code without testing via `python scripts/prove.py` or `agamc run` and `agamc build --backend llvm`.
3. **Bug Ledger Rule**: When encountering any compiler bug, crash, or lowering failure, immediately log it in `issues.md` with priority score and update the summary counters.
4. **Context Hygiene**: Never dump raw cargo output. Use `python scripts/cargo_lens.py <check|test|build>`.

## Quick Start
- **Parity Truth**: `note.md`
- **Problem Ledger**: `issues.md`
- **Active Phase**: `.agent/specs/active/current.md` | Next: `.agent/specs/active/next.md`
- **Syntax & Tooling Redesign Specs**: `.agent/specs/syntax/000-INDEX.md`
- **Rules**: `.agent/rules/` (`bug-ledger.md`, `language-guardrails.md`, `zero-panic-invariant.md`, `wasm-parity-invariant.md`, `commit-discipline.md`, `truth-first-docs.md`, `error-message-quality.md`, `project-structure.md`, `token-efficiency.md`, `context-hygiene.md`, `compiler-literature.md`, `algorithm-synthesis.md`)
- **Skills** (`.agent/skills/`): `cargo-lens`, `language-guard`, `caveman`, `audit-harden`, `unwrap-ratchet`, `diff-fuzz`, `spec-archiver`, `benchmark-guard`, `doctest-guard`, `golden-test`, `safe-commit`.

## Architecture & Memory
- Persistent memory: Consult `.agent/memory/handoff.md` and `.agent/notes/` before refactoring.
- Remote Test Node: Intel i5 secondary validation target at `192.168.0.150` (see `.agent/notes/remote_test_node.md`).
