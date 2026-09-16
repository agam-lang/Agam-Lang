# 010 — Manifest Completion: Features, Targets, Profiles, Semver

**Status:** proposed
**Depends on:** **003 (hard — adds `[project] syntax`)**
**Component:** `agam_pkg`, `agam_driver`
**Ledger:** new — file as `B-Grade: #7`

---

## 1. Motivation

`agam_pkg` already defines a credible Cargo-shaped manifest: `WorkspaceManifest`,
`ProjectManifest`, `WorkspaceDefinition`, `DependencySpec`, `ToolchainRequirement`,
`EnvironmentSpec`, and a lockfile (`WorkspaceLockfile`, `LockedPackage`,
`LockedPackageSource`, `LockedEnvironment`) with `agam.toml` / `agam.lock` paths
established at `lib.rs:611` and `:863`. This spec closes four concrete gaps in
it. It is **not** a redesign.

**Gap 1 — the feature system has a consumer side but no producer side.**
`DependencySpec` carries `features: Vec<String>` and `optional: bool`, so a
package can *request* `features = ["tls"]` from a dependency. But
`WorkspaceManifest` has no `[features]` table, so no package can *declare* `tls`.
A half-implemented feature system silently ignores every request.

**Gap 2 — there are no build targets.** `ProjectManifest` has a single
`entry: Option<String>`. `agamc test` and `agamc bench` exist as verbs with
nothing in the manifest telling them what to build. Multi-binary packages,
examples, and integration tests are unexpressible.

**Gap 3 — optimization settings have no manifest home.** `LtoMode { Thin, Full,
ThinParallel, Distributed }` and `-O` levels are CLI flags; `preferred_backend`
lives in `[toolchain]` and `[environments.*]`. There is no
`[profile.release]`, so a project cannot pin reproducible optimization settings.

**Gap 4 — no dependency version policy is defined.**
`check_manifest_compatibility` compares the *manifest format* version exactly;
that is not a dependency resolution policy. I found no range syntax definition
and no statement of what `version = "1.2"` means. **This must be decided before
the first package is published, because it cannot be changed afterward.**

---

## 2. Formal schema diff

### 2.1 `[features]` — new

```toml
[features]
default = ["std"]
std     = []
tls     = ["dep:openssl"]           # enables an optional dependency
full    = ["std", "tls"]            # feature implying other features

[dependencies]
openssl = { version = "0.10", optional = true }
```

```rust
// agam_pkg::WorkspaceManifest — NEW field
#[serde(default)]
pub features: BTreeMap<String, Vec<String>>,
```

Rules, normative:

- A feature value entry is either another feature name in the same package, or
  `dep:<name>` naming an `optional = true` dependency, or
  `<dep>/<feature>` enabling a feature of a dependency.
- `default` is activated unless `--no-default-features` is passed.
- Feature resolution is **additive and union-based**: if two dependents of a
  package request different feature sets, the union is built. Features may not
  be mutually exclusive.
- Requesting an undeclared feature is `E0190`.
- A feature cycle is `E0191`.

### 2.2 `[[bin]]` / `[lib]` / `[[example]]` / `[[test]]` / `[[bench]]` — new

```toml
[lib]
path = "src/lib.agam"

[[bin]]
name = "calc"
path = "src/bin/calc.agam"

[[example]]
name = "hello"
path = "examples/hello.agam"

[[test]]
name = "integration"
path = "tests/integration.agam"

[[bench]]
name = "fib"
path = "benches/fib.agam"
```

```rust
pub struct TargetSpec {
    pub name: String,
    pub path: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub required_features: Vec<String>,
}

// on WorkspaceManifest:
#[serde(default, skip_serializing_if = "Option::is_none")] pub lib: Option<TargetSpec>,
#[serde(default, rename = "bin")]     pub bins: Vec<TargetSpec>,
#[serde(default, rename = "example")] pub examples: Vec<TargetSpec>,
#[serde(default, rename = "test")]    pub tests: Vec<TargetSpec>,
#[serde(default, rename = "bench")]   pub benches: Vec<TargetSpec>,
```

Auto-discovery, when the table is absent: `src/main.agam` → a bin named after the
package; `src/lib.agam` → the lib; `src/bin/*.agam`, `examples/*.agam`,
`tests/*.agam`, `benches/*.agam` → the respective target kinds.

`ProjectManifest.entry` is **deprecated** in favour of `[[bin]]`, kept working
with a warning.

### 2.3 `[profile.*]` — new

```toml
[profile.dev]
opt-level = 0
backend   = "jit"
debug     = true

[profile.release]
opt-level = 3
backend   = "llvm"
lto       = "thin"          # "off" | "thin" | "full" | "thin-parallel" | "distributed"
debug     = false
```

