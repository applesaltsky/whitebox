from datetime import datetime
from pathlib import Path
import platform
import dotenv
import os



def is_windows():
    return platform.system() == "Windows"

class Config:
    def __init__(self):
        self.PATH_APP_PY =  Path(__file__)
        self.PATH_PROJECT = self.PATH_APP_PY.parent

        self.PATH_TEMPLATES = Path(self.PATH_PROJECT,'templates')
        self.PATH_STATIC = Path(self.PATH_PROJECT,'static')
        self.PATH_JAVASCRIPT = Path(self.PATH_STATIC,'js')
        self.PATH_CSS = Path(self.PATH_STATIC,'css')
        self.PATH_IMAGE = Path(self.PATH_STATIC,'images')

        self.PATH_DB = Path(self.PATH_PROJECT,'databases','main.db')
        self.PATH_DB_TMP = Path(self.PATH_PROJECT,'databases','tmp.db')

        self.PATH_ENV = Path(self.PATH_PROJECT,'.env')
        dotenv.load_dotenv(str(self.PATH_ENV))

        self.PATH_BCRYPT_SALT = Path(self.PATH_PROJECT,'salt.pickle')

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

        self.global_title = "whitebox"

        self.time_server_started = datetime.now()
        self.time_format = "%Y-%m-%d %H:%M:%S"
        self.reload = False
        if is_windows():
            self.reload = True

        #config write content previlage
        #self.write_content_previlage = ['admin','user']  #admin, normal user can write content
        self.write_content_previlage = ['admin']          #only admin can write content

        #config session
        self.max_session_age = 3600 * 12  #sec 

        #Delete unused image function is executed every {self.cycle_delete_unused_image} requests.
        self.cycle_delete_unused_image = 1024
        self.cycle_delete_old_log = 1024

        #page config on home.html
        self.max_page_count = 10 
        self.row_cnt_list = [5,10,20,30]

        #page config admin panel
        self.limit_admin_panel_view = 1000

        #config for logging
        self.log_timekey_format = "%Y%m%d%H%M%S"
        self.log_expiration_date = 90

        self.default_category_list = ['DataScience','Backend','ComputerScience']

        self.admin_id = os.getenv("ADMIN_ID")
        self.admin_pw = os.getenv("ADMIN_PW")


        self.PORT = 5000
         

