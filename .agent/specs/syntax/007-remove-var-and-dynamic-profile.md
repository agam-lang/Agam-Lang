# 007 — Remove `var` and `@lang.base.dynamic`

**Status:** proposed
**Depends on:** **002 (hard — arity/type checking must exist first)**, 003
**Component:** `agam_lexer`, `agam_parser`, `agam_ast`, `agam_sema`, `agam_pkg`
**Ledger:** new — file as `B-Grade: #6`

---

## 1. Motivation

Two advertised features do nothing.

**`@lang.base.dynamic` is a no-op.** `grep -rn 'BaseDynamic' crates/ --include='*.rs'`
returns four hits, all in `lexer.rs`, and in every one it appears in a
disjunction with `BaseStatic` and is treated identically:

```rust
if self.mode == SyntaxMode::BaseStatic || self.mode == SyntaxMode::BaseDynamic { ... }
```

No downstream stage reads the mode. `var` is reachable in every dialect because
`parse_var_stmt` (`parser.rs:1073`) is unconditional.

**`var` and `dyn` are `Any` under a different name.** HIR lowering,
`agam_hir/src/lower.rs:1111-1113`:

```rust
agam_ast::types::TypeExprKind::Dynamic | agam_ast::types::TypeExprKind::Any => {
    self.types.any()
}
```

There is no runtime type tag, no dynamic dispatch, no runtime type error.
`TypeMode::{Static, Dynamic, Inferred}` is carried on every `TypeExpr` and never
consulted after HIR lowering. `agam_ast/src/types.rs`'s doc comment describing a
"dual typing system" with "runtime checked, like Python" semantics describes
something that does not exist.

This matters more after spec 002 lands. Once arity and argument types are
actually checked, a keyword that silently opts a binding out of checking — while
being named as a *typing mode* rather than an escape hatch — becomes the obvious
hole. TypeScript's own trajectory is the reference: `noImplicitAny` became
default-on under `strict` in TS 2.3, and `unknown` was added in 3.0, both in
response to the documented complaint that an invisible escape-hatch type was the
main source of "the type checker didn't catch my bug."

Kotlin's `!!` is the contrasting design: the unsafe operation is deliberately
ugly and greppable. `var` is the opposite — an unsafe operation with a
safe-sounding name.

---

## 2. Formal grammar diff

```ebnf
(* OLD *)
ProfileDirective    = "@lang.base" | "@lang.base.dynamic" | "@lang.advance" ;
Statement           = LetStmt | VarStmt | ConstDecl | ... ;
VarStmt             = "var" , Identifier , [ ":" , Type ] , [ "=" , Expression ] , [ ";" ] ;
Type                = ... | "dyn" | ... ;

(* NEW *)
ProfileDirective    = "@lang.base" | "@lang.advance" ;
Statement           = LetStmt | ConstDecl | ... ;
(*  VarStmt is removed.  The `var` keyword is removed from TokenKind.        *)

Type                = ... | "Any" | ... ;
(*  `dyn` as a standalone type is removed.  `dyn Trait` (DynTrait) is UNAFFECTED
    and remains legal — it means dynamic dispatch, not dynamic typing.
    The universal escape-hatch type is spelled `Any` and REQUIRES an explicit
    annotation; it is never inferred.                                        *)

LetStmt             = "let" , [ "mut" ] , Pattern , [ ":" , Type ] , [ "=" , Expression ] , [ ";" ] ;
(*  A `let` with no annotation infers a concrete type.  It NEVER infers `Any`.
    If inference would produce `Any`, that is error E0170.                    *)
```

Manifest: `SyntaxProfile::BaseDynamic` is removed from the enum introduced in
spec 003. `syntax = "base.dynamic"` becomes `E0143` (unknown profile).

---

## 3. AST / HIR / MIR impact

**AST:** delete `TypeMode` entirely (`agam_ast/src/types.rs`) and the `mode` field
on `TypeExpr`. Delete `TypeExprKind::Dynamic`. **Keep** `TypeExprKind::Any` and
**keep** `TypeExprKind::DynTrait` — these are different features.

**Lexer:** delete `TokenKind::Var` and `TokenKind::Dyn`'s standalone-type role.
`Dyn` must remain tokenizable if `dyn Trait` is supported; verify before deleting
the token.

**Parser:** delete `parse_var_stmt`.

**HIR:** `lower.rs:1111` loses the `Dynamic` arm; `Any` continues to map to
`self.types.any()`.

**Sema:** new check — a `let` binding whose inferred type resolves to `any`
without an explicit `: Any` annotation is `E0170`.

**MIR / backends:** none.

### Dialect symmetry statement

This is a pure removal applied identically to both remaining dialects. Symmetry
is preserved trivially: neither dialect can express the removed constructs.

---

## 4. Worked examples

### 4.1 Valid — migration of the dynamic example

Before (`examples/hello_base_dynamic.agam`, which I believe does not compile
today — see open question 1):

```agam
@lang.base.dynamic
fn main():
    name = "World"
    print("Hello,", name)
```

