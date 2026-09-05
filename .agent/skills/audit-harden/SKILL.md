---
name: audit-harden
description: "Unified compiler hardening and cross-language parity audit. Automates zero-warning linter passes, numerical checksum parity, and integration test expansion across all 27 crates."
---

# audit-harden

**Purpose**: Single unified skill for workspace audits, zero-warning clippy cleanup, latent bug remediation, and cross-language numerical parity verification.

## Trigger Words
- `/harden`
- `/audit`
- `/parity-audit`
- `/verify-benchmarks`

---

## Workflow Protocol

### Step 1: Fast Syntax & Parity Sanity
Run the 2-second dual-backend proof harness:
```powershell
python scripts/prove.py
```
Assert 100% of canonical examples compile and run identically on both Cranelift JIT and LLVM AOT.

### Step 2: Zero-Warning Static Analysis
Run clippy with zero warnings denied:
```powershell
python scripts/cargo_lens.py clippy --all-targets -- -D warnings
```
Fix all redundant conversions, unhandled results, and style lints across all 27 crates.

### Step 3: Numerical & Cross-Language Checksum Parity
When testing benchmark algorithms:
```powershell
python scripts/verify_all_comparison_codes.py
```
Verify bitwise output match across Agam, C++, Rust, and Python.

### Step 4: Regression Lock & Full Test Run
```powershell
python scripts/cargo_lens.py test
```
Add failing edge cases as permanent integration tests in `crates/tooling/agam_test/src/`.
