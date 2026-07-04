import marshal
import struct

with open('__pycache__/translations.cpython-314.pyc', 'rb') as f:
    magic = f.read(4)
    bitfield = f.read(4)
    mtime = f.read(4)
    size = f.read(4)
    code = marshal.load(f)

# code.co_consts will contain the UI_TEXT dictionary
for const in code.co_consts:
    if isinstance(const, dict):
        if 'category_cash' in const:
            print("Found UI_TEXT dict!")
            import json
            with open('recovered_translations.json', 'w', encoding='utf-8') as out:
                json.dump(const, out, indent=2, ensure_ascii=False)
            print("Recovered to recovered_translations.json")
            break