After:

```agam
@lang.base
fn main() -> i32:
    let name = "World"
    println("Hello, ", name)
    return 0
```

Expected: compiles, prints `Hello, World`. (The two-argument `println` is legal
by spec 002's variadic declaration.)

### 4.2 Valid — explicit `Any` escape hatch

```agam
@lang.advance
fn describe(x: Any) -> i32 {
    print(x);
    return 0;
}

fn main() -> i32 {
    let v: Any = 42;
    return describe(v);
}
```

Expected: compiles, prints `42`. `Any` remains fully usable — it is now visible.

### 4.3 Valid — `dyn Trait` unaffected

```agam
@lang.advance
trait Shape { fn area(self) -> f64; }

fn total(s: &dyn Shape) -> f64 { return s.area(); }
```

Expected: parses and compiles exactly as before. **`dyn Trait` is not touched by
this spec.** If it regresses, the implementation deleted too much.

### 4.4 Invalid — `var` keyword

```agam
@lang.advance
fn main() -> i32 {
    var x = 42;
    return x;
}
```

Expected, exactly:

```
error[E0171]: `var` has been removed
 --> input.agam:3:5
  |
3 |     var x = 42;
  |     ^^^ `var` is no longer a keyword
  |
  = fix: use `let x = 42;` for an inferred type,
         or `let x: Any = 42;` to opt out of static checking
  = law: AGAM-SYNTAX-007 §2
```

### 4.5 Invalid — `@lang.base.dynamic` directive

```agam
@lang.base.dynamic
fn main() -> i32:
    return 0
```

Expected:

```
error[E0172]: the `base.dynamic` syntax profile has been removed
 --> input.agam:1:1
  |
1 | @lang.base.dynamic
  | ^^^^^^^^^^^^^^^^^^ this profile had no distinct behaviour
  |
  = fix: use `@lang.base`
  = law: AGAM-SYNTAX-007 §2
```

### 4.6 Invalid — implicit `Any` inference

```agam
@lang.advance
fn takes_any(x: Any) -> Any { return x; }

fn main() -> i32 {
    let v = takes_any(1);
    return 0;
}
```

Expected:

```
error[E0170]: type of `v` would be `Any`
 --> input.agam:5:9
  |
5 |     let v = takes_any(1);
  |         ^ inferred type is `Any`, which disables static checking
  |
  = fix: annotate explicitly: `let v: Any = takes_any(1);`
  = law: AGAM-SYNTAX-007 §2
```

Escaping into `Any` must always be a deliberate, visible act.

### 4.7 Invalid — `dyn` as a standalone type

```agam
@lang.advance
fn main() -> i32 { let x: dyn = 1; return 0; }
```

Expected: `E0173`, "`dyn` is not a type; write `Any`, or `dyn Trait` for dynamic
dispatch".

---

## 5. Acceptance criteria

- **AC-1** — 4.1, 4.2, 4.3 compile and produce identical stdout under both
  backends.
- **AC-2** — 4.4, 4.5, 4.6, 4.7 produce exactly `E0171`, `E0172`, `E0170`, `E0173`.
- **AC-3** — `grep -rn 'TokenKind::Var\|TypeMode\|TypeExprKind::Dynamic\b' crates/`
  returns nothing outside of the migration errors themselves. Grep output pasted
  into the commit message.
- **AC-4** — `grep -rn 'BaseDynamic' crates/` returns nothing outside
  `SyntaxProfile` parsing (where it must produce `E0172`).
- **AC-5** — `dyn Trait` still parses and lowers. A dedicated test, because this
  is the most likely thing to be broken by over-deletion.
- **AC-6 (symmetry)** — 4.4's error is byte-identical (modulo spans) when the
  same program is written in `@lang.base`.
- **AC-7** — `examples/hello_base_dynamic.agam` is migrated per 4.1 (or deleted,
  see open question 1) and added to the CI compile corpus.
- **AC-8** — `docs/CHEATSHEET.md` and `agam_ast/src/types.rs`'s doc comment no
  longer describe a "dual typing system". `docs/` passes
  `python scripts/doctest_check.py`.
- **AC-9** — `cargo test`, `clippy -D warnings`, `fmt --check` via
  `python scripts/cargo_lens.py`.
- **AC-10** — `issues.md` gains `B-Grade: #6`, closed.

---

## 6. Required mutation test — MANDATORY

Add `crates/middle/agam_sema/tests/mutation_007_any_containment.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-007.
//! `Any` must be reachable ONLY through an explicit annotation, at every
//! position, and `dyn Trait` must survive intact.

/// Positions where a type can appear, as a format template with one `{}` slot.
fn type_positions() -> Vec<&'static str> {
    vec![
        "fn m() -> i32 {{ let v: {} = def(); return 0; }}",
        "fn take(p: {}) -> i32 {{ return 0; }}\nfn m() -> i32 {{ return 0; }}",
        "fn give() -> {} {{ return def(); }}\nfn m() -> i32 {{ return 0; }}",
        "struct S {{ f: {} }}\nfn m() -> i32 {{ return 0; }}",
    ]
}

#[test]
fn explicit_any_is_accepted_in_every_type_position() {
    for (i, tpl) in type_positions().iter().enumerate() {
        let src = format!("@lang.advance\nfn def() -> Any {{ return 1; }}\n{}\n",
                          tpl.replace("{}", "Any"));
        assert!(compile_str(&src).is_ok(), "position {i}: explicit `Any` must be accepted");
    }
}

#[test]
fn removed_spellings_are_rejected_in_every_type_position() {
    for (i, tpl) in type_positions().iter().enumerate() {
        let src = format!("@lang.advance\nfn def() -> Any {{ return 1; }}\n{}\n",
                          tpl.replace("{}", "dyn"));
        assert_eq!(compile_str(&src).unwrap_err().code(), "E0173",
            "position {i}: bare `dyn` must be rejected");
    }
}

#[test]
fn implicit_any_is_rejected_at_every_inference_depth() {
    // Chain N calls that each return Any; inference must still be blocked.
    for depth in 1..=5 {
        let mut chain = "seed()".to_string();
        for _ in 0..depth { chain = format!("pass({chain})"); }
        let src = format!(
            "@lang.advance\nfn seed() -> Any {{ return 1; }}\nfn pass(x: Any) -> Any {{ return x; }}\n\
             fn m() -> i32 {{ let v = {chain}; return 0; }}\n");
        assert_eq!(compile_str(&src).unwrap_err().code(), "E0170",
            "depth={depth}: implicit Any must be rejected");
        // The same program with an explicit annotation must be accepted.
        let annotated = src.replace("let v =", "let v: Any =");
        assert!(compile_str(&annotated).is_ok(), "depth={depth}: annotated form must pass");
    }
}

#[test]
fn dyn_trait_survives_removal() {
    // Over-deletion of the `dyn` token would break this. Must NOT regress.
    for arity in 1..=3 {
        let methods: Vec<String> = (0..arity)
            .map(|i| format!("fn m{i}(self) -> f64;")).collect();
        let src = format!(
            "@lang.advance\ntrait T {{ {} }}\nfn f(s: &dyn T) -> f64 {{ return s.m0(); }}\n",
            methods.join(" "));
        assert!(compile_str(&src).is_ok(), "arity={arity}: `dyn Trait` must still parse");
    }
}

#[test]
fn var_is_rejected_wherever_let_is_accepted() {
    // Defeats a fix that only removes `var` from one statement position.
    let contexts = [
        "fn m() -> i32 {{ {} x = 1; return 0; }}",
        "fn m() -> i32 {{ if true {{ {} x = 1; }} return 0; }}",
        "fn m() -> i32 {{ while false {{ {} x = 1; }} return 0; }}",
    ];
    for (i, ctx) in contexts.iter().enumerate() {
        let good = format!("@lang.advance\n{}\n", ctx.replace("{}", "let"));
        assert!(compile_str(&good).is_ok(), "context {i}: `let` must work");
        let bad = format!("@lang.advance\n{}\n", ctx.replace("{}", "var"));
        assert_eq!(compile_str(&bad).unwrap_err().code(), "E0171",
            "context {i}: `var` must be rejected");
    }
}
```

**Required property:** `implicit_any_is_rejected_at_every_inference_depth` and
`var_is_rejected_wherever_let_is_accepted` must FAIL on the pre-fix compiler.
Record this.

---

## 7. Open questions — DO NOT decide these yourself

1. **Does `examples/hello_base_dynamic.agam` compile today?** I could not run
   `agamc`. It uses bare `name = "World"` with no declaration keyword, which
   should be an unresolved-symbol error, and `scores.len()` on an array literal.
   **Determine this first.** If it does not compile, the right action may be
   deletion rather than migration, and that is a call for the maintainer.

2. **Is this removal wanted at all?** This is the one spec in the set with a
   product cost, not just an engineering one: it removes the "Python-like
   dynamic scripting" pitch from the language's story. The engineering case is
   unambiguous; the product case is not mine to make. **This spec must be
   explicitly approved before implementation, not merely assigned.**

3. **Should `Any` remain in the language at all**, or should the escape hatch be
   removed entirely once static checking is real? Keeping it is the conservative
   choice and what this spec assumes. **Escalate if removal is preferred.**

4. **Is `dyn Trait` actually implemented**, or is `TypeExprKind::DynTrait` also
   parsed-and-dropped like `Refined`? I did not verify. If it is also a no-op,
   spec 008's treatment (reject explicitly) may apply to it too. **Check and
   escalate; do not silently extend this spec to cover it.**

5. **`TypeMode` deletion blast radius.** It is a field on every `TypeExpr`.
   `agam_lsp`, `agam_fmt`, `agam_doc`, and `agam_gui/src/eval.rs` may read it.
   **Enumerate all readers before deleting and escalate if any depends on it
   semantically rather than structurally.**