```rust
pub struct ProfileSpec {
    #[serde(rename = "opt-level", default)] pub opt_level: Option<u8>,   // 0..=3
    #[serde(default)] pub backend: Option<RuntimeBackend>,
    #[serde(default)] pub lto: Option<LtoMode>,
    #[serde(default)] pub debug: Option<bool>,
}
// on WorkspaceManifest:
#[serde(default)] pub profile: BTreeMap<String, ProfileSpec>,
```

Precedence, normative, highest first: **CLI flag > `[profile.<name>]` >
`[environments.<env>]` > built-in default.** A test must assert all four levels.

### 2.4 Semver policy — normative statement

```
Agam adopts Cargo-compatible caret semantics.

  "1.2"    ==  "^1.2"  ==  >=1.2.0, <2.0.0
  "0.3"    ==  "^0.3"  ==  >=0.3.0, <0.4.0     (0.x: minor is breaking)
  "0.0.5"  ==  "^0.0.5" == >=0.0.5, <0.0.6     (0.0.x: patch is breaking)
  "=1.2.3"                 exactly 1.2.3
  ">=1.2, <1.5"            explicit range

Resolution: pick the MAXIMUM version satisfying all constraints.
Compatible ranges unify to one copy; incompatible majors may coexist.
Resolution is recorded in agam.lock and is authoritative on subsequent builds.
```

**Rationale for choosing Cargo's model over Go's MVS** (stated so a future reader
does not relitigate it blindly): MVS's principal benefit is reproducibility
without a lockfile. Agam already ships a lockfile with per-package
`content_hash`. Having both is redundant; lockfile + caret resolution is the
combination with two mature reference implementations whose diagnostics can be
copied.

### 2.5 Lockfile hardening

- `LockedPackage.content_hash` must be specified as `sha256:<64 hex chars>` over
  a canonical package archive. The canonicalisation must be documented in
  `docs/` (file ordering, timestamp normalisation, permission normalisation).
  Verified on every fetch; mismatch is `E0192`.
- `WorkspaceLockfile.packages: Vec<LockedPackage>` must be sorted by
  `(name, version, source.location)`. This is a documented invariant with a test,
  so lockfile diffs do not churn.

### 2.6 Publishing metadata — new required fields for `agamc publish`

```toml
[project]
license     = "MIT OR Apache-2.0"
description = "A calculator"
repository  = "https://github.com/…"
readme      = "README.md"
authors     = ["…"]
```

Optional in the schema; **required by `agamc publish`**, which errors `E0193`
listing every missing field at once.

---

## 3. AST / HIR / MIR impact

**None.** This spec touches `agam_pkg` and `agam_driver` only.

### Dialect symmetry statement

Not applicable — no language surface is affected. Stated explicitly so a reviewer
does not look for it.

**One cross-reference:** spec 003's `[project] syntax` key must already exist.
`TargetSpec` deliberately has **no** per-target `syntax` override; the profile is
package-wide. If per-target dialects are wanted, that is a separate decision —
see open question 5.

---

## 4. Worked examples

### 4.1 Valid — complete manifest

```toml
format_version = 1

[project]
name        = "calc"
version     = "0.2.0"
agam        = "0.1"
syntax      = "advance"
license     = "MIT OR Apache-2.0"
description = "A calculator"
repository  = "https://github.com/example/calc"

[features]
default = ["std"]
std     = []
tls     = ["dep:openssl"]

[dependencies]
openssl = { version = "0.10", optional = true }
mathlib = "1.2"

[[bin]]
name = "calc"
path = "src/bin/calc.agam"

[[bench]]
name = "fib"
path = "benches/fib.agam"
required_features = ["std"]

[profile.release]
opt-level = 3
backend   = "llvm"
lto       = "thin"
```

Expected: parses; `agamc build --release` resolves `mathlib` to the highest
`>=1.2.0, <2.0.0`; `openssl` is absent unless `--features tls`.

### 4.2 Valid — auto-discovery with no target tables

Directory `src/main.agam`, `examples/hello.agam`, `benches/fib.agam`; manifest
with no `[[bin]]`/`[[example]]`/`[[bench]]`.

Expected: one bin named `calc`, one example `hello`, one bench `fib`.

### 4.3 Valid — profile precedence

Manifest has `[profile.release] opt-level = 3`. Invocation:
`agamc build --release -O 1`.

Expected: `-O 1` wins. A test asserts the resolved opt-level is 1, and a second
asserts it is 3 without the flag.

### 4.4 Invalid — undeclared feature

```bash
$ agamc build --features quic
```

Expected:

