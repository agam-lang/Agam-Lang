---
name: golden-test
description: "Differential and golden snapshot testing to prevent runtime or output regressions across compiler backends."
---

# Golden Test Guard

**Purpose**: Verifies that compiler output and generated binaries match expected outputs without silent regressions.

## Workflow

1. Canonical baseline outputs are verified through the proof harness:
   ```powershell
   python scripts/prove.py
   ```
2. For numeric and algorithmic suites, verify cross-language checksum parity:
   ```powershell
   python scripts/verify_all_comparison_codes.py
   ```
3. If modifying codegen or MIR optimization passes, assert that generated values match expected canonical stdout.
