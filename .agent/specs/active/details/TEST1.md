# Phase TEST1 — Advanced Testing Infrastructure

**Status:** open
**Tier:** 1 (Developer Experience Excellence)
**Pillar:** 7 (Tooling)

## Vision

Build a **world-class testing framework** that goes beyond unit tests to include property-based testing, fuzzing, snapshot testing, and doctests — all integrated into `agamc test` with zero external dependencies.

## Motivation

In 2026, modern testing has evolved far beyond simple assertion-based tests:
- **Property-based testing** (QuickCheck, Hypothesis): generates thousands of test inputs automatically, finding edge cases humans miss
- **Fuzzing** (AFL, libFuzzer): compiler-guided mutation testing for security-critical code
- **Doctests** (Rust's rustdoc): documentation examples are automatically tested, ensuring docs never go stale
- **Snapshot testing**: captures output and alerts on unexpected changes

Agam's `agamc test` (Phase DX5) covers the basic framework. This phase adds the advanced capabilities that differentiate a premium testing experience.

## Deliverables

### Property-Based Testing
- [ ] `@property` annotation: auto-generate random inputs for function parameters
- [ ] Built-in generators for primitive types, ranges, strings, collections
- [ ] Custom generator combinators: `Gen.one_of`, `Gen.map`, `Gen.filter`
- [ ] Shrinking: automatically minimize failing inputs to the smallest reproduction
- [ ] `agamc test --property` to run only property tests

### Integrated Fuzzing
- [ ] `@fuzz` annotation: mark functions for fuzz testing
- [ ] Coverage-guided mutation via LLVM's SanitizerCoverage (libFuzzer integration)
- [ ] Corpus management: persistent fuzzing corpus in `.agam_cache/fuzz/`
- [ ] `agamc fuzz <target>` CLI command
- [ ] Crash deduplication and triage

### Doctests
- [ ] Code blocks in doc comments (`///`) are automatically compiled and tested
- [ ] `agamc test --doc` runs all documentation examples
- [ ] Hidden setup lines (prefix with `#`) for boilerplate
- [ ] `should_panic`, `ignore`, `compile_fail` attributes on code blocks
- [ ] Documentation examples appear in `agamc doc` output with "Run" button (links to playground)

### Snapshot Testing
- [ ] `assert_snapshot!(expression)` — captures output, saves to `.snap` file
- [ ] `agamc test --update-snapshots` to accept new snapshots
- [ ] Inline snapshots: embed expected output directly in source
- [ ] Diff display on snapshot mismatch with colorized output

### Benchmark Testing
- [ ] `@bench` annotation: mark functions for benchmarking
- [ ] Statistical analysis: detect performance regressions with confidence intervals
- [ ] `agamc bench` with comparison to baseline
- [ ] CI integration: fail on performance regression beyond threshold

## Design References

- **Rust's testing ecosystem**: Doctests (rustdoc), property testing (proptest), fuzzing (cargo-fuzz), benchmarks (criterion).
- **Hypothesis (Python)**: Gold-standard property-based testing with shrinking.
- **Jest snapshots**: Snapshot testing UX with `--update` flow.
- **Agam advantage**: All testing modes built into `agamc test` — no external tools needed.

## Responsible Crates

- `agam_test` — test runner, property generators, snapshot engine
- `agam_driver` — `agamc test`, `agamc fuzz`, `agamc bench` CLI commands
- `agam_doc` — doctest extraction and compilation
- `agam_codegen` — fuzzing instrumentation (SanitizerCoverage)

## Dependencies

- Phase DX5 (Testing Framework Maturity) — basic `agamc test` infrastructure
- Phase DX3 (Documentation Generation) — doctest extraction
- Phase O1 (LLVM Optimization) — SanitizerCoverage for fuzzing
