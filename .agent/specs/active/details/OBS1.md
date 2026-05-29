# Phase OBS1 — Native Observability and Telemetry

**Status:** open
**Tier:** 2 (Runtime and Concurrency)
**Pillar:** 7 (Tooling)

## Vision

Make Agam programs **observable by default** with zero-boilerplate OpenTelemetry integration. The compiler and runtime should emit traces, metrics, and structured logs without requiring manual instrumentation — achieving "observability-native" status.

## Motivation

In 2026, OpenTelemetry is the universal standard for observability. Compiler-level tracing injection (demonstrated in Kotlin and Go ecosystems) eliminates boilerplate while providing consistent, cross-platform visibility. For Agam's target domains (AI/ML, distributed systems, edge computing), built-in observability is a major differentiator.

**Key industry insight**: Organizations are now instrumenting the compilation phase itself — tracking build times, dependency resolution, and codegen bottlenecks. Agam should do both: instrument compiled programs AND instrument the compiler.

## Deliverables

### Compiler Instrumentation
- [ ] `agamc build --trace` emits OpenTelemetry spans for each compilation phase (parse, sema, codegen)
- [ ] Build performance metrics (time per crate, cache hit rates, codegen throughput)
- [ ] OTLP (OpenTelemetry Protocol) export from `agamc` to any compatible backend
- [ ] `agamc profile` visualization of compilation bottlenecks

### Language-Level Tracing
- [ ] `@trace` annotation on functions: compiler auto-injects span start/end
- [ ] `@metric` annotation: compiler generates counter/histogram instrumentation
- [ ] Automatic context propagation across async boundaries (after Phase R2)
- [ ] Structured log emission via `agam_std::log` with trace correlation

### Runtime Telemetry
- [ ] `agam_std::telemetry` module: OpenTelemetry SDK bindings
- [ ] Zero-config OTLP exporter (auto-detects collector endpoint)
- [ ] Semantic conventions for Agam-specific operations (tensor ops, GPU launches, effects)
- [ ] Sampling and filtering at the source to control telemetry volume

### Build System Observability
- [ ] Daemon (Phase 15F) emits health metrics via OTLP
- [ ] `agamc cache status` includes hit/miss telemetry
- [ ] CI integration: build trace spans visible in CI dashboards

## Design References

- **OpenTelemetry**: Universal observability standard. OTLP is the wire protocol.
- **Kotlin compiler plugins (2025)**: Demonstrated compile-time tracing injection across JVM/JS/Native targets.
- **Deno**: Built-in `--inspect` with OpenTelemetry support, zero config.

## Responsible Crates

- `agam_profile` — compiler instrumentation, build tracing
- `agam_runtime` — runtime telemetry SDK
- `agam_std` — `telemetry`, `log` modules
- `agam_codegen` — `@trace` / `@metric` annotation lowering

## Dependencies

- Phase R2 (async) — context propagation across async boundaries
- Phase R3 (networking) — OTLP export over gRPC/HTTP
