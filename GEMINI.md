# Gemini CLI / Antigravity — Agam-Lang

> Core compiler → `agam/CLAUDE.md`. This file = Gemini-specific setup.

## Multi-AI Workflow

You share this workspace with Claude and Codex. Read existing context, respect checklists.

## Skills

@c:\Users\ksvik\Projects\Agam-Lang\.agent\skills\caveman\SKILL.md
@c:\Users\ksvik\Projects\Agam-Lang\.agent\skills\caveman-compress\SKILL.md
@c:\Users\ksvik\Projects\Agam-Lang\.agent\skills\graphify\SKILL.md

## Rules

- `.agent/rules/token-efficiency.md` — terse output
- `.agent/rules/language-guardrails.md` — Agam ≠ Python ≠ Rust
- `.agent/rules/project-structure.md` — crate boundaries

## Quick Start

| Task | Read |
|------|------|
| Compiler work | `agam/CLAUDE.md` |
| Current phases | `.agent/phases/current.md` |
| Next priority | `.agent/phases/next.md` |

## Build & Verify

```powershell
cargo check --manifest-path agam/Cargo.toml
cargo test  --manifest-path agam/Cargo.toml
```
