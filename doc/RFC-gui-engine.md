# Agam GUI Engine Architecture RFC

> **Status:** 🟡 Design and migration RFC. Existing UI prototype: [`agam/crates/experiments/agam_ui/`](../agam/crates/experiments/agam_ui/). New native engine: ⚪ proposed as `agam/crates/experiments/agam_gui/`.  
> **Decision:** GPU-rendered, cross-platform widgets with an Agam-owned Fluent/HIG-inspired identity layer; do not embed WinUI/AppKit widgets. This corrects the older target document's hand-rolled platform-backend plan ([`architecture/gui-architecture.md`](architecture/gui-architecture.md)).

## 1. Layered Architecture & Adopt-vs-Build Matrix

The policy follows [`ADOPTED_DEPENDENCIES.md`](ADOPTED_DEPENDENCIES.md): adopt mature correctness-critical infrastructure and own all script-facing identity and diagnostics. `agam_ui` currently provides widget, style, display-list, and `Rc<RefCell>` reactive prototypes ([`agam_ui/src/lib.rs`](../agam/crates/experiments/agam_ui/src/lib.rs), [`reactive.rs`](../agam/crates/experiments/agam_ui/src/reactive.rs), [`backend.rs`](../agam/crates/experiments/agam_ui/src/backend.rs)); it has no `winit`, `wgpu`, text, or accessibility dependency ([`agam_ui/Cargo.toml`](../agam/crates/experiments/agam_ui/Cargo.toml)).

| Layer | Status | Policy / pinned evaluation baseline | Agam value-add and facade ownership |
|---|:---:|---|---|
| Windowing, DPI, keyboard, pointer, IME | ⚪ | **ADOPT** `winit = 0.30.13` | `agam_gui::platform` maps events to Agam-owned `GuiEvent`/Nyāya errors; no `winit` types, errors, app ID, or terminology reach scripts. |
| GPU abstraction and surface lifecycle | ⚪ | **ADOPT** `wgpu = 29.0.3` | `agam_gui::gpu` owns adapter policy, resource lifetime, device-loss recovery, and all errors; never surface backend names or `wgpu` errors. Resolved: 29.0.3 is vello 0.10.0's required range; wgpu 30's mesh-shader/multiview features are irrelevant for 2D UI ([`WEEKLY-REVIEW-2026-08-29.md`](WEEKLY-REVIEW-2026-08-29.md)). |
| 2D vector scene renderer | ⚪ | **ADOPT** `vello = 0.10.0` (requires `wgpu ^29.0.3`) | Vello is Rust/`wgpu` 2D scene rendering; Agam owns retained scene nodes, damage regions, clipping policy, shader-quality selection, and paint diagnostics. **Reject `skia-safe`**: its native Skia build/binding supply chain adds platform/toolchain complexity that contradicts the workspace's hermetic-dependency policy. Version resolved per [`WEEKLY-REVIEW-2026-08-29.md`](WEEKLY-REVIEW-2026-08-29.md). |
| Text shaping, layout, font fallback | ⚪ | **ADOPT** `cosmic-text = 0.19.0` | `agam_gui::text` owns font selection, fallback policy, glyph-cache budgeting, and user-facing errors; no fontdb/cosmic terminology leaks. Version resolved per [`WEEKLY-REVIEW-2026-08-29.md`](WEEKLY-REVIEW-2026-08-29.md). |
| Accessibility tree and OS bridge | ⚪ | **ADOPT** `accesskit = 0.24.1` + compatible `accesskit_winit` | `agam_gui::a11y` maps stable widget keys to Agam semantic roles/actions. It owns labels, localization, focus policy, and all accessibility diagnostics. |
| Image decode/upload | 🟡 | **BUILD on existing** `agam_std::image`; later **ADOPT** a decoder only when formats beyond Netpbm are required | Reuse `ImageBuffer`, `Rgb8`, `Rgba8`, and structured `ImageError` from [`agam_std/src/image.rs`](../agam/crates/runtime/agam_std/src/image.rs). Convert validated RGBA buffers to GPU textures; do not create a second pixel-buffer model. The current implementation supports Netpbm codecs, not PNG/JPEG. |
| Layout engine | ⚪ | **BUILD** | Agam-owned constraints, retained widget layout, stable keys, and dirty-rect propagation. This is language/runtime semantics, not a third-party identity. |
| Reactive state and widget API | 🟡 | **BUILD / migrate** existing `Signal`, `Computed`, batching, widget and style concepts | Replace single-threaded `Rc<RefCell>` scheduling in [`reactive.rs`](../agam/crates/experiments/agam_ui/src/reactive.rs) with UI-thread ownership plus cross-thread message ingress; make subscriptions drive invalidation rather than immediate rendering. |
| Design tokens, motion, theming | 🟡 | **BUILD / migrate** existing theme/style concepts | The current themes/styles are prototype-only ([`agam_ui/src/theme.rs`](../agam/crates/experiments/agam_ui/src/theme.rs), [`style.rs`](../agam/crates/experiments/agam_ui/src/style.rs)). `agam_gui::design` owns Fluent/HIG-inspired tokens, platform adaptation, and Agam visual identity. |

