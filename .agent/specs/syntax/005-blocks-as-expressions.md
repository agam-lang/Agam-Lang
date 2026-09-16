# 005 — Blocks as Expressions

**Status:** proposed
**Depends on:** **004 (hard prerequisite — do not start without it)**, 001, PRE-000
**Component:** `agam_parser`, `agam_hir`
**Ledger:** new — file as `A-Grade: #5`

---

## 1. Motivation

`agam_ast::expr` defines `ExprKind::Block(Block)` and `ExprKind::BlockExpr(Block)`,
and `Block` carries `expr: Option<Box<Expr>>` for a trailing value. The parser
**cannot produce either**. The only `TokenKind::LBrace =>` arm in the expression
parser (`parser.rs:2058`) parses a struct literal; there is no `LBrace` arm in
`parse_prefix`.

Three user-visible consequences:

1. **No implicit return.** Every function must `return`. All 36 `.agam` files in
   the repository do.
2. **Match arms cannot hold statements.** `parse_match_expr` parses each arm body
   as `self.parse_expression(0)` (`parser.rs:1825`, `:1852`). `Pattern => { a(); b() }`
   has no parse.
3. **`if` and `match` are not reliably value-producing**, because their branches
   can only yield a value through `Block.expr`, which the parser never populates.
   `docs/CHEATSHEET.md` advertises `let status = if score >= 50 { "Pass" } else { "Fail" };`
   which I could not find working in any example.

The AST promises Rust's expression orientation. The parser delivers C's statement
orientation. Rust's match-with-block-arms is one of the most consistently praised
constructs in the language's reception history; Agam has Rust's pattern
*language* attached to a crippled arm body.

**Why 004 is a hard prerequisite:** after this change, `{` in prefix position has
two possible meanings. No lookahead distinguishes them reliably. The restriction
mechanism from 004 is what makes the grammar decidable. Implementing 005 first
produces a parser that is ambiguous by construction.

---

## 2. Formal grammar diff

