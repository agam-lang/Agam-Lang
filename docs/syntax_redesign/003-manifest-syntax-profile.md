# 003 — Manifest Syntax Profile & Strict Directive Placement

**Status:** proposed
**Depends on:** PRE-000
**Component:** `agam_lexer`, `agam_pkg`, `agam_driver`
**Ledger:** new — file as `S-Grade: #3` before starting (silent wrong-mode lexing)

---

## 1. Motivation

A source file's syntax dialect is currently decided by `Lexer::detect_mode`
(`lexer.rs:52-70`), which skips **whitespace only** and then tests
`starts_with("@lang....")`. If no directive is found at that position, the mode
silently defaults to `BaseStatic` — indentation-significant.

Therefore:

```agam
// Copyright 2026 Agam contributors. Licensed MIT OR Apache-2.0.
@lang.advance
fn main() -> i32 {
    let x = 1;
    return x;
}
```

...is lexed in **base** mode. The directive is never seen, because a comment
precedes it and `eat_while` does not skip comments. Every indented line now emits
`Indent`/`Dedent`. The failure surfaces as `expected expression, found Indent`
in whichever construct doesn't drain layout tokens — a diagnostic that names
neither the real cause nor the file's dialect.

A license header is the most standard file-authoring convention in existence.
This is a silent-wrong-behaviour bug on ordinary input, which is why it is
S-Grade rather than B-Grade.

Two independent fixes are required:

**Fix A — directive placement becomes a checked rule.** The directive must be
the first non-whitespace, non-comment token, and it must be diagnosed (not
ignored) if it appears elsewhere.

**Fix B — the default moves to the manifest.** A per-file magic comment cannot be
the only source of truth for a project-wide property. `agam.toml` gains a
`syntax` key; the file directive becomes a per-file override.

This mirrors Rust's `edition`, which lives in `Cargo.toml` specifically so a file
cannot be silently interpreted under the wrong rules.

---

## 2. Formal grammar diff

```ebnf
(* OLD *)
Program             = [ ProfileDirective ] , { TopLevelItem } ;
ProfileDirective    = "@lang.base" | "@lang.base.dynamic" | "@lang.advance" ;

(* NEW *)
Program             = [ ProfileDirective ] , { TopLevelItem } ;
ProfileDirective    = "@lang.base" | "@lang.base.dynamic" | "@lang.advance" ;

(*  PLACEMENT RULE (new, lexical):
    A ProfileDirective is recognised only if every preceding character in the
    file belongs to Whitespace, LineComment, BlockComment, or a UTF-8 BOM.
    At most one ProfileDirective may appear in a file.
    A token sequence matching ProfileDirective appearing after the first
    TopLevelItem is a lexical error E0140, not a directive and not an
    annotation.                                                              *)

(*  RESOLUTION ORDER for a file's SyntaxMode:
      1. ProfileDirective present in the file  -> that mode
      2. else agam.toml  [project] syntax = "..."  -> that mode
      3. else `agamc --syntax=<mode>` CLI flag     -> that mode
      4. else                                      -> error E0141
    There is no implicit default.                                            *)
```

### Manifest schema addition

```toml
[project]
name    = "calc"
version = "0.1.0"
agam    = "0.1"
syntax  = "advance"      # NEW. one of: "base" | "base.dynamic" | "advance"
```

Rust type change in `agam_pkg::ProjectManifest`:

```rust
pub struct ProjectManifest {
    pub name: String,
    pub version: String,
    pub agam: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub syntax: Option<SyntaxProfile>,        // NEW
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub entry: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub keywords: Vec<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum SyntaxProfile { Base, #[serde(rename = "base.dynamic")] BaseDynamic, Advance }
```

`SyntaxProfile` must map 1:1 onto `agam_lexer::SyntaxMode`. Add a test asserting
the mapping is total in both directions.

---

## 3. AST / HIR / MIR impact

**AST / HIR / MIR: none.** This spec changes only how a `SyntaxMode` is selected
before lexing begins. No node type changes.

**API change:** `agam_lexer::tokenize(src, source_id)` must gain an explicit mode
parameter, or a sibling `tokenize_with_mode(src, source_id, mode)`. Callers —
`agam_parser` tests, `agam_test::differential::compile_to_mir`, `agam_driver`,
`agam_lsp`, `agam_fmt` — must all be updated. **Do not leave a defaulting
overload in place**; the whole point is removing the implicit default.

### Dialect symmetry statement

This spec does not change what either dialect can express. It changes only which
dialect a given file is interpreted under. Symmetry is unaffected, and a test must
confirm that the same program text under an explicit directive and under a
manifest key produces identical ASTs (AC-5).

---

## 4. Worked examples

### 4.1 Valid — header comment then directive

```agam
// Copyright 2026 Agam contributors.
// Licensed MIT OR Apache-2.0.
@lang.advance
fn main() -> i32 { return 0; }
```

Expected: lexed in `Advance` mode. Zero `Indent`/`Dedent` tokens. Compiles.
**This is the case that silently misbehaves today.**

