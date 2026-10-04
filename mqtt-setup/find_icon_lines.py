path = r"d:\Proyek Penetas Telur\TernakTelur-Web\js\dashboard.js"
with open(path, encoding='utf-8') as f:
    content = f.read()

# Show all lines that still reference locationSVG or speciesSVG in TABLE contexts
lines = content.split('\n')
for i, line in enumerate(lines, 1):
    if 'locationSVG' in line or 'speciesSVG' in line:
        print(f"Line {i}: {repr(line[:100])}")