```ebnf
(* OLD *)
Primary             = Literal
                    | Identifier
                    | ArrayLiteral
                    | StructInit
                    | ClosureExpr
                    | "(" , Expression , ")" ;

Block               = "{" , { Statement } , "}"
                    | INDENT , { Statement } , DEDENT ;

(* NEW *)
Primary             = Literal
                    | Identifier
                    | ArrayLiteral
                    | StructInit
                    | ClosureExpr
                    | BlockExpr                          (* NEW *)
                    | "(" , Expression , ")" ;

BlockExpr           = "{" , { Statement } , [ TailExpr ] , "}"          (* advance form *)
                    | ":" , INDENT , { Statement } , [ TailExpr ] , DEDENT ;  (* base form *)

TailExpr            = Expression ;                (* NOT followed by ";" *)

(*  TAIL-EXPRESSION RULE:
    The final Statement of a BlockExpr is reinterpreted as a TailExpr iff
      (a) it is an ExprStmt, AND
      (b) it is not terminated by ";" (advance) or is the final line (base).
    Otherwise the block's value is unit.                                     *)

(*  A BlockExpr in Primary position is subject to the restriction set R from
    AGAM-SYNTAX-004.  `{` in a NO_STRUCT_LITERAL position begins a Block,
    never a StructInit.  This is what makes the grammar decidable.           *)

MatchArm            = Pattern , [ "if" , Expression ] , "=>" , ( Expression | BlockExpr ) , [ "," ] ;
IfStmt              = "if" , Expression_NoStructLit , BlockExpr ,
                      [ "else" , ( IfStmt | BlockExpr ) ] ;
```

`Block` (the statement-context production) becomes an alias for `BlockExpr` whose
value is discarded. There is one block parser, not two.

---

## 3. AST / HIR / MIR impact

**AST:** no new node types. `ExprKind::Block(Block)` becomes reachable.
`ExprKind::BlockExpr(Block)` is a duplicate of `ExprKind::Block` — **one of them
must be deleted** as part of this work. Pick `Block` (it is the one referenced by
`ExprKind::If`'s branches) and remove `BlockExpr` from `expr.rs`, updating
`visitor.rs` and `pretty.rs`.

**HIR:** `HirLowering` must lower a block expression to the value of its tail
expression, or to unit when absent. If `lower.rs` currently assumes blocks are
statement-only, this is the substantive work.

**MIR:** none expected. A block is a sequence of instructions plus a result
`ValueId`; SSA already models this. **If a MIR change appears necessary, stop and
escalate** — it likely means HIR lowering is wrong.

**Backends:** none. **Any backend diff in this change is a bug.**

### Dialect symmetry statement

`BlockExpr` has two surface forms with identical semantics, and the tail-expression
rule is stated for both. AC-6 requires a test asserting that the base and advance
renderings of the same function produce identical HIR. This is the highest-risk
symmetry claim in the spec set, because the base form introduces an
indentation-sensitive *expression* grammar — see open question 1.

---

## 4. Worked examples

### 4.1 Valid — implicit return, advance

```agam
@lang.advance
fn double(n: i32) -> i32 {
    n * 2
}

fn main() -> i32 {
    print_int(double(21));
    return 0;
}
```

Expected: compiles, prints `42`.

### 4.2 Valid — implicit return, base

```agam
@lang.base
fn double(n: i32) -> i32:
    n * 2

fn main() -> i32:
    print_int(double(21))
    return 0
```

Expected: compiles, prints `42`. Identical HIR to 4.1.

### 4.3 Valid — block expression bound to a name

```agam
@lang.advance
fn main() -> i32 {
    let x = {
        let t = 20;
        t + 1
    };
    print_int(x);
    return 0;
}
```

Expected: compiles, prints `21`.

### 4.4 Valid — match arms with statement blocks

```agam
@lang.advance
enum Op { Add, Sub }

fn apply(o: Op, a: i32, b: i32) -> i32 {
    match o {
        Op::Add => {
            print_int(1);
            a + b
        },
        Op::Sub => a - b,
    }
}

fn main() -> i32 {
    print_int(apply(Op::Add, 2, 3));
    return 0;
}
```

Expected: compiles, prints `1` then `5`.

### 4.5 Valid — match arms with indented blocks, base

```agam
@lang.base
enum Op:
    Add
    Sub

fn apply(o: Op, a: i32, b: i32) -> i32:
    match o:
        Op::Add =>
            print_int(1)
            a + b
        Op::Sub => a - b
```

Expected: compiles, identical HIR to 4.4's `apply`. **This is the hardest case in
the spec.** Requires 001.

### 4.6 Valid — `if` as an expression

```agam
@lang.advance
fn main() -> i32 {
    let score = 70;
    let pass = if score >= 50 { 1 } else { 0 };
    print_int(pass);
    return 0;
}
```

Expected: compiles, prints `1`.

### 4.7 Valid — trailing semicolon suppresses the value

```agam
@lang.advance
fn f() -> void {
    let x = 1;
    x + 1;
}
```

Expected: compiles. Block value is unit, not `2`, because of the `;`. A test must
assert the HIR result type is unit.

### 4.8 Invalid — tail expression type mismatch

```agam
@lang.advance
fn double(n: i32) -> i32 {
    "not an int"
}
```

Expected, exactly:

```
error[E0308]: mismatched types
 --> input.agam:3:5
  |
2 | fn double(n: i32) -> i32 {
  |                      --- expected `i32` because of the return type
3 |     "not an int"
  |     ^^^^^^^^^^^^ expected `i32`, found `str`
  |
  = law: AGAM-SYNTAX-005 §2
```

### 4.9 Invalid — non-final expression statement without a semicolon, advance

```agam
@lang.advance
fn f() -> i32 {
    1 + 1
    2 + 2
}
```

Expected:

```
error[E0151]: expected `;` after expression statement
 --> input.agam:3:10
  |
3 |     1 + 1
  |          ^ only the final expression in a block may omit `;`
  |
  = law: AGAM-SYNTAX-005 §2
```

### 4.10 Invalid — mismatched if/else branch types

```agam
@lang.advance
fn main() -> i32 {
    let x = if true { 1 } else { "two" };
    return 0;
}
```

Expected: `E0308` naming `i32` and `str` as the two branch types, with both
branch spans shown.

---

## 5. Acceptance criteria

- **AC-1** — 4.1 through 4.7 compile and produce the stated stdout under
  **both** `agamc run` and `agamc build --backend llvm`, byte-identical.
- **AC-2** — 4.8, 4.9, 4.10 produce exactly `E0308`, `E0151`, `E0308` with the
  stated spans.
- **AC-3** — `ExprKind::BlockExpr` no longer exists.
  `grep -rn 'BlockExpr' crates/core/agam_ast/src/` returns nothing. Grep output
  pasted into the commit message.
- **AC-4** — 4.7's block has HIR result type unit; 4.3's has type `i32`. Asserted
  directly against HIR, not inferred from program output.
- **AC-5** — Every existing `.agam` file in the repository still compiles
  unchanged. Explicit `return` must remain fully legal; this spec adds a form, it
  does not remove one.
- **AC-6 (symmetry)** — Tests assert HIR equality for the pairs (4.1, 4.2) and
  (4.4's `apply`, 4.5's `apply`) after span normalisation.
- **AC-7** — Zero diff in `crates/backends/`. Asserted by the reviewer, stated in
  the commit message.
- **AC-8** — `cargo test`, `clippy -D warnings`, `fmt --check` via
  `python scripts/cargo_lens.py`.
- **AC-9** — `issues.md` gains `A-Grade: #5`, closed.
- **AC-10** — `docs/CHEATSHEET.md`'s `if`-expression example now actually
  compiles; it is added to the `doctest_check.py` corpus.

---

## 6. Required mutation test — MANDATORY

A shallow implementation can pass §4 by special-casing "a lone expression as the
last statement of a function body". This test defeats that by nesting and by
varying position.

Add `crates/middle/agam_hir/tests/mutation_005_block_expressions.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-005.
//! Block value must be computed structurally at any nesting depth and must
//! track which statement is final.

/// Build a block nested `depth` levels deep whose innermost tail is `value`.
fn nested(depth: usize, value: i32) -> String {
    let mut inner = format!("{value}");
    for _ in 0..depth {
        inner = format!("{{ let _t = 0; {inner} }}");
    }
    format!("@lang.advance\nfn main() -> i32 {{ let r = {inner}; print_int(r); return 0; }}\n")
}

#[test]
fn block_value_propagates_through_arbitrary_nesting() {
    for depth in 0..=6 {
        for value in [0, 1, 42, -7] {
            let out = run_jit(&nested(depth, value))
                .unwrap_or_else(|e| panic!("depth={depth} value={value}: {e:?}"));
            assert_eq!(out.trim(), value.to_string(), "depth={depth} value={value}");
        }
    }
}

#[test]
fn jit_and_llvm_agree_at_every_depth() {
    // Parity is the invariant most at risk from this change.
    for depth in 0..=6 {
        let src = nested(depth, 42);
        assert_eq!(run_jit(&src).unwrap(), run_llvm(&src).unwrap(), "depth={depth}");
    }
}

#[test]
fn semicolon_mutation_flips_the_block_type() {
    // The ONLY difference between these two is a trailing ';'.
    let valued = "@lang.advance\nfn f() -> i32 { let x = 1; x + 1 }\n";
    let unit   = "@lang.advance\nfn f() -> i32 { let x = 1; x + 1; }\n";
    assert!(compile_str(valued).is_ok(), "tail expression form must typecheck");
    let err = compile_str(unit).expect_err("unit-valued body must not satisfy -> i32");
    assert_eq!(err.code(), "E0308");
}

#[test]
fn tail_position_mutation_is_tracked() {
    // Move the un-semicoloned expression through every position in a 4-stmt block.
    for tail_at in 0..4 {
        let stmts: Vec<String> = (0..4)
            .map(|i| if i == tail_at { format!("{i}") } else { format!("let _v{i} = {i};") })
            .collect();
        let src = format!("@lang.advance\nfn f() -> i32 {{ {} }}\n", stmts.join(" "));
        let result = compile_str(&src);
        if tail_at == 3 {
            assert!(result.is_ok(), "expression in final position must be the tail");
        } else {
            assert_eq!(result.unwrap_err().code(), "E0151",
                "expression at position {tail_at} of 4 must require a `;`");
        }
    }
}

#[test]
fn base_and_advance_block_expressions_produce_identical_hir() {
    for value in [0, 1, 42] {
        let adv  = format!("@lang.advance\nfn f() -> i32 {{\n    {value}\n}}\n");
        let base = format!("@lang.base\nfn f() -> i32:\n    {value}\n");
        assert_eq!(normalize_hir(&lower_str(&adv).unwrap()),
                   normalize_hir(&lower_str(&base).unwrap()),
                   "value={value}: dialects must produce identical HIR");
    }
}

#[test]
fn match_arm_block_bodies_track_statement_count() {
    // Defeats a recogniser that only handles single-statement arm blocks.
    for n in 1..=5 {
        let body: Vec<String> = (0..n - 1).map(|i| format!("let _a{i} = {i};")).collect();
        let src = format!(
            "@lang.advance\nenum E {{ A, B }}\n\
             fn f(e: E) -> i32 {{ match e {{ E::A => {{ {} 7 }}, E::B => 0, }} }}\n\
             fn main() -> i32 {{ print_int(f(E::A)); return 0; }}\n",
            body.join(" "));
        assert_eq!(run_jit(&src).unwrap().trim(), "7", "n={n}");
    }
}
```

**Required property:** every test here must FAIL on the pre-fix compiler — most
by failing to parse. Record the pre-fix failure mode for each in the commit
message.

---

## 7. Open questions — DO NOT decide these yourself

1. **How is the base-mode block expression delimited when it appears inside an
   expression, e.g. bound by `let`?** §4.5 shows match arms, where the `=>`
   provides an anchor. But `let x =` followed by a newline and an indented block
   has no closing marker except the dedent, and dedent-based expression
   termination interacts badly with binary operators continuing across lines.
   F# spent several releases on exactly this (`#light` and the "undentation"
   exception list in the F# spec §15.1.10). **This is the single highest-risk
   open item in the spec set. Escalate with a concrete proposal before
   implementing the base form of `BlockExpr` outside match arms.**

2. **Does `parse_block`'s one-statement heuristic (`parser.rs:1195-1198`) survive
   this change?** It probably cannot — a heuristic that truncates a block after
   one statement is incompatible with tail-expression detection. **Determine
   whether it must be deleted, and escalate if deleting it breaks `if x: return 0`
   single-line form.**

3. **Should `loop` be expression-valued (`break value`)?** Rust does this. This
   spec does not address it. **Do not add it here.**

4. **Unit-typed tail expressions.** Is `fn f() -> void { g() }` (no semicolon,
   `g` returns unit) legal, or must it be `g();`? §2 permits it. **Confirm this is
   intended.**

5. **Interaction with effect handler clause bodies.** `HandlerClause { body: Expr }`
   takes a single expression, same limitation as match arms had. This spec does
   not extend it. **Flag whether it should be in scope; do not extend it
   silently.**

6. **`ExprKind::Block` vs `ExprKind::BlockExpr` deletion.** AC-3 chooses to
   delete `BlockExpr`. If `agam_hir` or `agam_gui`'s AST evaluator depends on
   `BlockExpr` specifically, this choice may be wrong. **Check
   `crates/experiments/agam_gui/src/eval.rs` before deleting and escalate if it
   is used there.**
