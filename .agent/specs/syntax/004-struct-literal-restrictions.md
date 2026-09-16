# 004 — Struct-Literal Restriction Flags

**Status:** proposed
**Depends on:** PRE-000
**Blocks:** 005 (blocks as expressions) — **005 is unsound without this**
**Component:** `agam_parser`
**Ledger:** new — file as `B-Grade: #4`

---

## 1. Motivation

Agam disambiguates `Ident {` between a struct literal and a block using **two
different, mutually inconsistent lookahead heuristics**.

**Heuristic 1** — `looks_like_struct_literal()`, `parser.rs:60-80`. Used from the
path branch of `parse_prefix` (`parser.rs:1396`). It **skips** `Newline`,
`LineComment`, `BlockComment`, `Indent`, `Dedent` before testing for
`Identifier|StringLiteral` followed by `Colon`.

**Heuristic 2** — the postfix loop, `parser.rs:1238-1251`:

```rust
let first = self.peek_at(1);
(first == TokenKind::Identifier || first == TokenKind::StringLiteral)
    && self.peek_at(2) == TokenKind::Colon
```

Raw offsets. **No trivia skipping.** A multi-line struct literal

```agam
let p = Point {
    x: 1,
};
```

has `Newline` at `peek_at(1)`, fails the test, and is not recognised as a struct
literal on this path.

One construct, two rules, differing on the single most common formatting choice
(putting fields on their own lines). Which rule applies depends on which parser
path reached the `{`, which is not a property a user can reason about.

Separately, lookahead is the wrong mechanism. Rust encountered this identical
ambiguity and solved it with an explicit parser restriction threaded through
condition positions (`Restrictions::NO_STRUCT_LITERAL`), documented in the Rust
Reference as "struct expressions are not allowed in the condition of an if". That
approach is decidable by construction rather than by lookahead depth, and it is
the prerequisite for spec 005: once `{` can also begin a block expression in
prefix position, no amount of lookahead disambiguates reliably.

---

## 2. Formal grammar diff

```ebnf
(* OLD — ambiguity resolved by unspecified lookahead *)
Postfix             = Primary , { CallSuffix | IndexSuffix | FieldSuffix } ;
StructInit          = Identifier , "{" , [ FieldInit , { ( "," | Newline ) , FieldInit } ] ,
                      [ "," | Newline ] , "}" ;

(* NEW — ambiguity resolved by a context restriction *)

(*  The parser carries a restriction set R.
    R contains NO_STRUCT_LITERAL in exactly these positions:
      - IfStmt      condition
      - WhileStmt   condition
      - ForStmt     iterable
      - MatchExpr   scrutinee
    R is CLEARED inside any "(" ... ")", "[" ... "]", or CallSuffix argument list.
    R has no other members and is not user-visible.                          *)

StructInit          = PathExpr , StructInitBody ;                 (* only when NO_STRUCT_LITERAL not in R *)
StructInitBody      = "{" , [ Trivia ] ,
                      [ FieldInit , { FieldSep , [ Trivia ] , FieldInit } ] ,
                      [ FieldSep ] , [ Trivia ] , "}" ;
FieldSep            = "," | Newline ;
Trivia              = { Newline | LineComment | BlockComment | INDENT | DEDENT } ;

IfStmt              = "if" , Expression_NoStructLit , Block , [ "else" , ( IfStmt | Block ) ] ;
WhileStmt           = "while" , Expression_NoStructLit , Block ;
ForStmt             = "for" , Pattern , "in" , Expression_NoStructLit , Block ;
MatchExpr           = "match" , Expression_NoStructLit , MatchBody ;
```

A struct literal in a restricted position is legal when parenthesised:
`if (Config { debug: true }).enabled { ... }`.

**Both existing heuristics are deleted.** `looks_like_struct_literal()` is
removed. The postfix raw-offset test at `parser.rs:1238-1251` is removed. There
must be exactly one code path that decides `{` after a path expression.

---

## 3. AST / HIR / MIR impact

**AST:** none. `ExprKind::StructLiteral { path, fields }` unchanged.

**HIR / MIR / backends:** none.

**Parser internals:** `parse_expression`, `parse_prefix`, `parse_infix` gain a
`restrictions: Restrictions` parameter (or the parser struct gains a field with
save/restore at the four sites). Prefer the explicit parameter — a struct field
with manual save/restore is the classic source of leak bugs.

### Dialect symmetry statement

The restriction is applied to the same four syntactic positions in both dialects,
and `Trivia` in `StructInitBody` explicitly includes `INDENT`/`DEDENT`, so
multi-line struct literals behave identically in base and advance mode. AC-4
asserts this directly.

---

## 4. Worked examples

### 4.1 Valid — multi-line struct literal, advance

```agam
@lang.advance
struct Point { x: i32, y: i32 }

fn main() -> i32 {
    let p = Point {
        x: 3,
        y: 4,
    };
    print_int(p.x + p.y);
    return 0;
}
```

