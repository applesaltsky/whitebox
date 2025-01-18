from datetime import datetime
from pathlib import Path
import platform
import dotenv
import os

dotenv.load_dotenv()

def is_windows():
    return platform.system() == "Windows"

class GlobalConfig:
    def __init__(self):
        self.PATH_APP_PY =  Path(__file__)
        self.PATH_PROJECT = self.PATH_APP_PY.parent
        self.PATH_DB = Path(self.PATH_PROJECT,'databases','main.db')
        self.NAME_CONTENT_TABLE = 'CONTENT_TABLE'
        self.NAME_COMMENT_TABLE = 'COMMENT_TABLE'
        self.NAME_USER_TABLE = 'USER_TABLE'
        self.PATH_TEMPLATES = Path(self.PATH_PROJECT,'templates')
        self.time_server_started = datetime.now()
        self.reload = False
        if is_windows():
            self.reload = True

        self.max_session_age = 3600 * 12  #sec 

        self.category_list = ['DataProcessing','Backend','ComputerScience']

        self.admin_id = os.getenv("ADMIN_ID")
        self.admin_pw = os.getenv("ADMIN_PW")
         

global_config = GlobalConfig()
