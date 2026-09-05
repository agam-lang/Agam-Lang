---
name: safe-commit
description: "Pre-commit verification workflow enforcing zero-warning builds, dual-backend proofs, and conventional commits."
---

# Safe Commit

**Purpose**: Enforces non-bypassable pre-commit hygiene for all human and AI contributors.

## Pre-Commit Checklist

Before issuing any git commit:

1. **Dual-Backend Proof**:
   ```powershell
   python scripts/prove.py
   ```
   Must pass 100% of canonical tests across both JIT and LLVM.

2. **Clean Typecheck & Lints**:
   ```powershell
   python scripts/cargo_lens.py check
   ```

3. **Stage Review**:
   Never `git add .` blindly. Check `git status` to ensure no `.pdb`, `.exe`, `.ll`, or temp scratch files are staged.

4. **Conventional Commit Format**:
   Write structured commit messages:
   - `feat(<crate>): ...`
   - `fix(<crate>): ...`
   - `docs(<crate>): ...`
   - `refactor(<crate>): ...`
