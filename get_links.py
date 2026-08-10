import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT name, token FROM guests")
guests = cursor.fetchall()

print("إليك روابط الضيوف جاهزة:")
for name, token in guests:
    # هذا الرابط هو الذي ستحوله إلى QR Code
    link = f"http://127.0.0.1:5000/?token={token}"
    print(f"الضيف: {name} | الرابط: {link}")

conn.close()