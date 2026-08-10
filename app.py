from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# 1. جعل لوحة التحكم هي الصفحة الأساسية التي تفتح فوراً على رابط الموقع الرئيسي
@app.route('/')
def admin_dashboard():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, token, status FROM guests")
    raw_guests = cursor.fetchall()
    
    # توليد الرابط الخاص بكل صيدلاني ليوجهه لصفحة الدعوة مع التوكن الخاص به
    guests = []
    for name, token, status in raw_guests:
        link = f"https://nmp-sy.onrender.com/invite?token={token}"
        guests.append((name, token, status, link))
    
    cursor.execute("SELECT COUNT(*) FROM guests")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM guests WHERE status = 'سأحضر'")
    attending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM guests WHERE status = 'أعتذر عن الحضور'")
    declined = cursor.fetchone()[0]
    
    pending = total - (attending + declined)
    
    conn.close()
    
    return render_template('admin.html', guests=guests, total=total, attending=attending, declined=declined, pending=pending)

# 2. صفحة الدعوة الفردية الخاصة بكل صيدلاني
@app.route('/invite')
def index():
    token = request.args.get('token')
    if not token:
        return "الرابط غير صالح أو غير مكتمل."
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, token, status FROM guests WHERE token = ?", (token,))
    guest_data = cursor.fetchone()
    conn.close()
    
    if not guest_data:
        return "الرابط غير موجود أو تم حذفه."
    
    guest = {
        'name': guest_data[0],
        'token': guest_data[1],
        'status': guest_data[2]
    }
    
    if guest['status'] in ['سأحضر', 'أعتذر عن الحضور']:
        return render_template('thankyou.html', guest=guest, already_voted=True)
    
    return render_template('card.html', guest=guest)

@app.route('/submit', methods=['POST'])
def submit():
    token = request.form.get('token')
    attendance = request.form.get('attendance')
    
    if token and attendance:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT status FROM guests WHERE token = ?", (token,))
        current_status = cursor.fetchone()
        
        if current_status and (not current_status[0] or current_status[0] == 'لم يجب'):
            cursor.execute("UPDATE guests SET status = ? WHERE token = ?", (attendance, token))
            conn.commit()
            
        conn.close()
    
    return render_template('thankyou.html', already_voted=False)

@app.route('/reset/<token>')
def reset_vote(token):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE guests SET status = 'لم يجب' WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
