# The LLM Wiki (Second Brain)

This directory (`.agent/wiki/`) is the persistent knowledge base for all AI agents working on the Agam-Lang repository.

## Rules for Agents

1. **Synthesize, Don't Forget:** If you make a major architectural breakthrough, discover a subtle bug in how the AST is structured, or realize an approach *does not work*, do not let it get lost in the chat history. Write a concise `.md` file in this directory detailing your findings.
2. **Query Before Starting:** When starting a complex task, check this directory (using `list_dir` or `grep_search`) for any existing knowledge related to the component you are modifying.
3. **Structured Naming:** Name files clearly (e.g., `ast-memory-model.md`, `failed-type-inference-approaches.md`).
4. **No Code Dumps:** This is for conceptual synthesis and rules of thumb, not for storing massive blocks of code. Use progressive disclosure.
