import os
import re
import yaml

FIELD_TYPES = {'text', 'textarea', 'number', 'date', 'select', 'checkbox', 'email'}
SQL_TYPES = {
    'text': 'TEXT', 'textarea': 'TEXT', 'select': 'TEXT', 'email': 'TEXT',
    'date': 'TEXT', 'number': 'REAL', 'checkbox': 'INTEGER',
}


def _validate_form_id(form_id: str):
    if not re.match(r'^[a-z][a-z0-9_]*$', form_id):
        raise ValueError(f'フォームIDが不正です: {form_id}')


def load_form_definitions(forms_dir: str) -> dict:
    forms = {}
    if not os.path.isdir(forms_dir):
        return forms
    for filename in sorted(os.listdir(forms_dir)):
        if not filename.endswith(('.yaml', '.yml')):
            continue
        path = os.path.join(forms_dir, filename)
        with open(path, encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        form_id = data.get('id') or os.path.splitext(filename)[0]
        _validate_form_id(form_id)
        data['id'] = form_id
        data.setdefault('title', form_id)
        data.setdefault('table', form_id)
        data.setdefault('roles', {})
        roles = data['roles']
        roles.setdefault('view', ['admin', 'user'])
        roles.setdefault('create', ['admin', 'user'])
        roles.setdefault('edit', ['admin', 'user'])
        roles.setdefault('delete', ['admin'])
        data.setdefault('fields', [])
        for field in data['fields']:
            field.setdefault('type', 'text')
            field.setdefault('required', False)
            if field['type'] not in FIELD_TYPES:
                raise ValueError(f"未対応のフィールド型: {field['type']} ({form_id})")
        forms[form_id] = data
    return forms


def can_access(form_def: dict, action: str, role: str) -> bool:
    allowed = form_def.get('roles', {}).get(action, [])
    return role in allowed


def list_viewable_forms(forms: dict, role: str) -> list:
    return [f for f in forms.values() if can_access(f, 'view', role)]