Expected: compiles, prints `7`. **This is a case that fails today on the postfix
path.**

### 4.2 Valid — multi-line struct literal, base

```agam
@lang.base
struct Point:
    x: i32
    y: i32

fn main() -> i32:
    let p = Point {
        x: 3,
        y: 4,
    }
    print_int(p.x + p.y)
    return 0
```

Expected: compiles, prints `7`. Requires spec 001 to be landed.

### 4.3 Valid — identifier followed by a block in condition position

```agam
@lang.advance
fn main() -> i32 {
    let ready = true;
    if ready {
        print_int(1);
    }
    return 0;
}
```

Expected: `ready` is a condition, `{` opens a block. Compiles, prints `1`. Under
the restriction this is decided structurally, not by lookahead.

### 4.4 Valid — parenthesised struct literal in condition position

```agam
@lang.advance
struct Cfg { debug: bool }

fn main() -> i32 {
    if (Cfg { debug: true }).debug {
        print_int(1);
    }
    return 0;
}
```

Expected: compiles, prints `1`. The restriction is cleared inside `(...)`.

### 4.5 Valid — struct literal in call-argument position

```agam
@lang.advance
struct Point { x: i32, y: i32 }
fn norm(p: Point) -> i32 { return p.x + p.y; }

fn main() -> i32 {
    if norm(Point { x: 1, y: 2 }) > 2 {
        print_int(9);
    }
    return 0;
}
```

Expected: compiles, prints `9`. The restriction is cleared inside a call's
argument list even though the call itself is in condition position.

### 4.6 Invalid — bare struct literal in condition position

```agam
@lang.advance
struct Cfg { debug: bool }
fn main() -> i32 {
    if Cfg { debug: true }.debug { return 1; }
    return 0;
}
```

Expected, exactly:

```
error[E0150]: struct literals are not allowed in this position
 --> input.agam:4:8
  |
4 |     if Cfg { debug: true }.debug { return 1; }
  |        ^^^^^^^^^^^^^^^^^^ struct literal in an `if` condition is ambiguous
  |
  = fix: wrap it in parentheses: `if (Cfg { debug: true }).debug { ... }`
  = law: AGAM-SYNTAX-004 §2
```

### 4.7 Invalid — same, in a `match` scrutinee

```agam
@lang.advance
struct Cfg { debug: bool }
fn main() -> i32 {
    match Cfg { debug: true } {
        _ => 0,
    }
}
```

Expected: `E0150` with the span covering `Cfg { debug: true }` and the same
parenthesise fix.

### 4.8 Valid — trailing comma and comments inside the literal

```agam
@lang.advance
struct P { a: i32, b: i32 }
fn main() -> i32 {
    let p = P {
        // first field
        a: 1,
        /* second */ b: 2,
    };
    return p.a;
}
```

Expected: compiles, exit value derived from `p.a == 1`. `Trivia` in the grammar
must cover both comment forms.

---

## 5. Acceptance criteria

- **AC-1** — 4.1, 4.2, 4.3, 4.4, 4.5, 4.8 compile and produce identical stdout
  under `agamc run` and `agamc build --backend llvm`.
- **AC-2** — 4.6 and 4.7 produce exactly `E0150` with the stated span and the
  parenthesise fix line.
- **AC-3** — `grep -n 'looks_like_struct_literal' crates/core/agam_parser/src/`
  returns **nothing**. The implementing agent pastes this grep into the commit
  message.
- **AC-4 (symmetry)** — A test parses 4.1 and 4.2, pretty-prints the `main`
  function bodies, and asserts they are identical after span normalisation.
- **AC-5** — A test asserts the restriction is cleared inside parens, brackets,
  and call arguments, for each of the four restricted positions — a 4 × 3 matrix
  of 12 cases, all of which must compile.
- **AC-6** — A test asserts the restriction does **not** leak into the block
  body: `if ready { let p = Point { x: 1, y: 2 }; }` compiles.
- **AC-7** — `cargo test`, `clippy -D warnings`, `fmt --check` via
  `python scripts/cargo_lens.py`.
- **AC-8** — `issues.md` gains `B-Grade: #4`, closed.

---

## 6. Required mutation test — MANDATORY

A shallow implementation can pass §4 by keeping the old lookahead and adding a
special case for `if`. This test detects that.

