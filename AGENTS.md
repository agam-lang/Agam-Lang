# Agam-Lang Agent Instructions

- This is the organization workspace. For compiler work, read `agam/CLAUDE.md`.
- State assumptions before coding, keep changes minimal, and avoid unrelated edits.
- Use `.agent/specs/active/`, `.agent/evals/`, and `.agent/wiki/` only when relevant.
- **CRITICAL**: Do NOT place implementation plans, task checklists, or walkthroughs in your internal/hidden artifact directories (e.g. `.gemini` or `.cursor`). **ALL** project-related specs, plans, and checklists must be placed locally in `.agent/specs/active/details/` so that all agents can read them and cross-collaborate.
- Treat `.agam` files as Agam source, not Python or Rust.

## Compiler Verify

```powershell
cargo check --manifest-path agam/Cargo.toml
cargo test  --manifest-path agam/Cargo.toml
```
