from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import uuid

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'لم يجب',
            location TEXT DEFAULT 'حمص نادي الأطباء والمهندسين',
            date TEXT DEFAULT 'يوم الاثنين 24/8/2026',
            time TEXT DEFAULT 'الساعة 3:00 ظهراً'
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    init_db()
    token = request.args.get('token')
    
    if not os.path.exists('database.db'):
        return "خطأ: ملف قاعدة البيانات غير موجود على السيرفر."
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        if not tables:
            return "قاعدة البيانات فارغة من الجداول."
        table_name = tables[0]['name']
        
        cursor.execute(f"PRAGMA table_info([{table_name}]);")
        columns = [col['name'] for col in cursor.fetchall()]
        
        if 'location' not in columns:
            cursor.execute(f"ALTER TABLE [{table_name}] ADD COLUMN location TEXT DEFAULT 'حمص نادي الأطباء والمهندسين'")
            cursor.execute(f"ALTER TABLE [{table_name}] ADD COLUMN date TEXT DEFAULT 'يوم الاثنين 24/8/2026'")
            cursor.execute(f"ALTER TABLE [{table_name}] ADD COLUMN time TEXT DEFAULT 'الساعة 3:00 ظهراً'")
            conn.commit()

        if not token:
            cursor.execute(f"SELECT * FROM [{table_name}]")
            raw_guests = cursor.fetchall()
            
            guests = []
            attending = 0
            declined = 0
            
            for row in raw_guests:
                # قراءة البيانات بأمان تام لتجنب أي خطأ في المفاتيح
                row_keys = row.keys()
                name_k = 'name' if 'name' in row_keys else list(row_keys)[1]
                token_k = 'token' if 'token' in row_keys else list(row_keys)[2]
                status_k = 'status' if 'status' in row_keys else (list(row_keys)[3] if len(row_keys) > 3 else None)
                
                name = row[name_k]
                guest_token = row[token_k]
                status = row[status_k] if status_k and row[status_k] else 'لم يجب'
                
                if status == 'سأحضر':
                    attending += 1
                elif status == 'أعتذر عن الحضور':
                    declined += 1
                    
                link = f"https://nmp-sy.onrender.com/?token={guest_token}"
                guests.append({
                    'name': name,
                    'token': guest_token,
                    'status': status,
                    'link': link
                })
            
            total = len(guests)
            pending = total - (attending + declined)
            conn.close()
            
            return render_template('admin.html', guests=guests, total=total, attending=attending, declined=declined, pending=pending)
        
        # عرض بطاقة الضيف
        cursor.execute(f"SELECT * FROM [{table_name}] WHERE token = ?", (token,))
        guest_data = cursor.fetchone()
        conn.close()
        
        if not guest_data:
            return "الرابط غير موجود أو تم حذفه."
        
        row_keys = guest_data.keys()
        name_k = 'name' if 'name' in row_keys else list(row_keys)[1]
        token_k = 'token' if 'token' in row_keys else list(row_keys)[2]
        status_k = 'status' if 'status' in row_keys else (list(row_keys)[3] if len(row_keys) > 3 else None)
        loc_k = 'location' if 'location' in row_keys else 'حمص نادي الأطباء والمهندسين'
        date_k = 'date' if 'date' in row_keys else 'يوم الاثنين 24/8/2026'
        time_k = 'time' if 'time' in row_keys else 'الساعة 3:00 ظهراً'
        
        guest = {
            'name': guest_data[name_k],
            'token': guest_data[token_k],
            'status': guest_data[status_k] if status_k and guest_data[status_k] else 'لم يجب',
            'location': guest_data[loc_k] if 'location' in row_keys and guest_data[loc_k] else 'حمص نادي الأطباء والمهندسين',
            'date': guest_data[date_k] if 'date' in row_keys and guest_data[date_k] else 'يوم الاثنين 24/8/2026',
            'time': guest_data[time_k] if 'time' in row_keys and guest_data[time_k] else 'الساعة 3:00 ظهراً'
        }
        
        if guest['status'] in ['سأحضر', 'أعتذر عن الحضور']:
            return render_template('thankyou.html', guest=guest, already_voted=True)
        
        return render_template('card.html', guest=guest)
        
    except Exception as e:
        import traceback
        return f"<pre>{traceback.format_exc()}</pre>"

@app.route('/add', methods=['POST'])
def add_guest():
    name = request.form.get('name')
    if name:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            new_token = str(uuid.uuid4())[:8]
            cursor.execute("INSERT INTO guests (name, token, status, location, date, time) VALUES (?, ?, ?, ?, ?, ?)",
                           (name, new_token, 'لم يجب', 'حمص نادي الأطباء والمهندسين', 'يوم الاثنين 24/8/2026', 'الساعة 3:00 ظهراً'))
            conn.commit()
            conn.close()
        except Exception:
            pass
    return redirect(url_for('home'))

@app.route('/submit', methods=['POST'])
def submit():
    token = request.form.get('token')
    attendance = request.form.get('attendance')
    
    if token and attendance:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE guests SET status = ? WHERE token = ?", (attendance, token))
            conn.commit()
            conn.close()
        except Exception:
            pass
    
    return render_template('thankyou.html', already_voted=False)

@app.route('/reset/<token>')
def reset_vote(token):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE guests SET status = 'لم يجب' WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return redirect(url_for('home'))

@app.route('/edit/<token>')
def edit_guest(token):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM guests WHERE token = ?", (token,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return "الضيف غير موجود."
            
        row_keys = row.keys()
        guest = {
            'name': row['name'] if 'name' in row_keys else row[1],
            'token': row['token'] if 'token' in row_keys else row[2],
            'location': row['location'] if 'location' in row_keys and row['location'] else 'حمص نادي الأطباء والمهندسين',
            'date': row['date'] if 'date' in row_keys and row['date'] else 'يوم الاثنين 24/8/2026',
            'time': row['time'] if 'time' in row_keys and row['time'] else 'الساعة 3:00 ظهراً'
        }
        return render_template('edit.html', guest=guest)
    except Exception as e:
        return f"خطأ: {str(e)}"

@app.route('/update', methods=['POST'])
def update_guest():
    token = request.form.get('token')
    name = request.form.get('name')
    location = request.form.get('location')
    date = request.form.get('date')
    time = request.form.get('time')
    
    if token and name:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE guests SET name = ?, location = ?, date = ?, time = ? WHERE token = ?",
                           (name, location, date, time, token))
            conn.commit()
            conn.close()
        except Exception:
            pass
            
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
