# Next Implementation Order

Use this as the default answer to "what should Agam agents build next?"

## Recently Completed

- **Phase 20** — Language Surface Expansion (effect/handler/perform syntax)
- **Phase 21** — Runtime Hardening (Win32 Job Object and Linux prctl/setrlimit)
- **Phase 22** — Omni-Targeting Directives (`@target.iot`, `@target.enterprise`, `@target.hpc`)
- **Phase 23** — GPU/NPU Integration (NVPTX pipeline, shared memory, host-device transfer — advanced items pending)

## Recommended Next: Tier 0 — Foundation Completion

The highest-priority work is **Tier 0: Foundation Completion**. These are credibility-critical items that every world-class language must have before experienced engineers will evaluate Agam seriously.

### Build Order Within Tier 0

1. **Phase F1: Formal Grammar Specification**
   - Write complete EBNF/PEG grammar for all three syntax modes
   - Mechanically test against all existing `.agam` sources
   - No code dependencies — can start immediately
   - Detail: `details/F1.md`

2. **Phase F2: Type System Completion**
   - Generics, sum types/enums, pattern matching, type inference, Option/Result
   - This is the critical path — most Tier 1+ work depends on it
   - Detail: `details/F2.md`

3. **Phase F3: Object Model Completion**
   - struct/trait/impl end-to-end through all compiler passes
   - Depends on F2 (generics for trait bounds)
   - Detail: `details/F3.md`

4. **Phase F4: Module System and Visibility**
   - pub/private visibility, qualified imports, re-exports
   - Can be partially parallelized with F2/F3
   - Detail: `details/F4.md`

5. **Phase F5: Ergonomics and Syntax Cohesion**
   - Named args, defaults, destructuring, string interpolation, ranges
   - Builds on F2/F3 type and object foundations
   - Detail: `details/F5.md`

### Parallel Opportunities

- **F1** (grammar spec) has zero code dependencies and can be done alongside any other work
- **F4** (modules) is mostly orthogonal to F2/F3 and can overlap
- **DX1** (error messages) can start during F2 since parser recovery is independent of type system design

## After Tier 0

The next tiers in priority order:

1. **Tier 1: Developer Experience** — Error messages, LSP, docs, debugger, testing
2. **Tier 2: Runtime and Concurrency** — Memory model, async, networking
3. **Tier 3: Platform and Ecosystem** — WASM, cross-compilation, web playground
4. **Tier 4: Performance** — Advanced LLVM optimization, comptime, GPU completion
5. **Tier 5: AI-Native** — Autodiff, tensor types, ML primitives
6. **Tier 6: Frontier** — Self-hosting, formal verification, quantum/ZKP

## What Not To Prioritize First

- Frontier features (quantum, ZKP) before foundation is complete
- AI-native differentiation before the type system can express tensors properly
- New agent/ecosystem integrations before the language surface is stable enough to integrate against
- macOS/iOS backend bring-up beyond planning and driver hooks
- WSL-only shortcuts that weaken the real host-toolchain story
- Performance optimization phases before the type system and object model can express real programs
