"""
fix_translations.py  –  Remove control characters that cause SyntaxError
Reads translations.py as UTF-8, strips C1 control chars (U+0080..U+009F),
and rewrites the file.
"""
import re

FILE = "translations.py"
text = open(FILE, encoding="utf-8").read()

before = len(text)
# Remove C0/C1 control characters except tab (\x09), newline (\x0A), carriage return (\x0D)
cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
after = len(cleaned)

with open(FILE, "w", encoding="utf-8") as f:
    f.write(cleaned)

print(f"Removed {before - after} control characters. File rewritten as UTF-8.")

# Verify it parses
try:
    compile(cleaned, FILE, "exec")
    print("Syntax OK!")
except SyntaxError as e:
    print(f"Still has syntax error: {e}")