```
error[E0190]: package `calc` has no feature `quic`
  --> agam.toml
   |
   = note: available features: default, std, tls
   = law: AGAM-SYNTAX-010 §2.1
```

### 4.5 Invalid — feature cycle

```toml
[features]
a = ["b"]
b = ["c"]
c = ["a"]
```

Expected:

```
error[E0191]: feature cycle detected
  --> agam.toml
   |
   = note: a -> b -> c -> a
   = law: AGAM-SYNTAX-010 §2.1
```

The note must print the **full cycle path**, not just the fact of a cycle.

### 4.6 Invalid — checksum mismatch

Expected:

```
error[E0192]: checksum mismatch for `mathlib v1.2.4`
   |
   = note: agam.lock records sha256:aaaa…
   = note: downloaded archive is sha256:bbbb…
   = help: this may indicate a compromised registry or a corrupted cache
   = help: run `agamc clean --registry` and retry; if it persists, do not proceed
   = law: AGAM-SYNTAX-010 §2.5
```

### 4.7 Invalid — publish with missing metadata

```bash
$ agamc publish
```

Expected: `E0193` listing **every** missing field in one error, not one error per
field.

---

## 5. Acceptance criteria

- **AC-1** — 4.1 round-trips: deserialize → serialize → deserialize produces an
  identical `WorkspaceManifest`.
- **AC-2** — 4.2's auto-discovery produces exactly the stated target set, and
  explicit tables fully override discovery for that target kind.
- **AC-3** — Profile precedence is asserted at all four levels (CLI, profile,
  environment, default) with a 4-case test.
- **AC-4** — 4.4, 4.5, 4.6, 4.7 produce exactly `E0190`, `E0191`, `E0192`,
  `E0193`. 4.5's message contains the full cycle path.
- **AC-5** — Feature resolution is union-based: a test with two dependents
  requesting disjoint feature sets asserts the union is built.
- **AC-6** — `dep:`, `<dep>/<feature>`, and plain feature-name entries each have a
  test.
- **AC-7** — Lockfile ordering invariant: a test shuffles `packages`, serializes,
  and asserts the output is sorted by `(name, version, source.location)`.
- **AC-8** — `content_hash` format is validated (`sha256:` + 64 hex). Malformed
  values are rejected at parse time.
- **AC-9** — Semver: a table-driven test covers every row of §2.4 — `"1.2"`,
  `"0.3"`, `"0.0.5"`, `"=1.2.3"`, `">=1.2, <1.5"` — asserting the resolved
  bounds.
- **AC-10** — `ProjectManifest.entry` still works and emits a deprecation warning.
- **AC-11** — `format_version` is bumped and `check_manifest_compatibility`
  accepts both old and new. **An old manifest must not become unreadable.**
- **AC-12** — `cargo test`, `clippy -D warnings`, `fmt --check` via
  `python scripts/cargo_lens.py`.
- **AC-13** — `issues.md` gains `B-Grade: #7`, closed. §2.4 is copied verbatim
  into `docs/` as the canonical versioning policy.

---

## 6. Required mutation test — MANDATORY

The shallow implementation is a feature resolver that handles the examples in §4
and nothing else. This test is generative.

