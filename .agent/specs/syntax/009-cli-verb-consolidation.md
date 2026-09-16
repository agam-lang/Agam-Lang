# 009 — CLI Verb Consolidation

**Status:** proposed
**Depends on:** none (but should land **before** a public registry exists)
**Component:** `agam_driver` (`cli.rs`, `dispatch.rs`)
**Ledger:** new — file as `C-Grade: #1`

---

## 1. Motivation

`agam_driver/src/cli.rs` declares **33 top-level subcommands**: `Lock`, `Build`,
`Run`, `Package`, `Registry`, `Env`, `Publish`, `Doctor`, `Doc`, `Doctest`,
`Bindgen`, `Explain`, `Check`, `New`, `Dev`, `Cache`, `Exec`, `Repl`, `Fmt`,
`Lsp`, `Daemon`, `Add`, `Remove`, `Test`, `Bench`, `Lint`, `Audit`, `Sbom`,
`Vendor`, `Plugin`, `Mcp`, plus nested trees under `Registry`, `Package`,
`Plugin`, and `Mcp`.

Calibration: `cargo` has ~25 built-in commands after 11 years and 150k+ published
crates. `go` has ~15. Agam has 33 before its registry has a single package.

Specific incoherences:

- **Three ways to execute code:** `Run`, `Exec` (`--json`, sandboxed), `Repl` —
  plus `Dev` and `Daemon`, which both describe incremental compile loops.
- **Four overlapping supply-chain verbs:** `Audit`, `Sbom`, `Vendor`,
  `Registry Audit`.
- **`Doctest` as a peer of `Build`** rather than `test --doc`.
- **`Package` vs `Publish` vs `Registry`** with undocumented boundaries.
- **`Mcp`** — an agent-integration server sitting beside `build`.

The reference case is **npm**, whose command surface grew without namespace
discipline to ~60 commands with heavy aliasing. The documented consequence,
visible in every npm/yarn/pnpm comparison from 2017 onward, is that competitors
won adoption substantially on CLI coherence. Agam is small enough to avoid this
by choosing now, and published CLI documentation calcifies the moment a registry
opens.

**This is a pure renaming/namespacing change. No command is deleted and no
behaviour changes.**

---

## 2. Formal "grammar" diff

The CLI surface, in the same notation:

```ebnf
(* OLD — 33 peers *)
Command = "lock" | "build" | "run" | "package" | "registry" | "env" | "publish"
        | "doctor" | "doc" | "doctest" | "bindgen" | "explain" | "check" | "new"
        | "dev" | "cache" | "exec" | "repl" | "fmt" | "lsp" | "daemon" | "add"
        | "remove" | "test" | "bench" | "lint" | "audit" | "sbom" | "vendor"
        | "plugin" | "mcp" ;

(* NEW — 13 core verbs + 2 namespaces *)
Command     = CoreVerb | "tool" , ToolVerb | "registry" , RegistryVerb ;

CoreVerb    = "new"          (* was: new *)
            | "build"        (* was: build; absorbs --backend/--target/-O *)
            | "run"          (* was: run *)
            | "check"        (* was: check *)
            | "test"         (* was: test; --doc absorbs doctest; --bench absorbs bench *)
            | "fmt"
            | "lint"         (* absorbs the lint half of `audit` *)
            | "doc"
            | "add" | "remove" | "update"
            | "publish"      (* absorbs `package` + `registry publish` *)
            | "explain"      (* kept: pairs with the Nyaya diagnostic design *)
            | "clean" ;      (* was: cache *)

ToolVerb    = "lsp" | "mcp" | "daemon" | "dev" | "repl" | "exec"
            | "bindgen" | "doctor" | "sbom" | "vendor" | "env" | "lock" | "plugin" ;

RegistryVerb= "login" | "search" | "install" | "yank" | "audit" | "inspect" ;
```

### Mapping table — every old command has a new home

