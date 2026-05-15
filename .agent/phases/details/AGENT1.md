# Phase AGENT1 — Compiler-as-Agent-Tool

**Status:** open
**Tier:** 1 (Developer Experience Excellence)
**Pillar:** 10 (AI Compiler)

## Vision

Make Agam the most **agent-friendly compiler in existence**. Elevate `agamc`'s machine-parseable diagnostics, MCP (Model Context Protocol) server support, and agent-facing API into first-class features that AI coding assistants can leverage for autonomous development.

## Motivation

In 2026, AI coding agents (Claude Code, Cursor, Copilot Agent Mode) are autonomously executing compile-test-fix cycles. Compilers that provide **structured, machine-parseable diagnostics** and clear error recovery are massively preferred by agents. Agam already has `agamc exec --json` (Phase 18) and LangChain/LlamaIndex wrappers (Phase 19) — but these should be unified into a coherent "compiler-as-agent-tool" story.

**Key industry insight**: The Model Context Protocol (MCP) by Anthropic has become the "USB-C port for AI" — standardizing how agents connect to tools. A compiler that exposes MCP endpoints is instantly usable by every major AI agent.

## Deliverables

### MCP Server for `agamc`
- [ ] `agamc mcp serve` — start MCP-compatible server exposing compiler tools
- [ ] Tool: `compile` — compile source, return structured diagnostics
- [ ] Tool: `check` — type-check without codegen, return errors/warnings
- [ ] Tool: `explain_error` — given an error code, return explanation + fix suggestions
- [ ] Tool: `complete` — given a cursor position, return completions (delegates to LSP)
- [ ] Tool: `run` — compile and execute, return stdout/stderr/exit code
- [ ] Tool: `format` — format source code, return formatted output
- [ ] Resource: `diagnostics` — real-time diagnostic stream for open files
- [ ] Resource: `workspace` — workspace structure, dependencies, build graph

### Structured Diagnostic API
- [ ] Every diagnostic has: error code, severity, span, message, fix suggestions, related information
- [ ] `--json` flag on all commands produces machine-parseable output (extend Phase 18)
- [ ] SARIF (Static Analysis Results Interchange Format) output support
- [ ] Diagnostic stability contract: error codes are stable across versions

### Agent Integration SDK
- [ ] Python package `agam-agent` (extends Phase 19) with MCP client
- [ ] TypeScript package `@agam/agent` for Node.js-based agents
- [ ] OpenAPI schema for `agamc` HTTP mode
- [ ] Example: "Autonomous Agam development agent" using Claude Code + MCP

### LSP ↔ Agent Bridge
- [ ] LSP server exposes semantic verification endpoints for AI grounding
- [ ] LSIF (Language Server Index Format) export for static code intelligence
- [ ] Agent can query: "does this symbol exist?", "what's the type of X?", "is this import valid?"

## Design References

- **MCP (Anthropic)**: Universal agent-tool protocol. Standard for AI-tool integration.
- **SARIF**: Microsoft's Static Analysis Results Interchange Format. Industry standard for machine-readable diagnostics.
- **LSIF**: Language Server Index Format. Enables IDE features in static environments (GitHub).
- **Agam advantage**: No other compiler is designed from the ground up for agent interaction. Most compilers bolt on agent support as an afterthought.

## Responsible Crates

- `agam_driver` — MCP server implementation, CLI JSON output
- `agam_lsp` — agent verification endpoints, LSIF export
- `agam_errors` — diagnostic stability contract, SARIF format
- External: `agam-agent` Python/TypeScript packages

## Dependencies

- Phase 18 (Agent-Facing Execution) — extends existing `agamc exec` contract
- Phase 19 (LangChain/LlamaIndex Wrappers) — extends existing Python integration
- Phase DX2 (LSP Production Quality) — LSP must be functional first
