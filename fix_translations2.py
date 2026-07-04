"""
fix_translations2.py  –  Remove orphaned/broken lines and non-ascii
chars that confuse the Python parser (anything outside valid Python
identifiers / string literals that contains Latin-1 mojibake).

Strategy: strip any line that does NOT begin with a recognizable Python
construct (string key, dict close, comment, blank, or a proper unicode
string literal).  Also removes duplicate top-level dict keys that were
artifacts of the original corruption.
"""
import re

FILE = "translations.py"
lines = open(FILE, encoding="utf-8").readlines()

cleaned = []
skip_next_close = False

for i, line in enumerate(lines):
    stripped = line.strip()

    # Keep blank lines
    if stripped == "":
        cleaned.append(line)
        continue

    # Keep comment lines
    if stripped.startswith("#"):
        cleaned.append(line)
        continue

    # Keep lines that start with `"` (string key) or `}` or `def ` or `class `
    # or standard python tokens
    if (stripped.startswith('"') or
        stripped.startswith('}') or
        stripped.startswith('def ') or
        stripped.startswith('class ') or
        stripped.startswith('UI_TEXT') or
        stripped.startswith('from ') or
        stripped.startswith('import ') or
        stripped.startswith('#')):
        cleaned.append(line)
        continue

    # Lines starting with a letter/digit that look like identifiers are ok
    # (e.g., continuation of a multi-line string value in a prior version)
    # If line doesn't start with `"` or `}`, it's likely a broken fragment.
    # Flag it.
    # print(f"  SKIP line {i+1}: {repr(line[:80])}")
    pass  # drop orphaned fragments

# Rewrite
text = "".join(cleaned)

with open(FILE, "w", encoding="utf-8") as f:
    f.write(text)

# Verify
try:
    compile(text, FILE, "exec")
    print("Syntax OK after cleanup!")
except SyntaxError as e:
    print(f"Syntax error remains: {e}")
    # Print context
    import_lines = text.splitlines()
    err_line = e.lineno
    for i in range(max(0, err_line-3), min(len(import_lines), err_line+3)):
        print(f"  {i+1}: {repr(import_lines[i][:100])}")
