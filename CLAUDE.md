# Claude Code — Agam-Lang Organization

> Core compiler → `agam/CLAUDE.md` (self-contained briefing).

This is the organization-level workspace. For compiler work, read `agam/CLAUDE.md`.
For cross-repo coordination, read `AGENTS.md`.

**CRITICAL RULE FOR CLAUDE**: You MUST place ALL artifacts, implementation plans, and checklists locally in `c:\Users\ksvik\Projects\Agam-Lang\.agent\specs\active\details\`! DO NOT save them in hidden directories or internal storage. This is a hard requirement so that other AI agents can collaborate on the project!
## Build & Verify

```powershell
cargo check --manifest-path agam/Cargo.toml
cargo test  --manifest-path agam/Cargo.toml
```
