# 008 — Refinement Types: Reject Explicitly

**Status:** proposed
**Depends on:** PRE-000
**Component:** `agam_hir`, `agam_errors`
**Ledger:** new — file as `A-Grade: #6` (silent loss of a user-written constraint)

---

## 1. Motivation

`agam_ast/src/types.rs` defines:

```rust
/// Refinement type: `{ base | predicate }`.  E.g., `{v: i32 | v > 0}`
Refined { base: Box<TypeExpr>, predicate: Box<super::expr::Expr> },
```

HIR lowering, `agam_hir/src/lower.rs:1174`:

```rust
agam_ast::types::TypeExprKind::Refined { base, .. } => self.resolve_type_expr(base),
```

The predicate is discarded with `..`. No error, no warning. A user who writes
`fn sqrt(x: {v: f64 | v >= 0.0}) -> f64` gets a function taking plain `f64` and
believes it is constrained.

This is worse than not supporting the syntax. An unsupported construct produces a
parse error the user can act on; this produces a program that compiles and lies.
It is the same class of defect as the JIT's `Op::Syscall` returning
`default_value(0)` — a silent no-op standing in for a real operation.

There is an `agam_smt` crate (498 LOC) that presumably exists to discharge these
obligations, but nothing connects it to this path.

**This spec chooses the small, immediate fix: reject explicitly.** Implementing
refinement checking is a large project (see §7.2) and should not gate closing a
correctness hole that can be closed in an hour.

---

## 2. Formal grammar diff

**None.** The syntax remains parseable — deliberately, so the error can be
precise and point at the predicate.

```ebnf
(* Grammar UNCHANGED.  Refinement types continue to parse. *)
Type                = ... | RefinedType | ... ;
RefinedType         = "{" , Identifier , ":" , Type , "|" , Expression , "}" ;

(*  Static semantics, NEW:
    Lowering a RefinedType to HIR is error E0180.
    The predicate expression is NOT type-checked, NOT evaluated, and NOT
    discarded silently.                                                       *)
```

If the project later implements checking, only the static-semantics clause
changes; the grammar is already correct.

---

## 3. AST / HIR / MIR impact

**AST:** none. `TypeExprKind::Refined` stays.

**HIR:** `lower.rs:1174` changes from silently resolving the base to emitting
`E0180`. The `..` in the pattern must be replaced with a binding on `predicate`
so its span can be reported — **the `..` is the bug, textually.**

**MIR / backends:** none.

### Dialect symmetry statement

The error is emitted during HIR lowering, downstream of all syntax. Both dialects
produce the identical diagnostic. AC-3 asserts this.

---

## 4. Worked examples

### 4.1 Invalid — refinement in a parameter type

```agam
@lang.advance
fn sqrt_pos(x: {v: f64 | v >= 0.0}) -> f64 {
    return x;
}
```

Expected, exactly:

```
error[E0180]: refinement types are parsed but not checked
 --> input.agam:2:16
  |
2 | fn sqrt_pos(x: {v: f64 | v >= 0.0}) -> f64 {
  |                ^^^^^^^^^^^^^^^^^^^ this predicate would be silently ignored
  |                         --------- predicate `v >= 0.0` is not enforced
  |
  = note: accepting this would compile a program whose stated constraint
          has no effect
  = fix: use `f64` and check the precondition explicitly:
           if x < 0.0 { return -1.0; }
  = law: AGAM-SYNTAX-008 §2
```

The secondary span **must** point at the predicate, not the whole type — that is
the part being dropped.

### 4.2 Invalid — refinement in a return type

```agam
@lang.advance
fn abs_val(n: i32) -> {v: i32 | v >= 0} {
    if n < 0 { return 0 - n; }
    return n;
}
```

Expected: `E0180`, primary span on `{v: i32 | v >= 0}`, secondary on `v >= 0`.

### 4.3 Invalid — refinement in a let annotation, base mode

```agam
@lang.base
fn main() -> i32:
    let x: {v: i32 | v > 0} = 5
    return x
```

Expected: `E0180`, identical message body to 4.1 modulo spans.

