import re, os

def remove_emojis(text):
    # Pola regex untuk mendeteksi berbagai jenis emoji
    # Menghapus karakter di luar rentang ASCII dasar dan latin, kecuali untuk beberapa simbol dasar
    # Lebih amannya kita list manual emoji yang muncul:
    emojis = ['📊', '👤', '🥚', '⭐', '📡', '🐔', '🦆', '🦢', '🦃', '📍', '🟢', '📈', '✨', '⚡', '🔥', '🚀', '👇', '🐣', '✅', '❌', '💡']
    for emoji in emojis:
        text = text.replace(emoji, '')
    
    # Perbaikan khusus untuk JS fallback
    text = text.replace("|| '🥚'", "|| ''")
    text = text.replace("|| ' '", "|| ''")
    return text

dir_path = r"d:\Proyek Penetas Telur\TernakTelur-Web"
files_to_check = [
    os.path.join(dir_path, "dashboard.html"),
    os.path.join(dir_path, "index.html"),
    os.path.join(dir_path, "js", "dashboard.js"),
    os.path.join(dir_path, "js", "main.js"),
]

for fp in files_to_check:
    if os.path.exists(fp):
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Coba regex emoji standard
        # Hapus semua karakter emoji Unicode
        try:
            import emoji
            content = emoji.replace_emoji(content, replace='')
        except ImportError:
            pass # akan pakai manual list

        content = remove_emojis(content)
        
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)

print("Local emojis removed!")
