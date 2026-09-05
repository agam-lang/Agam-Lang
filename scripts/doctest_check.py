#!/usr/bin/env python3
"""
Doctest Guard for Agam-Lang.
Extracts code snippets marked with ```agam or ```agamc from documentation markdown files,
executes them against agamc.exe, and reports pass/fail status.
"""

import os
import re
import sys
import tempfile
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
AGAMC_BIN = ROOT_DIR / "agam" / "target" / "release" / "agamc.exe"
DOCS_DIR = ROOT_DIR / "docs"

CODE_BLOCK_REGEX = re.compile(r"```(?:agam|agamc)\s*\n(.*?)```", re.DOTALL)

def find_markdown_files():
    files = []
    if DOCS_DIR.exists():
        files.extend(list(DOCS_DIR.rglob("*.md")))
    readme = ROOT_DIR / "README.md"
    if readme.exists():
        files.append(readme)
    return files

def run_cmd(cmd, cwd):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15
    )
    return result.returncode, result.stdout, result.stderr

def test_snippet(snippet: str, source_file: Path, block_num: int, backend_directive: str):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_agam = Path(tmpdir) / f"doctest_{block_num}.agam"
        tmp_agam.write_text(snippet, encoding="utf-8")

        # Test JIT if not llvm-only
        if backend_directive != "llvm-only":
            code, stdout, stderr = run_cmd([str(AGAMC_BIN), "run", str(tmp_agam)], cwd=ROOT_DIR)
            if code != 0:
                return False, f"JIT error: {stderr.strip() or stdout.strip()}"

        # Test LLVM if not jit-only
        if backend_directive != "jit-only":
            code, stdout, stderr = run_cmd([str(AGAMC_BIN), "build", "--backend", "llvm", str(tmp_agam)], cwd=ROOT_DIR)
            if code != 0:
                return False, f"LLVM lowering error: {stderr.strip() or stdout.strip()}"

    return True, "OK"

def main():
    if not AGAMC_BIN.exists():
        print(f"[ERROR] agamc executable not found at: {AGAMC_BIN}")
        sys.exit(1)

    md_files = find_markdown_files()
    total_snippets = 0
    passed_snippets = 0
    failed_snippets = []
    skipped_snippets = 0

    print(f"=== Agam Doctest Guard: Scanning {len(md_files)} markdown files ===")

    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            continue

        lines = content.splitlines()
        in_code_block = False
        current_block = []
        directive = "both"
        block_count = 0
        start_line = 0

        for line_idx, line in enumerate(lines, 1):
            if not in_code_block:
                if line.strip().startswith("```agam") or line.strip().startswith("```agamc"):
                    in_code_block = True
                    start_line = line_idx
                    current_block = []
                    # Check preceding line for directive
                    if line_idx > 1:
                        prev = lines[line_idx - 2].strip()
                        if "<!-- SKIP-DOCTEST -->" in prev or "<!-- doctest:skip -->" in prev:
                            directive = "skip"
                        elif "<!-- BACKEND: llvm-only -->" in prev:
                            directive = "llvm-only"
                        elif "<!-- BACKEND: jit-only -->" in prev:
                            directive = "jit-only"
                        else:
                            directive = "both"
                    else:
                        directive = "both"
            else:
                if line.strip().startswith("```"):
                    in_code_block = False
                    block_count += 1
                    snippet_code = "\n".join(current_block).strip()
                    
                    if not snippet_code or directive == "skip":
                        skipped_snippets += 1
                        continue

                    # If snippet does not have fn main, wrap or skip if fragment
                    if "fn main" not in snippet_code:
                        skipped_snippets += 1
                        continue

                    total_snippets += 1
                    rel_path = md_file.relative_to(ROOT_DIR)
                    ok, msg = test_snippet(snippet_code, md_file, block_count, directive)
                    if ok:
                        passed_snippets += 1
                        print(f"  [PASS] {rel_path}:{start_line} (Block {block_count})")
                    else:
                        failed_snippets.append((rel_path, start_line, msg))
                        print(f"  [FAIL] {rel_path}:{start_line} (Block {block_count}) -> {msg}")
                else:
                    current_block.append(line)

    print(f"\nSummary: {passed_snippets}/{total_snippets} tested snippets passed ({skipped_snippets} skipped fragments).")
    if failed_snippets:
        print(f"\n[FAILURES DETECTED: {len(failed_snippets)}]")
        for fpath, lnum, reason in failed_snippets:
            print(f"  - {fpath}:{lnum} -> {reason}")
        sys.exit(1)
    else:
        print("[SUCCESS] All verifiable documentation snippets passed dual-backend checks!")
        sys.exit(0)

if __name__ == "__main__":
    main()
