from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import uuid
import os

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
    # التأكد من وجود الأعمدة حتى لو كانت قاعدة البيانات قديمة
    cursor.execute("PRAGMA table_info(guests)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'location' not in columns:
        cursor.execute("ALTER TABLE guests ADD COLUMN location TEXT DEFAULT 'حمص نادي الأطباء والمهندسين'")
    if 'date' not in columns:
        cursor.execute("ALTER TABLE guests ADD COLUMN date TEXT DEFAULT 'يوم الاثنين 24/8/2026'")
    if 'time' not in columns:
        cursor.execute("ALTER TABLE guests ADD COLUMN time TEXT DEFAULT 'الساعة 3:00 ظهراً'")
    conn.commit()
    conn.close()

@app.route('/')
def home():
    init_db()
    token = request.args.get('token')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not token:
        cursor.execute("SELECT * FROM guests")
        raw_guests = cursor.fetchall()
        
        guests = []
        attending = 0
        declined = 0
        
        for row in raw_guests:
            status = row['status'] if 'status' in row.keys() and row['status'] else 'لم يجب'
            if status == 'سأحضر':
                attending += 1
            elif status == 'أعتذر عن الحضور':
                declined += 1
                
            link = f"https://nmp-sy.onrender.com/?token={row['token']}"
            guests.append({
                'name': row['name'],
                'token': row['token'],
                'status': status,
                'link': link
            })
        
        total = len(guests)
        pending = total - (attending + declined)
        conn.close()
        
        return render_template('admin.html', guests=guests, total=total, attending=attending, declined=declined, pending=pending)
    
    cursor.execute("SELECT * FROM guests WHERE token = ?", (token,))
    guest = cursor.fetchone()
    conn.close()
    
    if not guest:
        return "الرابط غير موجود أو تم حذفه."
        
    guest_data = {
        'name': guest['name'],
        'token': guest['token'],
        'status': guest['status'] if 'status' in guest.keys() and guest['status'] else 'لم يجب',
        'location': guest['location'] if 'location' in guest.keys() and guest['location'] else 'حمص نادي الأطباء والمهندسين',
        'date': guest['date'] if 'date' in guest.keys() and guest['date'] else 'يوم الاثنين 24/8/2026',
        'time': guest['time'] if 'time' in guest.keys() and guest['time'] else 'الساعة 3:00 ظهراً'
    }
    
    if guest_data['status'] in ['سأحضر', 'أعتذر عن الحضور']:
        return render_template('thankyou.html', guest=guest_data, already_voted=True)
    
    return render_template('card.html', guest=guest_data)

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
        except Exception as e:
            print(f"Error adding guest: {e}")
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
        except Exception as e:
            print(f"Error submitting: {e}")
    
    return render_template('thankyou.html', already_voted=False)

@app.route('/reset/<token>')
def reset_vote(token):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE guests SET status = 'لم يجب' WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error resetting: {e}")
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
            
        guest = {
            'name': row['name'],
            'token': row['token'],
            'location': row['location'] if 'location' in row.keys() and row['location'] else 'حمص نادي الأطباء والمهندسين',
            'date': row['date'] if 'date' in row.keys() and row['date'] else 'يوم الاثنين 24/8/2026',
            'time': row['time'] if 'time' in row.keys() and row['time'] else 'الساعة 3:00 ظهراً'
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
        except Exception as e:
            print(f"Error updating: {e}")
            
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
