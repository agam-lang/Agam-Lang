# Phase PKG5 — Decentralized Federated Registry

**Status:** open
**Tier:** 3 (Platform and Ecosystem Breadth)
**Pillar:** 22 — The Decentralized Registry Pillar

## Vision

If the central Agam registry goes down, **nobody's deployment is blocked**. The package system is federated — pull packages from the official registry, a private corporate server, a GitHub repository, or even a peer-to-peer network. No single point of failure.

## Deliverables

### Multi-Source Resolution
- [ ] `agam.toml` supports multiple registry sources:
  ```toml
  [registries]
  default = "https://registry.agam-lang.org"
  corporate = "https://packages.mycompany.com"
  mirror = "https://mirror.agam-lang.org"
  ```
- [ ] Resolution order: project-local → corporate → default → mirrors
- [ ] Automatic failover: if primary registry is unreachable, try mirrors

### Source Types
- [ ] **Central registry** — `https://registry.agam-lang.org` (official, curated)
- [ ] **Corporate/private registry** — self-hosted, authenticated, air-gapped capable
- [ ] **Git repository** — `git = "https://github.com/user/repo"` (direct clone)
- [ ] **Local path** — `path = "../my-local-lib"` (already supported in Phase 17A)
- [ ] **Tarball URL** — `url = "https://example.com/package-1.0.tar.gz"`
- [ ] **IPFS** — `ipfs = "QmHash..."` (content-addressed, permanent, decentralized)

### Private Registry Server
- [ ] `agamc registry serve` — start a local registry server
- [ ] Compatible with the official registry protocol
- [ ] Authentication: API tokens, OIDC/SSO integration
- [ ] Access control: per-package read/write permissions
- [ ] Proxy mode: cache packages from the central registry locally

### Registry Mirroring
- [ ] `agamc registry mirror --source official --target ./mirror/`
- [ ] Incremental sync: only download new/updated packages
- [ ] Full offline mirror for air-gapped environments
- [ ] Mirror integrity verification via Merkle tree

### Federation Protocol
- [ ] Registries can peer with each other
- [ ] Package discovery across federated registries
- [ ] Trust delegation: "I trust packages from registry X if signed by key Y"
- [ ] Namespace federation: `@company/package` resolves to company's registry

## Responsible Crates

- `agam_pkg` — multi-source resolver, registry client, server, mirror
- `agam_driver` — `agamc registry` subcommands

## Dependencies

- Phase P3 (package manager) — base registry protocol
- Phase PKG3 (supply chain) — signing and verification across registries
- Phase PKG2 (reproducibility) — hash verification across sources
