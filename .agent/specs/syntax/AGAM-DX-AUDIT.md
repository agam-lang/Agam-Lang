# Agam Syntax, DX & Ecosystem Audit

**Date:** 2026-09-16
**Basis of analysis:** the compiler source as checked out, specifically
`agam/crates/core/agam_lexer/src/{lexer.rs,token.rs}`,
`agam/crates/core/agam_parser/src/parser.rs`,
`agam/crates/core/agam_ast/src/{expr.rs,decl.rs,pattern.rs,types.rs}`,
`agam/crates/middle/agam_hir/src/lower.rs`,
`agam/crates/middle/agam_sema/src/resolver.rs`,
`agam/crates/tooling/agam_pkg/src/lib.rs`,
`agam/crates/tooling/agam_driver/src/cli.rs`,
`docs/grammar.ebnf`, `docs/PARSER_GRAMMAR_SPECIFICATION.md`, `docs/CHEATSHEET.md`,
`examples/01_basics/*.agam`, `agam/examples/*.agam`, `note.md`, `issues.md`.

**Methodological note, stated up front:** `docs/grammar.ebnf` is not a usable
specification of Agam. It omits `match`, `trait`, `impl`, `effect`/`handle`/
`perform`/`resume`, `async`/`await`/`spawn`, f-strings, ranges, tuples, generic
bounds, attributes (`#[...]`), annotations (`@test`), `var`, `import`, and type
casts — all of which exist in `agam_ast` and are parsed by `agam_parser`. It also
specifies `strict` (`StrictBlock = "strict" , Block`), which has **zero**
implementation: `grep -n 'Strict' crates/core/agam_parser/src/parser.rs
crates/middle/agam_hir/src/lower.rs` returns nothing. I therefore audited the
parser and AST directly. Where I say "Agam does X," I mean the compiler does X,
and I cite the file and line.

---

# Part 1 — Syntax audit

## 1.0 The finding that subsumes most others: the dialects are not enforced

This is the single most consequential structural fact in the front end, and it
isn't documented anywhere in `docs/`.

`agam_parser` has **no dialect awareness at all**. There is no `SyntaxMode`
import, no profile parameter, no conditional branch on `@lang.base` vs
`@lang.advance` anywhere in `parser.rs`. The entire dialect distinction lives in
the lexer (`lexer.rs:52-70`), which decides one thing only: whether to synthesize
`Indent`/`Dedent` tokens.

The parser then accepts both block forms unconditionally
(`parser.rs:1164-1178`):

```rust
fn parse_block(&mut self) -> Result<Block, ParseError> {
    self.skip_newlines();
    let start = self.peek().span.start;
    let has_brace = self.eat(TokenKind::LBrace);
    if !has_brace {
        self.eat(TokenKind::Colon);
    }
    self.skip_newlines();
    let has_indent = if !has_brace { self.eat(TokenKind::Indent) } else { false };
```

Four accepted shapes: `{ ... }`, `: INDENT ... DEDENT`, `: <one statement>`, and
**no delimiter at all**. Consequences:

1. A `@lang.advance` file may freely use `:`-and-indent blocks. Braces are not
   required by anything.
2. A `@lang.base` file may freely use braces, because `parse_block` checks for
   `LBrace` first and the lexer's `Indent` tokens are then explicitly skipped
   inside brace bodies (`parser.rs:1181-1191`).
3. There is no diagnostic for mixing them within one file, or even within one
   function.

So "three syntaxes" is, at the parser level, one grammar with a permissive block
rule. That is a defensible implementation strategy — it's roughly what
**Haskell's layout rule** does (layout is sugar for explicit `{;}`, and both are
legal) — but Haskell *documents* the equivalence and defines it formally in the
Report §10.3. Agam documents the dialects as distinct profiles and then does not
enforce the distinction, which is the worst of both: users can't rely on the
constraint, and tooling can't either.

**Comparison with documented sentiment:** the closest analogue is **Perl's
`use strict`**, an opt-in pragma that changed the meaning of a file. The
community consensus that emerged (visible in Perl Best Practices, 2005, and in
the eventual `use v5.12` auto-enabling of strict) was that opt-in-per-file
language modes cause silent drift and that the mode should be lifted to a
package-level declaration. **Rust reached the same conclusion structurally**: the
`edition` key lives in `Cargo.toml`, not in a per-file comment, precisely so a
file can't silently be interpreted under the wrong rules. See §1.1 for why this
matters concretely for Agam.

### 1.0.1 A missing directive silently selects base mode

`lexer.rs:52-70`:

```rust
fn detect_mode(&mut self) {
    let saved_pos = self.cursor.pos();
    self.cursor.eat_while(|c| c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '\u{FEFF}');
    if self.cursor.starts_with("@lang.base.dynamic") { self.mode = SyntaxMode::BaseDynamic; }
    else if self.cursor.starts_with("@lang.base") { self.mode = SyntaxMode::BaseStatic; }
    else if self.cursor.starts_with("@lang.advance") { self.mode = SyntaxMode::Advance; }
    else { self.mode = SyntaxMode::BaseStatic; }   // <-- default
```

`eat_while` skips whitespace only. It does not skip comments. So:

```agam
// Copyright 2026 Agam contributors. Licensed MIT.
@lang.advance
fn main() -> i32 { ... }
```

...is lexed in **BaseStatic** mode. Indentation becomes significant in a
brace-formatted file. Any indented line inside `main` now emits `Indent`, and any
construct that doesn't skip layout tokens (see §1.4) fails with the confusing
`expected expression, found Indent` already recorded as B-Grade #1.

A license header at the top of a source file is not an exotic input. This is a
latent bug affecting the most standard file-authoring convention there is.

### 1.0.2 `@lang.base.dynamic` is currently a no-op

`grep -rn 'BaseDynamic' crates/ --include='*.rs'` returns four hits, all in
`lexer.rs`, and in every one of them `BaseDynamic` appears in a disjunction with
`BaseStatic` and is treated identically:

```rust
if self.mode == SyntaxMode::BaseStatic || self.mode == SyntaxMode::BaseDynamic { ... }
```

Nothing downstream — parser, sema, HIR — ever reads the mode. `var` is accepted
in every dialect because `parse_var_stmt` (`parser.rs:1073`) is reachable
unconditionally. So the third dialect does not exist as a dialect; it is a
comment that changes nothing.

`examples/hello_base_dynamic.agam` relies on features that follow from it not
existing:

```agam
@lang.base.dynamic
fn main():
    name = "World"          # bare assignment, no let/var
    print("Hello,", name)
    scores = [90, 85, 72, 95]
```

`name = "World"` parses as `ExprKind::Assign` to an unbound identifier. There is
no implicit-declaration path in `agam_sema`'s resolver. I could not run `agamc`
in this environment to confirm, so I'll state this as high-confidence rather than
verified: **this example almost certainly does not compile.** It should be
compiled in CI or deleted; a published example that doesn't build is exactly the
"false confidence" failure mode `note.md` §3 diagnoses.

