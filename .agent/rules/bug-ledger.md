# Rule: Live Problem Ledger & Bug Tracking Invariant

> **Rule ID**: `bug-ledger`  
> **Authority**: Mandatory for all AI Agents (Gemini, Claude, Codex) across all sessions.

---

## Directive

Whenever an AI agent encounters, diagnoses, or observes ANY defect, crash, lowering divergence, panic, syntax failure, or compiler inconsistency during execution:

1. **Do NOT silently bypass or ignore it.**
2. **Open `issues.md` immediately.**
3. **Classify the issue into its Priority Grade**:
   - **S-Grade**: Critical crashes, `STATUS_STACK_OVERFLOW`, memory safety corruption, panics on user input.
   - **A-Grade**: Backend divergence (Cranelift JIT $\ne$ LLVM AOT), missing lowering passes, unsupported primitive syntax.
   - **B-Grade**: Diagnostic clarity, missing Pratt error recovery tokens, layout lexer edge cases, doc syntax drift.
   - **C-Grade**: Minor ergonomic CLI formatting, warning noise, cosmetic doc typos.
4. **Assign the next sequential Problem Number within that Priority** (e.g. `S-Grade: #1`, `S-Grade: #2`, `A-Grade: #1`, etc.).
5. **Append entry to the Master Index Table** with `Index (Priority: Number)`, Component, Summary, and initial status `🔴 Still Exists`.
6. **Update the Summary Table counters** (increment `Total Found` and `Still Exists`).
7. **Add Detailed Section** containing:
   - Priority Grade & Problem Number
   - Component / Crate path
   - Symptoms & exact error logs
   - Root Cause Analysis
   - Reproducible `.agam` snippet
   - Proposed fix strategy & target stage
8. **When resolving an issue**:
   - Change status to `🟢 Yes (Fixed)`.
   - Decrement "Still Exists", increment "Fixed" in Summary Table.
   - Record the commit hash or PR reference.
