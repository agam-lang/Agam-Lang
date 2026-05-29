# Agam-Lang Organization — Agent Instructions

> **Core compiler** → read `agam/CLAUDE.md` (self-contained briefing).
> This root workspace is for organization-level cross-repo coordination.

## 🤖 4 Core AI Engineering Principles

All agents (Gemini, Claude, Codex) must strictly adhere to these rules:

1. **Think Before Coding:** Explicitly state assumptions and surface ambiguity before writing code. (Store architectural synthesis in `.agent/wiki/`)
2. **Simplicity First:** Write the absolute minimum amount of code required. No speculative features.
3. **Surgical Changes:** Touch only the code necessary to fulfill the request. Do not break unrelated code.
4. **Goal-Driven Execution:** Work towards testable success criteria. Loop independently against verification scripts in `.agent/evals/`.

## Organization Repos

| Category | Repositories |
| --- | --- |
| **Core** | `agam/` — compiler, runtime, tooling, packaging |
| **Libraries** | `agam-http/`, `agam-json/`, `agam-crypto/`, `agam-ml/`, `agam-db/`, `agam-web/`, `agam-async/`, `agam-cli/` |
| **Learning** | `agam-book/`, `agam-by-example/`, `examples/` |
| **IDE** | `agam-vscode/`, `agam-intellij/` |
| **Infra** | `benchmarks/`, `agamlab/`, `sdk-packs/`, `registry-index/`, `rfcs/` |
| **Web** | `agam-lang.github.io/` |
| **Community** | `awesome-agam/`, `.github/` |

## Quick Start & Specs Pipeline

| Task | Read |
| --- | --- |
| Compiler work | `agam/CLAUDE.md` |
| Active Tasks | `.agent/specs/active/` |
| Completed Tasks | `.agent/specs/archive/` |
| Evaluation Cases | `.agent/evals/` |
| LLM Knowledge Wiki | `.agent/wiki/` |

## Build & Verify (compiler)

```powershell
cargo check --manifest-path agam/Cargo.toml
cargo test  --manifest-path agam/Cargo.toml
```

## Skills

| Skill | Purpose |
| --- | --- |
| `caveman` | ~75% token reduction via terse output |
| `caveman-compress` | ~46% input token reduction on context files |
| `benchmark-guard` | Benchmark-driven validation |
| `language-guard` | Prevent treating `.agam` as Python/Rust |

Skills live in `.agent/skills/`.

## Rules

| Rule | File |
| --- | --- |
| Token efficiency | `.agent/rules/token-efficiency.md` |
| Language guardrails | `.agent/rules/language-guardrails.md` |
| Project structure | `.agent/rules/project-structure.md` |
