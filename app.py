from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
from werkzeug.utils import secure_filename
import sqlite3, os, json
from modules.placement_engine import get_eligible_students, get_eligible_drives
from modules.resume_engine import generate_resume_pdf
from modules.analytics import get_skill_gap, get_placement_stats
from modules.notifications import create_notification, get_notifications

app = Flask(__name__)
app.secret_key = 'placementpro_secret_2024'
DB = 'placementpro.db'

@app.template_filter('from_json')
def from_json_filter(s):
    try: return json.loads(s)
    except: return []

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','tpo','alumni'))
        );
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id),
            cgpa REAL DEFAULT 0,
            backlogs INTEGER DEFAULT 0,
            branch TEXT DEFAULT '',
            skills TEXT DEFAULT '[]',
            projects TEXT DEFAULT '[]',
            certificates TEXT DEFAULT '[]',
            phone TEXT DEFAULT '',
            dob TEXT DEFAULT '',
            linkedin TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS alumni_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE REFERENCES users(id),
            company TEXT DEFAULT '',
            role TEXT DEFAULT '',
            batch_year TEXT DEFAULT '',
            branch TEXT DEFAULT '',
            linkedin TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            open_to_mentor INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS alumni_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumni_id INTEGER REFERENCES users(id),
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT DEFAULT '',
            description TEXT DEFAULT '',
            apply_link TEXT DEFAULT '',
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS mentorship_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES users(id),
            alumni_id INTEGER REFERENCES users(id),
            message TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, alumni_id)
        );
        CREATE TABLE IF NOT EXISTS drives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            min_cgpa REAL NOT NULL,
            max_backlogs INTEGER NOT NULL,
            allowed_branches TEXT NOT NULL,
            description TEXT DEFAULT '',
            deadline TEXT,
            status TEXT DEFAULT 'active',
            package_lpa REAL DEFAULT 0,
            location TEXT DEFAULT '',
            job_type TEXT DEFAULT 'Full-Time',
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES users(id),
            drive_id INTEGER REFERENCES drives(id),
            status TEXT DEFAULT 'applied',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, drive_id)
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id),
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS resume_meta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES users(id),
            file_path TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS interview_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drive_id INTEGER REFERENCES drives(id),
            student_id INTEGER REFERENCES users(id),
            interview_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(drive_id, interview_date, time_slot)
        );
        CREATE TABLE IF NOT EXISTS referral_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER REFERENCES users(id),
            referral_post_id INTEGER REFERENCES alumni_referral_posts(id),
            alumni_id INTEGER REFERENCES users(id),
            message TEXT DEFAULT '',
            status TEXT DEFAULT 'requested',
            alumni_note TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(student_id, referral_post_id)
        );
        CREATE TABLE IF NOT EXISTS alumni_mentorship_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumni_id INTEGER REFERENCES users(id),
            topic TEXT NOT NULL,
            slot_date TEXT NOT NULL,
            slot_time TEXT NOT NULL,
            meet_link TEXT DEFAULT '',
            status TEXT DEFAULT 'available',
            booked_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS alumni_referral_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alumni_id INTEGER REFERENCES users(id),
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            description TEXT DEFAULT '',
            jd_link TEXT DEFAULT '',
            deadline TEXT DEFAULT '',
            package_lpa REAL DEFAULT 0,
            location TEXT DEFAULT '',
            job_type TEXT DEFAULT 'Full-Time',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    for col in [
        ("student_profiles","linkedin","TEXT DEFAULT ''"),
        ("student_profiles","photo_url","TEXT DEFAULT ''"),
        ("drives","status","TEXT DEFAULT 'active'"),
        ("drives","package_lpa","REAL DEFAULT 0"),
        ("drives","location","TEXT DEFAULT ''"),
        ("drives","job_type","TEXT DEFAULT 'Full-Time'"),
        ("alumni_referral_posts","package_lpa","REAL DEFAULT 0"),
        ("alumni_referral_posts","location","TEXT DEFAULT ''"),
        ("alumni_referral_posts","job_type","TEXT DEFAULT 'Full-Time'"),
    ]:
        try: c.execute(f"ALTER TABLE {col[0]} ADD COLUMN {col[1]} {col[2]}"); conn.commit()
        except: pass

    # Seed data
    try:
        c.execute("INSERT INTO users(name,email,password,role) VALUES('TPO Admin','tpo@college.edu','tpo123','tpo')")
        c.execute("INSERT INTO users(name,email,password,role) VALUES('Rahul Sharma','rahul@student.edu','pass123','student')")
        c.execute("INSERT INTO users(name,email,password,role) VALUES('Priya Singh','priya@student.edu','pass123','student')")
        c.execute("INSERT INTO users(name,email,password,role) VALUES('Amit Verma','amit@alumni.edu','pass123','alumni')")
        c.execute("INSERT INTO users(name,email,password,role) VALUES('Sneha Patel','sneha@alumni.edu','pass123','alumni')")
        c.execute("""INSERT INTO student_profiles(user_id,cgpa,backlogs,branch,skills,projects,certificates,phone,linkedin)
            VALUES(2,8.5,0,'CS','["Python","SQL","Machine Learning","Django"]',
            '[{"name":"E-Commerce Site","desc":"Built with Django and PostgreSQL","url":"https://github.com"}]',
            '[{"title":"Python for Everybody","issuer":"Coursera","year":"2024"}]','9876543210','https://linkedin.com/in/rahul')""")
        c.execute("""INSERT INTO student_profiles(user_id,cgpa,backlogs,branch,skills,projects,certificates,phone,linkedin)
            VALUES(3,7.2,1,'MCA','["Java","HTML","CSS","React"]',
            '[{"name":"Task Manager","desc":"React + Node.js app","url":""}]','[]','9123456780','')""")
        c.execute("""INSERT INTO alumni_profiles(user_id,company,role,batch_year,branch,linkedin,bio,open_to_mentor)
            VALUES(4,'Google','Senior Software Engineer','2021','CS','https://linkedin.com/in/amit',
            'IITian turned Googler. Happy to help with DSA, system design, and interview prep.',1)""")
        c.execute("""INSERT INTO alumni_profiles(user_id,company,role,batch_year,branch,linkedin,bio,open_to_mentor)
            VALUES(5,'Microsoft','Data Scientist','2022','MCA','https://linkedin.com/in/sneha',
            'Data Science @ Microsoft. Can guide on ML projects, resume reviews, and career strategy.',1)""")
        c.execute("""INSERT INTO alumni_jobs(alumni_id,company,role,location,description,apply_link)
            VALUES(4,'Google','Software Engineer Intern','Bangalore',
            'Looking for strong CS fundamentals, DSA, and system design knowledge. 6-month internship.','https://careers.google.com')""")
        c.execute("""INSERT INTO alumni_jobs(alumni_id,company,role,location,description,apply_link)
            VALUES(5,'Microsoft','Data Analyst','Hyderabad',
            'Referral opening for freshers with Python and SQL skills. Strong ML background preferred.','https://careers.microsoft.com')""")
        c.execute("""INSERT INTO drives(company,role,min_cgpa,max_backlogs,allowed_branches,description,deadline,status,created_by)
            VALUES('TCS','Software Engineer',7.0,0,'["CS","MCA","IT"]',
            'Join TCS Digital team. Online aptitude + technical interview.','2025-03-30','active',1)""")
        c.execute("""INSERT INTO drives(company,role,min_cgpa,max_backlogs,allowed_branches,description,deadline,status,created_by)
            VALUES('Infosys','Data Analyst',8.0,0,'["CS","MCA"]',
            'Infosys ML team. 3 rounds: aptitude, case study, HR.','2025-04-15','active',1)""")
        # Seed alumni names to match screenshots
        c.execute("UPDATE users SET name='Arjun Mehta' WHERE id=4")
        c.execute("UPDATE users SET name='Sneha Patel' WHERE id=5")
        c.execute("UPDATE alumni_profiles SET company='Google',role='Senior Software Engineer',batch_year='2020',branch='CS',bio='Passionate about helping juniors crack tech interviews. 4 years at Google.',open_to_mentor=1 WHERE user_id=4")
        c.execute("UPDATE alumni_profiles SET company='Microsoft',role='Data Scientist',batch_year='2021',branch='MCA',bio='ML/AI enthusiast. Happy to guide on data science careers.',open_to_mentor=1 WHERE user_id=5")
        c.execute("""INSERT INTO alumni_mentorship_slots(alumni_id,topic,slot_date,slot_time,meet_link,status) VALUES(4,'Mock Interview (DSA)','2025-03-25','10:00 AM','https://meet.google.com/abc','available')""")
        c.execute("""INSERT INTO alumni_mentorship_slots(alumni_id,topic,slot_date,slot_time,meet_link,status) VALUES(4,'Resume Review','2025-03-26','3:00 PM','https://meet.google.com/xyz','available')""")
        c.execute("""INSERT INTO alumni_mentorship_slots(alumni_id,topic,slot_date,slot_time,meet_link,status) VALUES(5,'Career Guidance (Data Science)','2025-03-27','11:00 AM','https://meet.google.com/pqr','available')""")
        c.execute("""INSERT INTO alumni_referral_posts(alumni_id,company,role,description,deadline) VALUES(4,'Google','SWE Intern','Summer internship. Strong DSA skills required.','2025-04-30')""")
        c.execute("""INSERT INTO alumni_referral_posts(alumni_id,company,role,description,deadline) VALUES(5,'Microsoft','Data Analyst','Entry-level on Azure data team. Python + SQL required.','2025-05-15')""")
        conn.commit()
    except: conn.rollback()
    conn.close()

