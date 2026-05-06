# Phase AI3 — Ecosystem Integration

**Status:** open (extends Phase 19 remaining work)
**Tier:** 5 (AI-Native Differentiation)

## Scope

Ship and maintain the external integration story: Python interop, ONNX model export/import, and compatibility with established ML frameworks.

## Deliverables

- [ ] Exercise the Python package release path end to end (Phase 19 remaining)
- [ ] Keep adapter surface current against upstream LangChain/LlamaIndex drift
- [ ] ONNX model export from Agam-trained models
- [ ] ONNX model import for inference
- [ ] NumPy-compatible tensor interop via C FFI
- [ ] Hugging Face model format compatibility (stretch)

## Responsible Crates

- `agam_ffi` — FFI layer
- `integrations/python` — Python package
- `agam_std` — ONNX serialization

## Dependencies

- Phase AI1 — tensor types for model representation
- Phase 19 — existing Python/LangChain/LlamaIndex infrastructure
