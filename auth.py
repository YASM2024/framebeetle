import functools
import flask
from db import verify_password, get_user_by_username, add_operation_log


def login_user(user: dict):
    flask.session['user_id'] = user['id']
    flask.session['username'] = user['username']
    flask.session['display_name'] = user['display_name']
    flask.session['role'] = user['role']


def logout_user():
    flask.session.clear()


def current_user():
    user_id = flask.session.get('user_id')
    if not user_id:
        return None
    return {
        'id': user_id,
        'username': flask.session.get('username'),
        'display_name': flask.session.get('display_name'),
        'role': flask.session.get('role'),
    }


def is_admin():
    user = current_user()
    return user and user['role'] == 'admin'


def authenticate(database: str, username: str, password: str):
    user = get_user_by_username(database, username)
    if user and verify_password(user, password):
        return user
    return None


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flask.flash('ログインが必要です。', 'warning')
            return flask.redirect(flask.url_for('login', next=flask.request.path))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            flask.flash('ログインが必要です。', 'warning')
            return flask.redirect(flask.url_for('login', next=flask.request.path))
        if user['role'] != 'admin':
            flask.flash('管理者のみ利用できます。', 'danger')
            return flask.redirect(flask.url_for('home'))
        return view(*args, **kwargs)
    return wrapped


def log_action(database: str, action: str, target: str, detail: str = ''):
    user = current_user()
    username = user['username'] if user else 'system'
    add_operation_log(database, username, action, target, detail)
