# Agam audit + spec drop — what's here and where it goes

## 1. `AGAM-DX-AUDIT.md`
Parts 1–6: syntax audit of both dialects, redesign proposals (R-1..R-8),
tooling/ecosystem gap analysis, honest core evaluation, scorecard, prioritized
roadmap. Read this first. It is standalone and not needed to implement the specs.

## 2. `spec-drop/.agent/specs/syntax/`
Part 7: eleven files, ready to copy into the repo.

Copy them in with:

```powershell
# from C:\Users\ksvik\Projects\Agam-Lang
mkdir .agent\specs\syntax
copy <downloaded>\spec-drop\.agent\specs\syntax\*.md .agent\specs\syntax\
```

Then add one line to `.agent/specs/active/next.md` pointing at
`.agent/specs/syntax/000-INDEX.md`, and one to `CLAUDE.md` / `AGENTS.md` under
"Read First" so agents pick it up.

### Path convention rationale
`.agent/specs/active/details/STAGE-NN-*.md` is your existing convention for
stage work. These are cross-cutting syntax/tooling changes that don't belong to
a single stage, so they get a sibling directory `.agent/specs/syntax/` with its
own numbering and index. If you'd rather fold them into the stage system, they
renumber cleanly — nothing references the filenames except `000-INDEX.md`.

## Before implementing anything
`000-INDEX.md` declares a hard precondition, `PRE-000`: the differential harness
in `crates/tooling/agam_test/src/differential.rs` must execute both backends and
compare stdout, instead of string-grepping LLVM IR. Every spec here changes the
front end and therefore both backends. Landing them against a grep-based parity
suite will introduce silent JIT/LLVM divergences at the rate features ship.
