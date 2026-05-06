# Phase AI1 — Autodiff and Tensor Types

**Status:** open
**Tier:** 5 (AI-Native Differentiation)

## Scope

Implement language-native automatic differentiation and first-class tensor types with compile-time shape checking. This is Agam's unique value proposition — AD as a compiler transform, not a library wrapper.

## Deliverables

### Tensor Types
- [ ] First-class `Tensor<T, Shape>` type with compile-time shape parameters
- [ ] Shape inference and checking at compile time (dimension mismatch = compile error)
- [ ] Broadcasting rules formalized in the type system
- [ ] Tensor literal syntax: `tensor[[1.0, 2.0], [3.0, 4.0]]`
- [ ] Integration with GPU backend for device tensors

### Automatic Differentiation
- [ ] Forward-mode AD as a compiler transform
- [ ] Reverse-mode AD (backpropagation) as a compiler transform
- [ ] `@differentiable` annotation on functions
- [ ] `grad(f)` to get the gradient function
- [ ] `jacobian(f)` and `hessian(f)` utilities
- [ ] Higher-order derivatives

### Integration
- [ ] AD through control flow (loops, conditionals)
- [ ] AD through function calls (cross-function differentiation)
- [ ] GPU-accelerated AD
- [ ] Custom gradient definitions for external/FFI functions

## Responsible Crates

- `agam_sema` — tensor type checking, shape inference
- `agam_hir` / `agam_mir` — AD transform implementation
- `agam_codegen` — efficient AD code generation
- `agam_std` — tensor operations and linear algebra

## Dependencies

- Phase F2 (type system) — const generics for tensor shapes
- Phase F3 (object model) — operator overloading for tensor math
- Phase O5 (GPU) — GPU-accelerated tensor operations
