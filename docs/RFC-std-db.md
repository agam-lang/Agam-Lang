# RFC: `std.db` — Adopted Pure-Rust Embedded Storage Facade

**Status:** Proposed architecture; no `std.db` implementation exists in this checkout.  
**Date:** 2026-09-13  
**Decision:** adopt `redb` as the persistent-engine implementation and build only the Agam-facing `agam_std::db` facade, diagnostics, capability boundary, and validation harness. Do **not** build a new page cache, WAL, B+tree, MVCC engine, or database wire protocol.

## 1. Evidence standard and repository baseline

This RFC treats prior roadmap/status prose as non-authoritative. A readiness claim is tagged **🟢** only when this checkout contains the cited implementation; **🟡** means a real, bounded dependency or constraint exists but does not provide the proposed subsystem; **⚪** means proposed/not present. This follows the write-level evidence discipline of [`AUDIT-optimizer-pipeline-honesty-2026-09-05.md:4,26-41`](AUDIT-optimizer-pipeline-honesty-2026-09-05.md), rather than inferring completion from names.

All architectural, specification, and RFC documentation is canonicalized under `docs/`. This RFC is placed at [`docs/RFC-std-db.md`](RFC-std-db.md).

| Verified fact | Status | Evidence | Consequence |
|:--|:--:|:--|:--|
| Adopt rather than re-create mature algorithms; a standard B-tree is already an explicit adoption decision. | 🟢 | [`ADOPTED_DEPENDENCIES.md:8-12,20-25`](ADOPTED_DEPENDENCIES.md) | A database’s on-disk tree/recovery algorithms are an even stronger case for adoption than an in-memory BTreeMap. |
| Every dependency needs pure Rust (or hermetic C), zero known `cargo audit` advisories, an explicit policy entry, and an Agam-owned facade/error voice. | 🟢 | [`ADOPTED_DEPENDENCIES.md:55-70`](ADOPTED_DEPENDENCIES.md) | `redb` admission is conditional on a pinned pure-Rust review, advisory check, and no third-party errors at the language boundary. |
| `PageAllocation` is a 435-line RAII virtual-memory primitive with four tests. | 🟢 | [`agam/crates/runtime/agam_runtime/src/pal/memory.rs:103-180,354-435`](../agam/crates/runtime/agam_runtime/src/pal/memory.rs) | Reuse it only for future volatile runtime memory needs; do not duplicate it. It is **not** a file-mapping API: Unix allocation explicitly uses `MAP_ANONYMOUS | MAP_PRIVATE` at `:172-180`. |
| Default memory is ARC + CoW; `strict {}` is affine and lexically scoped in the architectural specification. | 🟢 (specification) | [`MEMORY_MODEL.md:4,13,42-63,78-88`](MEMORY_MODEL.md) | Public handles must have explicit ownership/lifetime semantics and cannot expose borrowed page pointers beyond a transaction. This is a design constraint, not evidence that `std.db` exists. |
| Actor mailbox/reply and local synchronization primitives exist. | 🟢 | [`agam_runtime/src/actor.rs:154-217,347-405`](../agam/crates/runtime/agam_runtime/src/actor.rs), [`agam_std/src/sync.rs:95-169`](../agam/crates/runtime/agam_std/src/sync.rs) | `std.db` will compose these, not create a third scheduler or lock family. |
| A remote actor frame exists (24-byte header, CRC validation). | 🟢 | [`agam_runtime/src/actor.rs:453-470,599-650`](../agam/crates/runtime/agam_runtime/src/actor.rs) | It is not a database protocol and must not be silently repurposed as one. |
| `agam_std` currently has no `db` module or database dependency. | 🟢 | [`agam/crates/runtime/agam_std/Cargo.toml:1-18`](../agam/crates/runtime/agam_std/Cargo.toml); source-file search under `agam/crates` found no `db`/`database` module (only unrelated `runtime/src/sandbox.rs`). | The entire facade is ⚪ proposed; no claim of a hidden partial engine is made. |
| Workspace size is 30 crates, not the previously repeated 27. | 🟢 | The required `find crates -maxdepth 3 -name Cargo.toml \| wc -l` could not be invoked because this host denied Bash instance creation. Equivalent read-only PowerShell enumeration of `agam/crates` found 30 manifests; [`agam/Cargo.toml:3-33`](../agam/Cargo.toml) lists the same 30 members. | All scope estimates use 30 crates. |