**Facade rule:** every adopted-layer error is converted at the crate boundary to `GuiError { fact, reason, fix, law }`, then to `agam_errors::Diagnostic`/`NyayaProof` ([`agam_errors/src/diagnostic.rs`](../agam/crates/core/agam_errors/src/diagnostic.rs)). Fallible public operations return `Result<T, GuiError>`; no adopted error/panic/about string crosses the Agam API.

## 2. Module Boundaries

| Crate / module | Status | Role | May depend on |
|---|:---:|---|---|
| `core/agam_ast`, `middle/agam_hir`, `middle/agam_sema` | 🟡 | ⚪ Proposed `@ui` syntax nodes, validation, and lowering only | Existing lower-layer direction; no GUI runtime dependency. |
| `runtime/agam_runtime` | 🟢 | SIMD and hardware capability substrate; use existing `simd` APIs rather than duplicate SIMD dispatch ([`agam_runtime/src/simd.rs`](../agam/crates/runtime/agam_runtime/src/simd.rs)). | Platform/Rust primitives only; never `agam_std` or GUI. |
| `runtime/agam_std` | 🟡 | Existing safe image buffer/pixel types and standard-library surface ([`agam_std/src/image.rs`](../agam/crates/runtime/agam_std/src/image.rs)). | `agam_runtime`; no GUI renderer dependency. |
| `experiments/agam_gui` | ⚪ | Native window/event facade, retained scene, layout, text, renderer, a11y, tokens, reactive scheduler. | `agam_errors`, `agam_runtime`, `agam_std`, adopted GUI crates. No compiler-backend/tooling dependency. |
| `experiments/agam_ui` | 🟡 | Existing prototype; migration source only. Do not make it a parallel renderer. | ⚪ After migration, it becomes a compatibility facade over `agam_gui` or is retired in a separately approved change. |
| `tooling/agam_driver`, `agam_lsp`, `agam_debug` | 🟡 | ⚪ Proposed `agamc gui run`, inspector, and preview integration. | `agam_gui` only through an explicit tooling feature; GUI never depends on tooling. |

Dependency direction is strict: `core → middle → backends`; runtime is independent of compiler/tooling; `agam_std → agam_runtime`; `agam_gui → {agam_errors, agam_runtime, agam_std}`; tooling may consume GUI. This preserves the runtime/standard-library boundary specified in [`FUTURE_ARCHITECTURE.md`](FUTURE_ARCHITECTURE.md) and keeps platform/FFI interop behind the existing structured ABI approach ([`agam_ffi/src/c_abi.rs`](../agam/crates/experiments/agam_ffi/src/c_abi.rs), [`bindgen.rs`](../agam/crates/experiments/agam_ffi/src/bindgen.rs)).

`agam_gui` internal modules: `platform`, `gpu`, `scene`, `layout`, `text`, `image`, `input`, `reactive`, `design`, `a11y`, `diagnostic`. `platform` is the only module importing `winit`; `gpu` the only direct `wgpu`/Vello importer; `a11y` the only AccessKit importer. This prevents identity leakage and makes dependency substitution testable.

## 3. The Declarative Widget API (Agam's actual language-facing surface)

