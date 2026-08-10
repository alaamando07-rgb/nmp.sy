import sqlite3
import uuid

guests_list = [
    "الدكتور حسين حريري", 
    "الدكتور محمد فارس الرحال", 
    "الدكتورة مرح علوش"
]

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        token TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'لم يجب'
    )
''')

for name in guests_list:
    token = str(uuid.uuid4())[:8]
    try:
        cursor.execute("INSERT INTO guests (name, token) VALUES (?, ?)", (name, token))
    except sqlite3.IntegrityError:
        pass

conn.commit()
conn.close()
print("تمت إضافة الأسماء بنجاح!")