import sqlite3, json

DB = 'placementpro.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_eligible_students(drive_id):
    conn = get_db()
    drive = conn.execute('SELECT * FROM drives WHERE id=?', (drive_id,)).fetchone()
    if not drive: conn.close(); return []
    allowed = json.loads(drive['allowed_branches'])
    students = conn.execute('''SELECT u.id as user_id, u.name, u.email, sp.cgpa, sp.backlogs, sp.branch, sp.skills
        FROM users u JOIN student_profiles sp ON u.id = sp.user_id WHERE u.role = 'student' ''').fetchall()
    conn.close()
    eligible = []
    for s in students:
        if (s['cgpa'] >= drive['min_cgpa'] and
            s['backlogs'] <= drive['max_backlogs'] and
            (not allowed or s['branch'] in allowed)):
            eligible.append(dict(s))
    return eligible

def get_eligible_drives(student_id):
    conn = get_db()
    profile = conn.execute('SELECT * FROM student_profiles WHERE user_id=?', (student_id,)).fetchone()
    if not profile: conn.close(); return []
    # Only active drives
    drives = conn.execute("SELECT * FROM drives WHERE status='active' ORDER BY created_at DESC").fetchall()
    conn.close()
    eligible = []
    for d in drives:
        allowed = json.loads(d['allowed_branches'])
        if (profile['cgpa'] >= d['min_cgpa'] and
            profile['backlogs'] <= d['max_backlogs'] and
            (not allowed or profile['branch'] in allowed)):
            eligible.append(dict(d))
    return eligible

def count_eligible_preview(min_cgpa, max_backlogs, branches):
    conn = get_db()
    students = conn.execute('SELECT sp.cgpa, sp.backlogs, sp.branch FROM student_profiles sp').fetchall()
    conn.close()
    count = 0
    for s in students:
        if (s['cgpa'] >= min_cgpa and s['backlogs'] <= max_backlogs and
            (not branches or s['branch'] in branches)):
            count += 1
    return count
