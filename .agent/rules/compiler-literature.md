# Compiler Literature Mapping

> Architectural patterns and theoretical foundations referenced across compiler crates.

| Crate Group | Core Literature | Mandated Pattern / Theory |
| :--- | :--- | :--- |
| `agam_lexer`, `agam_parser` | *Crafting Interpreters* (Nystrom) | Pratt parsing for precedence, byte span error recovery |
| `agam_sema` | *Language Implementation Patterns* (Parr) | Scope graph symbol tables, bidirectional typing |
| `agam_hir`, `agam_mir` | *Engineering a Compiler* (Cooper & Torczon) | SSA Basic Block CFGs, dominance frontier minimal $\phi$-nodes |
| `agam_mir::opt` | *Modern Compiler Implementation in C* (Appel) | Explicit closure layout, decision trees for pattern matches |
| `agam_codegen` | *LLVM Code Generation* (Colombet) / *LLVM Best Practices* (Nacke) | Module/Builder patterns, GlobalISel lowering, ABI compliance |
| `agam_runtime` | *The C Programming Language* (K&R) | C-ABI compatibility, explicit alignment, standard calling conventions |
