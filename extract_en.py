import re, json

with open('translations.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

d = {}
# Find all top level dictionary keys and their "en" string
matches = re.findall(r'"([a-z_A-Z0-9]+)":\s*\{[^\}]*?"en":\s*"([^"]+)"', text)
for k, v in matches:
    d[k] = {'en': v}

with open('clean_translations.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=4)
print(f"Extracted {len(d)} English keys")