Add `crates/tooling/agam_pkg/tests/mutation_010_manifest.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-010.
//! Feature resolution, semver, and profile precedence must be computed, not
//! pattern-matched against known inputs.

#[test]
fn feature_closure_is_computed_at_arbitrary_depth() {
    // f0 -> f1 -> ... -> fN. Enabling f0 must enable all N+1.
    for depth in 1..=10 {
        let mut features = String::from("[features]\n");
        for i in 0..depth { features.push_str(&format!("f{i} = [\"f{}\"]\n", i + 1)); }
        features.push_str(&format!("f{depth} = []\n"));
        let m = parse_manifest(&with_project(&features)).expect("depth={depth}");
        let enabled = resolve_features(&m, &["f0".into()]).expect("must resolve");
        assert_eq!(enabled.len(), depth + 1, "depth={depth}: full closure required");
        for i in 0..=depth {
            assert!(enabled.contains(&format!("f{i}")), "depth={depth}: f{i} missing");
        }
    }
}

#[test]
fn feature_cycles_are_detected_at_every_length() {
    for len in 2..=8 {
        let mut features = String::from("[features]\n");
        for i in 0..len { features.push_str(&format!("f{i} = [\"f{}\"]\n", (i + 1) % len)); }
        let m = parse_manifest(&with_project(&features)).unwrap();
        let err = resolve_features(&m, &["f0".into()]).expect_err("len={len} must cycle");
        assert_eq!(err.code(), "E0191", "len={len}");
        // The reported path must name every member of the cycle.
        for i in 0..len {
            assert!(err.message().contains(&format!("f{i}")),
                "len={len}: cycle path must include f{i}, got: {}", err.message());
        }
    }
}

#[test]
fn feature_resolution_is_union_not_last_writer() {
    // Two dependents, disjoint sets. A naive impl keeps only the last.
    let m = parse_manifest(&with_project(
        "[features]\na = []\nb = []\nc = []\n")).unwrap();
    let got = resolve_features(&m, &["a".into(), "c".into()]).unwrap();
    assert!(got.contains("a") && got.contains("c"), "union required, got {got:?}");
    assert!(!got.contains("b"), "unrequested features must not leak");
}

#[test]
fn caret_semantics_hold_across_the_version_space() {
    // Table-driven over the whole documented matrix, including 0.x edge cases.
    let cases: &[(&str, &str, bool)] = &[
        ("1.2",     "1.2.0",  true),  ("1.2", "1.9.9", true),  ("1.2", "2.0.0", false),
        ("1.2",     "1.1.9",  false),
        ("0.3",     "0.3.0",  true),  ("0.3", "0.3.9", true),  ("0.3", "0.4.0", false),
        ("0.0.5",   "0.0.5",  true),  ("0.0.5", "0.0.6", false),
        ("=1.2.3",  "1.2.3",  true),  ("=1.2.3", "1.2.4", false),
        (">=1.2, <1.5", "1.4.9", true), (">=1.2, <1.5", "1.5.0", false),
    ];
    for (req, candidate, expected) in cases {
        assert_eq!(satisfies(req, candidate), *expected,
            "req={req} candidate={candidate}");
    }
}

#[test]
fn resolver_picks_the_maximum_compatible_version() {
    // Defeats a first-match resolver.
    for n in 2..=8 {
        let available: Vec<String> = (0..n).map(|i| format!("1.{i}.0")).collect();
        let picked = resolve_one("1.0", &available).expect("n={n}");
        assert_eq!(picked, format!("1.{}.0", n - 1), "n={n}: must pick the maximum");
    }
}

#[test]
fn profile_precedence_holds_at_all_four_levels() {
    // CLI > profile > environment > default, asserted by removing one level at a time.
    let levels = [
        (Some(1u8), Some(2u8), Some(3u8), 1u8),  // cli wins
        (None,      Some(2),   Some(3),   2),    // profile wins
        (None,      None,      Some(3),   3),    // environment wins
        (None,      None,      None,      0),    // built-in default
    ];
    for (i, (cli, profile, env, expected)) in levels.iter().enumerate() {
        assert_eq!(resolve_opt_level(*cli, *profile, *env), *expected, "level case {i}");
    }
}

#[test]
fn lockfile_ordering_is_stable_under_shuffling() {
    for seed in 0..16u64 {
        let lf = shuffled_lockfile(seed);
        let a = toml::to_string(&lf).unwrap();
        let b = toml::to_string(&shuffled_lockfile(seed ^ 0xFFFF)).unwrap();
        assert_eq!(a, b, "seed={seed}: lockfile serialization must be order-independent");
    }
}
```

`shuffled_lockfile` must build the same logical package set in a different `Vec`
order for each seed.

---

## 7. Open questions — DO NOT decide these yourself

1. **Is Cargo-style caret resolution definitely the choice?** §2.4 argues for it
   and gives the reasoning, but this is a permanent, ecosystem-defining decision
   and the MVS case is genuinely strong. **This section must be explicitly
   approved by the maintainer before implementation, not merely assigned.**

2. **Is a resolver implemented at all today?** `agamc lock` exists as a CLI verb;
   I did not read its implementation. If there is no resolver, §2.4 is a design
   for work not yet started and the cost estimate in the index is wrong.
   **Determine before scheduling.**

3. **Feature unification across major versions.** When `a` and `b` are both in
   the graph at incompatible majors, are their feature sets independent? Cargo
   says yes. **Confirm.**

4. **Should features be able to be mutually exclusive?** §2.1 says no (additive
   only), matching Cargo's documented rule. Some ecosystems want exclusivity.
   **Escalate if wanted — it changes the resolution algorithm fundamentally.**

5. **Per-target `syntax` override.** §3 deliberately omits it. A package
   migrating from base to advance incrementally would want it. **Escalate.**

6. **Workspace-level `[features]` and `[profile]` inheritance.** Cargo has
   `workspace = true` inheritance for dependencies and profiles. This spec does
   not address it. **Out of scope here; flag as future work.**

7. **Archive canonicalisation for `content_hash`.** §2.5 requires it be
   documented but does not specify it. File ordering, mtime normalisation,
   permission bits, and symlink handling all need decisions. **This is a real
   sub-design; escalate rather than inventing one.**
