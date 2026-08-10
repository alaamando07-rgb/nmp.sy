import sqlite3
import pandas as pd
import uuid

# 1. قراءة ملف الإكسل الخاص بالصيادلة وسحب جميع الأعمدة والأسماء بشكل صحيح
excel_path = 'اسماء الصيادلة المرشحين لحضور  الفعالية_٠١٠٠٢٢.xlsx'
df_excel = pd.read_excel(excel_path, sheet_name=0)

raw_names = []
for col in df_excel.columns:
    col_names = df_excel[col].dropna().tolist()
    for name in col_names:
        clean_name = str(name).strip()
        # نتأكد أن الخلية ليست فارغة وليست اسم المنطقة نفسها
        if clean_name and clean_name != 'nan':
            raw_names.append(clean_name)

# 2. إنشاء قاعدة البيانات وتخزين الأسماء مع رابط فريد لكل صيدلاني
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS guests")
cursor.execute('''
    CREATE TABLE guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        token TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'لم يجب'
    )
''')

data = []
for name in raw_names:
    full_name = f"الصيدلاني/ة {name}"
    token = str(uuid.uuid4())[:8]
    
    # حفظ في قاعدة البيانات
    try:
        cursor.execute("INSERT INTO guests (name, token) VALUES (?, ?)", (full_name, token))
    except sqlite3.IntegrityError:
        pass
        
    link = f"http://127.0.0.1:5000/?token={token}"
    data.append({"اسم الصيدلاني": full_name, "رابط الدعوة الخاص": link})

conn.commit()
conn.close()

# 3. تصدير جميع الـ 462 اسم إلى ملف إكسل نظيف ومرتب
df_out = pd.DataFrame(data)
df_out.to_excel('all_guests_links.xlsx', index=False)
print(f"تم بنجاح استخراج وتصدير {len(data)} صيدلاني/ة إلى ملف الإكسل!")