# 002 — Call Arity and Argument Type Checking

**Status:** proposed
**Depends on:** PRE-000 (differential harness)
**Component:** `agam_sema` (resolver / type check), `agam_errors`
**Ledger:** new — file as `A-Grade: #4` before starting

---

## 1. Motivation

**Agam does not check how many arguments a call passes.**

Evidence: `grep -rn 'arity\|wrong number of arg\|ArgumentCount' crates/middle/agam_sema/src/`
returns matches only in `exhaustive.rs`, where `arity` refers to pattern
constructor arity. There is no call-site arity check anywhere in the semantic
analyser.

Two consequences, one of them load-bearing for the project's own documentation:

**(a) Wrong-arity calls compile.** `foo(1, 2, 3)` against `fn foo(x: i32)` is not
diagnosed. What the backends then emit is undefined by any spec.

**(b) `note.md`'s blessed workaround depends on the hole.** GAP-05 prescribes
multi-argument printing as the verified substitute for format strings:

```agam
println("Sum = ", sum);   // note.md §2, "Verified Working Syntax"
```

But `agam_sema/src/resolver.rs:812-815` declares the builtin as taking exactly one
parameter:

```rust
("print",     vec![any],    unit_ty),
("println",   vec![any],    unit_ty),
("print_int", vec![int_ty], unit_ty),
("print_str", vec![str_ty], unit_ty),
```

So the documented idiom works **because argument count is unchecked**, not because
variadic `println` is defined. Adding arity checking without also declaring
`print`/`println` variadic would break every example file in the repository.
These two changes must land in the same commit.

---

## 2. Formal grammar diff

**None.** This spec changes no syntax. `CallSuffix = "(" , [ ArgumentList ] , ")"`
is unchanged.

The change is to the static semantics, specified here because the grammar cannot
express it:

```
(* Static semantics, new *)

For every call expression  callee ( a1 , ... , an ):
  let sig = signature_of(callee)
  if sig.is_variadic:
      require n >= sig.required_params.len()
      each a[i] for i < sig.required_params.len() must unify with sig.required_params[i]
      each a[i] for i >= that length must unify with sig.variadic_element_type
  else:
      require n == sig.params.len()                    -- error E0061 otherwise
      each a[i] must unify with sig.params[i]          -- error E0308 otherwise
```

### Builtin signature table change

```rust
// OLD — resolver.rs:812-815
("print",     vec![any],    unit_ty),
("println",   vec![any],    unit_ty),

// NEW — an explicit variadic marker
BuiltinSig { name: "print",     params: vec![],        variadic: Some(any), ret: unit_ty },
BuiltinSig { name: "println",   params: vec![],        variadic: Some(any), ret: unit_ty },
BuiltinSig { name: "print_int", params: vec![int_ty],  variadic: None,      ret: unit_ty },
BuiltinSig { name: "print_str", params: vec![str_ty],  variadic: None,      ret: unit_ty },
```

Every other entry in `builtin_function_signatures` becomes `variadic: None`.

**User-defined functions may not be variadic.** There is no surface syntax for it
and this spec does not add one. `variadic` is reachable only from the builtin
table.

---

## 3. AST / HIR / MIR impact

**AST:** none.

**HIR:** `HirFunctionSig` (or equivalent) gains an `is_variadic: bool` and
`variadic_element: Option<TypeId>`. If no such struct exists, the builtin table
is the only carrier and HIR is unchanged — determine this during implementation.

**MIR:** none. `Op::Call` already carries a `Vec<ValueId>` of arbitrary length.

**Backends:** none required. `llvm_emitter.rs:1036` and `agam_jit/src/lib.rs:3544`
already special-case the print family by name and already handle whatever
argument count arrives. **If a backend change seems necessary, stop and
escalate** — it means variadic lowering is not what this spec assumes.

### Dialect symmetry statement

Arity checking operates on HIR, downstream of all syntactic differences. Both
dialects reach the identical check. A test must assert that the same wrong-arity
call written in `@lang.base` and `@lang.advance` produces the identical error code
and message text (AC-6).

---

## 4. Worked examples

### 4.1 Valid — variadic print family

```agam
@lang.advance
fn main() -> i32 {
    let sum: i32 = 45;
    println("Sum = ", sum);
    println("a", "b", "c", 1, 2, 3);
    println();
    print_int(sum);
    return 0;
}
```

Expected: compiles. Output `Sum = 45`, then `abc123`, then an empty line, then
`45`. Identical under JIT and LLVM.

### 4.2 Valid — exact-arity user function

```agam
@lang.advance
fn add(a: i32, b: i32) -> i32 { return a + b; }

fn main() -> i32 {
    print_int(add(2, 3));
    return 0;
}
```

