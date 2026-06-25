import os
import logging
import flask
from log import setup
from config import Config
from utils import get_base_dir
from db import (
    init_db, list_users, create_user, update_user, delete_user,
    get_user_by_id, list_operation_logs, ROLE_LABELS, ROLES,
)
from auth import (
    authenticate, login_user, logout_user, current_user, is_admin,
    login_required, admin_required, log_action,
)
from forms_loader import load_form_definitions, list_viewable_forms
from crud import (
    ensure_table, list_records, get_record, create_record,
    update_record, delete_record, check_permission,
)

setup('server.log')
server = flask.Flask(__name__)

c = Config()
host = c.get('server', 'addr')
port = c.get('server', 'port')
database = os.path.join(get_base_dir(), c.get('server', 'database'))
forms_dir = os.path.join(get_base_dir(), 'forms')
server.secret_key = c.get('app', 'secret_key', fallback='framebeetle-dev-key')

FORM_DEFINITIONS = {}


def reload_forms():
    global FORM_DEFINITIONS
    FORM_DEFINITIONS = load_form_definitions(forms_dir)
    for form_def in FORM_DEFINITIONS.values():
        ensure_table(database, form_def)


def app_context():
    user = current_user()
    return {
        'title': c.get('app', 'appname'),
        'footer': c.get('app', 'developer'),
        'current_user': user,
        'is_admin': user and user['role'] == 'admin',
    }


@server.context_processor
def inject_globals():
    return app_context()


@server.errorhandler(404)
def not_found(e):
    flask.flash('ページが見つかりません。', 'danger')
    return flask.redirect(flask.url_for('home'))


@server.errorhandler(500)
def server_error(e):
    logging.exception('サーバーエラー')
    flask.flash('システムエラーが発生しました。操作ログを確認するか、管理者に連絡してください。', 'danger')
    return flask.redirect(flask.url_for('home'))


@server.route('/login', methods=['GET', 'POST'])
def login():
    if current_user():
        return flask.redirect(flask.url_for('home'))
    if flask.request.method == 'POST':
        username = flask.request.form.get('username', '').strip()
        password = flask.request.form.get('password', '')
        user = authenticate(database, username, password)
        if user:
            login_user(user)
            log_action(database, 'ログイン', '認証', f'ユーザー: {username}')
            next_url = flask.request.args.get('next') or flask.url_for('home')
            flask.flash(f'{user["display_name"]} さん、ようこそ。', 'success')
            return flask.redirect(next_url)
        flask.flash('ユーザー名またはパスワードが正しくありません。', 'danger')
    return flask.render_template('login.html')


@server.route('/logout')
def logout():
    user = current_user()
    if user:
        log_action(database, 'ログアウト', '認証', f'ユーザー: {user["username"]}')
    logout_user()
    flask.flash('ログアウトしました。', 'info')
    return flask.redirect(flask.url_for('login'))


@server.route('/')
@login_required
def home():
    user = current_user()
    forms = list_viewable_forms(FORM_DEFINITIONS, user['role'])
    return flask.render_template('home.html', forms=forms)


@server.route('/forms/<form_id>')
@login_required
def form_list(form_id):
    form_def = FORM_DEFINITIONS.get(form_id)
    if not form_def:
        flask.flash('フォームが見つかりません。', 'danger')
        return flask.redirect(flask.url_for('home'))
    user = current_user()
    err = check_permission(form_def, 'view', user['role'])
    if err:
        flask.flash(err, 'danger')
        return flask.redirect(flask.url_for('home'))
    records = list_records(database, form_def)
    list_cols = form_def.get('list_columns') or [f['name'] for f in form_def['fields'][:3]]
    return flask.render_template(
        'crud_list.html', form_def=form_def, records=records, list_cols=list_cols,
        can_create=not check_permission(form_def, 'create', user['role']),
        can_edit=not check_permission(form_def, 'edit', user['role']),
        can_delete=not check_permission(form_def, 'delete', user['role']),
    )


@server.route('/forms/<form_id>/new', methods=['GET', 'POST'])
@login_required
def form_new(form_id):
    form_def = FORM_DEFINITIONS.get(form_id)
    if not form_def:
        flask.flash('フォームが見つかりません。', 'danger')
        return flask.redirect(flask.url_for('home'))
    user = current_user()
    err = check_permission(form_def, 'create', user['role'])
    if err:
        flask.flash(err, 'danger')
        return flask.redirect(flask.url_for('form_list', form_id=form_id))
    if flask.request.method == 'POST':
        record_id, errors = create_record(database, form_def, flask.request.form, user['username'])
        if errors:
            for msg in errors:
                flask.flash(msg, 'danger')
            return flask.render_template('crud_form.html', form_def=form_def, record=flask.request.form, is_new=True)
        log_action(database, '新規登録', form_def['title'], f'ID: {record_id}')
        flask.flash('登録しました。', 'success')
        return flask.redirect(flask.url_for('form_list', form_id=form_id))
    return flask.render_template('crud_form.html', form_def=form_def, record={}, is_new=True)


