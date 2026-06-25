import os, sys
import logging
from config import Config

def setup(log_type: str):
    c = Config()

    # ログディレクトリを取得（なければ作成）
    log_dir = c.get('logging', 'log_dir')
    if not os.path.isabs(log_dir):
        log_dir = os.path.join(c.base_dir, log_dir)
    os.makedirs(log_dir, exist_ok=True)
    
    # ログファイルのパスを作成
    log_path = os.path.join(log_dir, log_type)

    # ログ設定（すでに設定済みならスキップ）
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s:%(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)  # コンソール出力
            ]
        )

    # グローバル例外ハンドラも設定（未処理例外をログに記録）
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.critical("未処理の例外が発生しました", exc_info=(exc_type, exc_value, exc_traceback))

    # exceptionhook設定（すでに設定済みならスキップ）
    if sys.excepthook == sys.__excepthook__:
        sys.excepthook = handle_exception

    return log_path


if __name__ == "__main__":
    
    setup("test.log")

    try:
        print(1 / 0)
    except Exception as e:
        logging.exception("エラーが発生しました")