Add `crates/core/agam_parser/tests/mutation_004_struct_restrictions.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-004.
//! The restriction must be positional and systematic, not keyword-special-cased,
//! and struct-literal recognition must not depend on internal whitespace.

const PRELUDE: &str = "@lang.advance\nstruct C { f: i32 }\n";

/// The four restricted positions, as (prefix, suffix) around the expression.
fn restricted_positions() -> Vec<(&'static str, &'static str)> {
    vec![
        ("fn m() -> i32 { if ",    ".f > 0 { return 1; } return 0; }"),
        ("fn m() -> i32 { while ", ".f > 0 { return 1; } return 0; }"),
        ("fn m() -> i32 { for _i in ", ".f { return 1; } return 0; }"),
        ("fn m() -> i32 { match ", ".f { _ => 0 } }"),
    ]
}

#[test]
fn every_restricted_position_rejects_a_bare_struct_literal() {
    for (i, (pre, post)) in restricted_positions().iter().enumerate() {
        let src = format!("{PRELUDE}{pre}C {{ f: 1 }}{post}\n");
        let err = compile_str(&src).expect_err("position {i} must reject");
        assert_eq!(err.code(), "E0150", "position {i}");
    }
}

#[test]
fn every_restricted_position_accepts_the_parenthesised_form() {
    for (i, (pre, post)) in restricted_positions().iter().enumerate() {
        let src = format!("{PRELUDE}{pre}(C {{ f: 1 }}){post}\n");
        assert!(compile_str(&src).is_ok(), "position {i} parenthesised must parse");
    }
}

#[test]
fn restriction_is_cleared_inside_every_bracketing_form() {
    // paren, bracket-index, and call-argument, in each restricted position.
    let wrappers: [&str; 3] = [
        "(C { f: 1 })",
        "ident_fn(C { f: 1 })",
        "arr[ C { f: 1 }.f ]",
    ];
    for (i, (pre, post)) in restricted_positions().iter().enumerate() {
        for (j, w) in wrappers.iter().enumerate() {
            let src = format!("{PRELUDE}{pre}{w}{post}\n");
            // We only assert it is not E0150; other errors (unknown fn) are fine here.
            if let Err(e) = compile_str(&src) {
                assert_ne!(e.code(), "E0150", "position {i} wrapper {j} must not be restricted");
            }
        }
    }
}

#[test]
fn struct_literal_recognition_is_whitespace_invariant() {
    // Same literal, 6 formattings. All must parse to an identical AST.
    let forms = [
        "C { f: 1 }",
        "C {f:1}",
        "C {\n    f: 1\n}",
        "C {\n    f: 1,\n}",
        "C { // c\n    f: 1,\n}",
        "C {\n    /* c */ f: 1\n}",
    ];
    let baseline = parse_expr_ast(&format!("{PRELUDE}fn m() -> i32 {{ let p = {}; return p.f; }}\n", forms[0]))
        .expect("baseline must parse");
    for (i, f) in forms.iter().enumerate().skip(1) {
        let got = parse_expr_ast(&format!("{PRELUDE}fn m() -> i32 {{ let p = {f}; return p.f; }}\n"))
            .unwrap_or_else(|e| panic!("form {i} failed to parse: {e:?}"));
        assert_eq!(normalize(&baseline), normalize(&got), "form {i} must match baseline AST");
    }
}

#[test]
fn field_count_mutation_is_tracked() {
    // Defeats a hardcoded single-field literal recogniser.
    for n in 1..=5 {
        let fields: Vec<String> = (0..n).map(|i| format!("f{i}: {i}")).collect();
        let decl: Vec<String> = (0..n).map(|i| format!("f{i}: i32")).collect();
        let src = format!(
            "@lang.advance\nstruct C {{ {} }}\nfn m() -> i32 {{ let p = C {{\n    {}\n}}; return p.f0; }}\n",
            decl.join(", "), fields.join(",\n    "));
        let lit = parse_first_struct_literal(&src).expect("n={n} must parse");
        assert_eq!(lit.fields.len(), n, "n={n}");
    }
}
```

**Required property:** `struct_literal_recognition_is_whitespace_invariant` must
FAIL on the pre-fix compiler for the multi-line forms. Record which forms fail in
the commit message.

---

## 7. Open questions — DO NOT decide these yourself

1. **Is `for` the right fourth restricted position?** Rust restricts `for`'s
   iterable expression. But Agam's `ForStmt` grammar is
   `"for" , Identifier , "in" , Expression , Block`, taking an `Identifier`, not a
   `Pattern` — §2 above writes `Pattern`, which may be a change this spec is not
   authorised to make. **Verify what `parse_for_stmt` actually accepts and
   escalate if §2 overstates it.**

2. **Should the restriction apply to `if let` / `while let`, if those exist?** I
   found no `if let` in the grammar or token stream. **Escalate if they exist.**

3. **Does clearing the restriction inside `[ ... ]` index brackets create a new
   ambiguity with array literals?** I believe not, but I did not prove it.
   **Escalate if a conflict appears during implementation; do not resolve it by
   narrowing the clearing rule silently.**

4. **Restriction behaviour inside a closure body appearing in condition
   position** — e.g. `if pred(|| C { f: 1 }) { }`. The closure body is not a
   bracketing form under §2's clearing rule, so the restriction would leak into
   it. That is probably wrong. **Escalate.**

5. **Error recovery.** When `E0150` fires, should the parser consume the struct
   literal and continue (better multi-error reporting) or bail? `B-Grade: #2`
   (Pratt panic-mode recovery) is in flight and may dictate this. **Coordinate;
   do not decide unilaterally.**
