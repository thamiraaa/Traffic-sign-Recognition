import re
text = open('translations.py','rb').read().decode('latin-1')
matches = re.findall(r'    "([a-z][a-z_0-9]+)":\s*\{', text)
for m in matches:
    print(m)
