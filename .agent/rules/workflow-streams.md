# Rule: Workflow Streams & Continuous Verification

All AI assistants working on Agam-Lang MUST adhere to the Operational Streams framework:

1. **Stream 1 (Construction):** Write clean, verified code following pipeline discipline (AST → HIR → MIR → Codegen).
2. **Stream 0 (Assurance & Push):** After completing ANY feature or fix, immediately:
   - Run `python scripts/cargo_lens.py check` (or `cargo check`)
   - Run unit/integration tests and proofs (`python scripts/prove.py`)
   - Verify zero unwrap regressions (`python scripts/unwrap_ratchet.py`)
   - Verify differential backend parity (`python scripts/diff_fuzz.py`)
   - Update `task.md` / `walkthrough.md`
   - Execute git commit with conventional format
3. **Stream 2 (Frontier Horizon):** Research frontier literature (e.g. polyhedral optimization, MLIR lowering, vectorization) and update specs.
