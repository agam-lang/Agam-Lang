# Error Message Quality

## Standard
Every compiler error and warning in `agam_errors` MUST provide:
1. Precise source location (`file:line:col`) with primary code span highlighting.
2. Concrete explanation of what failed (avoid abstract generic phrases).
3. Actionable remediation hint or suggestion whenever possible.

## Examples
- ❌ Bad: `type error`
- ✅ Good: `mismatched types: expected 'i32', found 'String' in argument 2 of 'add()'`
- ❌ Bad: `syntax error: unexpected token`
- ✅ Good: `unexpected '{' in '@lang.base' mode; use '@lang.advance' for brace-delimited blocks or write layout on a single line`

## Verification
When adding new syntax or diagnostics in `agam_errors` or `agam_sema`, add regression tests validating the diagnostic text.
