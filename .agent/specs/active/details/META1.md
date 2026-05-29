# Phase META1 — Metaprogramming and Macro System

**Status:** open (upgrading existing `agam_macro` stub)
**Tier:** 4 (Performance and Optimization Depth)

## Vision

Allow Agam to write its own code — procedural macros, compile-time code generation, and domain-specific language (DSL) construction for neural networks, web servers, database queries, and security policies.

## Deliverables

### Declarative Macros
- [ ] Pattern-matching macros: `macro_rules! vec { ($($x:expr),*) => { ... } }`
- [ ] Hygienic by default — macro-generated names don't clash with user code
- [ ] Recursive macro expansion with depth limits

### Procedural Macros
- [ ] `@derive(Serialize, Debug)` for auto-implementing traits
- [ ] Attribute macros: `@route("/api/users")` for web framework DSLs
- [ ] Function-like macros: `sql!("SELECT * FROM users WHERE id = ?", user_id)`
- [ ] Macros run at compile time in a sandboxed Agam interpreter

### Domain-Specific Languages
- [ ] Neural network definition DSL: `@nn { conv2d(3, 64) -> relu -> pool }`
- [ ] SQL query builder with compile-time type checking
- [ ] HTML/template DSL for web rendering
- [ ] Security policy DSL for capability declarations

### Compile-Time Reflection
- [ ] `@comptime` access to type metadata: field names, types, sizes
- [ ] Conditional compilation based on type properties
- [ ] Integrates with Phase O2 (comptime execution)

## Responsible Crates

- `agam_macro` — macro expansion engine, procedural macro sandbox
- `agam_parser` — macro invocation syntax
- `agam_sema` — macro hygiene, scope management

## Dependencies

- Phase F2 (type system) — macros need type information for derive
- Phase O2 (comptime) — shared compile-time execution infrastructure
