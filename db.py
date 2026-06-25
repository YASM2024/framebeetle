import sqlite3
from contextlib import contextmanager
from werkzeug.security import generate_password_hash, check_password_hash

ROLES = ('admin', 'user')
ROLE_LABELS = {'admin': '管理者', 'user': '一般'}


@contextmanager
def get_conn(database: str):
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(database: str):
    with get_conn(database) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT NOT NULL,
                detail TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if count == 0:
            conn.execute(
                'INSERT INTO users (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)',
                ('admin', generate_password_hash('admin'), '管理者', 'admin'),
            )
            conn.execute(
                'INSERT INTO users (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)',
                ('user', generate_password_hash('user'), '一般ユーザー', 'user'),
            )


def get_user_by_username(database: str, username: str):
    with get_conn(database) as conn:
        row = conn.execute(
            'SELECT * FROM users WHERE username = ? AND is_active = 1',
            (username,),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(database: str, user_id: int):
    with get_conn(database) as conn:
        row = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        return dict(row) if row else None


def verify_password(user: dict, password: str) -> bool:
    return check_password_hash(user['password_hash'], password)


def list_users(database: str):
    with get_conn(database) as conn:
        rows = conn.execute(
            'SELECT id, username, display_name, role, is_active, created_at FROM users ORDER BY id'
        ).fetchall()
        return [dict(r) for r in rows]


def create_user(database: str, username: str, password: str, display_name: str, role: str):
    with get_conn(database) as conn:
        conn.execute(
            'INSERT INTO users (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)',
            (username, generate_password_hash(password), display_name, role),
        )


def update_user(database: str, user_id: int, display_name: str, role: str, is_active: bool, password: str = ''):
    with get_conn(database) as conn:
        if password:
            conn.execute(
                'UPDATE users SET display_name=?, role=?, is_active=?, password_hash=? WHERE id=?',
                (display_name, role, int(is_active), generate_password_hash(password), user_id),
            )
        else:
            conn.execute(
                'UPDATE users SET display_name=?, role=?, is_active=? WHERE id=?',
                (display_name, role, int(is_active), user_id),
            )


def delete_user(database: str, user_id: int):
    with get_conn(database) as conn:
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))


def add_operation_log(database: str, username: str, action: str, target: str, detail: str = ''):
    with get_conn(database) as conn:
        conn.execute(
            'INSERT INTO operation_logs (username, action, target, detail) VALUES (?, ?, ?, ?)',
            (username, action, target, detail),
        )


def list_operation_logs(database: str, limit: int = 200):
    with get_conn(database) as conn:
        rows = conn.execute(
            'SELECT * FROM operation_logs ORDER BY id DESC LIMIT ?',
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
