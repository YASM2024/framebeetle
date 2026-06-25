import sys, os
import configparser

class Config:

    def __init__(self):
        self._base_dir = os.path.dirname(
            sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            )


    @property
    def base_dir(self):
        return self._base_dir
    
    def get(self, section: str, option: str, fallback=None):
        config = configparser.ConfigParser()
        config_path = os.path.join(self.base_dir, 'conf.ini')
        config.read(config_path, encoding='utf-8')
        if fallback is not None and not config.has_option(section, option):
            return fallback
        return config.get(section, option)
    

if __name__ == "__main__":
    
    # from config import Config
    c = Config()
    print(c.base_dir)
    print(c.get('dev', 'python_path'))