# ── AUTH ─────────────────────────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE email=? AND password=?',
        (request.form['email'], request.form['password'])).fetchone()
    conn.close()
    if user:
        session['user_id'] = user['id']; session['role'] = user['role']; session['name'] = user['name']
        return redirect(url_for('dashboard'))
    flash('Invalid credentials', 'error')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        conn = get_db()
        try:
            conn.execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)',
                (request.form['name'], request.form['email'], request.form['password'], request.form['role']))
            conn.commit()
            uid = conn.execute('SELECT id FROM users WHERE email=?', (request.form['email'],)).fetchone()['id']
            role = request.form['role']
            if role == 'student':
                conn.execute('INSERT INTO student_profiles(user_id) VALUES(?)', (uid,)); conn.commit()
            elif role == 'alumni':
                conn.execute('INSERT INTO alumni_profiles(user_id) VALUES(?)', (uid,)); conn.commit()
            flash('Account created! Please login.', 'success')
        except: flash('Email already registered.', 'error')
        conn.close()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('index'))
    r = session['role']
    if r == 'tpo': return redirect(url_for('tpo_dashboard'))
    if r == 'alumni': return redirect(url_for('alumni_dashboard'))
    return redirect(url_for('student_dashboard'))

# ── TPO ROUTES ────────────────────────────────────────────────────────
@app.route('/tpo')
def tpo_dashboard():
    if session.get('role') != 'tpo': return redirect(url_for('index'))
    conn = get_db()
    active_drives   = conn.execute("SELECT * FROM drives WHERE status='active' ORDER BY created_at DESC").fetchall()
    completed_drives= conn.execute("SELECT * FROM drives WHERE status='completed' ORDER BY created_at DESC").fetchall()
    total_students  = conn.execute("SELECT COUNT(*) as c FROM users WHERE role='student'").fetchone()['c']
    total_apps      = conn.execute('SELECT COUNT(*) as c FROM applications').fetchone()['c']
    placed_count    = conn.execute("SELECT COUNT(DISTINCT student_id) as c FROM applications WHERE status='selected'").fetchone()['c']
    notifs = get_notifications(session['user_id'])
    conn.close()
    return render_template('tpo_dashboard.html', active_drives=active_drives,
        completed_drives=completed_drives, total_students=total_students,
        total_apps=total_apps, placed_count=placed_count, notifs=notifs)

