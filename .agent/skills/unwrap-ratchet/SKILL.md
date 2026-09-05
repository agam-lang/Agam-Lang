---
name: unwrap-ratchet
description: "Ratchet down unwrap, expect, and panic calls across compiler crates to achieve a zero-panic compiler."
---

# Unwrap Ratchet

**Purpose**: Enforces that production compiler code in `agam/crates/` never introduces new unhandled `.unwrap()`, `.expect()`, or `panic!()` calls. The count can only decrease over time.

## Usage

### Run Check
Verify that the current codebase does not exceed the baseline:
```powershell
python scripts/unwrap_ratchet.py
```

### Verbose Breakdown by Crate
```powershell
python scripts/unwrap_ratchet.py -v
```

### Update Baseline (After Refactoring Out Panics)
```powershell
python scripts/unwrap_ratchet.py --update
```

## Ratchet Invariant
- If count increases: **Build/Commit Fails**.
- If count decreases: **Baseline automatically lowers** to permanently lock in the improvement.