@server.route('/forms/<form_id>/<int:record_id>/edit', methods=['GET', 'POST'])
@login_required
def form_edit(form_id, record_id):
    form_def = FORM_DEFINITIONS.get(form_id)
    if not form_def:
        flask.flash('フォームが見つかりません。', 'danger')
        return flask.redirect(flask.url_for('home'))
    user = current_user()
    err = check_permission(form_def, 'edit', user['role'])
    if err:
        flask.flash(err, 'danger')
        return flask.redirect(flask.url_for('form_list', form_id=form_id))
    record = get_record(database, form_def, record_id)
    if not record:
        flask.flash('データが見つかりません。', 'danger')
        return flask.redirect(flask.url_for('form_list', form_id=form_id))
    if flask.request.method == 'POST':
        errors = update_record(database, form_def, record_id, flask.request.form, user['username'])
        if errors:
            for msg in errors:
                flask.flash(msg, 'danger')
            return flask.render_template('crud_form.html', form_def=form_def, record=flask.request.form, is_new=False)
        log_action(database, '更新', form_def['title'], f'ID: {record_id}')
        flask.flash('更新しました。', 'success')
        return flask.redirect(flask.url_for('form_list', form_id=form_id))
    return flask.render_template('crud_form.html', form_def=form_def, record=record, is_new=False)


@server.route('/forms/<form_id>/<int:record_id>/delete', methods=['POST'])
@login_required
def form_delete(form_id, record_id):
    form_def = FORM_DEFINITIONS.get(form_id)
    if not form_def:
        flask.flash('フォームが見つかりません。', 'danger')
        return flask.redirect(flask.url_for('home'))
    user = current_user()
    err = check_permission(form_def, 'delete', user['role'])
    if err:
        flask.flash(err, 'danger')
        return flask.redirect(flask.url_for('form_list', form_id=form_id))
    delete_record(database, form_def, record_id)
    log_action(database, '削除', form_def['title'], f'ID: {record_id}')
    flask.flash('削除しました。', 'success')
    return flask.redirect(flask.url_for('form_list', form_id=form_id))


@server.route('/admin/users')
@admin_required
def admin_users():
    users = list_users(database)
    return flask.render_template('admin_users.html', users=users, role_labels=ROLE_LABELS)


@server.route('/admin/users/new', methods=['GET', 'POST'])
@admin_required
def admin_user_new():
    if flask.request.method == 'POST':
        username = flask.request.form.get('username', '').strip()
        password = flask.request.form.get('password', '')
        display_name = flask.request.form.get('display_name', '').strip()
        role = flask.request.form.get('role', 'user')
        if not username or not password or not display_name:
            flask.flash('ユーザー名・表示名・パスワードは必須です。', 'danger')
        elif role not in ROLES:
            flask.flash('ロールが不正です。', 'danger')
        else:
            try:
                create_user(database, username, password, display_name, role)
                log_action(database, 'ユーザー作成', '管理', f'ユーザー: {username}')
                flask.flash('ユーザーを作成しました。', 'success')
                return flask.redirect(flask.url_for('admin_users'))
            except Exception:
                flask.flash('ユーザーの作成に失敗しました。ユーザー名が重複している可能性があります。', 'danger')
    return flask.render_template('admin_user_form.html', user=None, roles=ROLES, role_labels=ROLE_LABELS)


@server.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_user_edit(user_id):
    user = get_user_by_id(database, user_id)
    if not user:
        flask.flash('ユーザーが見つかりません。', 'danger')
        return flask.redirect(flask.url_for('admin_users'))
    if flask.request.method == 'POST':
        display_name = flask.request.form.get('display_name', '').strip()
        role = flask.request.form.get('role', 'user')
        is_active = flask.request.form.get('is_active') == '1'
        password = flask.request.form.get('password', '')
        if not display_name:
            flask.flash('表示名は必須です。', 'danger')
        elif role not in ROLES:
            flask.flash('ロールが不正です。', 'danger')
        else:
            update_user(database, user_id, display_name, role, is_active, password)
            log_action(database, 'ユーザー更新', '管理', f'ユーザー: {user["username"]}')
            flask.flash('ユーザーを更新しました。', 'success')
            return flask.redirect(flask.url_for('admin_users'))
    return flask.render_template('admin_user_form.html', user=user, roles=ROLES, role_labels=ROLE_LABELS)


@server.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_user_delete(user_id):
    user = get_user_by_id(database, user_id)
    if not user:
        flask.flash('ユーザーが見つかりません。', 'danger')
        return flask.redirect(flask.url_for('admin_users'))
    if user['username'] == current_user()['username']:
        flask.flash('自分自身は削除できません。', 'danger')
        return flask.redirect(flask.url_for('admin_users'))
    delete_user(database, user_id)
    log_action(database, 'ユーザー削除', '管理', f'ユーザー: {user["username"]}')
    flask.flash('ユーザーを削除しました。', 'success')
    return flask.redirect(flask.url_for('admin_users'))


@server.route('/admin/logs')
@admin_required
def admin_logs():
    logs = list_operation_logs(database)
    return flask.render_template('admin_logs.html', logs=logs)


if __name__ == '__main__':
    init_db(database)
    reload_forms()
    server.run(host=host, port=port)
