# Agam Syntax & Tooling Redesign — Specification Index

> **Status:** proposed
> **Created:** 2026-09-16
> **Authority:** these specs are subordinate to `note.md` (Compiler Parity Truth)
> and `.agent/rules/`. Where a spec conflicts with observed compiler behaviour,
> `note.md` wins and the spec must be amended, not worked around.

## How to use this index

Each spec is self-contained. An implementing agent needs **only**:

1. The single spec file it is implementing.
2. `docs/grammar.ebnf` (the base grammar reference).
3. The compiler source.

Do **not** read the specs out of order and do **not** implement a spec whose
`Depends on` list is unsatisfied — several specs are unsound in isolation
(notably 005, which is unsafe without 004).

## Hard precondition for all specs

**None of these specs may be marked complete until the dual-backend differential
harness executes both backends and compares stdout byte-for-byte.** Today
`crates/tooling/agam_test/src/differential.rs` runs the JIT and string-greps the
LLVM IR (`llvm_ir.contains("add ")`). Every spec below changes the front end and
therefore both backends. Landing them against a grep-based parity suite will
introduce silent JIT/LLVM divergences at the rate features ship.

Track this as `PRE-000` and close it before starting `001`.

## Implementation order

| # | Spec | Fixes | Depends on | Cost |
|---|---|---|---|---|
| 001 | [Base-mode type declarations](001-base-mode-type-declarations.md) | ASYM-1 / B-Grade #1 — `@lang.base` cannot declare a multi-line struct or enum | — | Low |
| 002 | [Call arity and argument checking](002-call-arity-checking.md) | No arity checking exists anywhere in `agam_sema` | — | Low–Med |
| 003 | [Manifest syntax profile](003-manifest-syntax-profile.md) | Leading comment silently switches a file to base mode | — | Low |
| 004 | [Struct-literal restriction flags](004-struct-literal-restrictions.md) | Two conflicting struct-literal lookahead heuristics | — | Med |
| 005 | [Blocks as expressions](005-blocks-as-expressions.md) | No implicit return; match arms cannot hold statements | **004** | High |
| 006 | [Dialect enforcement](006-dialect-enforcement.md) | Dialects are unenforced; mixing is silently legal | **003** | Low |
| 007 | [Remove `var` and `@lang.base.dynamic`](007-remove-var-and-dynamic-profile.md) | `var` is a mislabelled `Any`; the dynamic profile is a no-op | **002** | Low |
| 008 | [Refinement types: reject explicitly](008-refinement-types-reject.md) | Refinement predicates are parsed then silently discarded | — | Low |
| 009 | [CLI verb consolidation](009-cli-verb-consolidation.md) | 33 top-level subcommands before the registry has one package | — | Med |
| 010 | [Manifest completion](010-manifest-completion.md) | No `[features]` producer side, no targets, no profiles | **003** | Med |

## Spec template contract

Every spec in this directory contains, in this order:

1. Status + motivation (linked to a named friction point)
2. Formal grammar diff (old production vs new production, EBNF)
3. AST / HIR / MIR impact, including an explicit dialect-symmetry statement
4. Worked examples — valid programs with expected output, invalid programs with exact expected errors
5. Acceptance criteria — concrete and checkable
6. A required mutation/fuzz test — **mandatory**, designed to fail a hardcoded implementation
7. Open questions the spec does **not** resolve

If any section is missing, the spec is not ready to implement. Escalate rather
than filling the gap by inference.

## Rule for implementing agents

**Where a spec's "Open questions" section flags something, you must stop and ask.
You may not decide it yourself.** These are core semantics questions that were
deliberately left open, not oversights. Silently choosing an answer is the
failure mode these specs exist to prevent.