### 4.2 Valid — block comment and BOM before directive

```agam
/* Agam sample
   multi-line header */
@lang.base
fn main() -> i32:
    return 0
```

Expected: lexed in `BaseStatic`. Compiles.

### 4.3 Valid — no directive, manifest supplies the mode

`agam.toml`:
```toml
[project]
name = "calc"
version = "0.1.0"
agam = "0.1"
syntax = "advance"
```

`src/main.agam`:
```agam
fn main() -> i32 { return 0; }
```

Expected: compiles in advance mode via `agamc build`.

### 4.4 Valid — directive overrides manifest, with a warning

Manifest says `syntax = "advance"`; file says `@lang.base`.

Expected: compiles in **base** mode, plus:

```
warning[W0140]: file overrides the package syntax profile
 --> src/legacy.agam:1:1
  |
1 | @lang.base
  | ^^^^^^^^^^ this file uses `base`; package default is `advance`
  |
  = note: per-file overrides are supported but complicate tooling
```

### 4.5 Invalid — directive after a declaration

```agam
fn main() -> i32 { return 0; }
@lang.advance
```

Expected, exactly:

```
error[E0140]: `@lang.advance` must appear before any declaration
 --> input.agam:2:1
  |
1 | fn main() -> i32 { return 0; }
  | ------------------------------ first declaration appears here
2 | @lang.advance
  | ^^^^^^^^^^^^^ directive must precede all declarations
  |
  = law: AGAM-SYNTAX-003 §2
```

### 4.6 Invalid — two directives

```agam
@lang.base
@lang.advance
fn main() -> i32: return 0
```

Expected:

```
error[E0142]: duplicate syntax profile directive
 --> input.agam:2:1
  |
1 | @lang.base
  | ---------- first directive here
2 | @lang.advance
  | ^^^^^^^^^^^^^ a file may declare at most one syntax profile
  |
  = law: AGAM-SYNTAX-003 §2
```

### 4.7 Invalid — no directive, no manifest, no flag

`agamc run scratch.agam` where `scratch.agam` has no directive and no `agam.toml`
exists in any ancestor directory.

Expected:

```
error[E0141]: no syntax profile for `scratch.agam`
  |
  = note: the file has no `@lang.*` directive
  = note: no `agam.toml` with `[project] syntax` was found
  = fix: add `@lang.advance` as the first line, or pass `--syntax advance`
  = law: AGAM-SYNTAX-003 §2
```

**No implicit default. This error is the point of the spec.**

### 4.8 Invalid — unknown manifest value

```toml
[project]
syntax = "pythonic"
```

Expected:

```
error[E0143]: unknown syntax profile `pythonic` in agam.toml
  |
  = note: expected one of: `base`, `base.dynamic`, `advance`
  = law: AGAM-SYNTAX-003 §2
```

---

## 5. Acceptance criteria

- **AC-1** — 4.1 and 4.2 lex with the stated mode. Asserted by a lexer unit test
  reading `Lexer::mode()` directly, not by downstream success.
- **AC-2** — A test asserts that tokenizing 4.1 yields **zero** `Indent` and
  **zero** `Dedent` tokens. (Today this fails.)
- **AC-3** — 4.5, 4.6, 4.7, 4.8 produce exactly `E0140`, `E0142`, `E0141`, `E0143`.
- **AC-4** — 4.4 compiles and emits `W0140` exactly once.
- **AC-5 (symmetry)** — A test compiles the same source text twice, once with an
  explicit `@lang.advance` directive and once with the directive removed and the
  mode supplied by manifest, and asserts the two ASTs pretty-print identically.
- **AC-6** — `agam_lexer` exposes no function that infers a mode. `grep -n
  'SyntaxMode::BaseStatic' crates/core/agam_lexer/src/lexer.rs` must show no
  occurrence in a fallback/`else` branch. The implementing agent must paste this
  grep output into the commit message.
- **AC-7** — `agamc new` writes `syntax = "advance"` into the generated
  `agam.toml`. Verified by an integration test that scaffolds and greps.
- **AC-8** — `agamc --syntax <mode>` flag exists on `build`, `run`, `check`, and
  `fmt`.
- **AC-9** — Every existing `.agam` file in the repo still compiles. Files that
  relied on the implicit default must be given explicit directives in the same
  commit; list them in the commit body.
- **AC-10** — `cargo test`, `clippy -D warnings`, `fmt --check` pass via
  `python scripts/cargo_lens.py`.
- **AC-11** — `issues.md` gains `S-Grade: #3`, closed, with counters updated.

---

## 6. Required mutation test — MANDATORY

A shallow implementation can pass §4 by special-casing "skip `//` lines". This
test defeats that.

