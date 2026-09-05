# WASM & Web Playground Parity Invariant

## Invariant
The Agam Web Playground (`agam-lang.github.io`) and documentation sandbox MUST execute genuine native Agam logic compiled to WebAssembly (`agam_wasm`). 

## Directives
1. **Zero Synthetic Polyfills**:
   - The web playground must NEVER simulate language features in JavaScript (e.g. JS array methods, regex placeholder formatting, fake closures) that do not compile natively in `agamc.exe`.
2. **Identical Error Diagnostics**:
   - Syntax, type, and semantic errors in the browser must match native compiler error codes and messages byte-for-byte.
3. **Parity Gate**:
   - Any feature demonstrated on the web portal must first be verified by `python scripts/prove.py` or the test suite.
