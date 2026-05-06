# Agam-Lang Organization — Agent Instructions

> **Core compiler** → read `agam/CLAUDE.md` (self-contained briefing).
> This root workspace is for organization-level cross-repo coordination.

## 🤖 Multi-AI Workflow

All agents (Gemini, Claude, Codex) share this workspace. Read existing context, respect ongoing checklists, don't invent separate workflows.

## Organization Repos

| Category | Repositories |
|----------|-------------|
| **Core** | `agam/` — compiler, runtime, tooling, packaging |
| **Libraries** | `agam-http/`, `agam-json/`, `agam-crypto/`, `agam-ml/`, `agam-db/`, `agam-web/`, `agam-async/`, `agam-cli/` |
| **Learning** | `agam-book/`, `agam-by-example/`, `examples/` |
| **IDE** | `agam-vscode/`, `agam-intellij/` |
| **Infra** | `benchmarks/`, `agamlab/`, `sdk-packs/`, `registry-index/`, `rfcs/` |
| **Web** | `agam-lang.github.io/` |
| **Community** | `awesome-agam/`, `.github/` |

## Quick Start

| Task | Read |
|------|------|
| Compiler work | `agam/CLAUDE.md` |
| Current phases | `.agent/phases/current.md` |
| What to build next | `.agent/phases/next.md` |
| Phase checklists | `.agent/phases/details/` |

## Build & Verify (compiler)

```powershell
cargo check --manifest-path agam/Cargo.toml
cargo test  --manifest-path agam/Cargo.toml
```

## Skills

| Skill | Purpose |
|-------|---------|
| `caveman` | ~75% token reduction via terse output |
| `caveman-compress` | ~46% input token reduction on context files |
| `graphify` | Codebase → knowledge graph |
| `benchmark-guard` | Benchmark-driven validation |
| `language-guard` | Prevent treating `.agam` as Python/Rust |

Skills live in `.agent/skills/`.

## Rules

| Rule | File |
|------|------|
| Token efficiency | `.agent/rules/token-efficiency.md` |
| Language guardrails | `.agent/rules/language-guardrails.md` |
| Project structure | `.agent/rules/project-structure.md` |
