# Algorithm & Theoretical Synthesis Rule

1. **Extract Mathematical Principles, Not Foreign Brand Names**:
   - Extract the underlying formal proofs, mathematical data structures, and algorithms (e.g., E-graph equality saturation, dominance analysis, lattice fixed-point inference).
   - Never copy external framework wrappers into Agam.

2. **Native First**:
   - Synthesize all algorithms natively into Agam's core crates (`agam_parser`, `agam_sema`, `agam_mir`, `agam_codegen`).
   - Agam is an independent, zero-cost systems language with native toolchains.