### 4.4 Invalid — refinement in a struct field

```agam
@lang.advance
struct Bounded { value: {v: i32 | v < 100} }
```

Expected: `E0180` on the field type.

### 4.5 Invalid — nested refinement

```agam
@lang.advance
fn f(x: [{v: i32 | v > 0}; 4]) -> i32 { return 0; }
```

Expected: `E0180` on the inner refinement. Exactly one error — the outer array
type must not produce a second diagnostic.

### 4.6 Valid — the base type alone

```agam
@lang.advance
fn sqrt_pos(x: f64) -> f64 {
    if x < 0.0 { return -1.0; }
    return x;
}
```

Expected: compiles. This is the migration target shown in 4.1's fix line.

---

## 5. Acceptance criteria

- **AC-1** — 4.1 through 4.5 each produce exactly one `E0180`.
- **AC-2** — In every case the secondary span covers the predicate expression
  only. Asserted by comparing the secondary span's byte range to the predicate's
  `Expr::span`, not by string matching.
- **AC-3 (symmetry)** — 4.1 and 4.3 produce identical `code` and identical message
  body after span normalisation.
- **AC-4** — 4.5 produces exactly one diagnostic, not two.
- **AC-5** — 4.6 compiles and runs under both backends.
- **AC-6** — `grep -n 'Refined { base, .. }' crates/middle/agam_hir/src/lower.rs`
  returns nothing. The `..` must be gone. Grep output pasted into the commit
  message.
- **AC-7** — No `.agam` file in the repository uses refinement syntax. Verified by
  a corpus grep; if any does, it is migrated in the same commit.
- **AC-8** — `cargo test`, `clippy -D warnings`, `fmt --check` via
  `python scripts/cargo_lens.py`.
- **AC-9** — `issues.md` gains `A-Grade: #6`, closed. A forward-looking entry is
  added to `.agent/specs/active/next.md` for the eventual implementation, citing
  `agam_smt`.

---

## 6. Required mutation test — MANDATORY

The shallow implementation here is obvious: match on the literal string
`"{v: i32 | v > 0}"` or on a single hardcoded type position. This test defeats
both.

