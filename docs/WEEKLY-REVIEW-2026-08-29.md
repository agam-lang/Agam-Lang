# Weekly Review — GUI Engine RFC Verification & Phase 1 Punch List

**Date:** 2026-08-29  
**Reviewer:** Antigravity (Claude Opus 4.6)  
**RFC Under Review:** [`docs/RFC-gui-engine.md`](RFC-gui-engine.md)  
**Status:** ⛔ **Phase 1 Blocked** — dependency version triple unresolvable as specified

---

## 1. RFC Verification — File Path & Type Audit

Every file path and type citation in the RFC was independently verified against the live checkout. Results below.

### 1.1 File Path Checks

| # | RFC Citation (relative to `docs/`) | Resolved Absolute Path | Status | Check Method |
|---|---|---|:---:|---|
| 1 | `../agam/crates/experiments/agam_ui/src/lib.rs` | `agam/crates/experiments/agam_ui/src/lib.rs` | ✅ PASS | `Test-Path` |
| 2 | `../agam/crates/experiments/agam_ui/src/reactive.rs` | `agam/crates/experiments/agam_ui/src/reactive.rs` | ✅ PASS | `Test-Path` |
| 3 | `../agam/crates/experiments/agam_ui/src/backend.rs` | `agam/crates/experiments/agam_ui/src/backend.rs` | ✅ PASS | `Test-Path` |
| 4 | `../agam/crates/experiments/agam_ui/Cargo.toml` | `agam/crates/experiments/agam_ui/Cargo.toml` | ✅ PASS | `view_file` — contents verified |
| 5 | `../agam/crates/experiments/agam_ui/src/theme.rs` | `agam/crates/experiments/agam_ui/src/theme.rs` | ✅ PASS | `Test-Path` |
| 6 | `../agam/crates/experiments/agam_ui/src/style.rs` | `agam/crates/experiments/agam_ui/src/style.rs` | ✅ PASS | `Test-Path` |
| 7 | `../agam/crates/experiments/agam_ui/src/widget.rs` (§3) | `agam/crates/experiments/agam_ui/src/widget.rs` | ✅ PASS | `Test-Path` |
| 8 | `../agam/crates/runtime/agam_std/src/image.rs` | `agam/crates/runtime/agam_std/src/image.rs` | ✅ PASS | `view_file` — 737 lines, types verified |
| 9 | `../agam/crates/runtime/agam_runtime/src/simd.rs` | `agam/crates/runtime/agam_runtime/src/simd.rs` | ✅ PASS | `Test-Path` |
| 10 | `../agam/crates/core/agam_errors/src/diagnostic.rs` | `agam/crates/core/agam_errors/src/diagnostic.rs` | ✅ PASS | `view_file` — `Diagnostic` L146, `NyayaProof` L107 |
| 11 | `../agam/crates/experiments/agam_ffi/src/c_abi.rs` | `agam/crates/experiments/agam_ffi/src/c_abi.rs` | ✅ PASS | `Test-Path` |
| 12 | `../agam/crates/experiments/agam_ffi/src/bindgen.rs` | `agam/crates/experiments/agam_ffi/src/bindgen.rs` | ✅ PASS | `Test-Path` |
| 13 | `ADOPTED_DEPENDENCIES.md` | `docs/ADOPTED_DEPENDENCIES.md` | ✅ PASS | `view_file` — 67 lines |
| 14 | `FUTURE_ARCHITECTURE.md` | `docs/FUTURE_ARCHITECTURE.md` | ✅ PASS | `view_file` |
| 15 | `MEMORY_MODEL.md` | `docs/MEMORY_MODEL.md` | ✅ PASS | `view_file` |
| 16 | `architecture/gui-architecture.md` | `docs/architecture/gui-architecture.md` | ✅ PASS | `Test-Path` |

### 1.2 `agam_ui/Cargo.toml` — No `winit`/`wgpu` Dependency

**Verified.** The file contains only `serde` and `serde_json` as dependencies. No `winit`, `wgpu`, `vello`, `cosmic-text`, or `accesskit` present.