⚪ **Proposed syntax, not implemented:** the current parser supports dual language profiles but has no verified `@ui` declaration in the compiler path; existing UI construction is Rust-side [`Widget`](../agam/crates/experiments/agam_ui/src/widget.rs). Both profiles lower to the same retained `UiNode { key, kind, props, children }`; keys are mandatory for stateful/repeated nodes and stable across renders.

```agam
# @lang.base — indentation-oriented surface
@lang.base
@ui
fn app() -> Window:
    state count = 0
    Window(title: "Counter", size: (360, 180)):
        Column(gap: 12, padding: 20):
            Text("Count: {count}")
            Button("Increment", on_click: fn(): count += 1)
```

```agam
// @lang.advance — explicit block/expression surface
@lang.advance
@ui
fn app() -> Window {
    let state count: i32 = 0;
    Window { title: "Counter", size: (360, 180),
        Column { gap: 12, padding: 20,
            Text { value: "Count: {count}" },
            Button { label: "Increment", on_click: || { count += 1 } },
        },
    }
}
```

**Reactive-to-frame contract (⚪ proposed):** reading `state` records `(SignalId, UiNodeKey)`; mutation queues one UI-thread transaction; frame scheduling coalesces mutations to one vsync; only dependent nodes are rebuilt. The existing prototype already models signal subscriptions and batching ([`reactive.rs`](../agam/crates/experiments/agam_ui/src/reactive.rs)), but its callbacks execute immediately and are not an event-loop scheduler.

**Damage contract (⚪ proposed):** reconciliation compares stable keyed nodes; property/layout changes mark the old and new bounds dirty; damage is unioned, expanded by effect outsets, clipped to the window, and passed to the retained scene renderer. Full repaint is permitted on resize, surface loss, or damage-area threshold; low-tier devices coalesce to one full repaint when fragmentation costs more than repainting. Scene/layout/image resources use ARC/CoW at the language boundary and UI-thread ownership for GPU handles, consistent with [`MEMORY_MODEL.md`](MEMORY_MODEL.md).

## 4. Hardware Tiering Strategy

`wgpu` chooses a supported platform backend and exposes adapter limits/features; Agam must not promise a particular API. The current runtime already exposes SIMD-oriented routines ([`agam_runtime/src/simd.rs`](../agam/crates/runtime/agam_runtime/src/simd.rs)); ⚪ `GuiCapabilities` combines its CPU/SIMD result with `wgpu` adapter limits and a startup micro-benchmark. The selected tier is observable in developer diagnostics, never in end-user strings.

| Tier | Admission | Required visual policy | Frame policy |
|---|---|---|---|
| **Safe** | Adapter/device unavailable or recovery mode | Solid surfaces, opaque layers, no backdrop blur/shaders; present a structured startup error if no render path exists. | Cap at 30 FPS only when a software fallback is explicitly implemented; no silent fallback exists today. |
| **Integrated** | Baseline adapter/limits | Rounded rects, gradients, text, clip stack; disable acrylic/backdrop sampling; one small shadow pass. | 60 FPS target; tile damage and cap glyph/image atlas memory. |
| **Balanced** | Baseline plus adequate texture/storage limits and stable benchmark | Cached shadows, bounded blur radius, animated opacity/transform. | Prefer damage rendering; 60/120 Hz follows display/vsync. |
| **Discrete** | Headroom validated by benchmark/limits | Full Fluent/HIG material stack, backdrop blur and high-resolution shadows, subject to battery/thermal policy. | 120 Hz target where the surface reports it; drop effects before dropping input responsiveness. |

⚪ Quality selection is deterministic and testable: `(adapter class, limits, benchmark, battery policy) → tier`; users may request a lower tier, never force an unavailable higher one. Device loss demotes one tier after recreation failure and emits Agam-owned Nyāya diagnostics.

## 5. Phased Milestone Breakdown

