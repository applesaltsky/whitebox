from global_config import global_config
from global_db_control import DBController

if __name__ == "__main__":
    #init db, and db control
    db_controller = DBController()
    db_controller.init_db(db_path=global_config.PATH_DB)

    #db_controller.delete_content(4)

    ##    print(i)