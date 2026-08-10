from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

@app.route('/')
def home():
    token = request.args.get('token')
    
    # التأكد من وجود ملف قاعدة البيانات
    if not os.path.exists('database.db'):
        return "خطأ: ملف قاعدة البيانات غير موجود على السيرفر! يرجى رفعه."
    
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        if not token:
            # عرض لوحة الأدمن
            cursor.execute("SELECT name, token, status FROM guests")
            raw_guests = cursor.fetchall()
            
            guests = []
            for row in raw_guests:
                name = row[0]
                guest_token = row[1]
                status = row[2] if len(row) > 2 else 'لم يجب'
                link = f"https://nmp-sy.onrender.com/?token={guest_token}"
                guests.append((name, guest_token, status, link))
            
            cursor.execute("SELECT COUNT(*) FROM guests")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM guests WHERE status = 'سأحضر'")
            attending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM guests WHERE status = 'أعتذر عن الحضور'")
            declined = cursor.fetchone()[0]
            
            pending = total - (attending + declined)
            conn.close()
            
            return render_template('admin.html', guests=guests, total=total, attending=attending, declined=declined, pending=pending)
        
        # عرض بطاقة الضيف الفردية
        cursor.execute("SELECT name, token, status FROM guests WHERE token = ?", (token,))
        guest_data = cursor.fetchone()
        conn.close()
        
        if not guest_data:
            return "الرابط غير موجود أو تم حذفه."
        
        guest = {
            'name': guest_data[0],
            'token': guest_data[1],
            'status': guest_data[2] if len(guest_data) > 2 else 'لم يجب'
        }
        
        if guest['status'] in ['سأحضر', 'أعتذر عن الحضور']:
            return render_template('thankyou.html', guest=guest, already_voted=True)
        
        return render_template('card.html', guest=guest)
        
    except Exception as e:
        return f"حدث خطأ في قاعدة البيانات أو النظام: {str(e)}"

@app.route('/submit', methods=['POST'])
def submit():
    token = request.form.get('token')
    attendance = request.form.get('attendance')
    
    if token and attendance:
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT status FROM guests WHERE token = ?", (token,))
            current_status = cursor.fetchone()
            
            if current_status and (not current_status[0] or current_status[0] == 'لم يجب'):
                cursor.execute("UPDATE guests SET status = ? WHERE token = ?", (attendance, token))
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
        cursor.execute("UPDATE guests SET status = 'لم يجب' WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