### 1.0.3 `var` / `dyn` collapse to `Any` — there is no dynamic typing

`agam_ast/src/types.rs` documents a "dual typing system" with `TypeMode::Static`
/ `Dynamic` / `Inferred`. HIR lowering (`agam_hir/src/lower.rs:1111-1113`):

```rust
agam_ast::types::TypeExprKind::Dynamic | agam_ast::types::TypeExprKind::Any => {
    self.types.any()
}
```

Both become the single `any` type. There is no runtime type tag, no dynamic
dispatch, no runtime type error. `TypeMode` is carried on `TypeExpr` and then
never consulted by HIR. So `var x = 42` is not "Python-like runtime checking"; it
is an untyped hole in an otherwise static system.

**Comparison:** TypeScript's `any` is the documented reference point. The TS team's
own retrospective position (the `noImplicitAny` flag, on by default under
`strict` since TS 2.3, and the introduction of `unknown` in 3.0) is that an
escape-hatch type that silently disables checking was the single biggest source
of "TypeScript didn't catch my bug" complaints. Agam currently has TypeScript's
`any` with none of `noImplicitAny`, `unknown`, or the strict-mode flag, and it is
reachable via a keyword that markets itself as a typing *mode*.

### 1.0.4 Refinement types are parsed and then discarded

`types.rs` defines `TypeExprKind::Refined { base, predicate }` for
`{v: i32 | v > 0}`. HIR lowering (`lower.rs:1174`):

```rust
agam_ast::types::TypeExprKind::Refined { base, .. } => self.resolve_type_expr(base),
```

The predicate is dropped with `..`. A program that writes a refinement type gets
no checking and no warning — it silently means the base type. There is an
`agam_smt` crate (498 LOC) which presumably was intended to discharge these, but
nothing connects it to this path. Silent semantic loss is worse than
non-support: the user believes they have a constraint.

---

## 1.1 Construct-by-construct: `@lang.advance`

### Variable declaration

```agam
let mut result: i32 = 1;
const MAX: i32 = 1000;
var x = 42;              // accepted, means "any"
```

`LetStmt` makes both the type annotation and the initializer optional
(`grammar.ebnf` line 45, matching `parse_let_stmt`). `let x;` with no type and no
value is grammatically legal. Whether sema rejects it, I did not verify — flagging
as unchecked.

**Friction:** three declaration keywords (`let` / `const` / `var`) with
overlapping meaning, where `var` is a no-op. Compare **Swift**, which shipped
`let`/`var` as a two-keyword system with a crisp rule (immutable/mutable) and got
consistently positive reception in the Swift Evolution discourse; versus
**JavaScript's `var`/`let`/`const`**, where the third keyword arriving later with
partially-overlapping semantics is the canonical example cited in ES6 migration
writeups as a permanent teaching tax. Agam has JS's shape without JS's excuse
(no backward-compatibility constraint exists yet).

### Function definition

```agam
fn power(base: i32, exp: i32) -> i32 { ... }
```

Clean, Rust-shaped. `FunctionDecl` supports generics, async, annotations,
visibility. No issues at the declaration site.

**Friction — implicit return does not exist in practice.** `Block` carries
`expr: Option<Box<Expr>>`, so the AST models trailing-expression returns. But I
found no `LBrace` arm in `parse_prefix` — the only `TokenKind::LBrace =>` in the
infix/postfix table (`parser.rs:2058`) parses a **struct literal**. So a
brace-block is not an expression. `let x = { compute(); value };` does not parse.
Every example file uses explicit `return`. The AST promises Rust's
expression-orientation; the parser delivers C's statement-orientation.

`docs/CHEATSHEET.md` compounds this by advertising a shorthand that does not
exist:

```agam
fn square(n: Int) -> Int => n * n;      // no parser support for `=>` fn bodies
```

`FatArrow` appears in `parser.rs` at exactly two sites (1824, 1851), both inside
`parse_match_expr`. Also `Int` is not a type — `is_primitive_type` in `types.rs`
lists `i8..i512`, `u8..u512`, `f32`, `f64`, `bool`, `char`, `str`, `String`,
`void`, `never`, `Any`. `Int`, `Float`, `Bool`, `Nil` are all fictional.

### Control flow

`if` / `while` / `for x in e` / `loop` / `break` / `continue` all present.

**Friction — `if` as an expression is unreliable.** `ExprKind::If` exists with an
`else_branch`, and the CHEATSHEET advertises
`let status = if score >= 50 { "Pass" } else { "Fail" };`. But since brace-blocks
are not expressions (above), the branches can only produce a value through
`Block.expr`, which requires a trailing expression the parser must populate —
which in turn requires statement-position expression parsing to distinguish
"last expression" from "expression statement." I could not confirm this works
end-to-end without running the compiler. **Flagging as unverified**, but note
that no example file in the repo uses an `if` expression, which is weak evidence
against.

**Friction — struct-literal / block ambiguity is handled by two *different*
heuristics.** Path 1, `parse_prefix` → path expression (`parser.rs:1396`), calls
`looks_like_struct_literal()` (`parser.rs:60-80`), which **skips** `Newline`,
`LineComment`, `BlockComment`, `Indent`, `Dedent` before testing. Path 2, the
postfix loop (`parser.rs:1238-1251`), uses raw offsets:

```rust
let first = self.peek_at(1);
(first == TokenKind::Identifier || first == TokenKind::StringLiteral)
    && self.peek_at(2) == TokenKind::Colon
```

No layout skipping. So whether

```agam
let p = Point {
    x: 1,
    y: 2,
};
```

is recognized depends on which of the two paths the parser reached — the
multi-line form fails the raw-offset test (`peek_at(1)` is `Newline`). Two
disambiguation rules for one construct is a defect regardless of which one wins
in practice.