| Phase | Scope | Shippable acceptance criteria |
|---|---|---|
| **1 — Window and shapes** | ⚪ Create `agam_gui`; `winit` window/event facade; `wgpu` surface; Vello rectangles/rounded clips; test headless scene serialization. | Windows/macOS/Linux CI opens/resizes/closes a window; pointer/key events normalize; device-loss is `Result`, no raw dependency error. |
| **2 — Text and images** | ⚪ `cosmic-text` facade, font fallback, glyph cache; upload existing `ImageBuffer<Rgba8>`; no new image-buffer type. | Unicode shaping/fallback golden tests; PPM/PGM rendering test uses [`image.rs`](../agam/crates/runtime/agam_std/src/image.rs); atlas eviction and invalid image input return Nyāya diagnostics. |
| **3 — Widget tree and reactive state** | ⚪ Stable keys, retained reconciliation, dirty-rect scheduler; migrate prototype conceptual API. | Counter example updates one text subtree; 10k-node dirty-node test proves bounded damage; no callback runs off UI thread. |
| **4 — Native visual identity** | ⚪ Token resolver, Fluent/HIG-inspired themes, quality tiering, motion and material degradation. | Screenshot goldens per tier; contrast/focus checks; Integrated tier proves blur is absent while core interaction remains responsive. |
| **5 — Accessibility** | ⚪ AccessKit bridge, focus/action synchronization, keyboard navigation, screen-reader semantics. | Automated tree/action tests plus Windows/macOS/Linux manual assistive-technology checklist; stable keys survive rerender. |

Each phase is one roughly week-long daily-cadence milestone. No phase changes `agam_runtime` PAL or duplicates image/SIMD abstractions without a separate runtime RFC; `pal/memory.rs` and `pal/event.rs` exist in this checkout and their APIs are available for GUI integration without a separate creation step.

## 6. Risk Register

| Adopted dependency | Largest risk | Mitigation / facade ownership |
|---|---|---|
| `winit 0.30.13` | Platform event-loop behavior differs, especially Wayland/IME. | Keep `GuiEvent`/`GuiWindow` owned by Agam; run platform integration tests; swap only `platform` if needed. |
| `wgpu 29.0.3` | Major-version churn and driver/device-loss variability. | Pin exact lockfile version; isolate in `gpu`; test device recreation and tier demotion; publish no backend names. |
| `vello 0.10.0` | Rapid API evolution and compatibility with selected `wgpu`. | Pin only a tested Vello/`wgpu` pair; retain Agam scene/display facade; permit renderer replacement without widget API change. |
| `cosmic-text` | Font fallback/complex-script correctness differs by host font inventory. | Bundle test fonts; define Agam fallback order; expose only `GuiTextError`, not fontdb/cosmic errors. |
| `accesskit 0.24.1` / adapter | OS bridge/platform coverage gaps. | Keep semantic tree independent; test actions/tree snapshots; report degraded accessibility explicitly in developer diagnostics. |
| Future image decoder | Codec CVEs and third-party error leakage. | Reuse current Netpbm path first; select a decoder through the adopted-dependency gate and map errors to `ImageError`/`GuiError`. |

## 7. Open Questions for the Weekly Reviewer

1. **Version-pair confirmation:** ✅ Resolved — `wgpu = 29.0.3`, `vello = 0.10.0`, `cosmic-text = 0.19.0` approved per [`WEEKLY-REVIEW-2026-08-29.md`](WEEKLY-REVIEW-2026-08-29.md). wgpu 30's mesh-shader/multiview features are irrelevant for 2D UI.  
2. **PAL location:** ✅ Resolved — `pal/memory.rs` and `pal/event.rs` exist in this checkout. GUI code may depend on their APIs.  
3. **Existing prototype fate:** approve whether [`agam_ui`](../agam/crates/experiments/agam_ui/) becomes a compatibility facade or is retired after Phase 3; maintaining two render paths is rejected.  
4. **Language syntax approval:** `@ui`, `state`, and the two examples are proposed syntax. Confirm parser/desugaring ownership and whether `state` is local-only or module-exportable.  
5. **Software fallback:** no verified software renderer exists. Decide whether Safe tier is a startup diagnostic only in Phases 1–5 or whether a separate adopted CPU renderer is required.  
6. **Licensing/release policy:** confirm the acceptable licenses and MSRV for the exact `winit`/`wgpu`/Vello/cosmic-text/AccessKit set before adding them to the workspace dependency governance table.
