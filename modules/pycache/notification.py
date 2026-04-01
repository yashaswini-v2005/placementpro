import sqlite3

DB = 'placementpro.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def create_notification(user_id, message):
    conn = get_db()
    conn.execute('INSERT INTO notifications(user_id, message) VALUES(?,?)', (user_id, message))
    conn.commit()
    conn.close()

def get_notifications(user_id, limit=10):
    conn = get_db()
    notifs = conn.execute(
        'SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT ?',
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(n) for n in notifs]
