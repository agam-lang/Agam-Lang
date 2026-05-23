# Agam-Lang Naming Conventions: The Dhātu System

Following Agam's first design principle—**Dhātu (Root Verb System)**—the standard library and all idiomatic Agam code must utilize a controlled vocabulary of action verbs. This prevents the fragmentation seen in other ecosystems where `fetch`, `retrieve`, `get`, and `read` are used interchangeably for the exact same semantic action.

## Core Rules

1.  **One Verb Per Action**: Never use synonyms for a canonical root.
2.  **Noun Follows Verb**: Methods performing an action should be structured as `<verb>_<noun>` (e.g., `read_lines`, not `lines_read`).
3.  **Boolean Queries**: Functions returning booleans must start with an interrogative root (`is_`, `has_`, `can_`).

## Canonical Root Verbs (Dhātus)

The following table defines the canonical roots for the Agam ecosystem.

| Semantic Action | Canonical Root | Forbidden Synonyms | Example |
| :--- | :--- | :--- | :--- |
| **Data Retrieval** | `get` | `fetch`, `retrieve` | `dict.get(key)` |
| **Data Insertion** | `insert` | `put`, `add`, `store` | `map.insert(k, v)` |
| **Data Removal** | `remove` | `delete`, `drop` | `list.remove(index)` |
| **I/O Reading** | `read` | `load`, `consume` | `file.read_to_string()` |
| **I/O Writing** | `write` | `save`, `flush` | `file.write_bytes(data)` |
| **Creation** | `create` | `make`, `build`, `new`* | `create_dir_all()` |
| **Parsing/Decoding** | `parse` | `decode`, `from_string` | `parse_json(str)` |
| **Formatting/Encoding**| `format` | `encode`, `to_string` | `format_date(date)` |
| **Computation** | `compute` | `calculate`, `eval` | `compute_hash(data)` |
| **State Mutation** | `update` | `modify`, `change` | `state.update(new_val)` |
| **Verification** | `verify` | `check`, `validate` | `verify_signature()` |

*(Note: `new()` is reserved strictly for struct instantiation, not for system-level creation like making a file).*

## Affixation

In the Dhātu tradition, meaning is modified systematically through affixes.

*   **`_mut` suffix**: Denotes a mutable borrow or operation (e.g., `get_mut()`).
*   **`_all` suffix**: Denotes exhaustive application (e.g., `read_all()`, `create_dir_all()`).
*   **`try_` prefix**: Denotes an operation that returns a `Result` instead of panicking on failure (e.g., `try_insert()`).

## Example: Refactoring to Agam Idioms

**Bad (Fragmented):**
```agam
let data = fetch_network_data();
let parsed = decode_payload(data);
save_to_disk(parsed);
```

**Good (Dhātu Compliant):**
```agam
let data = read_network_data();
let parsed = parse_payload(data);
write_to_disk(parsed);
```