Expected: compiles, prints `5`.

### 4.3 Invalid — too many arguments

```agam
@lang.advance
fn add(a: i32, b: i32) -> i32 { return a + b; }

fn main() -> i32 {
    print_int(add(2, 3, 4));
    return 0;
}
```

Expected, exactly:

```
error[E0061]: this function takes 2 arguments but 3 were supplied
 --> input.agam:5:15
  |
2 | fn add(a: i32, b: i32) -> i32 { return a + b; }
  |    --- defined here with 2 parameters
...
5 |     print_int(add(2, 3, 4));
  |               ^^^        - unexpected 3rd argument
  |
  = fix: remove the 3rd argument
  = law: AGAM-SYNTAX-002 §2
```

### 4.4 Invalid — too few arguments

```agam
@lang.advance
fn add(a: i32, b: i32) -> i32 { return a + b; }
fn main() -> i32 { print_int(add(2)); return 0; }
```

Expected:

```
error[E0061]: this function takes 2 arguments but 1 was supplied
 --> input.agam:3:30
  |
3 | fn main() -> i32 { print_int(add(2)); return 0; }
  |                              ^^^^^^ missing argument for parameter `b: i32`
  |
  = law: AGAM-SYNTAX-002 §2
```

Note singular "was supplied" for 1, plural "were supplied" otherwise.

### 4.5 Invalid — wrong argument type

```agam
@lang.advance
fn add(a: i32, b: i32) -> i32 { return a + b; }
fn main() -> i32 { print_int(add(2, "three")); return 0; }
```

Expected:

```
error[E0308]: mismatched types in argument 2
 --> input.agam:3:37
  |
3 | fn main() -> i32 { print_int(add(2, "three")); return 0; }
  |                                     ^^^^^^^ expected `i32`, found `str`
  |
  = law: AGAM-SYNTAX-002 §2
```

### 4.6 Invalid — arity error in base mode, identical diagnostic

```agam
@lang.base
fn add(a: i32, b: i32) -> i32:
    return a + b

fn main() -> i32:
    print_int(add(2, 3, 4))
    return 0
```

Expected: identical `E0061` text and structure to 4.3, differing only in span
coordinates.

### 4.7 Regression corpus — every example in the repo must still compile

After this change, all of the following must still pass `agamc check`:
`examples/01_basics/*.agam`, `agam/examples/*.agam`,
`benchmarks/suites/**/*.agam`. Any file that breaks either (a) had a genuine
latent arity bug, which must be fixed in the file and noted in the commit, or
(b) reveals a missing variadic marker, which must be fixed in the table.

---

## 5. Acceptance criteria

- **AC-1** — 4.1 and 4.2 compile and produce the stated stdout under **both**
  `agamc run` and `agamc build --backend llvm`, byte-identical.
- **AC-2** — 4.3, 4.4, 4.5 produce exactly `E0061`, `E0061`, `E0308` with the
  stated primary span. Diagnostic text compared by snapshot test.
- **AC-3** — 4.4's message uses the singular form "1 was supplied". A test asserts
  pluralisation for n = 0, 1, 2.
- **AC-4** — Zero-argument call to a zero-parameter function still compiles
  (`fn f() {} ... f();`).
- **AC-5** — `println()` with no arguments compiles and prints a newline.
- **AC-6 (symmetry)** — 4.3 and 4.6 produce identical `code` and identical message
  body after span normalisation. Asserted by test.
- **AC-7** — Every `.agam` file listed in 4.7 passes `agamc check` with exit 0. A
  CI step enumerates them; the list is not hardcoded in the test.
- **AC-8** — `note.md` GAP-05 is amended: the multi-argument `println` idiom is
  now documented as *defined* (variadic builtin) rather than as a workaround.
- **AC-9** — `cargo test`, `cargo clippy --all-targets -- -D warnings`,
  `cargo fmt --all -- --check` all pass via `python scripts/cargo_lens.py`.
- **AC-10** — New ledger entry `A-Grade: #4` created and closed in `issues.md`
  with counters updated.

---

## 6. Required mutation test — MANDATORY

A shallow implementation can pass §4 by hardcoding "if callee == \"add\" require 2".
This test detects that.

Add `crates/middle/agam_sema/tests/mutation_002_arity.rs`:

