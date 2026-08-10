import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# عرض كل البيانات لنرى من الذي قام بالتسجيل
cursor.execute("SELECT name, status FROM guests WHERE status IS NOT NULL")
results = cursor.fetchall()

print("الردود المسجلة حالياً في قاعدة البيانات:")
for row in results:
    print(f"الصيدلاني: {row[0]} | الرد: {row[1]}")

conn.close()