@app.route('/tpo/drive/create', methods=['GET','POST'])
def create_drive():
    if session.get('role') != 'tpo': return redirect(url_for('index'))
    if request.method == 'POST':
        branches = request.form.getlist('branches')
        conn = get_db()
        conn.execute('''INSERT INTO drives(company,role,min_cgpa,max_backlogs,allowed_branches,description,deadline,status,package_lpa,location,job_type,created_by)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''', (
            request.form['company'], request.form['role'],
            float(request.form['min_cgpa']), int(request.form['max_backlogs']),
            json.dumps(branches), request.form['description'],
            request.form['deadline'], 'active',
            float(request.form.get('package_lpa') or 0),
            request.form.get('location',''),
            request.form.get('job_type','Full-Time'),
            session['user_id']))
        drive_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.commit()
        eligible = get_eligible_students(drive_id)
        for s in eligible:
            create_notification(s['user_id'], f"🎯 New drive: {request.form['company']} ({request.form['role']}) — you're eligible!")
        flash(f'Drive created! {len(eligible)} eligible students notified.', 'success')
        conn.close()
        return redirect(url_for('tpo_dashboard'))
    return render_template('create_drive.html')

@app.route('/tpo/drive/<int:drive_id>/complete', methods=['POST'])
def complete_drive(drive_id):
    if session.get('role') != 'tpo': return redirect(url_for('index'))
    conn = get_db()
    conn.execute("UPDATE drives SET status='completed' WHERE id=?", (drive_id,)); conn.commit()
    apps = conn.execute('SELECT a.student_id, d.company FROM applications a JOIN drives d ON a.drive_id=d.id WHERE a.drive_id=?', (drive_id,)).fetchall()
    for a in apps: create_notification(a['student_id'], f"🏁 The {a['company']} drive has been closed.")
    conn.close()
    flash('Drive marked as completed.', 'success')
    return redirect(url_for('tpo_dashboard'))

@app.route('/tpo/drive/<int:drive_id>')
def drive_detail(drive_id):
    if session.get('role') != 'tpo': return redirect(url_for('index'))
    conn = get_db()
    drive = conn.execute('SELECT * FROM drives WHERE id=?', (drive_id,)).fetchone()
    eligible = get_eligible_students(drive_id)
    branch_breakdown = {}
    for s in eligible: branch_breakdown[s['branch']] = branch_breakdown.get(s['branch'], 0) + 1
    raw_apps = conn.execute('''SELECT a.*, u.name, u.email, sp.cgpa, sp.branch
        FROM applications a JOIN users u ON a.student_id=u.id
        JOIN student_profiles sp ON u.id=sp.user_id WHERE a.drive_id=?''', (drive_id,)).fetchall()
    schedules = conn.execute('''SELECT isch.*, u.name as student_name
        FROM interview_schedule isch JOIN users u ON isch.student_id=u.id
        WHERE isch.drive_id=?''', (drive_id,)).fetchall()
    all_students = conn.execute("SELECT u.id, u.name FROM users u WHERE u.role='student' ORDER BY u.name").fetchall()
    selected_students = conn.execute('''SELECT u.name, u.email, sp.cgpa, sp.branch
        FROM applications a JOIN users u ON a.student_id=u.id
        JOIN student_profiles sp ON u.id=sp.user_id
        WHERE a.drive_id=? AND a.status='selected' ''', (drive_id,)).fetchall()
    conn.close()
    return render_template('drive_detail.html', drive=drive, eligible=eligible,
        applications=raw_apps, branch_breakdown=branch_breakdown,
        schedules=schedules, all_students=all_students, selected_students=selected_students)

