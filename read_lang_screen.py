import sys
sys.stdout = open('lang_screen_out.txt', 'w', encoding='utf-8')
text = open('main.py','rb').read().decode('latin-1')
start = text.find('class LanguageScreen')
end = text.find('class CoinScreen')
print(text[start:end])
sys.stdout.close()
