# Phase FFI1 — Universal Foreign Function Interface

**Status:** open
**Tier:** 3 (Platform and Ecosystem Breadth)
**Priority:** No language succeeds in isolation — seamless interop with existing ecosystems is mandatory

## Vision

Call C, C++, Python, Rust, Java, JavaScript, and web technologies (HTML/CSS via WASM) with **zero friction and zero performance penalty**. Agam should be the universal translator between programming ecosystems.

## Deliverables

### C Interop (Zero-Overhead)
- [ ] `extern "C"` function declarations with automatic ABI matching
- [ ] C header parsing: `@import_c("header.h")` generates Agam bindings automatically
- [ ] C struct layout compatibility (repr(C) equivalent)
- [ ] Automatic nullable pointer → `Option` wrapping at FFI boundary
- [ ] Zero-copy buffer sharing between Agam and C

### C++ Interop
- [ ] C++ class binding via extern declarations
- [ ] Template instantiation binding (concrete types only)
- [ ] RAII interop: C++ destructors called at Agam scope exit
- [ ] Exception translation: C++ exceptions → Agam `Result`
- [ ] `@import_cpp("header.hpp", namespace: "std")` binding generation

### Python Interop (Bidirectional)
- [ ] Call Python from Agam: `@import_python("numpy")` with automatic type marshaling
- [ ] Call Agam from Python: `@export_python` generates Python-importable modules
- [ ] NumPy array ↔ Agam tensor zero-copy sharing via buffer protocol
- [ ] GIL management: automatic acquire/release around Python calls
- [ ] Extends existing `agam_ffi` Python package (Phase 19)

### Rust Interop
- [ ] Direct Rust crate linking via `@import_rust("serde")`
- [ ] Shared ownership model interop (Agam ARC ↔ Rust Arc)
- [ ] `repr(Rust)` struct compatibility where applicable

### JavaScript / WASM Interop
- [ ] `@import_js("module")` for calling JS from Agam-WASM
- [ ] `@export_js` for exposing Agam functions to JavaScript
- [ ] DOM access via typed JS bindings (when targeting WASM)
- [ ] Web API access: fetch, canvas, WebGL, WebGPU
- [ ] Depends on Phase P1 (WASM backend)

### Java / JVM Interop
- [ ] JNI binding generation: `@import_java("java.util.HashMap")`
- [ ] JVM object lifecycle management from Agam
- [ ] Android JNI integration for mobile development

### Binding Generation Tool
- [ ] `agamc bindgen --lang c --header foo.h` — auto-generate FFI bindings
- [ ] `agamc bindgen --lang python --module numpy` — Python module bindings
- [ ] Type safety verification at binding generation time
- [ ] Performance annotations: `@inline_ffi` for zero-overhead hot-path calls

## Responsible Crates

- `agam_ffi` — core FFI runtime, type marshaling, binding framework
- `agam_codegen` — ABI-compatible code emission
- `agam_driver` — `agamc bindgen` command
- `agam_pkg` — foreign dependency management

## Dependencies

- Phase F2 (type system) — generics for typed FFI wrappers
- Phase R1 (memory model) — ownership interop with foreign languages
- Phase P1 (WASM) — JavaScript/web interop