@app.route('/tpo/drive/<int:drive_id>/schedule', methods=['POST'])
def schedule_interview(drive_id):
    if session.get('role') != 'tpo': return redirect(url_for('index'))
    student_id = int(request.form['student_id'])
    interview_date = request.form['interview_date']
    time_slot = request.form['time_slot']
    notes = request.form.get('notes','')
    conn = get_db()
    existing = conn.execute('SELECT * FROM interview_schedule WHERE drive_id=? AND interview_date=? AND time_slot=?',
        (drive_id, interview_date, time_slot)).fetchone()
    if existing:
        flash('⚠️ Conflict! That slot is already booked.', 'error')
        conn.close(); return redirect(url_for('drive_detail', drive_id=drive_id))
    try:
        conn.execute('INSERT INTO interview_schedule(drive_id,student_id,interview_date,time_slot,notes) VALUES(?,?,?,?,?)',
            (drive_id, student_id, interview_date, time_slot, notes)); conn.commit()
        student = conn.execute('SELECT * FROM users WHERE id=?', (student_id,)).fetchone()
        drive   = conn.execute('SELECT * FROM drives WHERE id=?', (drive_id,)).fetchone()
        create_notification(student_id, f"📅 Interview scheduled for {drive['company']} on {interview_date} at {time_slot}")
        conn.execute('UPDATE applications SET status=? WHERE student_id=? AND drive_id=?', ('interview_scheduled', student_id, drive_id)); conn.commit()
        flash(f'Interview scheduled for {student["name"]} on {interview_date} at {time_slot}', 'success')
    except Exception as e: flash(f'Error: {str(e)}', 'error')
    conn.close(); return redirect(url_for('drive_detail', drive_id=drive_id))

@app.route('/tpo/notify/<int:drive_id>', methods=['POST'])
def notify_eligible(drive_id):
    if session.get('role') != 'tpo': return redirect(url_for('index'))
    eligible = get_eligible_students(drive_id)
    conn = get_db()
    drive = conn.execute('SELECT * FROM drives WHERE id=?', (drive_id,)).fetchone()
    conn.close()
    for s in eligible: create_notification(s['user_id'], f"📢 Reminder: Apply to {drive['company']} ({drive['role']}) before {drive['deadline']}!")
    flash(f'Notified {len(eligible)} eligible students!', 'success')
    return redirect(url_for('drive_detail', drive_id=drive_id))

@app.route('/tpo/notify-applicants/<int:drive_id>', methods=['POST'])
def notify_applicants(drive_id):
    if session.get('role') != 'tpo': return redirect(url_for('index'))
    message = request.form.get('message','').strip()
    if not message: flash('Message cannot be empty.', 'error'); return redirect(url_for('drive_detail', drive_id=drive_id))
    conn = get_db()
    drive = conn.execute('SELECT * FROM drives WHERE id=?', (drive_id,)).fetchone()
    applicants = conn.execute('SELECT student_id FROM applications WHERE drive_id=?', (drive_id,)).fetchall()
    conn.close()
    for a in applicants: create_notification(a['student_id'], f"📣 [{drive['company']}] {message}")
    flash(f'Message sent to {len(applicants)} applicant(s)!', 'success')
    return redirect(url_for('drive_detail', drive_id=drive_id))

@app.route('/tpo/application/<int:app_id>/status', methods=['POST'])
def update_status(app_id):
    if session.get('role') != 'tpo': return redirect(url_for('index'))
    new_status = request.form['status']
    conn = get_db()
    app_row = conn.execute('SELECT a.*, d.company FROM applications a JOIN drives d ON a.drive_id=d.id WHERE a.id=?', (app_id,)).fetchone()
    conn.execute('UPDATE applications SET status=? WHERE id=?', (new_status, app_id)); conn.commit()
    labels = {'applied':'Applied','aptitude':'Aptitude Round 📝','technical':'Technical Interview 💻','hr':'HR Round 🤝','interview_scheduled':'Interview Scheduled 📅','selected':'🎉 SELECTED! Congratulations!','rejected':'❌ Not Selected'}
    create_notification(app_row['student_id'], f"📋 [{app_row['company']}] Status: {labels.get(new_status, new_status)}")
    conn.close(); flash('Status updated!', 'success')
    return redirect(request.referrer)

@app.route('/tpo/stats')
def tpo_stats():
    if session.get('role') != 'tpo': return redirect(url_for('index'))
    stats = get_placement_stats()
    return render_template('tpo_stats.html', stats=stats)

