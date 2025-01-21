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
        self.NAME_IMAGE_TABLE = 'IMAGE_TABLE'
        self.PATH_TEMPLATES = Path(self.PATH_PROJECT,'templates')
        self.PATH_STATIC = Path(self.PATH_PROJECT,'static')
        self.PATH_JAVASCRIPT = Path(self.PATH_STATIC,'js')
        self.PATH_CSS = Path(self.PATH_STATIC,'css')
        self.PATH_IMAGE = Path(self.PATH_STATIC,'images')
        if not os.path.exists(self.PATH_IMAGE):
            os.makedirs(self.PATH_IMAGE)

        folders = [
                    self.PATH_DB.parent, 
                    self.PATH_TEMPLATES, 
                    self.PATH_STATIC,
                    self.PATH_JAVASCRIPT,
                    self.PATH_CSS,
                    self.PATH_IMAGE
                   ]
         
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)

        self.time_server_started = datetime.now()
        self.time_format = "%Y-%m-%d %H:%M:%S"
        self.reload = False
        if is_windows():
            self.reload = True

        #Delete unused image function is executed every {self.cycle_delete_unused_image} requests.
        self.cycle_delete_unused_image = 1000

        self.max_session_age = 3600 * 12  #sec 

        self.category_list = ['DataProcessing','Backend','ComputerScience']

        self.admin_id = os.getenv("ADMIN_ID")
        self.admin_pw = os.getenv("ADMIN_PW")


        self.PORT = 5000
         

global_config = GlobalConfig()
