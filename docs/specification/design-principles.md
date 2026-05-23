# Agam-Lang Design Principles: The Indic Linguistic Foundations

Agam is uniquely grounded in the world's oldest and most rigorous formal grammar systems: Pāṇini's *Aṣṭādhyāyī* (Sanskrit, ~4th century BCE) and the *Tolkāppiyam* (Tamil, ~3rd century BCE). These traditions are not aesthetic branding; they are the direct ancestors of modern formal language theory. 

By applying these millennia-old principles to programming language design, Agam achieves unparalleled regularity, composability, and clarity. This document outlines the seven core principles that guide Agam's syntax and semantics.

## 1. Dhātu (धातु) — Root Verb System

In Sanskrit grammar, every word is derived from a core verbal root (dhātu) combined with systematic affixes. Agam applies this to API design to eliminate naming chaos.

*   **Principle**: The standard library and ecosystem must use a strictly controlled vocabulary of canonical action verbs. 
*   **Application**: Instead of arbitrarily mixing `get`, `fetch`, `retrieve`, and `read`, Agam defines canonical root verbs for specific semantic actions. Every function that performs a read operation uses the root `read`.
*   **Detail**: See [naming-conventions.md](naming-conventions.md) for the canonical root verbs.

## 2. Vibhakti (विभक्ति) — Semantic Role Marking

Sanskrit and Tamil utilize rich case systems (vibhakti) where the grammatical role of a noun (agent, instrument, location, recipient) is explicitly marked, rather than relying solely on word order.

*   **Principle**: Code is read more often than written. The semantic role of arguments should be explicit at the call site.
*   **Application**: Agam enforces Named Arguments with semantic role labels for complex functions. Parameters carry their role (e.g., `from:`, `to:`, `using:`, `at:`).
*   **Example**:
    ```agam
    // Unclear roles based on position:
    memory.copy(src, dest, 1024) 
    
    // Explicit Vibhakti-style roles:
    memory.copy(from: src, to: dest, bytes: 1024)
    ```

## 3. Sandhi (सन्धि) — Type Junction Rules

Sandhi refers to the exact morphophonological rules that dictate how sounds change when they come together at a junction (e.g., a + i = e). 

*   **Principle**: The combination of types and modifiers must follow predictable, formally specified junction rules. No ad-hoc coercions or magic type flattening.
*   **Application**: Agam specifies a formal "Sandhi Table" for type composition. 
    *   `Optional<Optional<T>>` strictly evaluates to `Optional<T>`.
    *   Result types compose predictably via the `?` operator.
*   **Detail**: See [type-sandhi.md](type-sandhi.md).

## 4. Samāsa (समास) — Compound Type Formation

Sanskrit compound words follow canonical logical patterns. 

*   **Principle**: Type composition in Agam must map cleanly to these logical compound patterns, ensuring consistency in how traits, types, and annotations combine.
*   **Application**:
    *   **Dvandva (Coordinative)**: Combining equivalent traits (`Read + Write`).
    *   **Tatpuruṣa (Determinative)**: Generic specialization where the second element defines the first (`Parser<Json>`).
    *   **Bahuvrīhi (Possessive)**: Capability descriptions (`trait HasLength`).
    *   **Avyayībhāva (Adverbial)**: Modifier annotations that dictate behavior (`@inline`, `@gpu`).

## 5. Anuvṛtti (अनुवृत्ति) — Contextual Rule Inheritance

Pāṇini's grammar uses *anuvṛtti* to carry a rule forward from a previous sūtra to subsequent ones without restating it, compressing the grammar.

*   **Principle**: Reduce boilerplate through formally specified contextual inheritance.
*   **Application**: Agam uses anuvṛtti in block declarations. 
    *   Within an `impl T` block, `&self` inheritance is implied and carried forward unless explicitly overridden.
    *   A `pub mod` block carries the `pub` visibility to its immediate structural members by default.

## 6. Pratyāhāra (प्रत्याहार) — Constraint Shorthands

Pāṇini invented *pratyāhāra*, a system of categorical abbreviations where a short code represents an entire class of sounds.

*   **Principle**: Complex groups of trait bounds should be easily abbreviated to reduce signature noise and encourage generic programming.
*   **Application**: Agam introduces the `constraint` keyword to group trait bounds.
    ```agam
    // The pratyāhāra (shorthand):
    constraint Numeric = Add + Sub + Mul + Div + Ord;
    
    // Application:
    fn calculate<T: Numeric>(a: T, b: T) -> T
    ```

## 7. Oṭṭu (ஒட்டு) — Agglutinative Composition

Tamil is an agglutinative language, building complex meanings by stacking suffixes onto a root without fundamentally altering the root's core structure.

*   **Principle**: Data transformation pipelines should be cleanly stackable and non-destructive to the base container until a terminal operation is reached.
*   **Application**: Formally guaranteed fluent method chaining. Intermediate "suffixes" (e.g., `.filter()`, `.map()`) preserve the lazy iterator identity. Only terminal suffixes (e.g., `.collect()`) produce a new concrete memory layout.

---
*These principles act as the governing constitution for the Agam compiler's syntax and semantic validation rules.*
