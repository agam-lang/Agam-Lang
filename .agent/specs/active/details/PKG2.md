# Phase PKG2 — Immutable Reproducibility

**Status:** partial (Phase 17B lockfile exists, needs cryptographic guarantees)
**Tier:** 2 (Runtime — reproducibility is a safety/reliability concern)
**Pillar:** 19 — The Immutable Reproducibility Pillar

## Vision

If an Agam project compiles on your machine today, it is **mathematically guaranteed** to compile the exact same way on any machine, ten years from now, regardless of what the internet does. Every dependency — down to the exact compiler version — is cryptographically hashed and locked.

## Current State

Phase 17B already provides deterministic lockfile resolution. What's missing:

- ✅ `agam.lock` with deterministic resolution order
- ✅ Content drift detection
- ❌ Cryptographic content hashing of all dependencies
- ❌ Compiler version pinning and reproducible builds
- ❌ Build output hash verification
- ❌ Offline hermetic builds

## Deliverables

### Cryptographic Lockfile
- [ ] Every dependency entry in `agam.lock` includes `sha256` content hash
- [ ] Hash covers: source code + `agam.toml` + dependency tree (Merkle tree)
- [ ] `agamc lock --verify` — verify all installed deps match locked hashes
- [ ] Lock drift = compilation error, not warning
- [ ] Lockfile format is stable and machine-parseable (TOML)

### Compiler Version Pinning
- [ ] `agam.toml` includes `[toolchain] version = "0.2.0"` (exact compiler version)
- [ ] `agamc build` auto-downloads pinned compiler version if not installed
- [ ] `agamc lock` records compiler version hash in lockfile
- [ ] Different compiler version = different lockfile = explicit upgrade decision

### Reproducible Builds
- [ ] `agamc build --reproducible` — bit-for-bit identical output across machines
- [ ] Strip non-deterministic elements: timestamps, paths, random seeds
- [ ] `agamc build --verify-hash <expected>` — CI verifies build output matches
- [ ] Build provenance attestation: signed statement of "this binary was built from this exact source + deps + compiler"

### Hermetic Offline Builds
- [ ] `agamc vendor` — download all dependencies into local `vendor/` directory
- [ ] `agamc build --offline` — build using only vendored dependencies
- [ ] Air-gapped environments: copy `vendor/` to disconnected machine, build succeeds
- [ ] Registry snapshots: `agamc registry snapshot` saves point-in-time registry state

### Time-Travel Builds
- [ ] Given any commit + lockfile, reproduce the exact build from that point in time
- [ ] Registry preserves all historical versions (no yanking without replacement)
- [ ] `agamc build --lock-date 2025-01-01` — resolve as if it were that date

## Responsible Crates

- `agam_pkg` — lockfile hashing, vendoring, reproducibility
- `agam_driver` — `--reproducible`, `--offline`, `--verify-hash` flags

## Dependencies

- Phase 17B (lockfile) — extends existing lockfile infrastructure
- Phase P3 (package manager) — registry-side version preservation
- Phase SEC1 (security) — cryptographic signing shared infrastructure