```toml
[dependencies]
serde = { workspace = true }
serde_json = { workspace = true }
```
Source: [`Cargo.toml`](file:///c:/Users/ksvik/Projects/Agam-Lang/agam/crates/experiments/agam_ui/Cargo.toml)

### 1.3 `agam_std::image` Type Verification

| Type | RFC Claims | Actual (from source) | Status |
|---|---|---|:---:|
| `ImageBuffer<P: Pixel>` | Generic image buffer | `pub struct ImageBuffer<P: Pixel>` at L148 | ✅ PASS |
| `Rgb8` | 24-bit RGB pixel | `pub struct Rgb8 { pub r: u8, pub g: u8, pub b: u8 }` at L77 | ✅ PASS |
| `Rgba8` | 32-bit RGBA pixel | `pub struct Rgba8 { pub r: u8, pub g: u8, pub b: u8, pub a: u8 }` at L111 | ✅ PASS |
| `ImageError` | Nyāya-grounded structured error | `pub struct ImageError { pub cause, pub context, pub remedy }` at L12 | ✅ PASS |
| `Gray8` | (not cited in RFC but present) | `pub struct Gray8(pub u8)` at L54 | ℹ️ INFO |

Source: [`image.rs`](file:///c:/Users/ksvik/Projects/Agam-Lang/agam/crates/runtime/agam_std/src/image.rs)

### 1.4 `agam_errors::Diagnostic` / `NyayaProof` Type Verification

| Type | RFC Citation | Actual Location | Status |
|---|---|---|:---:|
| `Diagnostic` | `agam_errors::Diagnostic` | `pub struct Diagnostic` at [`diagnostic.rs:L146`](file:///c:/Users/ksvik/Projects/Agam-Lang/agam/crates/core/agam_errors/src/diagnostic.rs#L146) | ✅ PASS |
| `NyayaProof` | `agam_errors::NyayaProof` | `pub struct NyayaProof` at [`diagnostic.rs:L107`](file:///c:/Users/ksvik/Projects/Agam-Lang/agam/crates/core/agam_errors/src/diagnostic.rs#L107) | ✅ PASS |
| Re-export | Public API | `pub use diagnostic::{Diagnostic, ..., NyayaProof, ...}` at [`lib.rs:L15`](file:///c:/Users/ksvik/Projects/Agam-Lang/agam/crates/core/agam_errors/src/lib.rs#L15) | ✅ PASS |

### 1.5 Section 7 ("Open Questions for the Weekly Reviewer")

**Verified present.** Section 7 begins at line 110 of `RFC-gui-engine.md` and contains 6 numbered open questions. This section was correctly committed.

### 1.6 PAL Files — RFC Stale Claim

> **RFC §5 states:** *"requested `pal/memory.rs` and `pal/event.rs` files are not present at the stated path in this checkout."* RFC §7 Q2 repeats this.
>
> **This is now stale.** Both files exist:
> - [`pal/memory.rs`](file:///c:/Users/ksvik/Projects/Agam-Lang/agam/crates/runtime/agam_runtime/src/pal/memory.rs) — 436 lines, OS virtual memory allocation
> - [`pal/event.rs`](file:///c:/Users/ksvik/Projects/Agam-Lang/agam/crates/runtime/agam_runtime/src/pal/event.rs) — 894 lines, cross-platform I/O event demuxer
>
> The RFC should be updated to acknowledge these exist. Q2 in Section 7 is partially resolved: the files are present; their API suitability for GUI event bridging should be evaluated during Phase 1 Task 2.

### 1.7 CI Workflow Location

> The RFC references `.github/workflows/ci.yml`. No such file exists. The actual CI workflow is at [`.github/.github/workflows/rust-ci.yml`](file:///c:/Users/ksvik/Projects/Agam-Lang/.github/.github/workflows/rust-ci.yml) (17 lines, `ubuntu-latest` only, `workflow_call` trigger). The nested `.github/.github/` path structure is unusual — likely a nested submodule or configuration artifact.

---

## 2. Dependency Version Resolution — ⛔ BLOCKING FINDING

### 2.1 The Version Triple Problem

The RFC pins `wgpu = 30.0.1` and states `vello = 0.9.0` will match after lockfile validation. **This is incorrect.**

| Dependency | RFC-Specified Version | Actual `wgpu` Requirement | Source |
|---|---|---|---|
| `vello 0.9.0` | `wgpu 30.0.1` (assumed) | **`wgpu ^29.0.3`** | [crates.io API: vello 0.9.0 deps](https://crates.io/api/v1/crates/vello/0.9.0/dependencies) |
| `vello 0.10.0` | (not in RFC) | **`wgpu ^29.0.3`** | [crates.io API: vello 0.10.0 deps](https://crates.io/api/v1/crates/vello/0.10.0/dependencies) |

The `^29.0.3` semver range covers `29.0.3 ≤ v < 30.0.0`. **`wgpu 30.0.1` is excluded.** There is no published `vello` release that targets `wgpu 30.x`.

### 2.2 The `skrifa` Version Split

Even if the `wgpu` version were corrected, there is a transitive dependency concern:

| Crate | `skrifa` Requirement | Source |
|---|---|---|
| `vello 0.9.0` | `^0.42.1` | crates.io dep API |
| `vello 0.10.0` | `^0.44.0` | crates.io dep API |
| `cosmic-text 0.19.0` | `^0.40.0` | crates.io dep API |

For `0.x` crates, Cargo treats each `0.minor` as a separate major version. This means:
- `vello 0.9.0` (`skrifa ^0.42`) + `cosmic-text 0.19.0` (`skrifa ^0.40`) → **two separate `skrifa` versions** in the lockfile (duplication, not hard conflict, but shared font types won't be interoperable across the boundary)
- `vello 0.10.0` (`skrifa ^0.44`) + `cosmic-text 0.19.0` (`skrifa ^0.40`) → same problem, wider gap

### 2.3 Resolved Decision: Downgrade `wgpu`, Not Upgrade `vello`

> **No compatible `(wgpu 30.x, vello, cosmic-text)` triple exists as of 2026-08-29.** No published `vello` release targets `wgpu 30.x`.

**Recommended resolution (requires owner sign-off):**

| Option | `wgpu` | `vello` | `cosmic-text` | Trade-off |
|---|---|---|---|---|
| **A (Recommended)** | `29.0.3` | `0.10.0` | `0.19.0` | Loses wgpu 30 features (mesh shaders, multiview). `skrifa` duplication (0.44 + 0.40) is tolerable — Agam façade owns all font types at the boundary. |
| **B** | `29.0.3` | `0.9.0` | `0.19.0` | Narrower `skrifa` gap (0.42 vs 0.40). Older vello API, fewer bug fixes. |
| **C** | `30.0.1` | *(wait)* | *(wait)* | Block until Linebender ships a `vello` release targeting `wgpu 30.x`. Unknown timeline. |

**Option A is recommended** because `wgpu 30` features (mesh shaders, multiview) are irrelevant for a 2D UI renderer, and `vello 0.10.0` is the latest stable with more bug fixes than 0.9.0.

> **This document does NOT write the chosen triple to `ADOPTED_DEPENDENCIES.md` yet** because the RFC's `wgpu 30.0.1` pin was an explicit architectural decision — changing it requires owner approval. The Phase 1 punch list below assumes Option A is approved.

### 2.4 `winit` and `accesskit` Versions

| Dependency | RFC Version | Latest on crates.io | Status |
|---|---|---|---|
| `winit` | `0.30.13` | `0.30.13` | ✅ Confirmed latest stable |
| `accesskit` | `0.24.1` | `0.24.1` | ✅ Confirmed latest stable (released June 2026) |

---

## 3. CI Headless Testing Plan

### 3.1 Platform Assessment

| Runner | Display Server | GPU | `winit` Window | `wgpu` Adapter | Solution |
|---|---|---|---|---|---|
| `ubuntu-latest` | ❌ No X11/Wayland | ❌ No GPU | ❌ Fails | ❌ Fails | `xvfb-run` + Mesa `llvmpipe` software driver |
| `macos-latest` | ✅ Has display server | ❌ No discrete GPU (Metal available) | ✅ Works | ⚠️ Software Metal | Works with default adapter; may need `WGPU_BACKEND=metal` |
| `windows-latest` | ✅ Has desktop session | ❌ No discrete GPU (DX12 WARP available) | ✅ Works | ⚠️ WARP software | Works with DX12 WARP fallback |

### 3.2 Proposed CI Change

Add a new job to the CI workflow (the daily agent will wire this into the appropriate workflow file). **Do not implement yet.**

```yaml
# Proposed new job for gui-headless testing
gui-test:
  name: GUI Headless Tests
  strategy:
    matrix:
      include:
        - os: ubuntu-latest
          headless: true
        - os: macos-latest
          headless: false
        - os: windows-latest
          headless: false
  runs-on: ${{ matrix.os }}
  steps:
    - uses: actions/checkout@v4
    - uses: dtolnay/rust-toolchain@stable

    # Linux: install Xvfb + Mesa software drivers
    - name: Setup headless display (Linux)
      if: matrix.headless
      run: |
        sudo apt-get update -qq
        sudo apt-get install -y -qq xvfb mesa-vulkan-drivers mesa-utils
      shell: bash

    - name: Run GUI tests
      env:
        LIBGL_ALWAYS_SOFTWARE: "1"
        GALLIUM_DRIVER: llvmpipe
      run: |
        if [ "${{ matrix.headless }}" = "true" ]; then
          xvfb-run -a cargo test -p agam_gui --features headless-test
        else
          cargo test -p agam_gui --features headless-test
        fi
      shell: bash
```

### 3.3 Headless Test Architecture

For unit tests that don't need a real window:

1. **`#[cfg(test)]`-gated headless mode** in `agam_gui::platform`:
   - Export a `create_headless_event_source()` that produces synthetic `GuiEvent`s without touching `winit::EventLoop`
   - This tests event-mapping logic, `GuiEvent` normalization, and error conversion independently of windowing

2. **Scene serialization test**: Render a Vello scene to an offscreen texture (using `wgpu`'s software adapter), serialize the scene graph, and assert structural invariants. This does NOT require a window — only a `wgpu::Device` obtained via `wgpu::Instance::request_adapter()` with `power_preference: Low` on the software fallback.

3. **Feature flag `headless-test`**: Gates test-only code that skips `winit` window creation. Production code paths remain unaffected.

---

## 4. Phase 1 Punch List — Ordered Task List for Daily Agent

> **Precondition:** Owner must approve the dependency version triple (Option A recommended: `wgpu 29.0.3`, `vello 0.10.0`, `cosmic-text 0.19.0`) before the daily agent begins Task 0. Tasks below assume this approval.

### Task 0: Update `ADOPTED_DEPENDENCIES.md` with approved triple
**Scope:** Add 3 new rows to the adopt-vs-build matrix table for `wgpu`, `vello`, and `winit`. Update the `wgpu` version in the RFC from `30.0.1` to the approved version.  
**Acceptance:** `ADOPTED_DEPENDENCIES.md` has rows for `wgpu`, `vello`, `winit` with exact pinned versions and rationale. RFC §1 table reflects the corrected `wgpu` version.  
**Verify:** Diff review; no code changes.

### Task 1: Create `agam_gui` crate skeleton
**Scope:** Create `agam/crates/experiments/agam_gui/` with `Cargo.toml`, `src/lib.rs`, and empty module declarations for `platform`, `gpu`, `scene`, `input`, `diagnostic`. Add the crate to the workspace `Cargo.toml` members list.  
**Acceptance:** `cargo check -p agam_gui` passes. Dependencies: `winit`, `wgpu`, `vello` at approved versions + `agam_errors`, `agam_runtime`, `agam_std`.  
**Verify:** `cargo check -p agam_gui` succeeds with zero warnings.

### Task 2: Implement `agam_gui::platform` — Window/Event Facade
**Scope:** Implement `GuiWindow` (wraps `winit::Window`), `GuiEvent` enum (pointer, key, resize, close, focus, DPI-change), and `GuiError` struct mapping `winit` errors. `GuiEvent` must not contain any `winit` types — all conversion happens at the module boundary. Map `winit::event::WindowEvent` variants to `GuiEvent` variants. Evaluate existing [`pal/event.rs`](file:///c:/Users/ksvik/Projects/Agam-Lang/agam/crates/runtime/agam_runtime/src/pal/event.rs) for reusable I/O event patterns.  
**Acceptance:** Unit tests verify: (a) every `winit::WindowEvent` variant maps to a `GuiEvent`; (b) `GuiError` contains `{fact, reason, fix, law}` fields; (c) no `winit` type appears in `agam_gui`'s public API.  
**Verify:** `cargo test -p agam_gui -- platform` passes.

### Task 3: Implement `agam_gui::gpu` — Surface Lifecycle
**Scope:** Implement `GpuContext` (wraps `wgpu::Instance`, `Adapter`, `Device`, `Queue`), `GpuSurface` (wraps `wgpu::Surface`), and device-loss recovery. All `wgpu` errors map to `GuiError`. Expose adapter info via `GpuCapabilities` struct (no `wgpu` types). Device-loss triggers recreation attempt → on failure, demote tier and emit Nyāya diagnostic.  
**Acceptance:** (a) `GpuContext::new()` returns `Result<GpuContext, GuiError>`, never panics; (b) simulated device-loss test confirms `Result` return, not raw `wgpu` error; (c) no `wgpu` type in public API.  
**Verify:** `cargo test -p agam_gui -- gpu` passes.

### Task 4: Implement `agam_gui::scene` — Vello Rectangle/Clip Rendering
**Scope:** Create a retained `SceneNode` tree. Implement `draw_rect()`, `draw_rounded_rect()`, `clip_rect()` that build Vello `Scene` primitives. Expose `SceneBuilder` that serializes to a Vello `Scene` for rendering.  
**Acceptance:** Headless test: build a scene with 3 rects + 1 rounded clip, serialize the scene graph, assert node count and structure. No visual rendering needed for this task.  
**Verify:** `cargo test -p agam_gui -- scene` passes.

### Task 5: Wire CI headless testing job
**Scope:** Add the `gui-test` job from §3.2 to the appropriate CI workflow file. Add `headless-test` feature flag to `agam_gui/Cargo.toml`. Implement `create_headless_event_source()` in `platform` module behind `#[cfg(test)]`.  
**Acceptance:** CI pipeline runs `agam_gui` tests on all 3 OSes. Linux uses `xvfb-run` + `llvmpipe`.  
**Verify:** CI green on push (or manual trigger).

### Task 6: Integration — Window opens/resizes/closes on all 3 OSes
**Scope:** Write an integration test (or example binary) that opens a window, renders a colored rectangle via the scene→vello→wgpu pipeline, handles resize, and closes cleanly. This is the Phase 1 acceptance demo.  
**Acceptance:** Window opens, background renders, resize re-renders, close exits cleanly — verified on all 3 CI runners.  
**Verify:** CI `gui-test` job passes; manual visual check on dev machine.

### Task 7: Scene serialization golden test
**Scope:** Build a deterministic scene (fixed rects, clips, colors), serialize its node structure to JSON, compare against a checked-in golden file. This is the "headless scene-serialization test" from Phase 1 acceptance criteria.  
**Acceptance:** `cargo test -p agam_gui -- golden` passes. Golden file checked in under `agam_gui/tests/goldens/`.  
**Verify:** Deterministic output on all platforms.

---

## 5. Summary of Findings

| Finding | Severity | Action Required |
|---|---|---|
| `wgpu 30.0.1` incompatible with all published `vello` releases | ⛔ **Blocker** | Owner approves downgrade to `wgpu 29.0.3` (Option A) |
| `skrifa` version split between `vello` and `cosmic-text` | ⚠️ Warning | Tolerable with façade; revisit if `cosmic-text` updates to `skrifa 0.44` |
| RFC §7 Q2 (PAL files absent) — now stale | ℹ️ Info | Update RFC; evaluate `pal/event.rs` API for GUI use |
| CI workflow path mismatch (`ci.yml` vs `rust-ci.yml`) | ℹ️ Info | Daily agent targets correct path |
| RFC cites `wgpu 30.0.1` in §1 table | 🔧 Fix | Correct to approved version after sign-off |
| All other file paths and type citations | ✅ Pass | No action |
| Section 7 present in committed file | ✅ Pass | No action |
