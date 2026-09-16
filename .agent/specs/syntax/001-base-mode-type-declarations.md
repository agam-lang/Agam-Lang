# 001 — Base-Mode Type Declarations

**Status:** proposed
**Depends on:** PRE-000 (differential harness)
**Component:** `agam_lexer`, `agam_parser`
**Ledger:** closes `B-Grade: #1`; supersedes its stated fix location

---

## 1. Motivation

`@lang.base` cannot declare a struct or enum whose body spans more than one line.
This is not a cosmetic gap: it means one of the two advertised dialects cannot
define a data type, while the other can. Both dialects lower to the same
`agam_ast::decl::StructDecl`, so this is an expressiveness asymmetry, i.e. a bug.

Reproduction (fails today):

```agam
@lang.base
struct Point {
    x: i32,
    y: i32,
}
```

```
error: expected expression, found Indent
```

### Actual root cause (the ledger's attribution is wrong)

`issues.md` names `crates/core/agam_lexer/src/layout.rs`. **That file does not
exist.** Layout handling is in `crates/core/agam_lexer/src/lexer.rs:112-140`.

Two independent defects combine:

**Defect A — the lexer emits layout tokens inside brackets.** `lexer.rs:112-140`
synthesizes `Indent`/`Dedent` whenever a base-mode line's leading whitespace
changes, with no awareness of `{`/`[`/`(` nesting. So `struct Point {` followed by
an indented field line produces an `Indent` token between `{` and `x`.

**Defect B — `parse_struct_decl` does not drain layout tokens.**
`parser.rs:534-580`:

```rust
let has_brace = self.eat(TokenKind::LBrace);
let has_indent = if !has_brace { self.eat(TokenKind::Indent) } else { false };
self.skip_newlines();
while self.peek_kind() == TokenKind::Identifier || self.peek_kind() == TokenKind::Pub {
```

`skip_newlines()` skips `Newline` only. With `has_brace == true` the next token is
`Indent`, the field loop never runs, zero fields are parsed, and the subsequent
`eat(RBrace)` fails on `Indent`.

`parse_block` already solves Defect B locally at `parser.rs:1181-1191`. That fix
was never applied to `parse_struct_decl` or `parse_enum_decl`.

**Both defects must be fixed.** Fixing only A leaves the parser brittle against
any future layout-token leak; fixing only B leaves every not-yet-written
bracketed construct broken the same way.

---

## 2. Formal grammar diff

### 2.1 Lexical layer (new — currently unspecified)

```ebnf
(* OLD: no bracket-depth concept exists in the specification *)

(* NEW *)
BracketDepth        = (* lexer-internal counter, initial 0 *) ;
(*  incremented on each "{" , "[" , "(" token emitted
    decremented on each "}" , "]" , ")" token emitted
    never decremented below 0                                   *)

LayoutSuppression   = (* In BaseStatic and BaseDynamic modes, Indent and Dedent
                         tokens are NOT synthesized while BracketDepth > 0.
                         The indentation stack is neither pushed nor popped
                         while suppressed.                                    *) ;
```

### 2.2 Struct declaration

```ebnf
(* OLD *)
StructDecl          = "struct" , Identifier , [ GenericParams ] ,
                      "{" , { StructField } , "}" ;

(* NEW *)
StructDecl          = "struct" , Identifier , [ GenericParams ] , StructBody ;
StructBody          = "{" , { StructField } , "}"
                    | ":" , INDENT , StructField , { StructField } , DEDENT ;
StructField         = [ "pub" ] , Identifier , ":" , Type ,
                      [ "=" , Expression ] , [ "," | ";" ] ;
```

### 2.3 Enum declaration

```ebnf
(* OLD *)
EnumDecl            = "enum" , Identifier , "{" , { EnumVariant } , "}" ;

(* NEW *)
EnumDecl            = "enum" , Identifier , [ GenericParams ] , EnumBody ;
EnumBody            = "{" , { EnumVariant } , "}"
                    | ":" , INDENT , EnumVariant , { EnumVariant } , DEDENT ;
EnumVariant         = Identifier , [ VariantPayload ] , [ "," ] ;
VariantPayload      = "(" , Type , { "," , Type } , ")"
                    | "{" , StructField , { StructField } , "}" ;
```

Note: the brace-delimited body remains legal in **both** dialects. This spec does
not restrict it; that is spec 006's job.

---

## 3. AST / HIR / MIR impact

**AST:** none. `StructDecl { name, generics, fields, visibility, annotations, span }`
and `EnumDecl { name, generics, variants, visibility, span }` are unchanged. Both
surface forms must produce structurally identical `Decl` nodes.

**HIR:** none.

**MIR:** none.

**Backends:** none. No backend change is permitted by this spec. If a backend
change appears necessary, the implementation is wrong — stop and escalate.

