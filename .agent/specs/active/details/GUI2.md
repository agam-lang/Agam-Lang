# Phase GUI2 — Hardware-Accelerated Visual Engine

**Status:** open
**Tier:** 4 (Performance and Optimization Depth)
**Pillar:** 14 — Hardware-Accelerated Visual Engine

## Vision

The GUI cannot lag. Agam's rendering engine must bypass CPU rendering and talk directly to the GPU by default. Interfaces run at a **flawless 120 FPS** — capable of handling enterprise forms, real-time data visualization with thousands of data points, and interactive AI dashboards without dropping a frame.

## Architecture

```
Widget Paint Commands
    │
    ▼
┌─────────────────────────────────────┐
│  Render Pipeline                     │
│                                      │
│  Scene Graph → Display List →        │
│  Batched Draw Calls → GPU Submit     │
│                                      │
│  ┌──────────────────────────────┐    │
│  │ GPU Acceleration Layer        │    │
│  │                               │    │
│  │  Text: GPU glyph atlas       │    │
│  │  2D:   Anti-aliased paths    │    │
│  │  3D:   Scene integration     │    │
│  │  Data:  GPU-side transforms  │    │
│  └──────────────────────────────┘    │
└─────────────────────────────────────┘
    │
    ├──► Direct3D 12 (Windows)
    ├──► Metal (macOS/iOS)
    ├──► Vulkan (Linux/Android)
    └──► WebGPU (Browser)
```

## Deliverables

### GPU Render Pipeline
- [ ] Retained-mode scene graph with GPU-resident display lists
- [ ] Automatic draw call batching and instancing
- [ ] GPU-side rectangle, rounded-rect, circle, path rendering
- [ ] Anti-aliased vector graphics without CPU rasterization
- [ ] Sub-pixel text rendering via GPU glyph atlas (SDF-based)
- [ ] Frame pacing: target 120 FPS with vsync, graceful degradation

### Data Visualization Engine
- [ ] GPU-accelerated chart rendering: line, bar, scatter, heatmap
- [ ] Real-time streaming: 10,000+ data points at 60 FPS without jank
- [ ] GPU-computed layouts for large graphs and network diagrams
- [ ] Smooth zoom/pan with GPU-based level-of-detail
- [ ] Integration with tensor/ndarray types for direct GPU data binding

### Animation System
- [ ] Spring-based physics animations (like SwiftUI)
- [ ] GPU-interpolated transitions: position, color, opacity, scale
- [ ] Keyframe animation with easing curves
- [ ] `@animate` annotation for automatic property transitions
- [ ] 120 FPS guaranteed for all standard animations

### Compositing
- [ ] Off-screen render targets for complex effects (blur, shadow, glow)
- [ ] Layer-based compositing with GPU blending
- [ ] Clip regions and masks (GPU-accelerated)
- [ ] Multi-window rendering with independent GPU contexts

### Fallback and Degradation
- [ ] Software rasterizer fallback for headless/CI environments
- [ ] Feature detection: gracefully reduce effects on older hardware
- [ ] `@perf_budget(16ms)` annotation for frame-time assertions in tests

## Responsible Crates

- `agam_ui` — render pipeline, scene graph, animation system
- `agam_codegen` — GPU shader compilation for UI rendering
- `agam_runtime` — GPU context management, frame timing

## Dependencies

- Phase GUI1 (omni-platform renderer) — platform windowing layer
- Phase O5 (GPU) — GPU infrastructure shared with compute kernels
