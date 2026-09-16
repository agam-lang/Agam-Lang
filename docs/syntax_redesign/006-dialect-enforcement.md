# 006 — Dialect Enforcement

**Status:** proposed
**Depends on:** **003 (hard)**, 001
**Component:** `agam_parser`, `agam_errors`
**Ledger:** new — file as `B-Grade: #5`

---

## 1. Motivation

`agam_parser` contains no dialect awareness. There is no `SyntaxMode` import and
no conditional branch on the profile anywhere in `parser.rs`. `parse_block`
(`parser.rs:1164-1178`) accepts four shapes unconditionally: `{ ... }`,
`: INDENT ... DEDENT`, `: <one statement>`, and no delimiter at all. Brace bodies
additionally drain any layout tokens that appear inside them
(`parser.rs:1181-1191`).

Consequences today:

- A `@lang.advance` file may use colon-and-indent blocks.
- A `@lang.base` file may use braces.
- A single function may open with `{`, contain an indented block, and close with `}`.
- No diagnostic fires for any of this.

So the three advertised dialects are, at the parser level, one permissive grammar.
That is a legitimate implementation strategy — Haskell's layout rule is defined
as sugar for explicit `{;}` and both forms are legal — but Haskell **specifies**
the equivalence (Report §10.3) and its tooling relies on it. Agam documents the
dialects as distinct and then does not enforce the distinction, so neither users
nor tooling can depend on it. `agam_fmt` (237 lines, the smallest tooling crate
in the workspace) has no canonical form to normalise toward.

---

## 2. Formal grammar diff

```ebnf
(* OLD *)
Block               = "{" , { Statement } , "}"           (* In @lang.advance *)
                    | INDENT , { Statement } , DEDENT ;   (* In @lang.base *)
(*  the parenthetical comments are non-normative; nothing enforces them *)

(* NEW — the mode becomes normative *)

Block_advance       = "{" , { Statement } , [ TailExpr ] , "}" ;
Block_base          = ":" , INDENT , { Statement } , [ TailExpr ] , DEDENT
                    | ":" , Statement ;                   (* single-line form *)

Block               = Block_advance   (* iff SyntaxMode = Advance *)
                    | Block_base ;    (* iff SyntaxMode in { BaseStatic, BaseDynamic } *)

(*  A Block_base appearing in Advance mode is error E0160.
    A Block_advance appearing in a Base mode is error E0161.
    Struct, enum, impl, trait, effect and handler bodies follow the same rule
    via the same mechanism.                                                   *)
```

The `TailExpr` production is from spec 005. If 005 has not landed, omit it here
and keep `{ Statement }`.

**The parser gains a `mode: SyntaxMode` field**, supplied by the caller. It is
consulted at exactly the block-opening sites and nowhere else.

---

## 3. AST / HIR / MIR impact

**AST / HIR / MIR / backends: none.** This spec adds diagnostics only. Every
program that compiles after this change produces the same AST it produced before.

**API change:** `agam_parser::parse(tokens, source_id)` gains a mode parameter.
Spec 003 already threads a mode through `tokenize`; reuse the same value. **The
lexer's mode and the parser's mode must be the same value from the same source** —
add a debug assertion, because a mismatch would produce nonsensical errors.

### Dialect symmetry statement

This spec restricts *surface form*, not expressive power. For every program
expressible in one dialect there must remain an equivalent program in the other
producing an identical AST. AC-4 requires a corpus test asserting exactly this
over every example file in the repository, translated to the opposite dialect.

**If AC-4 cannot be satisfied for some construct, that construct has an
expressiveness asymmetry and this spec must not be landed until it is fixed** —
enforcing dialects while an asymmetry exists would make one dialect permanently
less capable rather than merely differently-punctuated.

---

## 4. Worked examples

### 4.1 Valid — advance, braces throughout

```agam
@lang.advance
fn main() -> i32 {
    if true {
        print_int(1);
    }
    return 0;
}
```

Expected: compiles, prints `1`.

### 4.2 Valid — base, colon-indent throughout