### Dialect symmetry statement

After this change, for every struct or enum declaration expressible in
`@lang.advance`, there exists a `@lang.base` source text producing a
byte-identical `Decl` subtree, and vice versa. This is directly checkable via
`agam_ast::pretty` and is required by acceptance criterion AC-5.

---

## 4. Worked examples

### 4.1 Valid — base, colon-indent struct

```agam
@lang.base
struct Point:
    x: i32
    y: i32

fn main() -> i32:
    let p = Point { x: 3, y: 4 }
    print_int(p.x + p.y)
    return 0
```

Expected: compiles. `agamc run` prints `7`. `agamc build --backend llvm` produces
a binary printing `7`.

### 4.2 Valid — base, brace struct (regression case for Defect A)

```agam
@lang.base
struct Point {
    x: i32,
    y: i32,
}

fn main() -> i32:
    let p = Point { x: 3, y: 4 }
    print_int(p.y)
    return 0
```

Expected: compiles, prints `4`. **This is the case that fails today.**

### 4.3 Valid — base, colon-indent enum

```agam
@lang.base
enum Shape:
    Circle(f64)
    Rect(f64, f64)
    Empty

fn area_code(s: Shape) -> i32:
    match s:
        Shape::Circle(_) => 1
        Shape::Rect(_, _) => 2
        Shape::Empty => 0
```

Expected: compiles; exhaustiveness check in `agam_sema::exhaustive` passes.

### 4.4 Valid — advance, unchanged

```agam
@lang.advance
struct Point { x: i32, y: i32 }
```

Expected: compiles exactly as today. No behavioural change.

### 4.5 Invalid — empty colon body

```agam
@lang.base
struct Point:

fn main() -> i32:
    return 0
```

Expected, exactly:

```
error[E0130]: struct body cannot be empty
 --> input.agam:2:13
  |
2 | struct Point:
  |             ^ expected at least one field after `:`
  |
  = fix: add a field, e.g. `x: i32`, or write `struct Point {}` for a unit struct
  = law: AGAM-SYNTAX-001 §2.2
```

The grammar in §2.2 requires `StructField , { StructField }` — one or more — after
`:`. An empty brace body `{}` remains legal.

### 4.6 Invalid — dedent mid-body

```agam
@lang.base
struct Point:
    x: i32
  y: i32
```

Expected, exactly:

```
error[E0131]: inconsistent field indentation in struct body
 --> input.agam:4:3
  |
3 |     x: i32
  |     ------ field body established at column 5
4 |   y: i32
  |   ^ this field is indented less than the first field
  |
  = law: AGAM-SYNTAX-001 §2.2
```

### 4.7 Invalid — layout token leak must not resurface

```agam
@lang.base
struct Outer {
    inner: [
        i32; 4
    ],
}
```

Expected: compiles. Bracket-depth suppression must hold for `[` as well as `{`.
If this produces `expected expression, found Indent`, Defect A is not fixed.

---

## 5. Acceptance criteria

The implementing agent must satisfy **all** of the following. Each is
mechanically checkable.

- **AC-1** — Each of examples 4.1, 4.2, 4.3, 4.4, 4.7 compiles with `agamc check`
  exit code 0, and runs under both `agamc run` (JIT) and `agamc build --backend llvm`
  producing **identical stdout**.
- **AC-2** — Examples 4.5 and 4.6 produce the exact error codes `E0130` and
  `E0131` respectively, with the span pointing at the column stated.
- **AC-3** — `Lexer` exposes a `bracket_depth: usize` field. A unit test in
  `agam_lexer` asserts that tokenizing `"@lang.base\nstruct P {\n    x: i32\n}\n"`
  yields a token stream containing **zero** `Indent` and **zero** `Dedent` tokens.
- **AC-4** — A unit test asserts the indentation stack is unchanged across a
  suppressed region: after tokenizing a bracketed multi-line block, the stack
  depth equals its value before the opening bracket.
- **AC-5 (symmetry)** — A test parses 4.1 and 4.4, pretty-prints both `Decl`
  subtrees via `agam_ast::pretty`, and asserts the two strings are equal.
- **AC-6** — `parse_struct_decl` and `parse_enum_decl` each drain
  `Indent`/`Dedent`/`Newline` at the top of their member loop, mirroring
  `parser.rs:1181-1191`. Verified by a test that injects a synthetic `Indent`
  token into an otherwise-valid advance-mode token stream and asserts the struct
  still parses with the correct field count.
- **AC-7** — Full workspace suite passes: `cargo test`, `cargo clippy --all-targets -- -D warnings`,
  `cargo fmt --all -- --check`. Run via `python scripts/cargo_lens.py`.
