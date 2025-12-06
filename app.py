import subprocess
import os, time
import webbrowser
import signal
import logging
from log import setup
from utils import get_base_dir
from config import Config

def handle_sigterm(signum, frame):
    print("\nSIGTERM を受け取りました。サーバーを停止します。")
    app.stop_server()
    exit(0)

class App:

    def __init__(self):
        c = Config()
        self._venv_python   = c.get('dev', 'python_path')
        self._edge_path     = c.get('dev', 'edge_path')
        self._server_script = os.path.join(get_base_dir(), "server.py")
        self._ip_addr       = c.get('server', 'addr')
        self._port_no       = c.get('server', 'port')
        self._app_url       = f"http://{self._ip_addr}:{self._port_no}"
        self._server_proc   = None
        logging.info("アプリケーションが初期化されました")

    def start_server(self):
        self._server_proc = subprocess.Popen([self._venv_python, self._server_script])
        logging.info("サーバーを起動しました！")
        time.sleep(1)  # サーバー起動待ち（必要に応じて調整）

    def stop_server(self):
        if self._server_proc:
            self._server_proc.terminate()
            self._server_proc.wait()
            logging.info("サーバーを停止しました")

    def open_edge(self):
        webbrowser.register('edge', None, webbrowser.BackgroundBrowser(self._edge_path))
        webbrowser.get('edge').open(self._app_url)
        logging.info("Edgeを起動しました")


if __name__ == "__main__":
    # EdgeでURLを開く
    setup('app.log')
    # from app import App
    app = App()
    signal.signal(signal.SIGTERM, handle_sigterm)

    try:
        print("サーバーを起動しています...\n")
        app.start_server()
        app.open_edge()
        print("Ctrl + C キーでサーバーを停止します...\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        app.stop_server()
        logging.info("サーバーを停止しました。")
