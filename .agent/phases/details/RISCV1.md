# Phase RISCV1 — RISC-V Backend Validation

**Status:** open
**Tier:** 3 (Platform and Ecosystem)
**Pillar:** 12 (Multi-Target)

## Vision

Validate and optimize Agam's output for RISC-V architectures, positioning Agam as a viable language for the next generation of open-ISA hardware including embedded, server, and AI accelerator targets.

## Motivation

RISC-V has matured significantly by 2026:
- RVA23 profile ratified (stable compilation baseline for application processors)
- AI-specific matrix extensions (AME) shipping in production silicon
- LLVM RISC-V backend is Tier 1 quality
- Server-grade RISC-V (SiFive, Esperanto) reaching data center deployments

Since Agam uses LLVM, basic RISC-V compilation comes "almost free" — but explicit validation, testing, and optimization ensures credibility and catches codegen edge cases.

## Deliverables

### Backend Validation
- [ ] `agamc build --target riscv64-linux` end-to-end compilation
- [ ] `agamc build --target riscv32-none-eabi` bare-metal/embedded target
- [ ] Validate LLVM IR emission for RISC-V Vector extension (RVV) auto-vectorization
- [ ] Validate standard library I/O paths on RISC-V Linux (QEMU or real hardware)
- [ ] Add RISC-V to `agamc doctor` hardware detection

### Optimization
- [ ] Verify SIMD auto-vectorization maps to RVV instructions
- [ ] Test GPU kernel compilation targeting RISC-V AI accelerator extensions (stretch)
- [ ] Benchmark suite validation: run `benchmarks/` on RISC-V (QEMU if no hardware)

### Ecosystem
- [ ] Add `riscv64-linux` to SDK distribution matrix (Phase 15H)
- [ ] Add RISC-V to cross-compilation documentation
- [ ] CI: QEMU-based RISC-V test runner in GitHub Actions

## Design References

- **RVA23 Profile**: Stable RISC-V application processor baseline. Includes RVV 1.0 (vector), Zba/Zbb/Zbs (bit manipulation).
- **RISC-V AI Extensions**: AME (Attached Matrix Extension) for tensor processing. Future Agam GPU/NPU pipeline could target these.
- **Zig's approach**: Zero-config cross-compilation with bundled sysroots. Agam should aspire to `agamc build --target riscv64-linux` working without extra toolchain installation.

## Responsible Crates

- `agam_codegen` — RISC-V target triple validation
- `agam_runtime` — RISC-V host detection in `hwinfo.rs`
- `agam_driver` — `--target` flag RISC-V support
- Devops: CI configuration for QEMU-based testing

## Dependencies

- Phase P2 (Cross-Compilation Matrix) — RISC-V is one target in the matrix
- Phase O1 (LLVM Optimization) — auto-vectorization for RVV