- **AC-8** — `issues.md` `B-Grade: #1` is moved to `🟢 Yes (Fixed)` with the
  resolution commit cited, and the counter table is updated. Its stated component
  is corrected from the non-existent `layout.rs` to `lexer.rs`.

---

## 6. Required mutation test — MANDATORY

A shallow implementation can pass §4 by special-casing the literal token sequence
`struct <ident> {`. This test exists to detect that. **It is not optional and the
spec may not be marked done without it.**

Add `crates/core/agam_parser/tests/mutation_001_base_type_decls.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-001.
//! Asserts the parser responds to STRUCTURAL changes in base-mode type bodies,
//! not to a memorised token pattern.

const BASE: &str = "@lang.base\nstruct P:\n    a: i32\n    b: i32\n    c: i32\n";

#[test]
fn field_count_tracks_source_mutation() {
    // Removing a field line must reduce the parsed field count by exactly one.
    for drop_line in 0..3 {
        let kept: Vec<&str> = ["    a: i32", "    b: i32", "    c: i32"]
            .iter().enumerate()
            .filter(|(i, _)| *i != drop_line)
            .map(|(_, s)| *s).collect();
        let src = format!("@lang.base\nstruct P:\n{}\n", kept.join("\n"));
        let decl = parse_single_struct(&src).expect("must still parse");
        assert_eq!(decl.fields.len(), 2, "dropping line {drop_line} must yield 2 fields");
    }
}

#[test]
fn field_names_and_types_track_mutation() {
    // Renaming a field must change the AST, not just the source.
    let mutated = BASE.replace("b: i32", "renamed: f64");
    let decl = parse_single_struct(&mutated).expect("must parse");
    assert!(decl.fields.iter().any(|f| f.name.as_str() == "renamed"));
    assert!(!decl.fields.iter().any(|f| f.name.as_str() == "b"));
}

#[test]
fn indentation_mutation_is_rejected() {
    // De-indenting the last field must become an E0131, not silently parse.
    let mutated = BASE.replace("    c: i32", "  c: i32");
    let err = parse_single_struct(&mutated).expect_err("must reject");
    assert_eq!(err.code(), "E0131");
}

#[test]
fn brace_and_colon_forms_are_structurally_identical() {
    // The two surface forms must produce identical ASTs after mutation too.
    let colon = "@lang.base\nstruct P:\n    z: f64\n";
    let brace = "@lang.base\nstruct P {\n    z: f64\n}\n";
    assert_eq!(
        agam_ast::pretty::render_decl(&parse_single_struct(colon).unwrap()),
        agam_ast::pretty::render_decl(&parse_single_struct(brace).unwrap()),
    );
}

#[test]
fn enum_variant_count_tracks_mutation() {
    let base = "@lang.base\nenum E:\n    A\n    B\n    C\n";
    for n in 1..=3 {
        let variants: Vec<&str> = ["    A", "    B", "    C"][..n].to_vec();
        let src = format!("@lang.base\nenum E:\n{}\n", variants.join("\n"));
        assert_eq!(parse_single_enum(&src).unwrap().variants.len(), n);
    }
    let _ = base;
}
```

Helper functions `parse_single_struct` / `parse_single_enum` must be written by
the implementing agent; they tokenize, parse, and return the first `StructDecl` /
`EnumDecl`, or the first `ParseError`.

**Required property:** each test must be shown to FAIL against the pre-fix
compiler (except where it fails to parse at all) and PASS after. Record this in
the commit message.

---

## 7. Open questions — DO NOT decide these yourself

1. **Should the colon-indent struct body require a trailing comma to be legal, or
   forbid it?** §2.2 currently makes `[ "," | ";" ]` optional per field, so
   `x: i32,` and `x: i32` are both legal in indent form. This may be
   undesirable — `agam_fmt` will need one canonical form. **Escalate before
   choosing.**

2. **Should `struct P:` with an empty body be `E0130` (this spec's choice) or
   silently a unit struct?** I chose the error because silent unit-struct
   creation from an apparent typo is a footgun, but the project may prefer
   consistency with `struct P {}`. **Escalate.**

3. **Does bracket-depth suppression interact correctly with multi-line closures
   in base mode?** `|x| {` opens a brace and therefore suppresses layout inside —
   which may be exactly right, or may make indented closure bodies unreachable.
   This spec does not address closures. **Flag any interaction found during
   implementation; do not fix it here.**

4. **Should `@lang.advance` accept the colon-indent form for structs?** This spec
   permits it (the grammar is dialect-neutral). Spec 006 may forbid it. If 006
   lands first, revisit §2.2. **Do not restrict it in this spec.**

5. **Tab/space handling inside a suppressed region.** Unknown whether
   `skip_whitespace` currently rejects mixed tabs and spaces. Out of scope here,
   but if the implementation touches indentation measurement, **escalate rather
   than changing tab semantics as a side effect.**
