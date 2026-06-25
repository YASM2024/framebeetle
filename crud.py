import re
from db import get_conn
from forms_loader import SQL_TYPES, can_access

_SAFE_NAME = re.compile(r'^[a-z][a-z0-9_]*$')


def _safe_identifier(name: str) -> str:
    if not _SAFE_NAME.match(name):
        raise ValueError(f'識別子が不正です: {name}')
    return name


def ensure_table(database: str, form_def: dict):
    table = _safe_identifier(form_def['table'])
    columns = ['id INTEGER PRIMARY KEY AUTOINCREMENT']
    columns.append('created_by TEXT NOT NULL')
    columns.append('updated_by TEXT')
    columns.append('created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    columns.append('updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    for field in form_def['fields']:
        col = _safe_identifier(field['name'])
        sql_type = SQL_TYPES[field['type']]
        columns.append(f'{col} {sql_type}')
    ddl = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
    with get_conn(database) as conn:
        conn.execute(ddl)


def list_records(database: str, form_def: dict, limit: int = 500):
    table = _safe_identifier(form_def['table'])
    with get_conn(database) as conn:
        rows = conn.execute(
            f'SELECT * FROM {table} ORDER BY id DESC LIMIT ?',
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_record(database: str, form_def: dict, record_id: int):
    table = _safe_identifier(form_def['table'])
    with get_conn(database) as conn:
        row = conn.execute(
            f'SELECT * FROM {table} WHERE id = ?',
            (record_id,),
        ).fetchone()
        return dict(row) if row else None


def _parse_form_data(form_def: dict, form_data: dict) -> tuple[dict, list[str]]:
    values = {}
    errors = []
    for field in form_def['fields']:
        name = field['name']
        raw = form_data.get(name, '')
        if field['type'] == 'checkbox':
            values[name] = 1 if raw in ('1', 'on', 'true', True) else 0
            continue
        value = str(raw).strip() if raw is not None else ''
        if field.get('required') and not value:
            errors.append(f'「{field.get("label", name)}」は必須です。')
            continue
        if field['type'] == 'number' and value:
            try:
                float(value)
            except ValueError:
                errors.append(f'「{field.get("label", name)}」は数値で入力してください。')
                continue
        values[name] = value
    return values, errors


def create_record(database: str, form_def: dict, form_data: dict, username: str):
    values, errors = _parse_form_data(form_def, form_data)
    if errors:
        return None, errors
    table = _safe_identifier(form_def['table'])
    cols = ['created_by', 'updated_by'] + list(values.keys())
    placeholders = ', '.join(['?'] * len(cols))
    col_names = ', '.join(_safe_identifier(c) for c in cols)
    params = [username, username] + list(values.values())
    with get_conn(database) as conn:
        cur = conn.execute(
            f'INSERT INTO {table} ({col_names}) VALUES ({placeholders})',
            params,
        )
        return cur.lastrowid, []


def update_record(database: str, form_def: dict, record_id: int, form_data: dict, username: str):
    values, errors = _parse_form_data(form_def, form_data)
    if errors:
        return errors
    table = _safe_identifier(form_def['table'])
    sets = ['updated_by = ?', 'updated_at = CURRENT_TIMESTAMP']
    params = [username]
    for name, value in values.items():
        sets.append(f'{_safe_identifier(name)} = ?')
        params.append(value)
    params.append(record_id)
    with get_conn(database) as conn:
        conn.execute(
            f'UPDATE {table} SET {", ".join(sets)} WHERE id = ?',
            params,
        )
    return []


def delete_record(database: str, form_def: dict, record_id: int):
    table = _safe_identifier(form_def['table'])
    with get_conn(database) as conn:
        conn.execute(f'DELETE FROM {table} WHERE id = ?', (record_id,))


def check_permission(form_def: dict, action: str, role: str):
    if not can_access(form_def, action, role):
        return f'この操作（{action}）の権限がありません。'
    return None
