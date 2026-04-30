from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'secret123'

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://outing_leave_mangement_user:XJydpzLaRNGWEcmmCji1dHaInQc8vG1N@dpg-d7g632t7vvec73bm67c0-a/outing_leave_mangement')

def get_conn():
    return psycopg2.connect(DATABASE_URL)

# ---------- DATABASE SETUP ----------
def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS students (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        roll_no TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        hostel_room TEXT,
        photo TEXT
    )''')
    c.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS photo TEXT")

    c.execute('''CREATE TABLE IF NOT EXISTS outing_requests (
        id SERIAL PRIMARY KEY,
        student_id INTEGER,
        destination TEXT,
        reason TEXT,
        out_time TEXT,
        return_time TEXT,
        status TEXT DEFAULT 'Pending'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS leave_requests (
        id SERIAL PRIMARY KEY,
        student_id INTEGER,
        from_date TEXT,
        to_date TEXT,
        reason TEXT,
        leave_type TEXT,
        status TEXT DEFAULT 'Pending',
        proof TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        message TEXT,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    

    c.execute("INSERT INTO students (name, roll_no, password, hostel_room, photo) VALUES ('Admin', 'admin', 'admin123', 'N/A', NULL) ON CONFLICT (roll_no) DO NOTHING")

    conn.commit()
    conn.close()

def add_notification(user_id, message):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO notifications (user_id, message) VALUES (%s, %s)", (user_id, message))
    conn.commit()
    conn.close()

def get_notifications(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
    notifs = c.fetchall()
    conn.close()
    return notifs

def get_unread_count(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM notifications WHERE user_id=%s AND is_read=0", (user_id,))
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
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM students WHERE roll_no=%s AND password=%s", (roll, pwd))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['roll_no'] = user[2]
            session['photo'] = user[5] if user[5] else None
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
        photo_filename = None

        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '':
                from werkzeug.utils import secure_filename
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                photo_filename = secure_filename(photo.filename)
                photo.save(os.path.join(upload_folder, photo_filename))

        conn = get_conn()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO students (name, roll_no, password, hostel_room, photo) VALUES (%s,%s,%s,%s,%s)",
                      (name, roll, pwd, room, photo_filename))
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
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM outing_requests WHERE student_id=%s", (session['user_id'],))
    outings = c.fetchall()
    c.execute("SELECT * FROM leave_requests WHERE student_id=%s", (session['user_id'],))
    leaves = c.fetchall()
    conn.close()
    notifs = get_notifications(session['user_id'])
    unread = get_unread_count(session['user_id'])
    return render_template('dashboard.html', outings=outings, leaves=leaves, notifs=notifs, unread=unread)

@app.route('/mark_read')
def mark_read():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=%s", (session['user_id'],))
    conn.commit()
    conn.close()
    return redirect(url_for('student_dashboard'))

@app.route('/outing', methods=['GET', 'POST'])
def outing():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO outing_requests (student_id, destination, reason, out_time, return_time) VALUES (%s,%s,%s,%s,%s)",
                  (session['user_id'], request.form['destination'], request.form['reason'],
                   request.form['out_time'], request.form['return_time']))
        conn.commit()
        conn.close()
        conn = get_conn()
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
        proof_filename = None
        if 'proof' in request.files:
            proof = request.files['proof']
            if proof.filename != '':
                from werkzeug.utils import secure_filename
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                proof_filename = secure_filename(proof.filename)
                proof.save(os.path.join(upload_folder, proof_filename))

        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO leave_requests (student_id, from_date, to_date, reason, leave_type, proof) VALUES (%s,%s,%s,%s,%s,%s)",
                  (session['user_id'], request.form['from_date'], request.form['to_date'],
                   request.form['reason'], request.form['leave_type'], proof_filename))
        conn.commit()
        conn.close()
        conn = get_conn()
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
    conn = get_conn()
    c = conn.cursor()
    c.execute('''SELECT o.id, s.name, s.roll_no, o.destination, o.reason, o.out_time, o.return_time, o.status
                 FROM outing_requests o JOIN students s ON o.student_id = s.id''')
    outings = c.fetchall()
    c.execute('''SELECT l.id, s.name, s.roll_no, l.from_date, l.to_date, l.reason, l.leave_type, l.status, l.proof
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
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read=1 WHERE user_id=%s", (session['user_id'],))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/approve/<type>/<int:req_id>')
def approve(type, req_id):
    if session.get('roll_no') != 'admin':
        return redirect(url_for('login'))
    conn = get_conn()
    c = conn.cursor()
    table = 'outing_requests' if type == 'outing' else 'leave_requests'
    c.execute(f"UPDATE {table} SET status='Approved' WHERE id=%s", (req_id,))
    c.execute(f"SELECT student_id FROM {table} WHERE id=%s", (req_id,))
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
    conn = get_conn()
    c = conn.cursor()
    table = 'outing_requests' if type == 'outing' else 'leave_requests'
    c.execute(f"UPDATE {table} SET status='Rejected' WHERE id=%s", (req_id,))
    c.execute(f"SELECT student_id FROM {table} WHERE id=%s", (req_id,))
    student = c.fetchone()
    conn.commit()
    conn.close()
    if student:
        label = 'Outing' if type == 'outing' else 'Leave'
        add_notification(student[0], f"❌ Your {label} request #{req_id} has been Rejected.")
    return redirect(url_for('admin_dashboard'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_conn()
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        room = request.form['hostel_room']
        photo_filename = None

        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '':
                from werkzeug.utils import secure_filename
                upload_folder = os.path.join('static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                photo_filename = secure_filename(photo.filename)
                photo.save(os.path.join(upload_folder, photo_filename))

        if photo_filename:
            c.execute("UPDATE students SET name=%s, password=%s, hostel_room=%s, photo=%s WHERE id=%s",
                      (name, password, room, photo_filename, session['user_id']))
        else:
            c.execute("UPDATE students SET name=%s, password=%s, hostel_room=%s WHERE id=%s",
                      (name, password, room, session['user_id']))

        conn.commit()
        session['name'] = name
        conn.close()
        return redirect(url_for('student_dashboard'))

    c.execute("SELECT * FROM students WHERE id=%s", (session['user_id'],))
    student = c.fetchone()
    conn.close()
    return render_template('edit_profile.html', student=student)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- RUN ----------
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)