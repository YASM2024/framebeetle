import os
import sqlite3
import flask
from log import setup
from config import Config
from utils import get_base_dir

setup('server.log')
server = flask.Flask(__name__)

c = Config()
host     = c.get('server', 'addr')
port     = c.get('server', 'port')
database = os.path.join(get_base_dir(), c.get('server', 'database'))

def init_db():
    if not os.path.exists(database):
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        # ここで必要なテーブルを作成する
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

@server.route("/")
def home():
    context = {
        "title": c.get('app', 'appname'),
        "user_name": "mimi",
        "footer": c.get('app', 'developer'),
    }
    return flask.render_template("home.html", **context)

if __name__ == "__main__":
    init_db()
    server.run(host=host, port=port)#, debug=True)

