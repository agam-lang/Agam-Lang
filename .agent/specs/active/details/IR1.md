# Phase IR1 — Multi-Level IR Architecture

**Status:** open
**Tier:** 4 (Performance and Optimization Depth)
**Pillar:** 1 (Performance)

## Vision

Design Agam's MIR for **dialect extensibility**, inspired by MLIR's progressive lowering and cuda-oxide's Pliron framework. Enable domain-specific optimization passes at the right abstraction level without monolithic IR rewrites.

## Motivation

In 2025–2026, MLIR has become the dominant framework for heterogeneous compiler construction. Languages like Mojo are built directly on it. Agam's current single-level MIR forces GPU, tensor, and control-flow optimizations to share one representation — limiting optimization opportunities.

**Key insight from cuda-oxide**: Pliron (pure-Rust MLIR analog) uses three dialects (dialect-mir, dialect-llvm, dialect-nvvm) to cleanly separate concerns. Agam can adopt a lighter version.

## Deliverables

### Dialect-Extensible MIR Framework
- [ ] Define `MirDialect` trait: operations, types, attributes per dialect
- [ ] Refactor current `agam_mir` ops into a `core` dialect (arithmetic, control flow, memory)
- [ ] Define `gpu` dialect (kernel launch, thread intrinsics, shared memory, barriers)
- [ ] Define `tensor` dialect (tensor ops, shape annotations, broadcasting rules)
- [ ] Progressive lowering pipeline: tensor-MIR → core-MIR → LLVM IR

### Domain-Specific Optimization Passes
- [ ] Tensor dialect: operator fusion, layout optimization, broadcast elimination
- [ ] GPU dialect: occupancy-aware tiling, shared memory promotion, warp scheduling
- [ ] Core dialect: existing constant fold, DCE, inline, loop unroll (already implemented)

### Backend Dispatch
- [ ] LLVM emitter reads from core dialect (no special-casing per domain)
- [ ] GPU emitter reads from gpu dialect + core dialect
- [ ] SPIR-V emitter reads from gpu dialect (shared with NVPTX path)

## Design References

- **MLIR (LLVM project)**: Multi-level IR with extensible dialects. Industry standard for heterogeneous compilation (TensorFlow, PyTorch, Mojo).
- **Pliron (cuda-oxide)**: Pure-Rust MLIR-inspired IR with dialect-mir, dialect-llvm, dialect-nvvm. Proves the concept works in Rust without C++ MLIR dependency.
- **Key principle**: "Optimize at the level where the information exists." Tensor fusion is easier in tensor-MIR than in LLVM IR.

## Responsible Crates

- `agam_mir` — dialect trait, core dialect, existing pass refactoring
- `agam_codegen` — backend dispatch from dialect-aware MIR
- New: `agam_mir::dialects::gpu` — GPU-specific ops and lowering
- New: `agam_mir::dialects::tensor` — tensor-specific ops and lowering

## Dependencies

- Phase F2 (type system) — const generics for tensor shapes
- Phase O5 (GPU) — GPU emitter already exists, needs refactoring into dialect
- Phase AI1 (autodiff) — AD transforms benefit hugely from tensor dialect