```rust
//! Mutation test for AGAM-SYNTAX-002.
//! The arity check must be derived from the resolved signature, not memorised.

/// Generate `fn f_N(p0..pN-1: i32) -> i32` and call it with M arguments.
fn program(declared: usize, supplied: usize) -> String {
    let params: Vec<String> = (0..declared).map(|i| format!("p{i}: i32")).collect();
    let args: Vec<String> = (0..supplied).map(|i| i.to_string()).collect();
    format!(
        "@lang.advance\nfn target({}) -> i32 {{ return 0; }}\n\
         fn main() -> i32 {{ return target({}); }}\n",
        params.join(", "), args.join(", ")
    )
}

#[test]
fn arity_check_scales_across_the_whole_matrix() {
    // 0..=6 declared x 0..=6 supplied. Accept iff equal. 49 cases.
    for declared in 0..=6 {
        for supplied in 0..=6 {
            let result = check_program(&program(declared, supplied));
            if declared == supplied {
                assert!(result.is_ok(),
                    "declared={declared} supplied={supplied} must be accepted");
            } else {
                let err = result.expect_err(
                    "declared={declared} supplied={supplied} must be rejected");
                assert_eq!(err.code(), "E0061");
                assert!(err.message().contains(&declared.to_string()));
                assert!(err.message().contains(&supplied.to_string()));
            }
        }
    }
}

#[test]
fn renaming_the_function_does_not_change_the_verdict() {
    // Defeats any name-keyed hardcoding.
    for name in ["target", "zzz", "print_int_lookalike", "println_x", "add"] {
        let src = program(2, 3).replace("target", name);
        let err = check_program(&src).expect_err("{name} must still be rejected");
        assert_eq!(err.code(), "E0061");
    }
}

#[test]
fn variadic_builtins_accept_any_count_but_fixed_ones_do_not() {
    for n in 0..=8 {
        let args: Vec<String> = (0..n).map(|i| i.to_string()).collect();
        let ok = format!("@lang.advance\nfn main() -> i32 {{ println({}); return 0; }}\n",
                         args.join(", "));
        assert!(check_program(&ok).is_ok(), "println with {n} args must be accepted");

        let bad = format!("@lang.advance\nfn main() -> i32 {{ print_int({}); return 0; }}\n",
                          args.join(", "));
        if n == 1 {
            assert!(check_program(&bad).is_ok());
        } else {
            assert_eq!(check_program(&bad).unwrap_err().code(), "E0061",
                "print_int with {n} args must be rejected");
        }
    }
}

#[test]
fn argument_type_mutation_is_detected_positionally() {
    // Poison exactly one argument position at a time; the reported index must follow.
    for poison in 0..4 {
        let args: Vec<String> = (0..4)
            .map(|i| if i == poison { "\"s\"".to_string() } else { i.to_string() })
            .collect();
        let src = format!(
            "@lang.advance\nfn target(a: i32, b: i32, c: i32, d: i32) -> i32 {{ return 0; }}\n\
             fn main() -> i32 {{ return target({}); }}\n", args.join(", "));
        let err = check_program(&src).expect_err("poisoned arg {poison} must be rejected");
        assert_eq!(err.code(), "E0308");
        assert!(err.message().contains(&format!("argument {}", poison + 1)),
            "error must name argument {}, got: {}", poison + 1, err.message());
    }
}
```

`check_program` must run lex → parse → HIR → sema and return the first
diagnostic. **Each test must be shown to FAIL on the pre-fix compiler** (all
cases pass today, since nothing is checked) — record this in the commit message.

---

## 7. Open questions — DO NOT decide these yourself

1. **Should user code be able to declare a variadic function?** This spec says no
   and provides no syntax. If the project wants `fn f(args: ...i32)`, that is a
   separate spec. **Do not add surface syntax for it here.**

2. **What is `print`/`println`'s separator and terminator when given multiple
   arguments?** Today's behaviour appears to be concatenation with no separator
   (`println("a","b")` → `ab`), inferred from `examples/` and the note.md idiom,
   but I did not verify it against the runtime. §4.1's expected output assumes
   no separator. **Verify against `agam_runtime` and escalate if it differs** —
   do not change runtime behaviour to match this spec.

3. **Should default parameter values participate in arity?** `FunctionParam` in
   `agam_ast::decl` has a `default: Option<Expr>` field. If defaults are
   implemented, the required-arity rule in §2 is wrong (it should be
   `required <= n <= total`). **Determine whether defaults are implemented before
   writing the check, and escalate if they are.**

4. **Method calls (`ExprKind::MethodCall`) vs free calls (`ExprKind::Call`).**
   This spec's examples only cover free calls. Whether method-call arity uses the
   same code path is unknown to me. **Escalate if they diverge**; do not
   silently check only one.

5. **Effect operation calls (`perform E.op(args)`).** Arity for effect operations
   is declared in `EffectOp { params, .. }`. Whether they route through the same
   check is unknown. **Escalate.**
