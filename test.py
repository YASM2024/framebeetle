import os, sys
import subprocess
from config import Config

def get_current_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def main():
    c = Config()
    current_dir = get_current_dir()
    python_exe = c.get('dev', 'python_path')
    app_path = os.path.join(current_dir, "app.py")
    print(f"{app_path}のテストを開始します...\n")
    if not os.path.isfile(app_path):
        input(f"{app_path}が見当たりません。\n\nプログラムのテストを終了します。何かキーを押してください...")
        return
    try:
        subprocess.run([python_exe, app_path], check=True)
    
    except subprocess.CalledProcessError as e:
        input(f"エラーが発生しました: {e}。\n\nプログラムのテストを終了します。何かキーを押してください...")
        sys.exit(1)

if __name__ == "__main__":
    main()
    