| Old | New | Notes |
|---|---|---|
| `lock` | `agamc tool lock` | also implied by `build` |
| `build` `run` `check` `fmt` `doc` `new` `add` `remove` `explain` | unchanged | — |
| `test` | `agamc test` | unchanged |
| `doctest` | `agamc test --doc` | — |
| `bench` | `agamc test --bench` | — |
| `lint` | `agamc lint` | unchanged |
| `audit` | split: `agamc lint` (style) / `agamc registry audit` (advisories) | **see open question 2** |
| `cache` | `agamc clean` | subcommands preserved as flags |
| `package` | `agamc publish --no-upload` | — |
| `publish` | `agamc publish` | — |
| `registry <sub>` | `agamc registry <sub>` | unchanged |
| `env` `sbom` `vendor` `bindgen` `doctor` `dev` `daemon` `repl` `exec` `lsp` `mcp` `plugin` | `agamc tool <same>` | — |

**Every old invocation remains functional as a hidden alias** emitting a
deprecation warning, for at least one release.

---

## 3. AST / HIR / MIR impact

**None.** This spec touches `agam_driver` only. No compiler stage changes.

### Dialect symmetry statement

Not applicable — no language surface is affected. Stated explicitly so a reviewer
does not look for it.

---

## 4. Worked examples

### 4.1 Valid — new form

```bash
$ agamc build --backend llvm -O 3
$ agamc test --doc
$ agamc test --bench
$ agamc tool lsp
$ agamc registry search http
$ agamc clean --all
```

Expected: all succeed with behaviour identical to their old equivalents.

### 4.2 Valid — old form still works, with a warning

```bash
$ agamc doctest
warning: `agamc doctest` is deprecated; use `agamc test --doc`
         this alias will be removed in a future release
... (identical output to `agamc test --doc`)
```

Expected: exit code and stdout byte-identical to `agamc test --doc`; the warning
goes to **stderr**, so piped stdout is unchanged.

### 4.3 Valid — help output shows only the new surface

```bash
$ agamc --help
```

Expected: 13 core verbs plus `tool` and `registry`. **Deprecated aliases must not
appear in help.**

### 4.4 Invalid — unknown verb suggests the nearest new one

```bash
$ agamc benchmarks
```

Expected:

```
error: unrecognized subcommand `benchmarks`
  |
  = help: a similar subcommand exists: `agamc test --bench`
  = help: run `agamc --help` for the full list
```

### 4.5 Invalid — removed namespace collision

```bash
$ agamc mcp serve
```

Expected: runs (deprecated alias) with:

```
warning: `agamc mcp` is deprecated; use `agamc tool mcp`
```

---

## 5. Acceptance criteria

- **AC-1** — Every row of §2's mapping table has a test asserting the new form
  produces byte-identical stdout and exit code to the old form.
- **AC-2** — Every old form emits exactly one deprecation warning, on **stderr**.
  A test asserts stdout is unchanged when the warning fires.
- **AC-3** — `agamc --help` lists exactly 13 core verbs plus `tool` and
  `registry`, and no deprecated alias. Asserted by snapshot test.
- **AC-4** — 4.4's did-you-mean suggestion fires for at least: `benchmarks`,
  `doctests`, `packages`, `caches`.
- **AC-5** — `agamc tool --help` and `agamc registry --help` list their full
  subcommand sets.
- **AC-6** — No behavioural change: a test harness runs the full existing driver
  test suite (`main_tests.rs`, 3,905 lines) against the new surface unmodified via
  aliases, and it passes.
- **AC-7** — `docs/CHEATSHEET.md` §7 is updated to the new surface.
- **AC-8** — `cargo test`, `clippy -D warnings`, `fmt --check` via
  `python scripts/cargo_lens.py`.
- **AC-9** — `issues.md` gains `C-Grade: #1`, closed.

---

## 6. Required mutation test — MANDATORY

The shallow implementation is a hand-written `match` of old string → new string
that drifts out of sync with the real command set. This test makes the mapping
self-checking.

