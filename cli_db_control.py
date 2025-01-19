from global_config import global_config
from global_db_control import DBController
import sqlite3

if __name__ == "__main__":
    #init db, and db control
    db_controller = DBController()
    db_controller.init_db(db_path=global_config.PATH_DB)

    with sqlite3.connect(str(db_controller.db_path)) as conn:
        cursor = conn.cursor()
        sql = """
        PRAGMA table_info
        (
            image_table
        )
        """
        for i in cursor.execute(sql):
            print(i)