Add `crates/middle/agam_hir/tests/mutation_008_refinement_rejection.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-008.
//! Rejection must follow the AST shape at every type position and for any
//! predicate, and must never fire on a non-refined type.

/// Every syntactic position a type can occupy, with one `{}` slot.
fn type_positions() -> Vec<&'static str> {
    vec![
        "fn f(p: {}) -> i32 {{ return 0; }}",
        "fn f() -> {} {{ return def(); }}",
        "fn f() -> i32 {{ let v: {} = def(); return 0; }}",
        "struct S {{ field: {} }}",
        "fn f(p: [{}; 4]) -> i32 {{ return 0; }}",
        "fn f(p: &{}) -> i32 {{ return 0; }}",
        "type Alias = {};",
    ]
}

/// Structurally distinct refinements — no two share a token sequence.
fn refinements() -> Vec<&'static str> {
    vec![
        "{v: i32 | v > 0}",
        "{n: i64 | n != 0}",
        "{x: f64 | x >= 0.0}",
        "{b: bool | b}",
        "{k: i32 | k > 0 && k < 100}",
        "{s: i32 | helper(s)}",
    ]
}

#[test]
fn every_refinement_is_rejected_in_every_type_position() {
    // 7 positions x 6 refinements = 42 cases. A hardcoded matcher fails this.
    for (i, pos) in type_positions().iter().enumerate() {
        for (j, refi) in refinements().iter().enumerate() {
            let src = format!(
                "@lang.advance\nfn def() -> i32 {{ return 0; }}\nfn helper(s: i32) -> bool {{ return true; }}\n{}\n",
                pos.replace("{}", refi));
            let err = compile_str(&src)
                .unwrap_or_else(|_| panic!("pos={i} refi={j} unexpectedly compiled"))
                ;
            assert_eq!(err.code(), "E0180", "pos={i} refi={j}");
        }
    }
}

#[test]
fn the_secondary_span_tracks_the_predicate_not_the_type() {
    // Lengthening the predicate must lengthen the reported secondary span.
    let mut last_len = 0usize;
    for extra in 0..5 {
        let pred = std::iter::repeat("v > 0").take(extra + 1)
            .collect::<Vec<_>>().join(" && ");
        let src = format!(
            "@lang.advance\nfn f(p: {{v: i32 | {pred}}}) -> i32 {{ return 0; }}\n");
        let err = compile_str(&src).unwrap_err();
        let len = err.secondary_span().expect("must have a secondary span").len();
        assert!(len > last_len, "extra={extra}: secondary span must grow with the predicate");
        last_len = len;
    }
}

#[test]
fn non_refined_types_are_never_rejected() {
    // Defeats an over-broad matcher that fires on any braced type.
    let benign = ["i32", "f64", "bool", "[i32; 4]", "&i32", "Any", "S"];
    for (i, pos) in type_positions().iter().enumerate() {
        for (j, t) in benign.iter().enumerate() {
            let src = format!(
                "@lang.advance\nstruct S {{ a: i32 }}\nfn def() -> i32 {{ return 0; }}\n{}\n",
                pos.replace("{}", t));
            if let Err(e) = compile_str(&src) {
                assert_ne!(e.code(), "E0180", "pos={i} type={j} ({t}) must not be E0180");
            }
        }
    }
}

#[test]
fn nested_refinement_yields_exactly_one_error() {
    for depth in 1..=3 {
        let mut ty = "{v: i32 | v > 0}".to_string();
        for _ in 0..depth { ty = format!("[{ty}; 2]"); }
        let src = format!("@lang.advance\nfn f(p: {ty}) -> i32 {{ return 0; }}\n");
        let errs = collect_errors(&src);
        assert_eq!(errs.iter().filter(|e| e.code() == "E0180").count(), 1,
            "depth={depth} must yield exactly one E0180");
    }
}

#[test]
fn both_dialects_produce_the_same_diagnostic() {
    let adv  = "@lang.advance\nfn f(p: {v: i32 | v > 0}) -> i32 { return 0; }\n";
    let base = "@lang.base\nfn f(p: {v: i32 | v > 0}) -> i32:\n    return 0\n";
    let a = compile_str(adv).unwrap_err();
    let b = compile_str(base).unwrap_err();
    assert_eq!(a.code(), b.code());
    assert_eq!(normalize_message(&a), normalize_message(&b));
}
```

**Required property:** `every_refinement_is_rejected_in_every_type_position` must
FAIL on all 42 cases pre-fix (everything compiles today). Record this.

---

## 7. Open questions — DO NOT decide these yourself

1. **Error or warning?** This spec chooses a hard error, on the reasoning that a
   warning still lets a program ship with an unenforced constraint the author
   believes is enforced. A warning is the gentler migration path if any existing
   code uses the syntax. **AC-7 checks whether any does; if some exists, escalate
   rather than choosing severity yourself.**

2. **Should the predicate be type-checked before rejection?** Checking it would
   give better errors for malformed predicates but requires lowering an expression
   in a type position, which has its own scoping questions (what is `v` bound to?).
   This spec deliberately does not check it. **Escalate if better predicate
   diagnostics are wanted.**

3. **The real implementation.** Discharging refinements needs: a binder scope for
   the refinement variable, a translation from `Expr` to an SMT term, integration
   with `agam_smt`, a decision on where obligations are checked (call sites?
   assignments? both?), and a story for what happens when the solver times out.
   **That is a full stage-sized spec, not an extension of this one. Do not
   attempt it here.**

4. **Is `TypeExprKind::DynTrait` also parsed-and-dropped?** I did not verify.
   If it is, the same treatment may apply and should be a sibling spec.
   **Check and report; do not extend this spec to cover it.**

5. **Are there other `..`-discarding arms in `lower.rs`?** The `Refined` arm was
   found by inspection, not by exhaustive audit. **Audit every
   `TypeExprKind::` and `ExprKind::` arm in `agam_hir/src/lower.rs` for silently
   dropped fields and report findings, even if they are out of scope here.** This
   is the highest-value side task attached to this spec.
