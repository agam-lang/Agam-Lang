# Phase AI1 — Autodiff and Tensor Types

**Status:** open
**Tier:** 5 (AI-Native Differentiation)

## Scope

Implement language-native automatic differentiation and first-class tensor types with compile-time shape checking. This is Agam's unique value proposition — AD as a compiler transform, not a library wrapper.

## AD Architecture: Enzyme-Style IR-Level Transforms

> **Critical design decision**: AD should operate at the **MIR/LLVM IR level**, not the AST level. MIT's Enzyme project demonstrates that post-optimization AD achieves **4.2–4.5× speedups** over pre-optimization AD. This is because the optimizer eliminates redundant computation before the AD pass duplicates it.
>
> Enzyme works across C, C++, Rust, Julia, Swift, Fortran via LLVM IR. Agam can achieve the same by implementing AD as an MIR-to-MIR transform, then letting LLVM optimize the result.

## Deliverables

### Tensor Types
- [ ] First-class `Tensor<T, Shape>` type with compile-time shape parameters
- [ ] Shape inference and checking at compile time (dimension mismatch = compile error)
- [ ] Broadcasting rules formalized in the type system
- [ ] Tensor literal syntax: `tensor[[1.0, 2.0], [3.0, 4.0]]`
- [ ] Integration with GPU backend for device tensors

### Automatic Differentiation (IR-Level)
- [ ] Forward-mode AD as an MIR-to-MIR compiler transform
- [ ] Reverse-mode AD (backpropagation) as an MIR-to-MIR compiler transform
- [ ] Activity analysis: skip AD for values that don't affect the output (Enzyme-style)
- [ ] Efficient adjoint caching: recompute vs. cache trade-off analysis
- [ ] `@differentiable` annotation on functions
- [ ] `grad(f)` to get the gradient function
- [ ] `jacobian(f)` and `hessian(f)` utilities
- [ ] Higher-order derivatives

### Integration
- [ ] AD through control flow (loops, conditionals)
- [ ] AD through function calls (cross-function differentiation)
- [ ] AD through parallel constructs (GPU kernels, structured concurrency)
- [ ] GPU-accelerated AD (kernel-level gradient generation)
- [ ] Custom gradient definitions for external/FFI functions (`@custom_grad`)

## Design References

- **Enzyme (MIT)**: LLVM-based AD plugin. Operates on optimized IR for maximum performance. Supports AD through OpenMP, MPI, and language-specific task models.
- **JAX (Google)**: Functional-style AD with `jit`, `grad`, `vmap` transforms. Python-level, not compiler-level.
- **Swift for TensorFlow (Google, discontinued)**: Attempted compiler-level AD via `@differentiable`. Failed partly due to Swift's complexity, but the language design ideas are sound.
- **Agam advantage**: Agam owns the entire compiler pipeline, so AD can be deeply integrated into MIR optimization passes — unlike Enzyme (which is an LLVM plugin) or JAX (which is Python-level).

## Responsible Crates

- `agam_sema` — tensor type checking, shape inference, `@differentiable` validation
- `agam_mir` — AD transform implementation (MIR-to-MIR), activity analysis
- `agam_codegen` — efficient AD code generation via LLVM
- `agam_std` — tensor operations and linear algebra

## Dependencies

- Phase F2 (type system) — const generics for tensor shapes
- Phase F3 (object model) — operator overloading for tensor math
- Phase O5 (GPU) — GPU-accelerated tensor operations
- Phase IR1 (Multi-Level IR) — tensor dialect for fusion and layout optimization
