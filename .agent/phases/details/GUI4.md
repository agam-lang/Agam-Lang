# Phase GUI4 — Declarative and Reactive UI Syntax

**Status:** open
**Tier:** 0 (Foundation Completion — this is language syntax, not just a library)
**Pillar:** 16 — Declarative & Reactive Syntax

## Vision

UI code should be **declarative** — you describe *what* the interface should look like, and the compiler figures out *how* to draw it. When data changes (an AI model returns a prediction, a sensor updates), bound UI components update **automatically** with zero boilerplate event listeners.

## Syntax Design

```agam
# Declarative UI in Agam base mode
@ui
fn dashboard(state: AppState) -> View:
    Column(spacing: 16, padding: 24):
        Text("AI Dashboard", style: .title)

        # Reactive binding — updates automatically when state.predictions changes
        LineChart(data: state.predictions, animate: true)

        Row(spacing: 8):
            Button("Train Model", on_click: || state.train()):
                style: .primary
            Button("Export", on_click: || state.export()):
                style: .secondary

        # Conditional rendering
        if state.is_loading:
            Spinner(size: 32)
        else:
            DataGrid(rows: state.results, columns: ["Name", "Score", "Status"])
```

## Deliverables

### Declarative Widget DSL
- [ ] `@ui` annotation marks functions as UI builders
- [ ] Indentation-based nesting (base mode) or brace-based (advance mode)
- [ ] Widget constructors with named parameters: `Button("label", on_click: handler)`
- [ ] Conditional rendering: `if`/`else` in widget trees
- [ ] List rendering: `for item in items: ListItem(item.name)`
- [ ] Widget composition: custom widgets are just functions returning `View`

### Reactive State Management
- [ ] `@observable` annotation on state structs — changes trigger UI re-render
- [ ] Fine-grained reactivity: only re-render widgets that depend on changed fields
- [ ] Derived state: computed properties that update when dependencies change
- [ ] `@binding` for two-way data binding on input widgets
- [ ] No manual `setState()` or event listener registration needed

### State Architecture
- [ ] Local state: `@state var count = 0` within a widget
- [ ] Shared state: `@shared` state accessible across widget tree
- [ ] Global state: App-level state store with action dispatch
- [ ] State persistence: `@persist` auto-saves to disk between sessions
- [ ] Time-travel debugging: record and replay state changes

### Automatic UI Updates
- [ ] Background data changes propagate to UI on the main thread
- [ ] Batched updates: multiple state changes = single re-render
- [ ] Async data integration: `@async` data sources update UI when resolved
- [ ] WebSocket/streaming data: live data feeds auto-update bound widgets

### Clean Separation of Concerns
- [ ] Logic (`.agam` functions) — data processing, AI, networking
- [ ] Presentation (`@ui` functions) — widget tree description
- [ ] Styling (theme engine) — visual properties
- [ ] No mixing of rendering code with business logic

## Responsible Crates

- `agam_parser` — `@ui` DSL syntax parsing
- `agam_sema` — reactive dependency tracking
- `agam_ui` — reactive runtime, widget diffing, state management
- `agam_hir` — UI tree lowering

## Dependencies

- Phase F2 (type system) — generics for typed state containers
- Phase F5 (ergonomics) — closures for event handlers, named args for widgets
- Phase R2 (async) — async data sources driving UI updates
