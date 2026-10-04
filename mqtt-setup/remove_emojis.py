import os

html_path = r"d:\Proyek Penetas Telur\TernakTelur-Web\dashboard.html"
js_path = r"d:\Proyek Penetas Telur\TernakTelur-Web\js\dashboard.js"

with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace HTML emojis
html = html.replace('📊 Overview Dashboard', 'Overview Dashboard')
html = html.replace('>👤<', '><')
html = html.replace('>🥚<', '><')
html = html.replace('>⭐<', '><')
html = html.replace('>📡<', '><')
html = html.replace('>🐔 Ayam<', '>Ayam<')
html = html.replace('>🥚 Puyuh<', '>Puyuh<')
html = html.replace('>🦆 Bebek<', '>Bebek<')
html = html.replace('>🦢 Angsa<', '>Angsa<')
html = html.replace('>🦃 Kalkun<', '>Kalkun<')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace JS emojis
js = js.replace("'🐔 Ayam', '🥚 Puyuh', '🦆 Bebek', '🦢 Angsa', '🦃 Kalkun'", "'Ayam', 'Puyuh', 'Bebek', 'Angsa', 'Kalkun'")
js = js.replace("{ Ayam:'🐔', Puyuh:'🥚', Bebek:'🦆', Angsa:'🦢', Kalkun:'🦃' }", "{ Ayam:'', Puyuh:'', Bebek:'', Angsa:'', Kalkun:'' }")
js = js.replace("|| '🥚'} ", "|| ''} ")
js = js.replace("${speciesEmoji[inc.species]} ", "")
js = js.replace("'📊 Overview Dashboard'", "'Overview Dashboard'")
js = js.replace("'👤 Data Peternak'", "'Data Peternak'")
js = js.replace("'🟢 Inkubator Live'", "'Inkubator Live'")
js = js.replace("'📈 Statistik & Analitik'", "'Statistik & Analitik'")

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Emojis removed locally.")