```agam
@lang.base
fn main() -> i32:
    if true:
        print_int(1)
    return 0
```

Expected: compiles, prints `1`. Identical AST to 4.1.

### 4.3 Valid — base single-line form

```agam
@lang.base
fn small(n: i32) -> i32:
    if n > 0: return 1
    return 0
```

Expected: compiles. The `Block_base` single-statement alternative covers this.

### 4.4 Invalid — colon block in advance mode

```agam
@lang.advance
fn main() -> i32:
    return 0
```

Expected, exactly:

```
error[E0160]: indentation block in `@lang.advance` source
 --> input.agam:2:17
  |
1 | @lang.advance
  | ------------- file declares the `advance` profile
2 | fn main() -> i32:
  |                 ^ `advance` requires a `{ ... }` block here
  |
  = fix: fn main() -> i32 { ... }
  = law: AGAM-SYNTAX-006 §2
```

### 4.5 Invalid — brace block in base mode

```agam
@lang.base
fn main() -> i32 {
    return 0
}
```

Expected:

```
error[E0161]: brace block in `@lang.base` source
 --> input.agam:2:18
  |
1 | @lang.base
  | ---------- file declares the `base` profile
2 | fn main() -> i32 {
  |                  ^ `base` requires `:` and an indented block here
  |
  = fix: fn main() -> i32:
  = law: AGAM-SYNTAX-006 §2
```

### 4.6 Invalid — mixed within one function

```agam
@lang.advance
fn main() -> i32 {
    if true:
        print_int(1)
    return 0;
}
```

Expected: `E0160` on the `:` at line 3. Exactly one error, not a cascade — the
parser must recover and continue.

### 4.7 Valid — struct literal braces are unaffected

```agam
@lang.base
struct P:
    x: i32

fn main() -> i32:
    let p = P { x: 1 }
    return p.x
```

Expected: compiles. **A struct literal is not a block.** `{` in expression
position is never subject to E0161. This distinction is the main implementation
hazard in this spec.

---

## 5. Acceptance criteria

- **AC-1** — 4.1, 4.2, 4.3, 4.7 compile with exit 0 and produce identical stdout
  under both backends.
- **AC-2** — 4.4, 4.5 produce exactly `E0160`, `E0161` with the stated spans and
  the profile-declaration secondary label.
- **AC-3** — 4.6 produces exactly one diagnostic.
- **AC-4 (symmetry, blocking)** — A corpus test takes every `.agam` file in
  `examples/`, `agam/examples/`, and `benchmarks/suites/`, mechanically translates
  it to the opposite dialect, and asserts both versions produce identical ASTs
  after span normalisation. **If any file cannot be translated, this spec is
  blocked.**
- **AC-5** — Array literals, struct literals, closure brace bodies, and match
  brace bodies are not affected by E0161 in base mode. One test per construct.
- **AC-6** — `agam_fmt` gains a canonical form per dialect and a round-trip test:
  `fmt(fmt(x)) == fmt(x)` for every corpus file.
- **AC-7** — Every existing `.agam` file compiles, after being migrated in the
  same commit if it mixed forms. List migrated files in the commit body.
- **AC-8** — `cargo test`, `clippy -D warnings`, `fmt --check` via
  `python scripts/cargo_lens.py`.
- **AC-9** — `issues.md` gains `B-Grade: #5`, closed.

---

## 6. Required mutation test — MANDATORY

