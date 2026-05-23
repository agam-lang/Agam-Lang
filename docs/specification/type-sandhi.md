# Agam-Lang Type Sandhi

In accordance with Agam's third design principle—**Sandhi (Type Junction Rules)**—the Agam type system defines rigorous, predictable rules for how types interact, flatten, and combine. There is no implicit coercion; all interactions are governed by formal Sandhi rules evaluated by `agam_sema`.

## 1. Optional Sandhi (Idempotence)

The `Optional<T>` (denoted syntactically as `T?`) is idempotent when nested.

*   **Rule**: `T??` reduces to `T?`.
*   **Mechanism**: The compiler automatically flattens nested Optionals. A value that might be absent, which itself might be absent, is logically just a value that might be absent.
*   **Code Example**:
    ```agam
    fn find_user() -> User?
    // If we map over an Optional, we don't get User??, we get User?
    let user_name: String? = find_user().map(|u| u.name)
    ```

## 2. Result Sandhi (Error Union)

When operations that return `Result<T, E>` are chained, the error types form a union.

*   **Rule**: `Result<T, E1> + Result<U, E2>` through the `?` propagation operator results in a return type requirement of `Result<U, E1 | E2>`.
*   **Mechanism**: Agam supports inline anonymous union types for errors.
*   **Code Example**:
    ```agam
    fn process() -> Result<Data, IoError | ParseError> {
        let text = read_file("data.txt")?; // returns Result<String, IoError>
        let data = parse_data(text)?;      // returns Result<Data, ParseError>
        return Ok(data);
    }
    ```

## 3. Reference Sandhi (Auto-Deref)

When references are chained or when methods are called on references, Agam applies a strict junction rule to avoid `&&&T` boilerplate.

*   **Rule**: Method resolution automatically dereferences `&T` to `T` to find implementations. 
*   **Rule**: Taking a reference of a reference `&(&T)` reduces to `&T` unless explicitly marked otherwise (e.g., `&&raw T` for FFI).

## 4. Trait Bound Sandhi (Intersection)

When multiple trait bounds meet via generic parameters, they form a strict intersection.

*   **Rule**: `T: A` and `T: B` in the same context resolve to `T: A + B`.
*   **Pratyāhāra Integration**: If `constraint C = A + B`, then `T: A` and `T: B` is completely interchangeable with `T: C` at the type-checking boundary.

## 5. Effect Sandhi (Perform/Handle)

Agam's algebraic effects system uses Sandhi to determine the total effect requirements of a function.

*   **Rule**: If function `A` performs effect `E1` and calls function `B` which performs effect `E2`, the signature of `A` must declare `effects(E1, E2)` unless `A` wraps `B` in a `handle_with` block that eliminates `E2`.
*   **Mechanism**: The compiler calculates the union of all unhandled effects in the AST to determine the required function signature.
