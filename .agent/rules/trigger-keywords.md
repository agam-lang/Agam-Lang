# Trigger Keywords for Operational Streams & Workflows

When the user enters any of the following trigger keywords in conversation, all AI agents MUST immediately execute the corresponding workflow sequence:

## Workflow Trigger Shortcuts

| Trigger Keyword | Operational Action | Stream |
| :--- | :--- | :--- |
| **`"Continue Development"`** | Read `.agent/specs/active/current.md` and `next.md`, pick up the active/highest priority uncompleted feature, and resume coding across technical stages. | **Stream 1 (Active Stages 0–7)** |
| **`"Start Debug"`** | Execute full Stream 0 debugging & assurance in an autonomous continuous loop: scan codebase for edge-case bugs, run fuzzing loops, collect telemetry data, add new unit tests for uncovered branches, apply fixes, run `cargo check` & `cargo test`, update `execution.log`, git commit & `git push`. | **Stream 0 (Assurance & Debug)** |
| **`"Start Build [Stage]"`** | Begin active code development for the specified Stage following pipeline discipline (AST → HIR → MIR → Codegen). | **Stream 1 (Active Stages 0–7)** |
| **`"Fix Error"`** | Inspect un-truncated error logs and tracebacks, identify underlying root causes, apply code fix, and run Stream 0 post-feature verification. | **Stream 0 / 1** |
| **`"Run Tests"`** | Execute `cargo check` and `cargo test` across all 27 workspace crates to verify cross-backend equivalence (LLVM / C / Cranelift JIT). | **Stream 0** |
| **`"Horizon Review"`** | Execute Stream 2 frontier research synthesis: analyze mathematical algorithms, update master specs, and archive digest. | **Stream 2** |
| **`"Run Benchmark"`** | Trigger benchmark execution (`benchmark-guard` skill), profile compilation throughput, measure execution latency, and compare against reference baselines. | **Stream 0 / 1** |
| **`"Recommend Feature"`** | Analyze current compiler capability gaps, evaluate Stage 0–7 catalog, suggest strategic algorithms, and add spec entries to the catalog/roadmap (do not directly modify Rust source code without explicit host permission). | **Stream 2 (Frontier Horizon Sync)** |
| **`"Status Report"`** | Render current stage progress, active tier state, backend matrix status, and recent `execution.log` entries. | **System** |
| **`"Analyze"`** | Execute a full project-wide context initialization sequence: inspect `AGENTS.md`, `CLAUDE.md`, `MANIFESTO.md`, `design-principles.md`, read `.agent/specs/active/current.md`, `.agent/memory/execution.log`, and render a complete project synthesis. | **System / Context Sync** |
| **`"Push"`** | Verify codebase (`cargo check`), append entry to `.agent/memory/execution.log`, stage files (`git add .`), commit with structured message, and push to remote (`git push`). | **Stream 0 / System** |
| **`"Handoff"`** | Refresh `.agent/memory/handoff.md` with current branch, commit hash, active stage, and next instruction for incoming AI agents. | **System** |

---

## Log Update Requirement

Whenever **`"Start Debug"`**, **`"Continue Development"`**, **`"Push"`**, or any feature phase completes, the agent MUST append a timestamped entry to `.agent/memory/execution.log` in the following format:

```text
[YYYY-MM-DD HH:MM:SS TZ] [EVENT_CATEGORY] Description of completed task or action
```