# ── STUDENT ROUTES ────────────────────────────────────────────────────
@app.route('/student')
def student_dashboard():
    if session.get('role') != 'student': return redirect(url_for('index'))
    conn = get_db()
    profile = conn.execute('SELECT * FROM student_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    my_apps = conn.execute('''SELECT a.*, d.company, d.role, d.deadline, d.status as drive_status
        FROM applications a JOIN drives d ON a.drive_id=d.id
        WHERE a.student_id=? ORDER BY a.applied_at DESC''', (session['user_id'],)).fetchall()
    conn.close()
    notifs = get_notifications(session['user_id'])
    eligible_drives = get_eligible_drives(session['user_id']) if profile else []
    return render_template('student_dashboard.html', profile=profile,
        applications=my_apps, notifs=notifs, eligible_drives=eligible_drives)

@app.route('/student/profile', methods=['GET','POST'])
def student_profile():
    if session.get('role') != 'student': return redirect(url_for('index'))
    conn = get_db()
    if request.method == 'POST':
        skills = [s.strip() for s in request.form.get('skills','').split(',') if s.strip()]
        projects_raw = request.form.getlist('project_name')
        proj_descs   = request.form.getlist('project_desc')
        proj_urls    = request.form.getlist('project_url')
        projects = [{'name':n,'desc':d,'url':u} for n,d,u in zip(projects_raw,proj_descs,proj_urls) if n.strip()]
        cert_titles  = request.form.getlist('cert_title')
        cert_issuers = request.form.getlist('cert_issuer')
        cert_years   = request.form.getlist('cert_year')
        certs = [{'title':t.strip(),'issuer':i.strip(),'year':y.strip()}
            for t,i,y in zip(cert_titles,cert_issuers,cert_years) if t.strip()]
        photo_url = ''
        if 'photo' in request.files and request.files['photo'].filename:
            photo = request.files['photo']
            os.makedirs('static/photos', exist_ok=True)
            fname = secure_filename(f"photo_{session['user_id']}.{photo.filename.rsplit('.',1)[-1]}")
            photo.save(f'static/photos/{fname}')
            photo_url = f'/static/photos/{fname}'
        existing = conn.execute('SELECT photo_url FROM student_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
        if not photo_url and existing:
            try: photo_url = existing['photo_url'] or ''
            except: photo_url = ''
        try: cgpa_val = float(request.form.get('cgpa') or 0)
        except: cgpa_val = 0.0
        try: backlogs_val = int(request.form.get('backlogs') or 0)
        except: backlogs_val = 0
        uid = session['user_id']
        conn.execute('INSERT OR IGNORE INTO student_profiles(user_id) VALUES(?)', (uid,))
        conn.execute('''UPDATE student_profiles
            SET cgpa=?,backlogs=?,branch=?,skills=?,projects=?,certificates=?,phone=?,dob=?,linkedin=?,photo_url=?
            WHERE user_id=?''', (cgpa_val, backlogs_val,
            request.form.get('branch',''), json.dumps(skills), json.dumps(projects), json.dumps(certs),
            request.form.get('phone',''), request.form.get('dob',''), request.form.get('linkedin','').strip(), photo_url, uid))
        conn.commit(); flash('Profile updated successfully!', 'success')
        conn.close(); return redirect(url_for('student_dashboard'))
    profile = conn.execute('SELECT * FROM student_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    user    = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('student_profile.html', profile=profile, user=user)

@app.route('/student/resume')
def resume_wizard():
    if session.get('role') != 'student': return redirect(url_for('index'))
    conn = get_db()
    profile = conn.execute('SELECT * FROM student_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    user    = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('resume_wizard.html', profile=profile, user=user)

@app.route('/student/resume/generate')
def generate_resume():
    if session.get('role') != 'student': return redirect(url_for('index'))
    conn = get_db()
    user    = conn.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    profile = conn.execute('SELECT * FROM student_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    if not user:
        conn.close(); flash('Session error. Please log in again.', 'error'); return redirect(url_for('index'))
    if not profile:
        # Create empty profile so resume can still generate
        conn.execute('INSERT OR IGNORE INTO student_profiles(user_id) VALUES(?)', (session['user_id'],))
        conn.commit()
        profile = conn.execute('SELECT * FROM student_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    conn.close()
    pdf_path = generate_resume_pdf(user, profile)
    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO resume_meta(student_id, file_path) VALUES(?,?)', (session['user_id'], pdf_path))
    conn.commit(); conn.close()
    return send_file(pdf_path, as_attachment=True, download_name=f"Resume_{user['name'].replace(' ','_')}.pdf")

@app.route('/student/apply/<int:drive_id>', methods=['POST'])
def apply_drive(drive_id):
    if session.get('role') != 'student': return redirect(url_for('index'))
    conn = get_db()
    drive = conn.execute('SELECT * FROM drives WHERE id=?', (drive_id,)).fetchone()
    if drive and drive['status'] == 'completed':
        flash('This drive is already closed.', 'error'); conn.close(); return redirect(url_for('student_dashboard'))
    try:
        conn.execute('INSERT INTO applications(student_id,drive_id) VALUES(?,?)', (session['user_id'], drive_id)); conn.commit()
        flash(f'Applied to {drive["company"]} successfully!', 'success')
    except: flash('Already applied!', 'error')
    conn.close(); return redirect(url_for('student_dashboard'))

@app.route('/student/skill-gap')
def skill_gap():
    if session.get('role') != 'student': return redirect(url_for('index'))
    target_role = request.args.get('role', 'Software Engineer')
    gap_data = get_skill_gap(session['user_id'], target_role)
    roles = ['Data Analyst','Software Engineer','Full Stack Developer','DevOps Engineer','ML Engineer']
    return render_template('skill_gap.html', gap=gap_data, target_role=target_role, roles=roles)

@app.route('/student/chatbot')
def chatbot():
    if session.get('role') != 'student': return redirect(url_for('index'))
    conn = get_db()
    drives = conn.execute("SELECT company,role,deadline,description,min_cgpa,max_backlogs,allowed_branches,package_lpa,location,job_type FROM drives WHERE status='active' LIMIT 10").fetchall()
    my_apps = conn.execute('SELECT a.status, d.company, d.role FROM applications a JOIN drives d ON a.drive_id=d.id WHERE a.student_id=?', (session['user_id'],)).fetchall()
    profile = conn.execute('SELECT cgpa, backlogs, branch FROM student_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('chatbot.html',
        drives_json=json.dumps([dict(d) for d in drives]),
        my_apps_json=json.dumps([dict(a) for a in my_apps]),
        student_profile=dict(profile) if profile else {})

# ── ALUMNI ROUTES ─────────────────────────────────────────────────────
@app.route('/alumni')
def alumni_dashboard():
    if session.get('role') != 'alumni': return redirect(url_for('index'))
    conn = get_db()
    ap = conn.execute('SELECT * FROM alumni_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    my_jobs = conn.execute('SELECT * FROM alumni_jobs WHERE alumni_id=? ORDER BY posted_at DESC', (session['user_id'],)).fetchall()
    my_referral_posts = conn.execute('SELECT * FROM alumni_referral_posts WHERE alumni_id=? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    my_slots = conn.execute('SELECT * FROM alumni_mentorship_slots WHERE alumni_id=? ORDER BY slot_date ASC', (session['user_id'],)).fetchall()
    referral_reqs = conn.execute('''SELECT rr.*, u.name as student_name, u.email as student_email, sp.cgpa, sp.branch,
        arp.company as ref_company, arp.role as ref_role FROM referral_requests rr
        JOIN users u ON rr.student_id=u.id JOIN student_profiles sp ON u.id=sp.user_id
        JOIN alumni_referral_posts arp ON rr.referral_post_id=arp.id
        WHERE rr.alumni_id=? ORDER BY rr.created_at DESC''', (session['user_id'],)).fetchall()
    mentor_reqs = conn.execute('''SELECT mr.*, u.name as student_name, u.email as student_email, sp.branch, sp.cgpa
        FROM mentorship_requests mr JOIN users u ON mr.student_id=u.id
        JOIN student_profiles sp ON u.id=sp.user_id
        WHERE mr.alumni_id=? ORDER BY mr.requested_at DESC''', (session['user_id'],)).fetchall()
    notifs = get_notifications(session['user_id'])
    conn.close()
    return render_template('alumni_dashboard.html', ap=ap, my_jobs=my_jobs, my_referral_posts=my_referral_posts,
        my_slots=my_slots, mentor_reqs=mentor_reqs, referral_reqs=referral_reqs, notifs=notifs)

@app.route('/alumni/profile', methods=['GET','POST'])
def alumni_profile():
    if session.get('role') != 'alumni': return redirect(url_for('index'))
    conn = get_db()
    if request.method == 'POST':
        conn.execute('''UPDATE alumni_profiles SET company=?,role=?,batch_year=?,branch=?,linkedin=?,bio=?,open_to_mentor=?
            WHERE user_id=?''', (request.form['company'], request.form['role'], request.form['batch_year'],
            request.form['branch'], request.form['linkedin'], request.form['bio'],
            1 if request.form.get('open_to_mentor') else 0, session['user_id']))
        conn.commit(); flash('Profile updated!', 'success')
        conn.close(); return redirect(url_for('alumni_dashboard'))
    ap = conn.execute('SELECT * FROM alumni_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('alumni_profile_edit.html', ap=ap)

@app.route('/alumni/post-job', methods=['POST'])
def alumni_post_job():
    if session.get('role') != 'alumni': return redirect(url_for('index'))
    conn = get_db()
    conn.execute('INSERT INTO alumni_jobs(alumni_id,company,role,location,description,apply_link) VALUES(?,?,?,?,?,?)',
        (session['user_id'], request.form['company'], request.form['role'],
         request.form['location'], request.form['description'], request.form['apply_link']))
    conn.commit(); conn.close()
    flash('Job referral posted!', 'success')
    return redirect(url_for('alumni_dashboard'))

@app.route('/alumni/mentorship/<int:req_id>/respond', methods=['POST'])
def respond_mentorship(req_id):
    if session.get('role') != 'alumni': return redirect(url_for('index'))
    action = request.form['action']
    conn = get_db()
    conn.execute('UPDATE mentorship_requests SET status=? WHERE id=? AND alumni_id=?', (action, req_id, session['user_id'])); conn.commit()
    req = conn.execute('SELECT mr.*, u.name as aname FROM mentorship_requests mr JOIN users u ON mr.alumni_id=u.id WHERE mr.id=?', (req_id,)).fetchone()
    if req:
        msg = f"✅ {req['aname']} accepted your mentorship request!" if action == 'accepted' else f"Your mentorship request to {req['aname']} was not accepted this time."
        create_notification(req['student_id'], msg)
    conn.close(); flash(f'Request {action}!', 'success')
    return redirect(url_for('alumni_dashboard'))

# Student-side alumni pages
@app.route('/alumni-connect')
def alumni_connect():
    return redirect(url_for('alumni_connect_board'))

@app.route('/alumni-connect/request/<int:alumni_id>', methods=['POST'])
def request_mentorship(alumni_id):
    if session.get('role') != 'student': return redirect(url_for('index'))
    message = request.form.get('message','Hi! I would love to connect and get your guidance.').strip()
    conn = get_db()
    try:
        conn.execute('INSERT INTO mentorship_requests(student_id,alumni_id,message) VALUES(?,?,?)',
            (session['user_id'], alumni_id, message)); conn.commit()
        alumni_user = conn.execute('SELECT * FROM users WHERE id=?', (alumni_id,)).fetchone()
        create_notification(alumni_id, f"📩 {session['name']} sent you a mentorship request!")
        flash(f'Mentorship request sent to {alumni_user["name"]}!', 'success')
    except: flash('Already sent a request to this alumni.', 'error')
    conn.close(); return redirect(url_for('alumni_connect'))
# ── ALUMNI MENTORSHIP SLOTS & REFERRAL POSTS ─────────────────────────
@app.route('/alumni/slot/add', methods=['GET','POST'])
def alumni_add_slot():
    if session.get('role') != 'alumni': return redirect(url_for('index'))
    if request.method == 'POST':
        conn = get_db()
        conn.execute('INSERT INTO alumni_mentorship_slots(alumni_id,topic,slot_date,slot_time,meet_link,status) VALUES(?,?,?,?,?,?)',
            (session['user_id'], request.form['topic'], request.form['slot_date'], request.form['slot_time'],
             request.form.get('meet_link',''), 'available'))
        conn.commit(); conn.close()
        flash('Mentorship slot added!', 'success')
        return redirect(url_for('alumni_dashboard'))
    return render_template('alumni_add_slot.html')

@app.route('/alumni/referral/post', methods=['GET','POST'])
def alumni_post_referral():
    if session.get('role') != 'alumni': return redirect(url_for('index'))
    conn = get_db()
    ap = conn.execute('SELECT * FROM alumni_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    if request.method == 'POST':
        conn.execute('INSERT INTO alumni_referral_posts(alumni_id,company,role,description,jd_link,deadline,package_lpa,location,job_type) VALUES(?,?,?,?,?,?,?,?,?)',
            (session['user_id'], request.form['company'], request.form['role'],
             request.form.get('description',''), request.form.get('jd_link',''), request.form.get('deadline',''),
             float(request.form.get('package_lpa') or 0), request.form.get('location',''), request.form.get('job_type','Full-Time')))
        conn.commit(); conn.close()
        flash('Referral post published!', 'success')
        return redirect(url_for('alumni_dashboard'))
    conn.close()
    return render_template('alumni_post_referral.html', ap=ap)

@app.route('/connect')
def alumni_connect_board():
    if 'user_id' not in session: return redirect(url_for('index'))
    conn = get_db()
    referrals = conn.execute('''SELECT arp.*, u.name as alumni_name, ap.role as alumni_role, ap.batch_year, ap.branch
        FROM alumni_referral_posts arp
        JOIN users u ON arp.alumni_id=u.id
        JOIN alumni_profiles ap ON u.id=ap.user_id
        ORDER BY arp.created_at DESC''').fetchall()
    # student's referral request statuses
    my_req_map = {}
    if session.get('role') == 'student':
        reqs = conn.execute('SELECT referral_post_id, status FROM referral_requests WHERE student_id=?', (session['user_id'],)).fetchall()
        my_req_map = {r['referral_post_id']: r['status'] for r in reqs}
    slots = conn.execute('''SELECT ams.*, u.name as alumni_name, ap.role as alumni_role, ap.company as alumni_company
        FROM alumni_mentorship_slots ams
        JOIN users u ON ams.alumni_id=u.id
        JOIN alumni_profiles ap ON u.id=ap.user_id
        WHERE ams.status='available'
        ORDER BY ams.slot_date ASC''').fetchall()
    alumni_list = conn.execute('''SELECT u.id, u.name, ap.company, ap.role, ap.batch_year, ap.branch, ap.bio, ap.open_to_mentor
        FROM users u JOIN alumni_profiles ap ON u.id=ap.user_id
        WHERE u.role='alumni'
        ORDER BY ap.batch_year DESC''').fetchall()
    notifs = get_notifications(session['user_id']) if session.get('role') != 'tpo' else []
    conn.close()
    return render_template('alumni_connect_board.html', referrals=referrals, slots=slots, alumni_list=alumni_list, notifs=notifs, my_req_map=my_req_map)

@app.route('/connect/book/<int:slot_id>', methods=['POST'])
def book_slot(slot_id):
    if session.get('role') != 'student': return redirect(url_for('index'))
    conn = get_db()
    slot = conn.execute('SELECT * FROM alumni_mentorship_slots WHERE id=? AND status=?', (slot_id,'available')).fetchone()
    if slot:
        conn.execute('UPDATE alumni_mentorship_slots SET status=?, booked_by=? WHERE id=?', ('booked', session['user_id'], slot_id))
        conn.commit()
        create_notification(slot['alumni_id'], f"📅 {session['name']} booked your '{slot['topic']}' slot on {slot['slot_date']} at {slot['slot_time']}!")
        create_notification(session['user_id'], f"✅ Slot booked: {slot['topic']} on {slot['slot_date']} at {slot['slot_time']}. Meeting link shared by mentor.")
        flash('Slot booked successfully!', 'success')
    else:
        flash('Slot no longer available.', 'error')
    conn.close()
    return redirect(url_for('alumni_connect_board'))


# ── APIS ──────────────────────────────────────────────────────────────
@app.route('/connect/request-referral/<int:post_id>', methods=['POST'])
def request_referral(post_id):
    if session.get('role') != 'student': return redirect(url_for('index'))
    conn = get_db()
    post = conn.execute('SELECT * FROM alumni_referral_posts WHERE id=?', (post_id,)).fetchone()
    if not post:
        flash('Post not found.', 'error'); conn.close(); return redirect(url_for('alumni_connect_board'))
    try:
        conn.execute('INSERT INTO referral_requests(student_id,referral_post_id,alumni_id,message,status) VALUES(?,?,?,?,?)',
            (session['user_id'], post_id, post['alumni_id'], request.form.get('message',''), 'requested'))
        conn.commit()
        create_notification(post['alumni_id'], f"📩 {session['name']} requested a referral for {post['company']} – {post['role']}!")
        flash('Referral request sent!', 'success')
    except: flash('Already requested this referral.', 'error')
    conn.close(); return redirect(url_for('alumni_connect_board'))

@app.route('/alumni/referral-request/<int:req_id>/respond', methods=['POST'])
def respond_referral_request(req_id):
    if session.get('role') != 'alumni': return redirect(url_for('index'))
    action = request.form['action']
    note = request.form.get('note','')
    conn = get_db()
    rr = conn.execute('SELECT rr.*, arp.company, arp.role FROM referral_requests rr JOIN alumni_referral_posts arp ON rr.referral_post_id=arp.id WHERE rr.id=? AND rr.alumni_id=?', (req_id, session['user_id'])).fetchone()
    if rr:
        conn.execute('UPDATE referral_requests SET status=?, alumni_note=? WHERE id=?', (action, note, req_id)); conn.commit()
        msgs = {'approved': f"✅ Referral approved for {rr['company']} – {rr['role']}!", 'referred': f"🎉 You have been referred for {rr['company']} – {rr['role']}!", 'rejected': f"Your referral request for {rr['company']} – {rr['role']} was not approved this time."}
        create_notification(rr['student_id'], msgs.get(action,'Referral request status updated.'))
    conn.close(); flash(f'Request {action}!', 'success')
    return redirect(url_for('alumni_dashboard'))

@app.route('/api/notifications/read/<int:nid>', methods=['POST'])
def mark_read(nid):
    conn = get_db()
    conn.execute('UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?', (nid, session['user_id']))
    conn.commit(); conn.close(); return jsonify({'ok': True})

@app.route('/api/resume-quality')
def resume_quality():
    if 'user_id' not in session: return jsonify({'error':'unauth'}), 401
    conn = get_db()
    profile = conn.execute('SELECT * FROM student_profiles WHERE user_id=?', (session['user_id'],)).fetchone()
    conn.close()
    if not profile: return jsonify({'score':0,'tips':['Complete your profile first']})
    score = 0; tips = []
    try: skills = json.loads(profile['skills']) if profile['skills'] else []
    except: skills = []
    try: projects = json.loads(profile['projects']) if profile['projects'] else []
    except: projects = []
    try: certs = json.loads(profile['certificates']) if profile['certificates'] else []
    except: certs = []
    try: linkedin = profile['linkedin'] or ''
    except: linkedin = ''
    if profile['cgpa'] and float(profile['cgpa']) > 0: score += 20
    else: tips.append('Add your CGPA')
    if profile['branch']: score += 5
    else: tips.append('Add your branch')
    if profile['phone']: score += 5
    else: tips.append('Add phone number')
    if profile['dob']: score += 5
    else: tips.append('Add date of birth')
    if linkedin: score += 5
    else: tips.append('Add your LinkedIn URL')
    if len(skills) >= 5: score += 20
    elif len(skills) >= 3: score += 12; tips.append('Add 2 more skills')
    elif skills: score += 5; tips.append('Add at least 5 skills')
    else: tips.append('Add your technical skills')
    if len(projects) >= 2: score += 25
    elif len(projects) == 1: score += 15; tips.append('Add one more project to reach 90%+')
    else: tips.append('Add at least 1 project')
    if len(certs) >= 2: score += 15
    elif len(certs) == 1: score += 8; tips.append('Add one more certificate')
    else: tips.append('Add a certificate (Coursera, NPTEL)')
    return jsonify({'score': score, 'tips': tips})

@app.route('/api/eligible-count', methods=['POST'])
def eligible_count():
    data = request.json
    from modules.placement_engine import count_eligible_preview
    return jsonify({'count': count_eligible_preview(data.get('min_cgpa',0), data.get('max_backlogs',10), data.get('branches',[]))})

if __name__ == '__main__':
    os.makedirs('static/resumes', exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
