from datetime import datetime
from pathlib import Path
import platform

def is_windows():
    return platform.system() == "Windows"

class GlobalConfig:
    def __init__(self):
        self.PATH_APP_PY =  Path(__file__)
        self.PATH_PROJECT = self.PATH_APP_PY.parent
        self.PATH_DB = Path(self.PATH_PROJECT,'databases','main.db')
        self.NAME_CONTENT_TABLE = 'CONTENT_TABLE'
        self.NAME_COMMENT_TABLE = 'COMMETN_TABLE'
        self.NAME_USER_TABLE = 'USER_TABLE'
        self.time_server_started = datetime.now()
        self.reload = False
        if is_windows():
            self.reload = True

global_config = GlobalConfig()