**Comparison:** Rust hit this exact ambiguity and solved it with an explicit
parser restriction flag (`Restrictions::NO_STRUCT_LITERAL`), threaded through
condition and match-scrutinee positions, rather than lookahead. The Rust
reference documents the restriction (`ExpressionWithBlock` / "struct expressions
are not allowed in the condition of an if"). Lookahead heuristics for this
problem are known to be brittle; Rust's approach is the tested one.

### Struct / enum definition

Advance mode works. Base mode does not — see §1.3, the hard asymmetry.

**Friction — enum variants cannot have named tuple fields.**
`VariantFields::Tuple(Vec<TypeExpr>)` in `decl.rs` holds types only. The
CHEATSHEET advertises `Processing(percent: Int)`. Not supported.

### Generics

`GenericParam { name, bounds, default }` supports `T: Trait + Other` and
defaults. But `grammar.ebnf` line 19 specifies
`GenericParams = "<" , Identifier , { "," , Identifier } , ">"` — no bounds at
all. The grammar is behind the AST by a whole feature.

`agam_mir/src/monomorphize.rs` exists, so monomorphization is the strategy. I did
not audit its completeness.

### Error handling

`ExprKind::Try(Box<Expr>)` for `?` exists; `TypeExprKind::Result { ok, err }` and
`Optional` exist. Yet `examples/calculator_advance.agam` — the flagship
demonstration program — does this:

```agam
if op == 4 {
    if rhs == 0 {
        return -999999;   // Error: division by zero
    }
    return lhs / rhs;
}
```

Sentinel error values, C-style. Across both calculator examples there is not one
`Result`, `Option`, `match`, `enum`, or `?`. The examples are written in the
subset that demonstrably works, which is the honest choice, but it means the
repo's own showcase code contradicts the feature list.

**Comparison:** this is the **Go pre-generics** situation in miniature. Go's
`interface{}`-and-copy-paste era produced a well-documented gap between what the
language advertised and what idiomatic code looked like; the Go team's own
generics design doc (Taylor/Griesemer, 2020) cites the accumulated workaround
patterns as primary evidence. The lesson from Go 1.18's reception is that closing
such a gap is received extremely well *when it lands* — but that the gap itself
is read by outsiders as the language's real capability level, regardless of what
the docs claim.

### Pattern matching

`PatternKind` is genuinely complete: wildcard, binding, literal, tuple, array
with rest, struct with rest, variant, or-patterns, ranges, `@`-bindings, typed
patterns. `agam_sema/src/exhaustive.rs` implements usefulness-based exhaustiveness
checking with proper constructor arity. This is the strongest part of the front
end.

**Friction — match arms cannot contain statement blocks.** `parse_match_expr`
(`parser.rs:1825, 1852`) parses each arm body as `self.parse_expression(0)`.
Since brace-blocks are not expressions, `Pattern => { do_a(); do_b() }` has no
parse. Compare **Rust**, where `match` arms taking blocks is one of the most
frequently praised ergonomics in the language (it's the construct that survives
essentially unchanged from 1.0 and is cited positively in every "what Rust got
right" retrospective). Agam has Rust's pattern *language* with a crippled arm
body.

### Concurrency / async

Tokens: `Async`, `Await`, `Spawn`. AST: `ExprKind::Await`, `ExprKind::Spawn`,
`FunctionDecl.is_async`. `docs/ASYNC_COROUTINE_ARCHITECTURE.md` exists. I did not
trace this to MIR and **will not claim it works or doesn't** — out of scope for
what I could verify statically.

### Modules / imports

Both `Use` and `Import` tokens exist; `grammar.ebnf` documents only `use`;
`.agent/memory/handoff.md` documents `import path::{A, B as C}`. `UseDecl`
supports path, alias, and item lists. Two keywords for one concept, documented
inconsistently across two files.

### String formatting

`FStringLiteral` with `FStringPart::{Literal, Expr}` is in the lexer and AST.
`note.md` GAP-05 says `{}`-style `println` format specifiers are *not* supported
and prescribes multi-argument printing as the workaround:

```agam
println("Sum = ", sum);   // note.md "Verified Working Syntax"
```

But `agam_sema/src/resolver.rs:812-815` declares:

```rust
("print",     vec![any],     unit_ty),
("println",   vec![any],     unit_ty),
("print_int", vec![int_ty],  unit_ty),
("print_str", vec![str_ty],  unit_ty),
```

One parameter. And `grep -n 'arity\|wrong number of arg' crates/middle/agam_sema/src/*.rs`
finds arity logic only in `exhaustive.rs` (pattern arity) — **there is no call
arity checking in sema at all.** So the officially-blessed workaround works
because argument count is unchecked, not because two-argument `println` is
defined. Calling `foo(1,2,3)` on a one-parameter user function is also, as far as
I can tell, not diagnosed. That's a significant missing diagnostic independent of
the formatting question.

Meanwhile f-strings exist and are used in `hello_base_dynamic.agam`. So Agam has
three printing idioms — `print_int`, variadic-by-accident `println`, and
f-strings — with the docs recommending the accidental one.

### Macros

`agam_macro` exists (702 LOC, in `experiments/`). No macro syntax in the token
set or AST. Treating as not-yet-a-language-feature; no audit.

---

## 1.2 Construct-by-construct: `@lang.base`

Everything in §1.1 applies, because it is the same parser. Base-specific
findings:

### The one-statement heuristic

`parser.rs:1195-1198`:

```rust
// Heuristic: stop after one statement in base mode if there was no indent
if !has_brace && !has_indent && !stmts.is_empty() {
    break;
}
```

A comment containing the word "heuristic" inside a block parser is a red flag.
This handles `if x: return 0` on one line. But combined with §1.0.1 (missing
directive → base mode) and with `Indent` emission depending on whitespace the
user can't see, the failure mode is *silent truncation of a block* rather than a
parse error. Silent wrong-code is categorically worse than a diagnostic.

### Comments participate in indentation decisions

`lexer.rs:118-121` skips indentation processing for lines beginning with `#` or
`//`. This is correct and matches Python. Worth noting as something done right.

### Base mode uses `#` for comments, advance uses `//`

Both tokenize in both modes (the lexer emits `LineComment` for either). So this
is convention, not rule. Another unenforced distinction.

### The base "cleanliness" claim is thin

`examples/01_basics/*_base.agam` vs `*_advance.agam`, same program:

```agam
# base
let mut result: i32 = 1
while e > 0:
    if e % 2 == 1:
        result = result * b

// advance
let mut result: i32 = 1;
while e > 0 {
    if e % 2 == 1 {
        result = result * b;
    }
}
```

Base saves braces and semicolons. It does not save type annotations, `let mut`,
or any other verbosity. The marketing framing ("clean, readable, Python-style
syntax without boilerplate", in the example header comment) oversells what is a
punctuation difference. **Python's actual ergonomic win over C-family syntax is
not indentation** — it's inference, duck typing, and comprehensions. Agam base has
none of those and keeps the annotations.

**Comparison:** the documented Python whitespace-significance debate is worth
reading accurately here. The sustained complaints in the Python community are not
about readability — they're about (a) tab/space mixing, resolved by PEP 8 and
then hard-enforced by Python 3 rejecting inconsistent tabs, and (b) copy-paste and
email/wiki transport corruption. Agam base inherits both risks and, unlike
Python 3, does **not** currently reject mixed tabs/spaces as far as I can see in
`skip_whitespace` — flagging as probable, not verified.

---

## 1.3 Expressiveness asymmetries between dialects — the real design bugs

These are things one dialect can express and the other cannot. Since both target
the same AST, every one of these is a bug, not a style difference.

### ASYM-1 (severe): base mode cannot declare a multi-line struct or enum

Already tracked as B-Grade #1 / GAP-04, but the ledger's root-cause attribution is
wrong and the fix location matters. `issues.md` points at
`crates/core/agam_lexer/src/layout.rs` — **that file does not exist**; layout is
in `lexer.rs`.

The actual mechanism, `parser.rs:534-580` (`parse_struct_decl`):

```rust
let has_brace = self.eat(TokenKind::LBrace);
let has_indent = if !has_brace { self.eat(TokenKind::Indent) } else { false };
self.skip_newlines();
while self.peek_kind() == TokenKind::Identifier || self.peek_kind() == TokenKind::Pub {
```

In base mode with `struct Point {` followed by a newline and an indented field,
the lexer has already queued an `Indent` token. `skip_newlines()` skips
`Newline`, not `Indent`. So `peek_kind()` is `Indent`, the field loop never
executes, zero fields are parsed, and `eat(RBrace)` then fails — producing
`expected expression, found Indent`.

`parse_block` solves exactly this at lines 1181-1191 by draining
`Indent`/`Dedent`/`Newline` inside brace bodies. `parse_struct_decl` and
`parse_enum_decl` never got that treatment. So the bug is a **missing three
lines in two functions**, not a lexer redesign — though the lexer-side
bracket-depth fix proposed in `issues.md` is the more durable one because it
fixes every present and future construct at once. Spec 001 (Part 7) specifies the
lexer fix and requires both.

Net effect today: base mode is not a general-purpose dialect. It cannot define a
data type across multiple lines. Advance mode can.

### ASYM-2 (severe): match arms with multiple statements work in neither, but for asymmetric reasons

Advance mode *should* allow `=> { a(); b() }` and cannot, because blocks aren't
expressions (§1.1). Base mode has no indent-based arm body syntax at all —
`parse_match_expr`'s colon branch parses each arm's body as a single expression
with no `Indent` handling. Fixing this requires two different changes, which is
how you get a permanent asymmetry if you only fix one.

### ASYM-3 (moderate): closures with block bodies are advance-only in principle

`ClosureExpr = ... , ( Expression | Block )`. A brace body `|x| { ... }` is
lexically available in base mode too (braces always tokenize), but an
indentation-delimited closure body has no syntax. So base-mode users writing
multi-statement closures must drop into braces — mixing dialects inside one file,
which nothing forbids and nothing formats consistently.

### ASYM-4 (moderate): trailing-comma and multi-line collection literals

`grammar.ebnf` explicitly permits `Newline` as a separator in `ArrayLiteral` and
`StructInit`, and commit `02339ae` is titled "support multiline arrays/tuples in
parser." But `Indent`/`Dedent` inside those constructs is handled by
`skip_struct_whitespace` in one path and not in others (§1.1's two-heuristic
problem). I could not fully establish which multi-line literal forms work in
base mode. **Flagging as unresolved** — it needs a test matrix, which Spec 001's
acceptance criteria require.

### ASYM-5 (advisory): nothing prevents dialect mixing within a file

Not an asymmetry but its enabling condition. Because no construct enforces a
dialect, a single function can open with `{`, contain an indented block, and
close with `}`. `agamc fmt` has no defined canonical form to normalize toward
(`agam_fmt` is 237 lines — the smallest tooling crate in the workspace, which
suggests it is a stub).

---

# Part 2 — Redesign proposal

Before the proposals: **the audience question must be answered first**, because
several of these trade against each other.

The repo does not answer it consistently. `MANIFESTO.md` and the website target
systems and AI workloads. The dual-dialect design targets beginners. The examples
are written in a C-subset. The stdlib surface (`dataframe_*`, `tensor_*`,
`dense_layer`, `conv2d` as *builtins* in `resolver.rs`) targets numerical
scripting.

**My recommendation, stated as an opinion and not a finding:** optimize for
"systems programmer already fluent in Rust/C++, with a low-ceremony on-ramp." That
means advance mode is the real language and base mode is a strict, formally-defined
*surface* over it — not a second language. The reason is capacity: every feature
must be designed, tested, documented, and fuzzed twice across dialects, and the
audit above shows the second copy is already systematically behind. One team
cannot maintain two co-equal syntaxes. Python/Ruby/Go each maintain one.

The proposals below assume that answer. If you choose the other answer
(beginner-first), R-2 and R-4 change materially, and I'd want to redo them.

---

### R-1 — Enforce dialect at the block level (fixes §1.0, ASYM-5)

**Before**

```agam
@lang.advance
fn main() -> i32:          # accepted today — colon block in advance mode
    let x = 1
    return x
```

**After**

```
error[E0110]: indentation block in `@lang.advance` source
 --> main.agam:2:17
  |
2 | fn main() -> i32:
  |                 ^ `@lang.advance` requires `{ ... }` blocks
  |
  = fix: fn main() -> i32 { ... }
  = law: AGAM-SYNTAX-001 §3
```

**Problem fixed:** the dialect is currently a suggestion. Tooling (`fmt`, LSP,
docs, syntax highlighting) cannot rely on it; users can't either.

**Given up:** files that currently mix forms stop compiling. Given the repo has
~36 `.agam` files total, migration cost is near zero *now* and rises monotonically.

**Beneficiaries:** tooling authors first, then everyone downstream of tooling.
Costs nothing to users who were already consistent.

---

### R-2 — Move the profile to the manifest; make the file directive an override (fixes §1.0.1)

**Before**

```agam
// Copyright 2026. Licensed MIT.
@lang.advance                 // silently ignored -> file lexed as base
fn main() -> i32 { ... }
```

**After**

```toml
# agam.toml
[project]
name = "calc"
version = "0.1.0"
agam = "0.1"
syntax = "advance"            # package-wide default
```

```agam
// Copyright 2026. Licensed MIT.
fn main() -> i32 { ... }      // no directive needed; inherits from manifest
```

Directive, when present, must be the **first non-whitespace, non-comment token**
and overrides for that file only. Absence of both manifest key and directive is
an error, not a silent base-mode default.

**Problem fixed:** the license-header trap; the invisible default; the inability
of `agamc fmt` to know a single file's dialect without heuristics.

**Given up:** single-file scripts (`agamc run foo.agam` with no manifest) now need
an explicit directive or a `--syntax` flag. That's real friction for the
throwaway-script use case. Mitigation: `agamc run` defaults to `advance` with a
warning, and `agamc new` always writes the key.

**Beneficiaries:** everyone building a real project. Mild cost to scratch scripts.

**Comparison:** this is Rust's `edition` decision verbatim. The Rust 2018 edition
guide is explicit that per-crate rather than per-file was chosen to avoid
exactly this class of ambiguity, and the edition mechanism is one of the few
Rust design decisions with essentially no community backlash.

---

### R-3 — Make brace-blocks and indent-blocks expressions (fixes §1.1 implicit return, ASYM-2)

**Before**

```agam
// advance: does not parse
let x = { let t = expensive(); t * 2 };

// advance: does not parse
match op {
    Add => { log("adding"); a + b },
    Sub => a - b,
}
```

**After** — add `BlockExpr` to prefix position in both dialects:

```agam
// advance
let x = { let t = expensive(); t * 2 };

match op {
    Add => { log("adding"); a + b },
    Sub => a - b,
}
```

```agam
# base
let x =
    let t = expensive()
    t * 2

match op:
    Add =>
        log("adding")
        a + b
    Sub => a - b
```

**Problem fixed:** the AST already has `Block.expr` and `ExprKind::Block`; the
parser can't produce them. Match arms gain statements. `if`/`match` become
genuinely expression-valued. Removes a whole class of "why do I need a temporary
`mut` variable" friction.

**Given up:** the struct-literal ambiguity gets worse, because `{` in prefix
position now has two meanings. This forces R-5 (restriction flags) as a hard
prerequisite — you cannot ship R-3 without it. Also: base-mode block expressions
introduce an indentation-sensitive expression grammar, which is genuinely harder
to get right (this is the part of **F#'s** offside rule that generated the most
`#light` era confusion, and F# ended up with a documented list of
"undentation" exceptions in the spec §15.1.10 rather than a clean rule).

**Beneficiaries:** systems programmers strongly; it's the single biggest
expressiveness gain available. Beginners neutral.

---

### R-4 — Delete `var` and `@lang.base.dynamic`; replace with explicit `Any` (fixes §1.0.2, §1.0.3)

**Before**

```agam
@lang.base.dynamic
fn main():
    name = "World"       # no declaration keyword
    var x = 42           # "dynamic" — actually just `any`
```

**After**

```agam
@lang.base
fn main() -> i32:
    let name = "World"
    let x: Any = 42      # explicit opt-out of static checking, greppable
    return 0
```

`var` and `@lang.base.dynamic` are removed. `Any` stays, spelled honestly, and
requires an annotation so it is never implicit.

**Problem fixed:** removes a whole advertised dialect that does nothing; removes
a keyword whose documented semantics (runtime type checking) are not implemented;
makes the escape hatch visible in review and greppable in CI.

**Given up:** the "Python-like scripting" pitch, which the implementation does not
currently back anyway. If you genuinely want dynamic typing later, it needs
runtime type tags in the value representation and dispatch in both backends —
that is a multi-month project, not a keyword.

**Beneficiaries:** everyone, via reduced surface. Costs the marketing story.

**Comparison:** **Kotlin's null-safety reception vs Java** is the instructive
case. Kotlin's `!!` operator is the deliberate, ugly, greppable escape hatch, and
the community consensus (visible in Kotlin style guides and in JetBrains' own
coding conventions) is that making the unsafe operation *visibly* unsafe is what
made the safe path stick. `var` in Agam is the opposite: an unsafe operation
wearing a safe-sounding name.

---

### R-5 — Replace struct-literal lookahead with an explicit restriction flag (fixes §1.1 two-heuristic defect; prerequisite for R-3)

**Before** — two incompatible heuristics, `parser.rs:60-80` and `parser.rs:1238-1251`.

**After** — one `Restrictions` bitflag threaded through the parser:

```rust
bitflags! { struct Restrictions: u8 { const NO_STRUCT_LITERAL = 1 << 0; } }
```

Set in: `if` / `while` condition, `match` scrutinee, `for` iterable. Cleared
inside any parenthesized or bracketed subexpression. Struct literals in those
positions require parens: `if (Config { debug: true }).enabled { ... }`.

**Problem fixed:** one rule instead of two; multi-line struct literals work
identically in both dialects; `if x { ... }` is unambiguous by construction
rather than by lookahead luck.

**Given up:** `if Config { debug: true }.enabled` becomes a parse error requiring
parens. This is exactly Rust's tradeoff and Rust's error message for it
(`E0658`-adjacent, "struct literals are not allowed here") is generally regarded
as an acceptable cost.

**Beneficiaries:** parser maintainers; anyone writing multi-line struct literals.

---

### R-6 — Add call arity and argument-type checking; define `println` honestly (fixes §1.1 formatting)

**Before**

```agam
println("Sum = ", sum);   // "works" — no arity check anywhere in sema
foo(1, 2, 3);             // foo takes 1 param; not diagnosed
```

**After**

```agam
println(f"Sum = {sum}");  // canonical: f-string
println("Sum = ", sum);   // still legal — println is *declared* variadic
foo(1, 2, 3);             // error[E0061]: expected 1 argument, found 3
```

Two separate changes that must land together: (a) real arity checking for all
calls, (b) an explicit variadic marker on the `print` family so the blessed
workaround stays legal *by design* rather than by absence of checking.

**Problem fixed:** a missing core diagnostic. Today Agam cannot tell you that you
called a function wrong.

**Given up:** some currently-compiling programs break. That is the point.

**Beneficiaries:** everyone. This is the highest ratio of user-visible value to
implementation cost in the whole list.

---

### R-7 — Either implement refinement types or reject them (fixes §1.0.4)

**Before**

```agam
fn sqrt(x: {v: f64 | v >= 0.0}) -> f64 { ... }   // predicate silently dropped
```

**After, option A (recommended now)**

```
error[E0120]: refinement types are not yet implemented
 --> lib.agam:1:14
  |
1 | fn sqrt(x: {v: f64 | v >= 0.0}) -> f64 {
  |            ^^^^^^^^^^^^^^^^^^^ parsed but not checked
  = note: tracked in STAGE-XX; use a runtime assert for now
```

**After, option B (later)** — route the predicate to `agam_smt` and discharge it.

**Problem fixed:** silent loss of a user-written constraint.

**Given up:** option A breaks any code using the syntax (probably none). Option B
is a large project.

**Beneficiaries:** anyone who would otherwise ship a program believing it was
checked.

---

### R-8 — Fix base-mode type declarations (fixes ASYM-1)

**Before**

```agam
@lang.base
struct Point {
    x: i32,
    y: i32,
}
# error: expected expression, found Indent
```

**After** — both forms legal in base, matching `parse_block`'s existing tolerance:

```agam
@lang.base
struct Point:
    x: i32
    y: i32
```

Fix at the lexer (suppress layout tokens at bracket depth > 0) *and* make
`parse_struct_decl` / `parse_enum_decl` drain layout tokens, because the two fixes
protect against different failure modes.

**Problem fixed:** base mode becomes able to define data types. Removes the
severest expressiveness asymmetry.

**Given up:** nothing. This is a pure bug fix.

**Beneficiaries:** every base-mode user. Currently the dialect is unusable for
non-trivial programs.

---

# Part 3 — Tooling / ecosystem design

Important correction to the prompt's framing: **the Cargo-equivalent layer
already exists** and is more complete than the syntax layer. `agam_pkg` (8,084
LOC) defines `WorkspaceManifest`, `ProjectManifest`, `WorkspaceDefinition`,
`DependencySpec`, `ToolchainRequirement`, `EnvironmentSpec`, `WorkspaceLockfile`,
`LockedPackage`, `LockedPackageSource`, `LockedEnvironment`, plus
`check_manifest_compatibility` and format-version constants. `agam.toml` and
`agam.lock` paths are established (`lib.rs:611`, `:863`). So this section is a
gap analysis, not a greenfield design.

## 3.1 Manifest — what exists and what's missing

Existing (from `agam_pkg/src/lib.rs:305-400`), reconstructed as TOML:

```toml
format_version = 1

[project]
name = "calc"
version = "0.1.0"
agam = "0.1"
entry = "src/main.agam"
keywords = ["cli"]

[workspace]
members = ["crates/*"]
default-members = ["crates/app"]

[dependencies]
http = { version = "1.2", features = ["tls"] }
local = { path = "../local" }
remote = { git = "https://…", rev = "abc123" }

[dev-dependencies]
[build-dependencies]

[toolchain]
agam = "0.1"
sdk = "0.1"
target = "x86_64-pc-windows-msvc"
runtime_abi = 1
preferred_backend = "llvm"

[environments.ci]
compiler = "0.1"
target = "x86_64-unknown-linux-gnu"
preferred_backend = "llvm"
profiles = ["release"]
```

That is a solid schema. Missing, in priority order:

1. **`syntax` key** — R-2. Without it the dialect can only be a per-file magic
   comment, which is the root of §1.0.1. This is the highest-value manifest
   addition and it is cheap.
2. **`[features]` table.** `DependencySpec` has a per-dependency `features: Vec<String>`
   and an `optional: bool`, which implies the consumer side of a feature system —
   but there is no producer side. A package cannot *declare* its own features.
   This is an incoherent half-system: you can request `features = ["tls"]` from a
   dependency that has no way to define `tls`.
3. **`[[bin]]` / `[lib]` targets.** Only a single `entry` string exists. Multi-binary
   packages, examples, benches, and integration tests all need target
   declarations. `agamc test` and `agamc bench` already exist as CLI verbs with
   nothing in the manifest to point them at.
4. **`[profile.*]`.** `-O` levels and `preferred_backend` are CLI flags and
   environment fields. Cargo's `[profile.release] opt-level = 3, lto = true`
   pattern is what makes reproducible optimization settings possible. Agam has
   `LtoMode { Thin, Full, ThinParallel, Distributed }` in the CLI with no manifest
   home.
5. **`edition` / spec version, separate from `agam` compiler version.** `project.agam`
   currently conflates "minimum compiler" with "language version."
6. **No `[registry]`/publishing metadata in `ProjectManifest`** — no `license`,
   `description`, `repository`, `authors`, `readme`. `agamc publish` exists as a
   verb; a registry will reject packages without these.

## 3.2 Semver policy — currently undefined, and this is urgent

`check_manifest_compatibility` compares the manifest *format* version exactly
(`version == WORKSPACE_MANIFEST_FORMAT_VERSION`, else `Unsupported`). That is a
format-version policy, not a dependency-version policy. I found no resolver
semantics, no range syntax definition, and no statement of what `version = "1.2"`
means.

This must be decided before the first package is published, because it is
unchangeable afterward. The two defensible options:

- **Cargo's caret-default.** `"1.2"` means `>=1.2.0, <2.0.0`; `0.x` treats the
  minor as breaking. Resolver picks the *maximum* compatible version, unifying
  compatible ranges into one copy and allowing multiple incompatible majors to
  coexist in one graph.
- **Go's minimal version selection.** `"1.2"` means "at least 1.2"; the resolver
  picks the *minimum* version satisfying all constraints. Builds are reproducible
  without a lockfile.

**Recommendation: Cargo's model.** Not because MVS is worse in principle — Russ
Cox's MVS writeup makes a genuinely strong argument, and Go's reproducibility
story is better. The reason is that Agam already ships a lockfile
(`WorkspaceLockfile` with `content_hash` per package), which is the thing MVS
exists to avoid needing. Having both is redundant; having the lockfile and
Cargo-style resolution is the well-trodden combination with two mature reference
implementations to copy diagnostics from.

**Uncertainty, stated plainly:** I have no visibility into whether a resolver is
implemented at all. `agamc lock` exists as a CLI verb. I did not read its
implementation. This recommendation is about policy, not about what to code next.

## 3.3 Lockfile

`WorkspaceLockfile` already has the right bones: `format_version`, workspace
identity, `Vec<LockedPackage>` with `name`/`version`/`source`/`content_hash`/
`dependencies`, plus per-environment resolved views. `LockedPackageSource` has
`kind`/`location`/`reference`.

Two gaps:

1. **`BTreeMap` is used for manifest dependency maps but `Vec` for locked
   packages.** `Vec<LockedPackage>` has no declared ordering, which means lockfile
   diffs will churn. Cargo sorts by `(name, version, source)`. Make the ordering
   a documented invariant with a test.
2. **No checksum algorithm is named.** `content_hash: String` — of what, computed
   how? An unspecified hash field is a supply-chain hole. Specify
   `sha256:<hex>` over a canonical archive, and verify on every fetch.

## 3.4 CLI surface — this is the clearest coherence problem in the tooling

`agam_driver/src/cli.rs` declares **33 top-level subcommands**: `Lock`, `Build`,
`Run`, `Package`, `Registry`, `Env`, `Publish`, `Doctor`, `Doc`, `Doctest`,
`Bindgen`, `Explain`, `Check`, `New`, `Dev`, `Cache`, `Exec`, `Repl`, `Fmt`,
`Lsp`, `Daemon`, `Add`, `Remove`, `Test`, `Bench`, `Lint`, `Audit`, `Sbom`,
`Vendor`, `Plugin`, `Mcp`, plus nested `Registry`/`Package`/`Mcp`/`Plugin`
subcommand trees.

For calibration: `cargo` has ~25 built-in commands accumulated over 11 years and
a package ecosystem of 150k+ crates. `go` has ~15. Agam has 33 before it has a
registry with a single published package.

Specific incoherences:

- **Three ways to run code:** `Run`, `Exec` (`--json` sandboxed), `Repl`. Plus
  `Dev` and `Daemon`, which both describe incremental loops.
- **Overlapping supply-chain verbs:** `Audit`, `Sbom`, `Vendor`, `Registry Audit`.
- **`Doctest` as a top-level verb** rather than `test --doc`.
- **`Package` and `Publish` and `Registry` and `Plugin`** with unclear boundaries.
- **`Mcp`** — an agent-integration server as a first-class compiler subcommand.
  Defensible given the project's agent-driven workflow, but it belongs behind
  `agamc tool mcp` or a plugin, not beside `build`.

Proposed minimal coherent verb set (13 core + namespaced extras):

```
agamc new <name>              # scaffold (absorbs current New)
agamc build                   # absorbs --backend, --target, -O
agamc run                     # build + execute
agamc check                   # type-check only
agamc test                    # --doc absorbs Doctest; --bench absorbs Bench
agamc fmt
agamc lint                    # absorbs Audit's lint half
agamc doc
agamc add / remove / update   # manifest editing
agamc publish                 # absorbs Package + Registry publish
agamc explain <CODE>          # keep — pairs with the Nyāya diagnostic design
agamc clean                   # absorbs Cache

agamc tool lsp | mcp | daemon | repl | bindgen | doctor | sbom | vendor
agamc registry <sub>          # login, search, yank, install
```

Everything currently top-level survives; twenty of them move behind `tool` or
`registry`. Nothing is deleted, so migration is aliases plus deprecation
warnings.

**Comparison:** the reference point is **npm**, whose command surface grew
without a namespace discipline and whose own docs now list ~60 commands with
heavy aliasing. The documented consequence — visible in every "npm vs yarn vs
pnpm" comparison from 2017 onward — is that competitors won users substantially
on CLI coherence alone. Agam is small enough to avoid this by choosing now.

---

# Part 4 — Honest evaluation of the shared-MIR / e-graph / dual-backend core

## Genuinely rare or differentiated

**1. E-graph equality saturation as a first-class MIR pass in a general-purpose
compiler.** `agam_mir/src/opt/egg_engine.rs` uses the `egg` crate and does
literal `inst.op = Op::Copy(...)` rewrites. E-graphs are well-established in
research (Willsey et al., *egg: Fast and Extensible Equality Saturation*, POPL
2021) and in *domain-specific* production compilers — Herbie for floating point,
Cranelift's own ISLE-adjacent work, TensorFlow/XLA-style rewrite systems. They are
**not** standard in general-purpose AOT pipelines: LLVM uses InstCombine (ordered
pattern rewriting), GCC uses match.pd, and both suffer the documented
phase-ordering problem that equality saturation exists to dissolve. Building the
main scalar optimizer around it is a real, defensible differentiator.

Caveat, and it matters: the audit at `docs/AUDIT-optimizer-pipeline-honesty-2026-09-05.md`
shows `egg_engine.rs:122-242` performing a fairly conventional set of algebraic
identities (`x * 1 → x`, `x + 0 → x`) using `egg` as a data structure, not a full
saturation-then-extract loop with a cost model. The *architecture* is
differentiated; I could not confirm the *implementation* yet exploits it. Don't
market this until extraction with a cost function is real.

**2. Diagnostics as a structured four-part proof (Fact/Reason/Fix/Law).** Rust's
`E####` codes plus `--explain` is the closest thing, and Elm's error messages are
the DX benchmark. Neither commits to a *fixed structural schema* for every
diagnostic. Agam's `agamc explain` + SARIF export + a mandated four-slot shape is
a stronger commitment than any shipping compiler I know of. Whether it survives
contact with 500 diagnostics is untested, but it is not a me-too design.

**3. The `.agent/` governance system itself.** Not a compiler feature, but worth
naming: ratchet files with per-crate baselines, a graded issue ledger with
mandatory update rules, skills with trigger conditions, and line-cited
falsifiable self-audits. I have not seen this degree of machine-legible process
discipline in a language project. It's a genuine asset and it's under-exploited —
the benchmark and parity failures in the previous audit are all cases where a
rule existed and wasn't enforced mechanically.

## Solid but ordinary — do not oversell

**1. SSA MIR between a typed HIR and multiple backends.** This is the standard
modern compiler shape. Rust: HIR → THIR → MIR (SSA-ish) → LLVM. Swift: AST → SIL
(SSA) → LLVM. Go: AST → SSA → obj. Zig: AST → ZIR → AIR → LLVM/self-hosted.
Julia, Kotlin, and Scala 3 all have an equivalent typed-IR layer. Agam's
`Source → Lexer → Parser → AST → HIR → MIR → Backend` is textbook. It is *correct*
and it is *well-executed* — `agam_mir/src/verifier.rs` at 1,184 lines with
dominance checking is more rigor than many hobby compilers manage. But it is not
novel and shouldn't be presented as such.

**2. Cranelift-for-JIT + LLVM-for-AOT.** Also standard. Cranelift was designed for
exactly this role and is used this way by Wasmtime, and Rust itself uses
`rustc_codegen_cranelift` as the fast debug backend with LLVM for release. The
dual-backend split is a well-trodden engineering choice, and the parity burden it
creates (five of eight open ledger issues are parity issues) is the known,
documented cost.

**3. NVPTX/GPU emission from the same MIR.** Also not rare: Julia's CUDA.jl,
Numba, Halide, and Rust's `nvptx64` target all do this. `gpu_emitter.rs` at 1,625
lines is credible work; it isn't a differentiator.

**4. Algebraic effects.** Genuinely interesting as a language feature, but the
comparison set is real and mature: Koka (Leijen), OCaml 5's effect handlers,
Eff, Unison, and Scala's capability work. Agam's version, judged by
`agam_sema/src/effects.rs`, is a handler-registry design rather than a
delimited-continuation implementation. That's a legitimate simplification, but
calling it "first-class algebraic effects" invites comparison to OCaml 5, which
Agam would currently lose.

## Where the architecture creates a structural liability

The dual-backend parity invariant is the project's stated core guarantee, and it
is the thing most at risk. Two backends means every lowering is written twice
(and three times with the C emitter, four with NVPTX). The evidence that this is
already failing: `Op::StoreIndex` implemented in LLVM and erroring in JIT;
`MirBinOp::Add` on strings correct in LLVM, pointer-arithmetic in JIT;
`Op::Syscall` with real inline asm in LLVM and `default_value(0)` — a **silent**
no-op — in JIT.

That last one is the architectural tell. A silent divergence is only possible
because nothing executes both backends and compares. Fix the differential harness
(previous audit, item 2) and the liability becomes manageable; leave it and the
invariant is decorative.

---

# Part 5 — Scorecard

Comparison set chosen for closest design intent: **Rust** (systems, same
backend strategy, same pattern-matching model), **Go** (systems, opposite
complexity philosophy), **Zig** (systems, self-hosted, comptime), **Python**
(the base dialect's stated model), **Kotlin** (dual-target, strong null-safety
DX benchmark).

Scores are 1–10 for Agam *as the pasted/read material shows it today*, not as
designed or aspired to.

| Criterion | Agam | Rust | Go | Zig | Python | Kotlin |
|---|---:|---:|---:|---:|---:|---:|
| Learnability curve | 4 | 3 | 9 | 5 | 9 | 7 |
| Expressiveness per line | 4 | 8 | 5 | 7 | 9 | 8 |
| Verbosity (higher = less verbose) | 5 | 6 | 5 | 6 | 9 | 8 |
| Syntactic consistency across constructs | 3 | 8 | 9 | 8 | 8 | 8 |
| Likely tooling-maturity ceiling | 7 | 9 | 9 | 7 | 6 | 9 |

### Learnability: 4

Two dialects to learn, only one of which can define a struct (ASYM-1). Three
declaration keywords where one is a no-op (§1.0.2). Three printing idioms where
the documented one works by accident (§1.1). The `docs/CHEATSHEET.md` a beginner
would start from teaches `Int`, `Float`, `String`, `.to_string()`, `Status.Idle`,
and `fn f() -> T => expr` — five constructs the compiler rejects. A beginner's
first hour is spent discovering the docs are wrong.

Scored above Rust (3) only because Agam has no borrow checker to fight; scored far
below Go (9) and Python (9) because those have one syntax that matches their docs.

### Expressiveness per line: 4

The load-bearing evidence is `examples/calculator_advance.agam` — 140 lines to
express a calculator, using integer opcodes (`1 = Addition`, `2 = Subtraction`)
and `-999999` error sentinels, in a language whose AST has enums, variant
patterns, exhaustiveness checking, `Result`, and `?`. The same program in Rust is
roughly 40 lines with a real `enum Op` and `Result<i32, CalcError>`.

The features exist in the AST. They are not reachable in practice — which is what
expressiveness measures.

### Verbosity: 5

Base mode drops braces and semicolons only. `examples/01_basics/02_quicksort_base.agam`
still writes `let mut checksum = 0` and `fn quicksort_partition(n: i32) -> i32:`.
Type annotations, `let mut`, and explicit `return` all remain. Compare Python (9),
which achieves brevity through inference and comprehensions, not punctuation.
Agam base is C with different delimiters.

### Syntactic consistency: 3 — the lowest score, and the most fixable

Concrete inconsistencies, each cited above:

- Two different struct-literal disambiguation heuristics (`parser.rs:60-80` vs
  `parser.rs:1238-1251`), one layout-aware and one not.
- `parse_block` drains layout tokens inside braces; `parse_struct_decl` does not.
  Same problem, two treatments.
- `match` supports both brace and colon-indent forms; `struct` and `enum`
  effectively support only braces.
- `grammar.ebnf` specifies `use`; the lexer has both `Use` and `Import`;
  `handoff.md` documents `import`.
- `grammar.ebnf` specifies `strict`, which has no implementation.
- Blocks are expressions in the AST and statements in the parser.

Go scores 9 here because `gofmt` plus a deliberately tiny grammar makes
inconsistency structurally difficult. Agam's `agam_fmt` is 237 lines, the
smallest tooling crate in the workspace, which is both a symptom and a cause.

### Tooling-maturity ceiling: 7

Scored on *ceiling*, not current state, and this is Agam's strongest column. A
real manifest and lockfile schema already exist (`agam_pkg`, 8,084 LOC), an LSP
crate exists, `agamc doc`/`fmt`/`lint`/`test`/`bench` are all wired, and there is
a native MCP server. The `.agent/` governance system is a genuine multiplier.

Capped at 7 rather than 9 by two things: the 33-verb CLI surface (§3.4) accreting
before there is a single published package, and the dual-backend parity burden
which taxes every future feature twice.

---

# Part 6 — Prioritized roadmap

Ranked by (severity of friction fixed) ÷ (implementation cost against the
existing architecture). Cost estimates assume one competent engineer familiar
with the codebase.

| # | Recommendation | Friction severity | Cost | Why this rank |
|---|---|---|---|---|
| 1 | **R-8** Base-mode struct/enum declarations | **Critical** — one dialect cannot define data types | **Low** — ~3 lines × 2 fns, plus lexer bracket-depth counter | Highest ratio in the list. Removes the severest expressiveness asymmetry for near-zero cost. Already diagnosed as B-Grade #1; the fix location in `issues.md` is wrong, which is probably why it's stalled. |
| 2 | **R-6** Call arity + argument type checking | **Critical** — the compiler cannot detect wrong-arity calls | **Low–Medium** — one pass in `agam_sema::resolver` | A compiler that doesn't check argument counts is not a type-checked language. Also retroactively legitimizes `note.md`'s blessed `println` workaround, which currently works only by omission. |
| 3 | **R-2** Manifest `syntax` key + strict directive placement | **High** — silent wrong-dialect lexing on any file with a header comment | **Low** — one manifest field, one lexer change, one error | Fixes a trap that hits the most standard file convention in existence. Prerequisite for R-1 and for a non-heuristic `agamc fmt`. |
| 4 | **R-5** Restriction flags replacing struct-literal lookahead | **High** — two conflicting heuristics; multi-line struct literals unreliable | **Medium** — bitflags threaded through `parse_expression` | Must land before R-3, and independently fixes a real correctness inconsistency. Copy Rust's design directly; it is well-documented and battle-tested. |
| 5 | **R-3** Blocks as expressions in both dialects | **High** — no implicit return, no multi-statement match arms, AST capability unreachable | **High** — new prefix production, base-mode indentation-sensitive expression grammar, MIR already supports it | Biggest expressiveness gain available, but genuinely the hardest, and strictly depends on #4. Do not start before #4 lands. |

**Deliberately below the line, with reasons:**

- **R-1** (enforce dialect at block level) — ranks 6th. Depends on R-2 landing
  first, and is mostly a diagnostics change once R-2 exists.
- **R-4** (delete `var` / `base.dynamic`) — ranks 7th. Correct, cheap, but it is a
  *removal*, and removals should follow the additions that make them
  uncontroversial. Also it's the one recommendation with a marketing cost, so it
  deserves a deliberate decision rather than being bundled.
- **R-7** (refinement types: reject or implement) — ranks 8th. Real correctness
  issue but almost certainly zero current users. Option A is a one-hour fix
  whenever you want it.
- **CLI consolidation (§3.4)** — ranks 9th. High long-term value, zero urgency,
  and it gets cheaper to defer than most things because it's pure aliasing. But
  do it before the registry opens, because published tooling docs calcify.
- **Manifest `[features]` / `[[bin]]` / `[profile]` (§3.1)** — ranks 10th+.
  Necessary before a registry exists; not before.

**Cross-cutting prerequisite that outranks all of the above:** the differential
test harness from the previous audit. Every one of R-1 through R-8 touches the
front end and therefore both backends. Landing them against a parity suite that
string-greps LLVM IR instead of executing it means you will introduce silent
divergences at exactly the rate you ship features. **Fix the harness first.**
It is not a syntax recommendation, which is why it isn't in the table, but it
gates everything in it.
