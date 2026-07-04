import json
import google.generativeai as genai
import config
import time
from google.api_core import exceptions

def fix_rupee(text):
    return text.replace("(\u00e2\u00b9)", "(₹)").replace("\u00e2\u00b9", "₹").replace("â¹", "₹").replace("â‚¹", "₹")

with open('clean_translations.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# Fix english texts
for k, v in d.items():
    if "en" in v:
        v["en"] = fix_rupee(v["en"]).replace("", "") # strip unknown chars

genai.configure(api_key=config.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash") # Use 2.5 flash

keys_to_translate = [k for k, v in d.items() if len(v) == 1 and "en" in v]
print(f"Keys left to translate: {len(keys_to_translate)}")

batch_size = 15
for i in range(0, len(keys_to_translate), batch_size):
    batch = keys_to_translate[i:i+batch_size]
    text_map = {k: d[k]["en"] for k in batch}
    
    prompt = f"""
Translate the following UI texts into Tamil (ta), Hindi (hi), Telugu (te), Kannada (kn), and Malayalam (ml).
Return a JSON object where each key maps to a dictionary of language codes and their translations.
Keep any emojis intact.

Texts to translate:
{json.dumps(text_map, indent=2, ensure_ascii=False)}

Expected JSON format:
{{
  "key1": {{"ta": "...", "hi": "...", "te": "...", "kn": "...", "ml": "..."}}
}}
Return ONLY the raw JSON object, without any markdown formatting.
"""
    
    success = False
    retries = 3
    while not success and retries > 0:
        try:
            response = model.generate_content(prompt)
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            translated = json.loads(text)
            
            for k, langs in translated.items():
                if k in d:
                    for lang_code, t_text in langs.items():
                        d[k][lang_code] = t_text
            print(f"Translated batch {i//batch_size + 1}/{len(keys_to_translate)//batch_size + 1}")
            success = True
            time.sleep(2) # Prevent slamming the API
        except exceptions.ResourceExhausted as e:
            print(f"Rate limit hit on batch {i//batch_size + 1}, waiting 35s...")
            time.sleep(35)
            retries -= 1
        except Exception as e:
            print(f"Failed batch {i//batch_size + 1}: {e}")
            break

out = [
    "# translations.py",
    "# Auto-generated clean UI translation dictionary for all supported languages.",
    "UI_TEXT = {"
]

for k, langs in d.items():
    out.append(f'    "{k}": {{')
    for lang, val in langs.items():
        val = val.replace('"', '\\"').replace('\n', '\\n')
        out.append(f'        "{lang}": "{val}",')
    out.append("    },")

out.append("}")
out.append("")
out.append("def t(key: str, lang: str = 'en') -> str:")
out.append('    """Helper function to fetch translated UI text."""')
out.append('    if key not in UI_TEXT:')
out.append('        return key')
out.append('    return UI_TEXT[key].get(lang, UI_TEXT[key].get("en", key))')
out.append("")

with open("translations.py", "w", encoding="utf-8") as f:
    f.write("\n".join(out))

with open("clean_translations.json", "w", encoding="utf-8") as f:
    json.dump(d, f, indent=4)

print("Created translations.py with full multilingual support!")