Add `crates/core/agam_lexer/tests/mutation_003_profile_detection.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-003.
//! Directive detection must be robust to arbitrary leading trivia, and the
//! selected mode must actually change the token stream.

const BODY_ADV: &str = "fn main() -> i32 {\n    let x = 1;\n    return x;\n}\n";
const BODY_BASE: &str = "fn main() -> i32:\n    let x = 1\n    return x\n";

/// Every leading-trivia shape that must NOT defeat detection.
fn trivia_variants() -> Vec<String> {
    vec![
        "".into(),
        "\n".into(),
        "\n\n\n".into(),
        "// one line\n".into(),
        "// a\n// b\n// c\n".into(),
        "/* block */\n".into(),
        "/* multi\n   line\n   block */\n".into(),
        "\u{FEFF}".into(),                       // BOM
        "\u{FEFF}// bom then comment\n".into(),
        "   \t \n// indented comment\n".into(),
        "/* a */ // b\n\n/* c */\n".into(),
    ]
}

#[test]
fn directive_survives_every_leading_trivia_shape() {
    for (i, trivia) in trivia_variants().iter().enumerate() {
        let src = format!("{trivia}@lang.advance\n{BODY_ADV}");
        let toks = tokenize_str(&src);
        assert_eq!(mode_of(&src), SyntaxMode::Advance, "trivia variant {i}");
        assert_eq!(
            toks.iter().filter(|t| matches!(t.kind, TokenKind::Indent | TokenKind::Dedent)).count(),
            0,
            "advance mode must emit no layout tokens; trivia variant {i}"
        );
    }
}

#[test]
fn mode_selection_actually_changes_the_token_stream() {
    // Not just a flag: base must produce layout tokens, advance must not.
    let base = tokenize_str(&format!("@lang.base\n{BODY_BASE}"));
    let adv  = tokenize_str(&format!("@lang.advance\n{BODY_ADV}"));
    let layout = |ts: &[Token]| ts.iter()
        .filter(|t| matches!(t.kind, TokenKind::Indent | TokenKind::Dedent)).count();
    assert!(layout(&base) > 0, "base mode must synthesize layout tokens");
    assert_eq!(layout(&adv), 0, "advance mode must not");
}

#[test]
fn misplaced_directive_is_rejected_at_every_position() {
    // Inserting the directive after each statement must yield E0140, never silence.
    let lines: Vec<&str> = BODY_ADV.lines().collect();
    for cut in 1..lines.len() {
        let mut v = lines.clone();
        v.insert(cut, "@lang.advance");
        let src = v.join("\n");
        let err = compile_str(&src).expect_err("cut={cut} must be rejected");
        assert_eq!(err.code(), "E0140", "cut={cut}");
    }
}

#[test]
fn absent_directive_and_absent_manifest_is_an_error_not_a_default() {
    let err = compile_str_without_manifest(BODY_ADV).expect_err("must not default");
    assert_eq!(err.code(), "E0141");
}

#[test]
fn every_manifest_value_round_trips_to_a_distinct_mode() {
    for (text, expected) in [
        ("base",         SyntaxMode::BaseStatic),
        ("base.dynamic", SyntaxMode::BaseDynamic),
        ("advance",      SyntaxMode::Advance),
    ] {
        assert_eq!(profile_from_manifest_str(text).unwrap().to_syntax_mode(), expected);
    }
    assert!(profile_from_manifest_str("pythonic").is_err());
    assert!(profile_from_manifest_str("Advance").is_err());   // case-sensitive
    assert!(profile_from_manifest_str("").is_err());
}
```

**Required property:** `directive_survives_every_leading_trivia_shape` must FAIL
on the pre-fix compiler for every comment-bearing variant. Record the failing
variant indices in the commit message.

---

## 7. Open questions — DO NOT decide these yourself

1. **Should a per-file directive be allowed to override the manifest at all?**
   §4.4 permits it with a warning. The stricter alternative — manifest is
   authoritative, directives are an error inside a package — is cleaner for
   tooling and worse for migration. **Escalate; do not choose.**

2. **What happens for a file outside any package that `agamc` is invoked on
   directly with a directive present?** §2 rule 1 says the directive wins, which
   I believe is right, but it means `agamc fmt some/random.agam` behaves
   differently depending on file contents. **Confirm this is intended.**

3. **Should `agamc run <file>` with no manifest default to `advance` with a
   warning instead of erroring?** §4.7 chooses hard error. The scratch-script
   ergonomics argument for a warning is real. **Escalate.**

4. **Does `agam_lsp` have a mode-selection path that also needs updating?**
   `agam_lsp/src/lib.rs` is 1,161 lines and I did not audit its lexer invocation.
   **Find and update it, or escalate if the design doesn't fit.**

5. **Workspace members with different `syntax` values.** `WorkspaceManifest`
   allows members; whether `syntax` is per-member or workspace-wide is
   unspecified here. **Escalate before implementing workspace resolution.**

6. **Should `@lang.*` remain lexed as ordinary tokens (`@`, `lang`, `.`, `base`)
   after `detect_mode` restores the cursor, as today?** That means the directive
   is also parsed as an annotation expression. Whether the parser currently
   discards it cleanly is unknown to me. **Verify; escalate if it is being parsed
   as a stray annotation.**
