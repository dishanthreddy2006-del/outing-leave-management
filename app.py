from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret123'

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_no TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        hostel_room TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS outing_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        destination TEXT,
        reason TEXT,
        out_time TEXT,
        return_time TEXT,
        status TEXT DEFAULT 'Pending'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS leave_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        from_date TEXT,
        to_date TEXT,
        reason TEXT,
        leave_type TEXT,
        status TEXT DEFAULT 'Pending'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    c.execute("INSERT OR IGNORE INTO students (name, roll_no, password, hostel_room) VALUES ('Admin', 'admin', 'admin123', 'N/A')")

    conn.commit()
    conn.close()

def add_notification(user_id, message):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO notifications (user_id, message) VALUES (?, ?)", (user_id, message))
    conn.commit()
    conn.close()

def get_notifications(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    notifs = c.fetchall()
    conn.close()
    return notifs

def get_unread_count(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

# ---------- ROUTES ----------

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        roll = request.form['roll_no']
        pwd = request.form['password']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE roll_no=? AND password=?", (roll, pwd))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['roll_no'] = user[2]
            if roll == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('student_dashboard'))
        return render_template('login.html', error='Invalid credentials!')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        roll = request.form['roll_no']
        pwd = request.form['password']
        room = request.form['hostel_room']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO students (name, roll_no, password, hostel_room) VALUES (?,?,?,?)", (name, roll, pwd, room))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            conn.close()
            return render_template('register.html', error='Roll number already exists!')
    return render_template('register.html')

@app.route('/dashboard')
def student_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM outing_requests WHERE student_id=?", (session['user_id'],))
    outings = c.fetchall()
    c.execute("SELECT * FROM leave_requests WHERE student_id=?", (session['user_id'],))
    leaves = c.fetchall()
    conn.close()
    notifs = get_notifications(session['user_id'])
    unread = get_unread_count(session['user_id'])
    return render_template('dashboard.html', outings=outings, leaves=leaves, notifs=notifs, unread=unread)

@app.route('/mark_read')
def mark_read():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (session['user_id'],))
    conn.commit()
    conn.close()
    return redirect(url_for('student_dashboard'))

@app.route('/outing', methods=['GET', 'POST'])
def outing():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO outing_requests (student_id, destination, reason, out_time, return_time) VALUES (?,?,?,?,?)",
                  (session['user_id'], request.form['destination'], request.form['reason'],
                   request.form['out_time'], request.form['return_time']))
        conn.commit()
        conn.close()
        # Notify admin
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE roll_no='admin'")
        admin = c.fetchone()
        conn.close()
        if admin:
            add_notification(admin[0], f"📋 New outing request from {session['name']} ({session['roll_no']})")
        return redirect(url_for('student_dashboard'))
    return render_template('outing_form.html')

@app.route('/leave', methods=['GET', 'POST'])
def leave():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO leave_requests (student_id, from_date, to_date, reason, leave_type) VALUES (?,?,?,?,?)",
                  (session['user_id'], request.form['from_date'], request.form['to_date'],
                   request.form['reason'], request.form['leave_type']))
        conn.commit()
        conn.close()
        # Notify admin
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE roll_no='admin'")
        admin = c.fetchone()
        conn.close()
        if admin:
            add_notification(admin[0], f"📋 New leave request from {session['name']} ({session['roll_no']})")
        return redirect(url_for('student_dashboard'))
    return render_template('leave_form.html')

@app.route('/admin')
def admin_dashboard():
    if session.get('roll_no') != 'admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''SELECT o.id, s.name, s.roll_no, o.destination, o.reason, o.out_time, o.return_time, o.status
                 FROM outing_requests o JOIN students s ON o.student_id = s.id''')
    outings = c.fetchall()
    c.execute('''SELECT l.id, s.name, s.roll_no, l.from_date, l.to_date, l.reason, l.leave_type, l.status
                 FROM leave_requests l JOIN students s ON l.student_id = s.id''')
    leaves = c.fetchall()
    conn.close()
    notifs = get_notifications(session['user_id'])
    unread = get_unread_count(session['user_id'])
    return render_template('admin.html', outings=outings, leaves=leaves, notifs=notifs, unread=unread)

@app.route('/admin/mark_read')
def admin_mark_read():
    if session.get('roll_no') != 'admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (session['user_id'],))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/approve/<type>/<int:req_id>')
def approve(type, req_id):
    if session.get('roll_no') != 'admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    table = 'outing_requests' if type == 'outing' else 'leave_requests'
    c.execute(f"UPDATE {table} SET status='Approved' WHERE id=?", (req_id,))
    # Get student id
    c.execute(f"SELECT student_id FROM {table} WHERE id=?", (req_id,))
    student = c.fetchone()
    conn.commit()
    conn.close()
    if student:
        label = 'Outing' if type == 'outing' else 'Leave'
        add_notification(student[0], f"✅ Your {label} request #{req_id} has been Approved!")
    return redirect(url_for('admin_dashboard'))

@app.route('/reject/<type>/<int:req_id>')
def reject(type, req_id):
    if session.get('roll_no') != 'admin':
        return redirect(url_for('login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    table = 'outing_requests' if type == 'outing' else 'leave_requests'
    c.execute(f"UPDATE {table} SET status='Rejected' WHERE id=?", (req_id,))
    # Get student id
    c.execute(f"SELECT student_id FROM {table} WHERE id=?", (req_id,))
    student = c.fetchone()
    conn.commit()
    conn.close()
    if student:
        label = 'Outing' if type == 'outing' else 'Leave'
        add_notification(student[0], f"❌ Your {label} request #{req_id} has been Rejected.")
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- RUN ----------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)