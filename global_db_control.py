import jinja2

import os, sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

class DBController:
    def __init__(self):
        self.db_path:Path = Path()

        self.SQL_PRAGMA = '''
        PRAGMA foreign_keys = ON;
        '''

        #(0, 0, 'hello world!', '20250117181554', 'test world')
        self.SQL_INIT_CONTENT_TABLE = '''
            CREATE TABLE IF NOT EXISTS CONTENT_TABLE (
                content_idx INTEGER PRIMARY KEY,
                user_idx INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                created_time TEXT NOT NULL,
                content TEXT NOT NULL
            )
        '''       

        self.SQL_INIT_COMMENT_TABLE = '''
            CREATE TABLE IF NOT EXISTS COMMENT_TABLE (
                comment_idx INTEGER PRIMARY KEY,
                content_idx INTEGER NOT NULL,
                user_idx INTEGER NOT NULL,
                created_time TEXT NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY (content_idx) REFERENCES ParentTable(content_idx) ON DELETE CASCADE
            )
        '''     

        self.SQL_INIT_USER_TABLE = '''
            CREATE TABLE IF NOT EXISTS USER_TABLE (
                user_idx INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                user_password TEXT NOT NULL,
                user_find_password_question TEXT NOT NULL,
                user_find_password_answer TEXT NOT NULL,
                user_email TEXT NOT NULL,
                created_time TEXT NOT NULL,
                previlage TEXT NOT NULL
            )
        '''

        self.SQL_PUSH_CONTENT = jinja2.Template(
        """
        INSERT 
        INTO CONTENT_TABLE (
            content_idx,
            user_idx,
            title,
            category,
            created_time,
            content
        )
        VALUES (
            {{content_idx}}, 
            {{user_idx}}, 
            "{{title}}", 
            "{{category}}",
            "{{created_time}}", 
            "{{content}}"
        )
        """
        )

        self.SQL_MAX_CONTENT_IDX = """
        SELECT MAX(content_idx)
        FROM CONTENT_TABLE
        """
        
        self.SQL_COUNT_CONTENT = """
        SELECT COUNT(content_idx)
        FROM CONTENT_TABLE
        """    

        self.SQL_GET_ALL_CONTENT = """
        SELECT  content_idx, 
                user_idx, 
                title, 
                category, 
                created_time, 
                content
        FROM CONTENT_TABLE
        """

        self.SQL_GET_CONTENT = jinja2.Template("""
        SELECT  content_idx, 
                user_idx, 
                title, 
                category, 
                created_time, 
                content
        FROM CONTENT_TABLE
        WHERE 1=1 
            AND CONTENT_IDX = {{content_idx}}
        """)

        self.SQL_GET_ALL_USER = """
        SELECT  user_idx,
                user_id,
                user_password,
                user_find_password_question,
                user_find_password_answer,
                user_email,
                created_time,
                previlage
        FROM USER_TABLE
        """

        self.SQL_FIND_USER_WITH_ID = jinja2.Template("""
        SELECT user_idx,
               user_id,
               user_password,
               user_find_password_question,
               user_find_password_answer,
               user_email,
               created_time,
               previlage
        FROM USER_TABLE
        WHERE 1=1
            AND USER_ID = "{{USER_ID}}"
        """)

        self.SQL_FIND_USER_WITH_IDX = jinja2.Template("""
        SELECT user_idx,
               user_id,
               user_password,
               user_find_password_question,
               user_find_password_answer,
               user_email,
               created_time,
               previlage
        FROM USER_TABLE
        WHERE 1=1
            AND USER_IDX = {{USER_IDX}}
        """)

        self.SQL_FIND_USER_WITH_ID_PW = jinja2.Template("""
        SELECT user_idx,
               user_id,
               user_password,
               user_find_password_question,
               user_find_password_answer,
               user_email,
               created_time,
               previlage
        FROM USER_TABLE
        WHERE 1=1
            AND USER_ID = "{{USER_ID}}"  
            AND USER_PASSWORD = "{{USER_PASSWORD}}"                                              
        """)

        self.SQL_MAX_USER_IDX = """
        SELECT MAX(user_idx)
        FROM USER_TABLE
        """

        self.SQL_PUSH_USER = jinja2.Template(
        """
        INSERT 
        INTO USER_TABLE (
            user_idx,
            user_id,
            user_password,
            user_find_password_question,
            user_find_password_answer,
            user_email,
            created_time,
            previlage
        )
        VALUES (
            {{user_idx}}, 
            "{{user_id}}", 
            "{{user_password}}", 
            "{{user_find_password_question}}", 
            "{{user_find_password_answer}}",
            "{{user_email}}",
            "{{created_time}}",
            "{{previlage}}"
        )
        """
        )

    def init_db(self,db_path:Path|str,init:bool=False):
        self.db_path:Path = Path(db_path)

        if init is True:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute(self.SQL_INIT_CONTENT_TABLE)
            cursor.execute(self.SQL_INIT_COMMENT_TABLE)
            cursor.execute(self.SQL_INIT_USER_TABLE)

            conn.commit()
    
    def push_content(self,
                    content_idx:int, 
                    user_idx:int,
                    title:str, 
                    category:str,
                    created_time:datetime,
                    content:str):
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            SQL_PUSH_CONTENT = self.SQL_PUSH_CONTENT.render(**{
                                                            'content_idx':content_idx,
                                                            'user_idx':user_idx,
                                                            'title':title,
                                                            'category':category,
                                                            'created_time':created_time.strftime("%Y%m%d%H%M%S"),
                                                            'content':content
                                                            })
            cursor.execute(SQL_PUSH_CONTENT)
            conn.commit()

    def get_max_content_idx(self)->int:
        ''' 
        return integer
        if content table is empty, return -1
        '''
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            for i in cursor.execute(self.SQL_MAX_CONTENT_IDX):
                rst = i[0]
                break

            NO_CONTENT = rst is None
            if NO_CONTENT:
                return -1
            else:
                return rst
            
    def get_content_list(self,init_row_idx=None,row_count=None)->tuple:
        SQL = self.SQL_GET_ALL_CONTENT
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = []
            for content_idx,user_idx,title,category,created_time,content in cursor.execute(SQL):
                rst.append({
                            'content_idx':content_idx,
                            'user_idx':user_idx,
                            'title':title,
                            'category':category,
                            'created_time':created_time,
                            'content':content
                            })
            return rst
                   
    def get_content(self,content_idx:int)->tuple:
        """
        return {
                    'content_idx':content_idx,
                    'user_idx':user_idx,
                    'title':title,
                    'created_time':created_time,
                    'content':content
                }
        """
        SQL = self.SQL_GET_CONTENT.render(**{"content_idx":content_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = []
            for content_idx,user_idx,title,category,created_time,content in cursor.execute(SQL):
                rst.append({
                            'content_idx':content_idx,
                            'user_idx':user_idx,
                            'title':title,
                            'category':category,
                            'created_time':created_time,
                            'content':content
                        })
            NO_CONTENT = len(rst) == 0
            if NO_CONTENT:
                return None
            else:
                return rst[0]

    def get_max_user_idx(self)->int:
        ''' 
        return integer
        if user table is empty, return -1
        '''
        SQL = self.SQL_MAX_USER_IDX
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            for i in cursor.execute(SQL):
                rst = i[0]
                break

            NO_CONTENT = rst is None
            if NO_CONTENT:
                return -1
            else:
                return rst
            
    def exist_user_id(self,user_id:str):
        SQL = self.SQL_FIND_USER_WITH_ID.render(**{'user_id':user_id})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cnt = 0
            for i in cursor.execute(SQL):
               cnt += 1
        return cnt > 0
    
    def get_user_with_id_password(self,user_id:str,user_password:str):
        SQL = self.SQL_FIND_USER_WITH_ID_PW.render({'USER_ID':user_id,'USER_PASSWORD':user_password})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()  
            rst = None
            for user_idx,user_id, user_password, user_find_password_question, user_find_password_answer,user_email,created_time,previlage  in cursor.execute(SQL):
                rst = {
                            'user_idx':user_idx,
                            'user_id':user_id,
                            'user_password':user_password,
                            'user_find_password_question':user_find_password_question,
                            'user_find_password_answer':user_find_password_answer,
                            'user_email':user_email,
                            'created_time':created_time,
                            'previlage':previlage
                            }
                break
            return rst      
        
               
    def get_user_list(self,init_row_idx=None,row_count=None):
        SQL = self.SQL_GET_ALL_USER
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = []
            for user_idx,user_id, user_password, user_find_password_question, user_find_password_answer,user_email,created_time,previlage in cursor.execute(SQL):
                rst.append({
                            'user_idx':user_idx,
                            'user_id':user_id,
                            'user_password':user_password,
                            'user_find_password_question':user_find_password_question,
                            'user_find_password_answer':user_find_password_answer,
                            'user_email':user_email,
                            'created_time':created_time,
                            'previlage':previlage
                            })
            return rst

    def push_user(self,user_idx:int,user_id:str, user_password:str,user_find_password_question:str, user_find_password_answer:str, user_email:str, created_time:datetime, previlage:str):
        SQL = self.SQL_PUSH_USER.render(**{
                                            'user_idx':user_idx,
                                            'user_id':user_id,
                                            'user_password':user_password,
                                            'user_find_password_question':user_find_password_question,
                                            'user_find_password_answer':user_find_password_answer,
                                            'user_email':user_email,
                                            'created_time':created_time.strftime("%Y%m%d%H%M%S"),
                                            'previlage':previlage
                                           })
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL)
            conn.commit()


        
            




