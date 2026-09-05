# Agam-Lang Organization — Claude Instructions

Root `.agent/` is canonical shared truth.

## Read First
- `note.md` (Compiler Parity Truth & Verified Syntax)
- `AGENTS.md`
- `.agent/specs/active/current.md`
- `.agent/rules/`

## Key Rules
- Compiler: `agam/CLAUDE.md`
- Dual-Backend Verification: Test all Agam code with `python scripts/prove.py` or `agamc run` & `agamc build --backend llvm`.
- Build Filter: Always use `python scripts/cargo_lens.py` instead of raw cargo.
- caveman active by default.