Add `crates/core/agam_parser/tests/mutation_006_dialect_enforcement.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-006.
//! Enforcement must be positional and exhaustive, not applied only to `fn`.

/// Every construct that opens a block, as (header, advance_body, base_body).
fn block_openers() -> Vec<(&'static str, &'static str, &'static str)> {
    vec![
        ("fn f() -> i32",          "{ return 0; }",       ":\n    return 0"),
        ("if true",                "{ x = 1; }",          ":\n    x = 1"),
        ("while false",            "{ x = 1; }",          ":\n    x = 1"),
        ("for i in 0..1",          "{ x = 1; }",          ":\n    x = 1"),
        ("struct S",               "{ a: i32 }",          ":\n    a: i32"),
        ("enum E",                 "{ A, B }",            ":\n    A\n    B"),
    ]
}

#[test]
fn every_block_opener_is_enforced_in_both_directions() {
    for (i, (header, adv_body, base_body)) in block_openers().iter().enumerate() {
        // advance form in base mode -> E0161
        let bad_base = wrap_base(&format!("{header} {adv_body}"));
        assert_eq!(compile_str(&bad_base).unwrap_err().code(), "E0161",
            "opener {i} ({header}): advance body in base mode must be E0161");

        // base form in advance mode -> E0160
        let bad_adv = wrap_advance(&format!("{header}{base_body}"));
        assert_eq!(compile_str(&bad_adv).unwrap_err().code(), "E0160",
            "opener {i} ({header}): base body in advance mode must be E0160");
    }
}

#[test]
fn matching_forms_are_always_accepted() {
    for (i, (header, adv_body, base_body)) in block_openers().iter().enumerate() {
        assert!(compile_str(&wrap_advance(&format!("{header} {adv_body}"))).is_ok(),
            "opener {i}: advance/advance must be accepted");
        assert!(compile_str(&wrap_base(&format!("{header}{base_body}"))).is_ok(),
            "opener {i}: base/base must be accepted");
    }
}

#[test]
fn expression_braces_are_never_enforced() {
    // Defeats a naive "reject all LBrace in base mode" implementation.
    let sources = [
        "let a = [1, 2, 3]",
        "let p = P { x: 1 }",
        "let f = |x| { x + 1 }",
        "let m = match 1 { _ => 0 }",
    ];
    for (i, s) in sources.iter().enumerate() {
        let src = wrap_base(&format!("fn f() -> i32:\n    {s}\n    return 0"));
        if let Err(e) = compile_str(&src) {
            assert_ne!(e.code(), "E0161", "expression form {i} must not be enforced");
        }
    }
}

#[test]
fn error_count_does_not_cascade() {
    // N mixed blocks must produce exactly N errors, not N^2 or 1.
    for n in 1..=4 {
        let bodies: Vec<String> = (0..n)
            .map(|i| format!("    if true:\n        print_int({i});"))
            .collect();
        let src = format!("@lang.advance\nfn main() -> i32 {{\n{}\n    return 0;\n}}\n",
                          bodies.join("\n"));
        let errs = collect_errors(&src);
        assert_eq!(errs.iter().filter(|e| e.code() == "E0160").count(), n,
            "n={n} mixed blocks must yield exactly {n} E0160s, got {errs:?}");
    }
}
```

**Required property:** `every_block_opener_is_enforced_in_both_directions` must
FAIL entirely on the pre-fix compiler (nothing is enforced today). Record this.

---

## 7. Open questions — DO NOT decide these yourself

1. **Is the base single-line form `if n > 0: return 1` (§4.3) definitely staying?**
   It is what `parse_block`'s one-statement heuristic exists to support, and spec
   005 open question 2 may require deleting that heuristic. **Coordinate with 005
   before implementing `Block_base`'s second alternative.**

2. **Should `@lang.base.dynamic` be enforced identically to `@lang.base`?** This
   spec assumes yes. Spec 007 proposes removing the profile entirely, which would
   make the question moot. **Sequence 007 first if it is accepted.**

3. **Migration severity.** Should E0160/E0161 be errors from day one, or warnings
   for one release? The repo has ~36 `.agam` files so migration cost is near zero
   now, which argues for errors. **Confirm before landing.**

4. **Does `impl` / `trait` / `effect` / `handler` body parsing go through
   `parse_block`?** The mutation test covers six openers; these four are not among
   them because I did not verify their parse paths. **Enumerate every block-opening
   site in `parser.rs` before implementing, add each to `block_openers()`, and
   escalate if any cannot be enforced through the same mechanism.**

5. **What is `agam_fmt`'s canonical form?** AC-6 requires one but does not specify
   it (trailing commas, brace placement, indent width). **This needs its own
   decision; escalate rather than inventing a style.**
