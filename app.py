from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

@app.route('/')
def home():
    token = request.args.get('token')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if not token:
        # جلب البيانات بشكل مباشر وآمن
        cursor.execute("SELECT name, token, status FROM guests")
        rows = cursor.fetchall()
        
        guests = []
        attending = 0
        declined = 0
        
        for r in rows:
            name = r[0]
            t = r[1]
            status = r[2] if r[2] else 'لم يجب'
            
            if status == 'سأحضر':
                attending += 1
            elif status == 'أعتذر عن الحضور':
                declined += 1
                
            link = f"https://nmp-sy.onrender.com/?token={t}"
            guests.append((name, t, status, link))
            
        total = len(guests)
        pending = total - (attending + declined)
        conn.close()
        
        return render_template('admin.html', guests=guests, total=total, attending=attending, declined=declined, pending=pending)
    
    # عرض بطاقة الضيف
    cursor.execute("SELECT name, token, status FROM guests WHERE token = ?", (token,))
    guest_data = cursor.fetchone()
    conn.close()
    
    if not guest_data:
        return "الرابط غير موجود."
        
    guest = {
        'name': guest_data[0],
        'token': guest_data[1],
        'status': guest_data[2] if guest_data[2] else 'لم يجب'
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
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
