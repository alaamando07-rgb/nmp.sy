from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import uuid

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
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
        
        name_col = columns[1] if len(columns) > 1 else columns[0]
        token_col = columns[2] if len(columns) > 2 else columns[0]
        status_col = columns[3] if len(columns) > 3 else None
        
        for c in columns:
            lc = c.lower()
            if 'name' in lc or 'اسم' in lc:
                name_col = c
            elif 'token' in lc or 'رابط' in lc or 'رمز' in lc or 'code' in lc:
                token_col = c
            elif 'status' in lc or 'حالة' in lc or 'رد' in lc:
                status_col = c

        if not token:
            if status_col:
                cursor.execute(f"SELECT rowid, [{name_col}], [{token_col}], [{status_col}] FROM [{table_name}]")
            else:
                cursor.execute(f"SELECT rowid, [{name_col}], [{token_col}] FROM [{table_name}]")
                
            raw_guests = cursor.fetchall()
            
            guests = []
            attending = 0
            declined = 0
            
            for row in raw_guests:
                name = row[name_col]
                guest_token = row[token_col]
                status = row[status_col] if status_col and row[status_col] else 'لم يجب'
                
                if status == 'سأحضر':
                    attending += 1
                elif status == 'أعتذر عن الحضور':
                    declined += 1
                    
                link = f"https://nmp-sy.onrender.com/?token={guest_token}"
                guests.append({
                    'id': row['rowid'],
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
        if status_col:
            cursor.execute(f"SELECT [{name_col}], [{token_col}], [{status_col}] FROM [{table_name}] WHERE [{token_col}] = ?", (token,))
        else:
            cursor.execute(f"SELECT [{name_col}], [{token_col}] FROM [{table_name}] WHERE [{token_col}] = ?", (token,))
            
        guest_data = cursor.fetchone()
        conn.close()
        
        if not guest_data:
            return "الرابط غير موجود أو تم حذفه."
        
        guest = {
            'name': guest_data[name_col],
            'token': guest_data[token_col],
            'status': guest_data[status_col] if status_col and guest_data[status_col] else 'لم يجب'
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
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_name = cursor.fetchone()['name']
            
            cursor.execute(f"PRAGMA table_info([{table_name}]);")
            columns = [col['name'] for col in cursor.fetchall()]
            name_col = columns[1] if len(columns) > 1 else columns[0]
            token_col = columns[2] if len(columns) > 2 else columns[0]
            status_col = columns[3] if len(columns) > 3 else None
            
            for c in columns:
                lc = c.lower()
                if 'name' in lc or 'اسم' in lc:
                    name_col = c
                elif 'token' in lc or 'رابط' in lc or 'رمز' in lc or 'code' in lc:
                    token_col = c
                elif 'status' in lc or 'حالة' in lc or 'رد' in lc:
                    status_col = c
            
            new_token = str(uuid.uuid4())[:8]
            if status_col:
                cursor.execute(f"INSERT INTO [{table_name}] ([{name_col}], [{token_col}], [{status_col}]) VALUES (?, ?, ?)", (name, new_token, 'لم يجب'))
            else:
                cursor.execute(f"INSERT INTO [{table_name}] ([{name_col}], [{token_col}]) VALUES (?, ?)", (name, new_token))
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
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_name = cursor.fetchone()['name']
            
            cursor.execute(f"PRAGMA table_info([{table_name}]);")
            columns = [col['name'] for col in cursor.fetchall()]
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_name = cursor.fetchone()['name']
        
        cursor.execute(f"PRAGMA table_info([{table_name}]);")
        columns = [col['name'] for col in cursor.fetchall()]
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

@app.route('/edit/<token>')
def edit_guest(token):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_name = cursor.fetchone()['name']
        
        cursor.execute(f"PRAGMA table_info([{table_name}]);")
        columns = [col['name'] for col in cursor.fetchall()]
        name_col = columns[1] if len(columns) > 1 else columns[0]
        token_col = columns[2] if len(columns) > 2 else columns[0]
        
        for c in columns:
            lc = c.lower()
            if 'name' in lc or 'اسم' in lc:
                name_col = c
            elif 'token' in lc or 'رابط' in lc or 'رمز' in lc or 'code' in lc:
                token_col = c
                
        cursor.execute(f"SELECT [{name_col}], [{token_col}] FROM [{table_name}] WHERE [{token_col}] = ?", (token,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return "الضيف غير موجود."
            
        guest = {'name': row[name_col], 'token': row[token_col]}
        return render_template('edit.html', guest=guest)
    except Exception as e:
        return f"خطأ: {str(e)}"

@app.route('/update', methods=['POST'])
def update_guest():
    token = request.form.get('token')
    new_name = request.form.get('name')
    
    if token and new_name:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            table_name = cursor.fetchone()['name']
            
            cursor.execute(f"PRAGMA table_info([{table_name}]);")
            columns = [col['name'] for col in cursor.fetchall()]
            name_col = columns[1] if len(columns) > 1 else columns[0]
            token_col = columns[2] if len(columns) > 2 else columns[0]
            
            for c in columns:
                lc = c.lower()
                if 'name' in lc or 'اسم' in lc:
                    name_col = c
                elif 'token' in lc or 'رابط' in lc or 'رمز' in lc or 'code' in lc:
                    token_col = c
                    
            cursor.execute(f"UPDATE [{table_name}] SET [{name_col}] = ? WHERE [{token_col}] = ?", (new_name, token))
            conn.commit()
            conn.close()
        except Exception:
            pass
            
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
