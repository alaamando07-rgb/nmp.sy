import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("SELECT name, token FROM guests")
guests = cursor.fetchall()

print("إليك روابط الضيوف جاهزة:")
for name, token in guests:
    # رابط الاستضافة السحابية المحدث
    link = f"https://nmp-sy.onrender.com/?token={token}"
    print(f"الضيف: {name} | الرابط: {link}")

conn.close()