`agam_gui::eval` is a useful boundary precedent, not a storage dependency: its real `UiRuntime { state: HashMap<...> }` and evaluator are at [`agam/crates/experiments/agam_gui/src/eval.rs:1-31,86-119`](../agam/crates/experiments/agam_gui/src/eval.rs). `std.db` likewise owns an actual facade state machine rather than returning a third-party object unchanged.

## 2. Decision record: adopt versus build

### Chosen dependency

⚪ **Proposed adoption:** add a version-pinned `redb` dependency to `agam/Cargo.toml` and `agam_std/Cargo.toml`, after the admission gate in Section 8 passes. `redb` documents itself as pure Rust, ACID, CoW B-trees, concurrent readers/writer MVCC, and crash safety ([crate documentation](https://docs.rs/redb/latest/redb/)). Its public design describes one writer and concurrent readers, serializable isolation, CoW B+trees, epoch-based page reclamation, checksummed commit slots, and recovery ([upstream design](https://github.com/cberner/redb/blob/master/docs/design.md)).

This is deliberately **not** an endorsement of a generic "native build everything" posture. It is an Agam-native *API and diagnostic* layer over an adopted, pure-Rust persistence engine. `rocksdb` is rejected because its Rust wrapper statically links RocksDB and requires Clang/LLVM ([upstream wrapper README](https://github.com/rust-rocksdb/rust-rocksdb)); that violates the zero-C-dependency goal. `sled` remains a valid candidate, but is not selected: its public docs establish an embedded BTreeMap-like API and transactions ([docs](https://docs.rs/sled/latest/sled/)), whereas `redb` directly documents the exact page-level CoW/MVCC/crash protocol required here.

| Layer requested by Track B | Decision | Status | Why this is the correctness-first boundary | Required Agam-owned work |
|:--|:--|:--:|:--|:--|
| WAL and crash recovery | **ADOPT `redb` durable commit/recovery; do not build a separate WAL.** | ⚪ | `redb` uses CoW commit slots and checksums rather than requiring an Agam WAL. Its documented default 1PC+C uses one `fsync`; two-phase commit is available for a hostile crash/write-order threat model ([design](https://github.com/cberner/redb/blob/master/docs/design.md), [API](https://docs.rs/redb/latest/redb/struct.WriteTransaction.html)). A second log beside an adopted engine creates two recovery authorities—a data-corruption risk. | Expose `Durability::Immediate` only for the durable public commit path; map recovery/open/commit errors to Nyāya diagnostics. Do not advertise a WAL that does not exist. |
| Page storage and B+tree | **ADOPT wholesale.** | ⚪ | The `redb` design is an on-disk CoW B+tree and allocator; tree splitting, page reuse, checksums, and recovery must be one proven unit. Splitting its tree from its allocator/cache invalidates its recovery invariants. | Define tables, key/value codec constraints, quotas, and error mapping; never expose pages, raw offsets, or `redb` table types. |
| Buffer pool | **ADOPT the engine-owned cache; no Agam pool in v1.** | ⚪ | A separately cached/mapped copy of the same file invites stale views and durability-order bugs. Existing PAL allocation is anonymous, not file-backed. | Record cache telemetry only through safe upstream statistics if exposed; no new `mmap`/`VirtualAlloc` layer. |
| MVCC and isolation | **ADOPT wholesale.** | ⚪ | Page epochs, reader registration, single-writer coordination, abort, savepoint, and recycle safety are inseparable. `redb` documents serializable isolation and a single write transaction with concurrent reads ([design](https://github.com/cberner/redb/blob/master/docs/design.md), [Database API](https://docs.rs/redb/latest/redb/struct.Database.html)). | Provide transaction verbs whose contract is no stronger than upstream; ensure transaction handles cannot leak borrowed values. |
| Concurrency | **COMPOSE existing actor + sync layers.** | 🟢 primitives / ⚪ DB actor | `ActorRef::tell` and `ask` already provide mailbox/reply behavior; `agam_std::sync` already wraps channel and mutex errors. Redb’s single writer is the storage serialization point, not a reason to invent another global mutex. | Optional `DbActor` serializes application write commands; direct local use calls the facade synchronously. |
| Multi-process wire protocol | **OUT OF SCOPE; build none.** | ⚪ | This is embedded, single-process storage. A DB server protocol changes trust, authentication, cancellation, backpressure, and versioning scope. The actor frame is for actor traffic, not durable DB semantics. | If multi-process service is separately approved, evaluate an adopted authenticated RPC framing; do not reuse or extend actor frames by default. |

### Durability and hostile-input policy

⚪ The default public `WriteTxn::commit` maps only to upstream `Durability::Immediate`; upstream says that level is persistent when commit returns ([Durability API](https://docs.rs/redb/latest/redb/enum.Durability.html)). A performance-only internal batch API may opt into `None`, but must be named `commit_non_durable`, unavailable to untrusted persistence paths, and document that a crash may lose that batch. For databases writable by a local adversary able to control workload and crash timing, enable upstream two-phase commit: upstream explicitly notes the non-cryptographic checksum limitation of the default one-phase path ([WriteTransaction security notes](https://docs.rs/redb/latest/redb/struct.WriteTransaction.html)). No software design can make dishonest storage hardware honor `fsync`; this RFC treats that as a documented platform assumption, not an erased risk.

## 3. Proposed public boundary, ownership, and placement

| Component | Status | Placement | Contract / non-goal |
|:--|:--:|:--|:--|
| `agam_std::db` | ⚪ | `agam/crates/runtime/agam_std/src/db/mod.rs` | Thin standard-library facade: open/create, typed table declaration, read/write transaction, commit/abort, integrity check, metrics. It owns all names and error text. |
| `Db`, `ReadTxn`, `WriteTxn`, `Table`, `DbError` | ⚪ | same module tree | `Db` is ARC-shareable; a transaction owns the underlying transaction and is not cloneable. Values crossing the public Agam boundary are owned copies (or a facade-owned value object) and cannot borrow a page after transaction end. `DbError` carries Pratyakṣa/context, Anumāna/cause, Upamāna/remedy, and Śabda/API rule—never raw `redb::Error`. |
| `DbActor` and message enum | ⚪ | `agam_std::db::actor` | Optional application orchestration, implemented with `agam_runtime::actor::{Actor, ActorRef}`. It may serialize business-level writes but may not claim stronger transaction ordering than the engine. |
| Persistent storage engine | ⚪ adoption | external `redb` behind private adapter | `redb` types are private. The facade pins and tests the adapter against one reviewed upstream version. |
| PAL changes | **Rejected** | none | `agam_runtime::pal::memory` remains unchanged. No custom file mapping, huge page, or buffer-pool allocator belongs in this RFC. |
| Compiler / MIR / JIT changes | **Rejected** | none | `std.db` is runtime standard-library work. No language syntax, effect lowering, backend, or new compiler feature is authorized by this RFC. |

This placement is consistent with the workspace taxonomy: `agam_std` is already designated for thin zero-panic wrappers over adopted storage and the ARC model ([`ADOPTED_DEPENDENCIES.md:42`](ADOPTED_DEPENDENCIES.md)); `agam_runtime` remains the PAL/actor substrate. No new crate is justified until the facade proves it needs a stable independent release boundary.

### Transaction state machine

⚪ **Proposed, exact facade behavior:**

```text
Db::open/create
  ├─ begin_read()  → ReadTxn(snapshot) → get/scan → drop (releases snapshot)
  └─ begin_write() → WriteTxn(open) → put/delete/open_table
                                      ├─ commit() → durable committed | mapped error
                                      └─ abort/drop → aborted
```

`ReadTxn` may coexist with writes as permitted by the adopted engine. `WriteTxn` must be scoped tightly: a live writer blocks later writers upstream. A facade table iterator owns its upstream iterator/transaction lifetime; it yields owned encoded data, not a `&[u8]` tied to an unmapped page. `strict {}` callers receive the same linear transaction behavior by construction: a transaction is consumed by `commit` or `abort` and cannot be copied. Default ARC callers may clone `Db`, never an active transaction. These are ⚪ interface commitments pending language binding design, constrained by the current memory-model specification rather than claiming existing enforcement.

## 4. Concurrency and process boundary

| Need | Chosen mechanism | Evidence and constraint |
|:--|:--|:--|
| Independent reads and engine serialization | Adopted database concurrency | Upstream allows multiple concurrent reads and one writer; `begin_write` blocks while one is live ([Database API](https://docs.rs/redb/latest/redb/struct.Database.html)). Do not add a global facade lock around reads. |
| Application command sequencing | ⚪ `DbActor` | Existing `ActorSystem::spawn` makes an actor with an `mpsc` mailbox at [`actor.rs:381-405`](../agam/crates/runtime/agam_runtime/src/actor.rs); `ask` already creates a bounded reply wait at `:200-217`. Use it only where an application wants serialized commands. |
| Local callbacks/background work | 🟢 `agam_std::sync` | Use existing channels/mutex wrappers at [`sync.rs:95-169`](../agam/crates/runtime/agam_std/src/sync.rs); do not expose `std::sync` poisoning or raw sender errors to Agam users. |
| Cross-process database access | ⚪ no support | A second process opens the file only under the adopted engine’s locking/open rules. There is no server listener, client protocol, or actor-frame reuse in this scope. |

## 5. Integrity, recovery, and validation plan

Unit tests alone cannot establish storage safety. The following gates are mandatory before `std.db` becomes a supported persistence feature.

| Test class | Status | Concrete harness and oracle | Acceptance criterion |
|:--|:--:|:--|:--|
| Facade contract tests | ⚪ | Temporary file; open/create, typed put/get/delete, absent key, abort, committed reopen, invalid declaration/path. Assert Agam `DbError` fields and absence of `redb` error text. | All public failure paths return structured diagnostics; zero raw third-party type/text reaches the Agam surface. |
| Differential model test | ⚪ | Seeded `proptest` command sequences against `BTreeMap` for a single committed state and a model of read snapshots; replay the same sequence after every failure seed. | For every operation and reopen, key/value set, scan order, and committed visibility match the model. |
| Concurrent schedule test | ⚪ | Deterministic barrier-controlled readers/writer; record snapshot IDs and expected serial order. Include long readers, writer contention, abort, savepoint if exposed, and iterator drop. | No reader sees torn data; no deadlock; observed history satisfies documented serializable/snapshot contract. |
| Crash-injection / kill-and-recover | ⚪ | Parent process drives a child worker with a durable operation journal and sends a unique commit sequence. Kill the child at named points: before commit, during repeated commits, immediately after commit return, during compaction, and during reopen. Restart and compare database state with journal’s set of acknowledged durable commits. Run on each supported OS/filesystem in CI/nightly. | Recovered state is exactly a prefix of durable acknowledged commits (or a documented atomic whole commit), `check_integrity` succeeds, and no unacknowledged partial transaction appears. |
| Corruption / truncated-file corpus | ⚪ | Mutate magic/header, commit slots, payload bytes, page truncation, oversized lengths, and random bit flips. Open in isolated process with time/memory bounds. | Safe structured rejection or upstream recovery; no panic, hang, out-of-bounds behavior, or silent acceptance of a value absent from the oracle. |
| Fuzzing | ⚪ | `cargo-fuzz`/libFuzzer target for facade encoding and transactional command decoder; seeded corpus from crash and corruption cases. Keep minimized reproducer files. | Sustained CI fuzz budget with zero untriaged crash; every reproducer becomes regression test. |
| Upstream regression gate | ⚪ | Pin exact `redb` release, lockfile review, `cargo audit`, upstream changelog/security review, then rerun all above before any update. | No new advisory; migration/recovery tests pass across old-to-new format only when upstream supports it. |

### Benchmark validation

⚪ This RFC does **not** claim a speedup before measurements exist. It defines proof after the facade is implemented:

| Workload | What it exercises | Before/after comparison | Proof threshold |
|:--|:--|:--|:--|
| `append-durable` | Small inserts with `Immediate` commit; fsync-bound latency | Facade version versus a direct, pinned `redb` control; report p50/p95/p99 and commits/s. | Facade median throughput ≥95% of direct control; otherwise profile/correct wrapper overhead before release. |
| `batched-write` | 1K/10K writes per transaction, sequential and random keys | Same direct control; bytes written/commit latency, process RSS. | No unexplained superlinear allocation or >5% facade-only time regression. |
| `snapshot-read-under-write` | Long scans plus a writer; MVCC page retention | Throughput, tail latency, peak RSS, upstream cache stats where available. | No deadlock; bounded RSS under a documented reader-lifetime cap; results match oracle. |
| `reopen-recovery` | Databases of 1 MiB, 1 GiB, and target-size fixture after kill points | Wall-clock recovery time, integrity result, durable-prefix match. | Every run preserves integrity; recovery target is recorded per hardware rather than invented. |
| `compaction-and-churn` | Insert/delete cycles and reopen | File size, compaction time, allocated bytes, integrity. | No data loss; storage growth explained by retained snapshots/savepoints and bounded after they drop. |

Metrics are collected by a facade debug counter (opened transactions, commits by durability, encoded bytes, copied-out bytes), OS process RSS, file length, and wall-clock monotonic time. Allocation counts require an opt-in test allocator or platform profiler; absent that instrumentation, the RFC forbids claiming allocation reduction. Existing repository benchmark material was not found to contain a persistent-storage workload, so these are new named workloads—not a false assertion that an existing suite exercises them.

## 6. Daily-cadence milestones and review gates

This uses the existing RFC convention: each phase is one approximately week-long, daily-cadence milestone ([`docs/RFC-gui-engine.md:87-97`](../docs/RFC-gui-engine.md)). A weekly review can stop the plan at any gate; no phase authorizes a bespoke storage engine.

| Phase | Daily-cadence scope | Shippable acceptance criteria | Weekly review decision |
|:--|:--|:--|:--|
| 0 — Admission | Verify exact `redb` release, source/license/MSRV/features, pure-Rust dependency graph, `cargo audit`, API compatibility, and update adopted-dependency policy entry. | Written dependency review; clean lockfile/audit; prototype opens a file without exposing upstream types. | Approve/reject dependency. Rejection ends the feature or restarts vendor evaluation—never silently becomes “build our own DB.” |
| 1 — Facade core | Implement `Db`, tables, owned codecs, read/write/abort, Nyāya `DbError`; add direct contract tests. | Reopen test preserves committed values; abort does not; error identity leak tests pass. | Verify public ownership/codec contract and package placement. |
| 2 — Transaction and actor integration | Add durability selection policy, transaction lifetime discipline, optional `DbActor`, and concurrent read/write tests. | Immediate commit/reopen semantics and contention tests pass; no new synchronization primitive. | Confirm actor is optional and does not mask engine blocking/deadlock behavior. |
| 3 — Recovery hardening | Add child-process kill/recover harness, corruption corpus, `check_integrity` route, and durable-prefix oracle. | Repeated OS-specific crash matrix passes; every failure preserves a reproducer/journal. | Block release on any unexplained loss, hang, or corrupted open. |
| 4 — Fuzz, benchmark, release decision | Add fuzz targets, model test, benchmark suite, docs/examples, dependency update procedure. | Targets run in CI/nightly; benchmark baseline captured; facade overhead threshold met. | Decide experimental vs supported status from recorded evidence, not prose. |

## 7. Risk register

| Risk | Severity | Mitigation / release gate | Residual risk |
|:--|:--:|:--|:--|
| Silent data corruption from a home-grown recovery protocol | Critical | Do not own WAL/tree/MVCC; adopt one integrated engine and execute crash/corruption tests. | Upstream implementation defect remains possible; pin, monitor, and update only through migration tests. |
| Loss after commit due to non-durable mode | Critical | Public durable path uses `Immediate`; non-durable mode is explicitly named/restricted; crash journal distinguishes acknowledged commits. | Hardware/FS may lie about `fsync`. Document it and support only tested environments. |
| Malicious crash/write-order checksum attack | High | Enable upstream two-phase commit for attacker-controlled database inputs; do not call non-cryptographic checksum authentication. | Hostile storage hardware can still violate assumptions. |
| Long readers retain CoW pages | High | Transaction lifetime guidance, metrics, soak tests, optional actor timeout/cancellation policy at application level. | Correct MVCC retention can grow storage until reader drops. |
| Identity/error leak or dangling view | High | Private adapter, owned values, compile-time facade-only API, error snapshot tests. | Encoding copies trade performance for safety; benchmark them. |
| Dependency supply-chain/license/MSRV drift | High | Pin release, lockfile/review, `cargo audit`, source/license review, controlled upgrades. | New upstream vulnerabilities require rapid review. |
| Duplicate concurrency/protocol abstraction | Medium | Reuse actor/sync locally; no IPC in scope; no wrapper-wide mutex. | Application misuse of optional actor still needs examples and tests. |

## 8. Open questions for weekly reviewer

1. **Threat model:** Are database files writable by an attacker who can also induce crashes? If yes, require two-phase commit and document storage-platform assumptions before Phase 1.
2. **Durability SLA:** Is `Immediate` on every public write acceptable, or is a separately named, explicitly lossy batching API required? No default may imply durability while using `None`.
3. **Language API shape:** Which Agam value types and codecs are stable enough for v1 tables? Until decided, restrict the Rust facade to ordered byte/string/integer codecs and avoid a premature ORM/SQL layer.
4. **Supported filesystems/platforms:** Which Windows, Linux, and macOS filesystem combinations are release targets for kill/recover CI? `fsync` guarantees are platform assumptions, not portable magic.
5. **Redb version and upgrade policy:** The exact release must be selected during Phase 0. Upstream docs observed during this RFC covered 4.1/4.2 endpoints; do not pin from prose alone.
6. **Operational ownership:** Who owns database compaction, quotas, backups, and encryption-at-rest? They are intentionally outside an embedded key-value v1 and need separate RFCs if required.
7. **Multi-process service:** If a server is later required, approve a separate transport/authentication RFC. This RFC explicitly provides no wire protocol.

## 9. Final decision

`std.db` should **not** become a home-grown storage engine. The production-safe, zero-C-dependency route is an Agam-owned `agam_std::db` facade over a vetted, pinned pure-Rust `redb` release, with the engine retaining exclusive ownership of its CoW B+tree, page/cache/recovery mechanism, and MVCC. The only acceptable claim of readiness is evidence from the admission, crash-recovery, fuzzing, and benchmark gates above; until then every `std.db` component remains ⚪ proposed.
