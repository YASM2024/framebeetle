import os, sys
import time, shutil
import subprocess
from config import Config

def get_current_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def exit_test(msg: str = ''):
    print(msg)
    input("プログラムを終了します。何かキーを押してください...")

def main():
    c = Config()
    current_dir = get_current_dir()
    pyinstaller_path = os.path.dirname(c.get('dev', 'python_path'))

    app_exe_path = os.path.join(current_dir, "app.exe")
    app_py_path = os.path.join(current_dir, "app.py")
    conf_ini_path = os.path.join(current_dir, "conf.ini")

    print(f"{app_py_path}のビルドを開始します...\n")
    error_flg = False
    if os.path.exists(app_exe_path): os.remove(app_exe_path); time.sleep(3)
    if not os.path.isfile(app_py_path): exit_test(msg = f"{app_py_path}が見当たりません。\n"); error_flg = True
    if not os.path.isfile(conf_ini_path): exit_test(msg = f"{conf_ini_path}が見当たりません。\n"); error_flg = True
    if error_flg: return

    try:
        subprocess.run([
            os.path.join(pyinstaller_path, "pyinstaller"),
            app_py_path,
            "--onefile",
            "--add-data", f"{conf_ini_path};."
        ], cwd=pyinstaller_path)
        built_path = os.path.join(pyinstaller_path, "dist", "app.exe")
        shutil.copy2(built_path, app_exe_path)
        
    except subprocess.CalledProcessError as e:
        input(f"ビルドに失敗しました。{e}\n\n終了するには何かキーを押してください...")
        return

    try:
        # app.exe を実行
        subprocess.run([app_exe_path])

    except subprocess.CalledProcessError as e:
        input(f"エラーが発生しました: {e}。\n\nプログラムのテストを終了します。何かキーを押してください...")
        sys.exit(1)

if __name__ == "__main__":
    main()
    
