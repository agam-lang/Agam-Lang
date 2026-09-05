---
name: cargo-lens
description: Compress cargo build/check/test output to errors and warnings only, saving tokens.
---

# cargo-lens

**Purpose**: Cargo dumps massive walls of text during compilation and testing. This skill enforces using the `scripts/cargo_lens.py` filter to extract only essential errors, warnings, and test summaries, cutting build output tokens by up to 90%.

## Usage

Always run cargo commands through the `cargo_lens.py` wrapper:

```powershell
# Fast check:
python scripts/cargo_lens.py check

# Run crate tests:
python scripts/cargo_lens.py test -p <crate_name>

# Run linter:
python scripts/cargo_lens.py clippy --all-targets -- -D warnings
```

**Strict Rule**: Never run raw `cargo check` or `cargo build` and dump 100+ lines of compiling noise into the conversation context.
