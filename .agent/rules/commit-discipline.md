# Git Commit Discipline

## Format
All commits MUST use Conventional Commits:
- `feat(parser): add tuple destructuring support`
- `fix(jit): correct string concat pointer arithmetic`
- `refactor(mir): split optimization pass into submodules`
- `test(codegen): add golden file tests for array lowering`
- `docs(note): update GAP-02 status to resolved`

## Rules
1. Never commit with generic messages like "fix", "update", "changes".
2. Scope must name the affected crate or component (`parser`, `jit`, `codegen`, `sema`, `runtime`, `driver`, `docs`).
3. Run `python scripts/prove.py` before every commit — zero exceptions.
4. Never `git add .` blindly — review staged files to ensure no `.pdb`, `.exe`, `.ll`, or temp scratch files leak into git.
