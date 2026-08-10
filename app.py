from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

@app.route('/')
def home():
    token = request.args.get('token')
    
    if not os.path.exists('database.db'):
        return "خطأ: ملف قاعدة البيانات غير موجود على السيرفر."
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # جلب اسم الجدول الأول في قاعدة البيانات تلقائياً
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if not tables:
            return "قاعدة البيانات فارغة من الجداول."
        table_name = tables[0][0]
        
        # جلب أسماء الأعمدة الحقيقية في الجدول
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in cursor.fetchall()]
        
        # ضمان اختيار أعمدة سليمة 100% لتجنب انهيار الاستعلام
        name_col = columns[1] if len(columns) > 1 else columns[0]
        token_col = columns[2] if len(columns) > 2 else columns[0]
        status_col = columns[3] if len(columns) > 3 else (columns[2] if len(columns) > 2 else None)
        
        # البحث المخصص إذا كانت أسماء الأعمدة تحتوي على الكلمات الدلالية
        for c in columns:
            lc = c.lower()
            if 'name' in lc or 'اسم' in lc:
                name_col = c
            elif 'token' in lc or 'رابط' in lc or 'رمز' in lc or 'code' in lc:
                token_col = c
            elif 'status' in lc or 'حالة' in lc or 'رد' in lc:
                status_col = c

        if not token:
            # جلب البيانات بالأسماء المكتشفة
            if status_col:
                cursor.execute(f"SELECT [{name_col}], [{token_col}], [{status_col}] FROM [{table_name}]")
            else:
                cursor.execute(f"SELECT [{name_col}], [{token_col}] FROM [{table_name}]")
                
            raw_guests = cursor.fetchall()
            
            guests = []
            attending = 0
            declined = 0
            
            for row in raw_guests:
                name = row[0]
                guest_token = row[1]
                status = row[2] if len(row) > 2 and row[2] else 'لم يجب'
                
                if status == 'سأحضر':
                    attending += 1
                elif status == 'أعتذر عن الحضور':
                    declined += 1
                    
                link = f"https://nmp-sy.onrender.com/?token={guest_token}"
                guests.append((name, guest_token, status, link))
            
            total = len(guests)
            pending = total - (attending + declined)
            conn.close()
            
            return render_template('admin.html', guests=guests, total=total, attending=attending, declined=declined, pending=pending)
        
        # عرض بطاقة الضيف الفردية
        if status_col:
            cursor.execute(f"SELECT [{name_col}], [{token_col}], [{status_col}] FROM [{table_name}] WHERE [{token_col}] = ?", (token,))
        else:
            cursor.execute(f"SELECT [{name_col}], [{token_col}] FROM [{table_name}] WHERE [{token_col}] = ?", (token,))
            
        guest_data = cursor.fetchone()
        conn.close()
        
        if not guest_data:
            return "الرابط غير موجود أو تم حذفه."
        
        guest = {
            'name': guest_data[0],
            'token': guest_data[1],
            'status': guest_data[2] if len(guest_data) > 2 and guest_data[2] else 'لم يجب'
        }
        
        if guest['status'] in ['سأحضر', 'أعتذر عن الحضور']:
            return render_template('thankyou.html', guest=guest, already_voted=True)
        
        return render_template('card.html', guest=guest)
        
    except Exception as e:
        return f"خطأ في التنفيذ: {str(e)}"

@app.route('/submit', methods=['POST'])
def submit():
    token = request.form.get('token')
    attendance = request.form.get('attendance')
    
    if token and attendance:
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_name = cursor.fetchone()[0]
            
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [col[1] for col in cursor.fetchall()]
            token_col = columns[2] if len(columns) > 2 else columns[0]
            status_col = columns[3] if len(columns) > 3 else None
            
            for c in columns:
                lc = c.lower()
                if 'token' in lc or 'رابط' in lc or 'رمز' in lc or 'code' in lc:
                    token_col = c
                elif 'status' in lc or 'حالة' in lc or 'رد' in lc:
                    status_col = c
            
            if status_col:
                cursor.execute(f"UPDATE [{table_name}] SET [{status_col}] = ? WHERE [{token_col}] = ?", (attendance, token))
                conn.commit()
                
            conn.close()
        except Exception:
            pass
    
    return render_template('thankyou.html', already_voted=False)

@app.route('/reset/<token>')
def reset_vote(token):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_name = cursor.fetchone()[0]
        
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in cursor.fetchall()]
        token_col = columns[2] if len(columns) > 2 else columns[0]
        status_col = columns[3] if len(columns) > 3 else None
        
        for c in columns:
            lc = c.lower()
            if 'token' in lc or 'رابط' in lc or 'رمز' in lc or 'code' in lc:
                token_col = c
            elif 'status' in lc or 'حالة' in lc or 'رد' in lc:
                status_col = c
        
        if status_col:
            cursor.execute(f"UPDATE [{table_name}] SET [{status_col}] = 'لم يجب' WHERE [{token_col}] = ?", (token,))
            conn.commit()
            
        conn.close()
    except Exception:
        pass
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
