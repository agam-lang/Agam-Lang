# Rule: Live Problem Ledger & Bug Tracking Invariant

> **Rule ID**: `bug-ledger`  
> **Authority**: Mandatory for all AI Agents (Gemini, Claude, Codex) across all sessions.

---

## Directive

Whenever an AI agent encounters, diagnoses, or observes ANY defect, crash, lowering divergence, panic, syntax failure, or compiler inconsistency during execution:

1. **Do NOT silently bypass or ignore it.**
2. **Open `issues.md` immediately.**
3. **Score the issue using the Priority Rubric**:
   - **S-Grade (100–120)**: Process crashes, `STATUS_STACK_OVERFLOW`, memory corruption, panics on user input.
   - **A-Grade (70–99)**: Cross-backend execution/emission divergence (JIT $\ne$ LLVM), missing lowering pass.
   - **B-Grade (40–69)**: Diagnostic quality, Pratt parser error recovery, layout lexer edge cases, doc drift.
   - **C-Grade (10–39)**: Minor ergonomic or non-blocking cosmetic defects.
4. **Append entry to the Master Index Table** with next available ID (`ISSUE-XXX`).
5. **Update the Summary Table** counters (Total Logged, Open, Resolution Rate).
6. **Add Detailed Section** containing:
   - Priority Score & Grade
   - Component / Crate path
   - Symptoms & exact error logs
   - Root Cause Analysis
   - Reproducible `.agam` snippet
   - Proposed fix strategy & target stage
7. **When resolving an issue**:
   - Change status to `🟢 FIXED`.
   - Update Summary Table counters.
   - Record the commit hash or PR reference.