Add `crates/tooling/agam_driver/tests/mutation_009_cli_surface.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-009.
//! The alias table must be TOTAL over the old surface and CONSISTENT with the
//! new one. Adding a command without mapping it must fail this test.

/// The complete pre-change top-level surface. Frozen; do not edit.
const LEGACY_SURFACE: &[&str] = &[
    "lock", "build", "run", "package", "registry", "env", "publish", "doctor",
    "doc", "doctest", "bindgen", "explain", "check", "new", "dev", "cache",
    "exec", "repl", "fmt", "lsp", "daemon", "add", "remove", "test", "bench",
    "lint", "audit", "sbom", "vendor", "plugin", "mcp",
];

#[test]
fn every_legacy_verb_still_resolves() {
    // Totality: no command may be silently dropped by the rename.
    for verb in LEGACY_SURFACE {
        let parsed = try_parse_cli(&["agamc", verb, "--help"]);
        assert!(parsed.is_ok(), "legacy verb `{verb}` no longer resolves");
    }
}

#[test]
fn every_legacy_verb_maps_to_a_resolvable_new_form() {
    // Consistency: the alias target must itself exist.
    for verb in LEGACY_SURFACE {
        let target = alias_target(verb)
            .unwrap_or_else(|| panic!("no alias mapping declared for `{verb}`"));
        let argv: Vec<&str> = std::iter::once("agamc")
            .chain(target.split_whitespace()).chain(["--help"]).collect();
        assert!(try_parse_cli(&argv).is_ok(),
            "`{verb}` maps to `{target}`, which does not resolve");
    }
}

#[test]
fn alias_table_is_exhaustive_over_the_current_surface() {
    // Defeats drift: any NEW top-level command added later must be either a
    // declared core verb or a declared namespace, never an unclassified peer.
    let declared: std::collections::HashSet<&str> =
        CORE_VERBS.iter().chain(["tool", "registry"].iter()).copied().collect();
    for cmd in enumerate_top_level_commands() {
        assert!(declared.contains(cmd.as_str()) || is_deprecated_alias(&cmd),
            "top-level command `{cmd}` is neither a core verb, a namespace, \
             nor a declared alias — classify it or move it under `tool`");
    }
}

#[test]
fn deprecation_warnings_go_to_stderr_only() {
    for verb in ["doctest", "bench", "cache", "mcp", "sbom"] {
        let out = run_cli(&["agamc", verb, "--help"]);
        assert!(out.stderr.contains("deprecated"), "`{verb}` must warn on stderr");
        assert!(!out.stdout.contains("deprecated"), "`{verb}` must not pollute stdout");
    }
}

#[test]
fn old_and_new_forms_are_observationally_identical() {
    // Byte-for-byte on stdout, and identical exit codes.
    for (old, new) in alias_pairs() {
        let a = run_cli(&["agamc", old, "--help"]);
        let b = run_cli(&(["agamc"].into_iter()
            .chain(new.split_whitespace()).chain(["--help"]).collect::<Vec<_>>()));
        assert_eq!(a.stdout, b.stdout, "stdout differs: `{old}` vs `{new}`");
        assert_eq!(a.code, b.code, "exit code differs: `{old}` vs `{new}`");
    }
}
```

`alias_target`, `alias_pairs`, `enumerate_top_level_commands`, and `CORE_VERBS`
must be real functions over the clap command tree — **not hand-maintained
duplicate lists**, or the test proves nothing. `enumerate_top_level_commands`
should walk `clap::Command::get_subcommands()`.

---

## 7. Open questions — DO NOT decide these yourself

1. **Is `explain` a core verb or a `tool` verb?** I kept it core because the
   four-part Nyāya diagnostic design makes `agamc explain E0061` a routine part
   of the edit-compile loop, not an occasional utility. That reasoning could go
   either way. **Escalate.**

2. **How does `audit` split?** §2 splits it into `lint` (style/quality) and
   `registry audit` (dependency advisories). I have not read `cli.rs`'s `Audit`
   definition closely enough to know whether it does both. **Read it and escalate
   if the split is not clean** — do not force it.

3. **`dev` vs `daemon`.** Both are under `tool` in §2, but they may be the same
   thing under two names, in which case one should be an alias of the other.
   **Determine and escalate.**

4. **Does `exec --json` have external consumers?** It looks like an
   agent/automation entry point. If `.agent/` tooling or CI scripts invoke
   `agamc exec` directly, moving it under `tool` breaks them. **Grep `scripts/`
   and `.github/workflows/` before moving it.**

5. **Deprecation window.** §2 says "at least one release." With no public users
   yet, immediate removal may be cleaner. **Confirm the policy.**

6. **Should `update` exist as a core verb?** §2 adds it (it is not in the current
   surface; version updating appears to live under `registry`). Adding a *new*
   verb in a consolidation spec is arguably out of scope. **Escalate; it is
   acceptable to drop it from this spec.**
