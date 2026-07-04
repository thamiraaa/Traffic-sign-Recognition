import marshal

with open('__pycache__/translations.cpython-314.pyc', 'rb') as f:
    f.read(16) # Skip header (16 bytes in python 3)
    code = marshal.load(f)

for c in code.co_consts:
    if isinstance(c, tuple): # Sometimes it's a tuple of consts
        for item in c:
            if isinstance(item, str) and len(item) > 3:
                print(item.encode('utf-8', 'ignore'))
    elif isinstance(c, str) and len(c) > 3:
        pass # print(c)

print("\n\nAll string constants:")
strings = [c for c in code.co_consts if isinstance(c, str)]
print(strings[:100])
