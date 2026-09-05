# Zero-Panic Invariant

## Invariant
The Agam compiler (`agamc`) MUST NEVER panic or crash on user-controlled input, regardless of how malformed, nonsensical, or deeply nested the source code is.

## Directives
1. **No Production Panics**:
   - Forbid `.unwrap()`, `.expect()`, `panic!()`, `unreachable!()`, and `todo!()` on code paths that parse, check, or lower user input.
   - Return `Result<T, AgamError>` or record diagnostics into `agam_errors::DiagnosticSink`.
2. **Internal Invariant Failures**:
   - If an internal compiler invariant is violated (an actual compiler bug), emit an `ICE` (Internal Compiler Error) with the AST span and compiler version, rather than an unformatted panic stack trace.
3. **Ratchet Enforcement**:
   - The unwrap count across `agam/crates/` must never increase. Use the `unwrap-ratchet` skill (`python scripts/unwrap_ratchet.py`) to verify.
