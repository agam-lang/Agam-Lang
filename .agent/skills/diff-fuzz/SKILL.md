---
name: diff-fuzz
description: "Differential fuzzing and backend execution parity testing between Cranelift JIT and LLVM AOT."
---

# Differential Fuzz Guard

**Purpose**: Verifies bitwise execution and output equivalence between Cranelift JIT (`agamc run`) and LLVM AOT (`agamc build --backend llvm`).

## Usage

### Run Differential Parity Check
Runs across all verified examples to ensure output matches byte-for-byte:
```powershell
python scripts/diff_fuzz.py
```

### Test a Specific File
```powershell
python scripts/diff_fuzz.py path/to/snippet.agam
```

## Failure Modes Detected
- **EXIT_CODE_DIVERGENCE**: One backend returned an error code or crashed while the other succeeded.
- **STDOUT_DIVERGENCE**: Both compiled, but emitted different string or numerical outputs (e.g. integer addition on string pointers vs string concatenation).
