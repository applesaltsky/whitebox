import jinja2

from pathlib import Path
from datetime import datetime
import os, time, sqlite3

class DBController:
    def __init__(self):
        self.db_path:Path = Path()

        self.SQL_PRAGMA = '''
        PRAGMA foreign_keys = ON;
        '''

        self.SQL_INIT_CONTENT_TABLE = '''
            CREATE TABLE IF NOT EXISTS CONTENT_TABLE (
                content_idx INTEGER PRIMARY KEY,
                user_idx INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                created_time TEXT NOT NULL,
                updated_time TEXT NOT NULL,
                content TEXT NOT NULL,
                view_count INTEGER DEFAULT 0
            )
        '''       

        self.SQL_INIT_COMMENT_TABLE = '''
            CREATE TABLE IF NOT EXISTS COMMENT_TABLE (
                comment_idx INTEGER PRIMARY KEY,
                content_idx INTEGER NOT NULL,
                user_idx INTEGER NOT NULL,
                created_time TEXT NOT NULL,
                comment TEXT NOT NULL,
                FOREIGN KEY (content_idx) REFERENCES ParentTable(content_idx) ON DELETE CASCADE
            )
        '''     

        self.SQL_INIT_USER_TABLE = '''
            CREATE TABLE IF NOT EXISTS USER_TABLE (
                user_idx INTEGER PRIMARY KEY,
                user_id TEXT NOT NULL,
                user_password TEXT NOT NULL,
                user_password_question TEXT NOT NULL,
                user_password_answer TEXT NOT NULL,
                created_time TEXT NOT NULL,
                previlage TEXT NOT NULL
            )
        '''

        self.SQL_INIT_IMAGE_TABLE = '''
            CREATE TABLE IF NOT EXISTS IMAGE_TABLE (
                filename TEXT PRIMARY KEY,
                content_idx int
            )
        '''

        self.SQL_PUSH_CONTENT = """
        INSERT 
        INTO CONTENT_TABLE (
            content_idx,
            user_idx,
            title,
            category,
            created_time,
            updated_time,
            content,
            view_count
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """

        self.SQL_UPDATE_CONTENT = """
        UPDATE CONTENT_TABLE
        SET title = ?,
            category = ?,
            updated_time = ?,
            content = ?
        WHERE 
            content_idx = ?
        """

        self.SQL_DELETE_CONTENT = jinja2.Template("""
        DELETE 
        FROM CONTENT_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)
        

        self.SQL_MAX_CONTENT_IDX = """
        SELECT MAX(content_idx)
        FROM CONTENT_TABLE
        """
        
        self.SQL_COUNT_CONTENT = """
        SELECT COUNT(content_idx)
        FROM CONTENT_TABLE
        """    

        self.SQL_GET_CONTENT_LIST = jinja2.Template("""
        SELECT  CONTENT.content_idx, 
                CONTENT.user_idx, 
                CONTENT.title, 
                CONTENT.category, 
                CONTENT.created_time, 
                CONTENT.updated_time,
                CONTENT.content,
                CONTENT.view_count,
                USER.user_id 
        FROM
            (
                SELECT  content_idx, 
                        user_idx, 
                        title, 
                        category, 
                        created_time, 
                        updated_time,
                        content,
                        view_count
                FROM CONTENT_TABLE
                WHERE 1=1
                   {% if category %}
                        AND category = "{{category}}"
                   {% endif %}                                                                                                                            
            ) AS CONTENT,
            (
                SELECT  user_idx,
                        user_id   
                FROM USER_TABLE
            ) AS USER
        WHERE 1=1
            AND CONTENT.user_idx = USER.user_idx 
        ORDER BY CONTENT.created_time DESC 
        LIMIT {{limit}}
        """ )  

        self.SQL_GET_CONTENT = jinja2.Template("""
        SELECT   CONTENT.content_idx, 
                 CONTENT.user_idx, 
                 CONTENT.title, 
                 CONTENT.category, 
                 CONTENT.created_time,
                 CONTENT.updated_time, 
                 CONTENT.content,
                 CONTENT.view_count,
                 USER.user_id                                                                   
        FROM (
                SELECT  content_idx, 
                        user_idx, 
                        title, 
                        category, 
                        created_time, 
                        updated_time,
                        content,
                        view_count
                FROM CONTENT_TABLE
                WHERE 1=1 
                    AND CONTENT_IDX = {{content_idx}}                                                                   
            ) AS CONTENT,
            (
                SELECT  user_idx,
                        user_id   
                FROM USER_TABLE                                                                                  
            ) AS USER     
        WHERE 1=1
            AND CONTENT.user_idx = USER.user_idx                                                                                                                                            
        
        """)

        self.SQL_GET_CONTENT_VIEW_COUNT = jinja2.Template("""
        SELECT view_count
        FROM CONTENT_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)

        self.SQL_GET_CONTENT_COUNT = jinja2.Template("""
        SELECT COUNT(CONTENT_IDX)
        FROM CONTENT_TABLE
        WHERE 1=1
            {% if category %}  
               AND category = "{{category}}"                                      
            {% endif %}                                           
        """)

        self.SQL_UPDATE_CONTENT_VIEW_COUNT = jinja2.Template("""
        UPDATE CONTENT_TABLE
        SET view_count = view_count + 1
        WHERE 1=1
            AND content_idx = {{content_idx}}                                             
        """)

        self.SQL_GET_ALL_USER = """
        SELECT  user_idx,
                user_id,
                user_password,
                user_password_question,
                user_password_answer,
                created_time,
                previlage
        FROM USER_TABLE
        """

        self.SQL_GET_USER_WITH_USER_IDX = jinja2.Template("""
        SELECT  user_idx,
                user_id,
                user_password,
                user_password_question,
                user_password_answer,
                created_time,
                previlage
        FROM USER_TABLE
        WHERE 1=1
            AND user_idx = {{user_idx}}
        """)

        self.SQL_FIND_USER_WITH_ID = jinja2.Template("""
        SELECT user_idx,
               user_id,
               user_password,
               user_password_question,
               user_password_answer,
               created_time,
               previlage
        FROM USER_TABLE
        WHERE 1=1
            AND user_id = "{{user_id}}"
        """)

        self.SQL_FIND_USER_WITH_ID_PW = jinja2.Template("""
        SELECT user_idx,
               user_id,
               user_password,
               user_password_question,
               user_password_answer,
               created_time,
               previlage
        FROM USER_TABLE
        WHERE 1=1
            AND user_id = "{{user_id}}"  
            AND user_password = "{{user_password}}"                                              
        """)

        self.SQL_MAX_USER_IDX = """
        SELECT MAX(user_idx)
        FROM USER_TABLE
        """

        self.SQL_PUSH_USER = """
        INSERT 
        INTO USER_TABLE (
            user_idx,
            user_id,
            user_password,
            user_password_question,
            user_password_answer,
            created_time,
            previlage
        )
        VALUES (
            ?,
            ?, 
            ?, 
            ?, 
            ?,
            ?,
            ?
        )
        """

        self.SQL_GET_USER_PASSWORD_QUESTSION_WITH_USER_ID = jinja2.Template("""
        SELECT user_idx,
                user_id,
                user_password,
                user_password_question,
                user_password_answer,
                created_time,
                previlage
        FROM USER_TABLE 
        WHERE 1=1
            AND user_id = "{{user_id}}"                                                          
        """)
        
        self.SQL_CHECK_USER_ID_AND_USER_PASSWORD_ANSWER = jinja2.Template("""
        SELECT user_idx,
                user_id,
                user_password,
                user_password_question,
                user_password_answer,
                created_time,
                previlage
        FROM USER_TABLE 
        WHERE 1=1
            AND user_id = "{{user_id}}"
            AND user_password_answer = "{{user_password_answer}}"                                                         
        """)

        self.SQL_UPDATE_USER_PASSWORD = """
        UPDATE USER_TABLE
        SET user_password = ?
        WHERE 1=1
            AND user_idx = ?
        """

        self.SQL_UPDATE_USER = """
        UPDATE USER_TABLE
        SET user_id = ?,
            user_password = ?,
            user_password_question = ?,
            user_password_answer = ?
        WHERE 1=1
            AND user_idx = ?
        """

        self.SQL_GET_IMAGE_ALL = """
        SELECT filename
        FROM IMAGE_TABLE
        """

        self.SQL_FIND_IMAGE_WITH_CONTENT_IDX = jinja2.Template("""
        SELECT filename
        FROM IMAGE_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)

        self.SQL_DELETE_IMAGE_WITH_CONTENT_IDX = jinja2.Template("""
        DELETE 
        FROM IMAGE_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)

        self.SQL_PUSH_IMAGE = """
        INSERT
        INTO IMAGE_TABLE (
            filename,
            content_idx
        )
        VALUES (
            ?,
            ?
        )
        """

        self.SQL_GET_COMMENT = jinja2.Template("""
        SELECT comment_idx,
               content_idx,
               user_idx,
               created_time,
               comment
        FROM COMMENT_TABLE
        WHERE 1=1
            AND comment_idx = {{comment_idx}}
        """)



        self.SQL_GET_COMMENT_LIST_WITH_CONTENT_IDX = jinja2.Template("""
        SELECT comment_idx,
               content_idx,
               user_idx,
               created_time,
               comment
        FROM COMMENT_TABLE
        WHERE 1=1
            AND content_idx = {{content_idx}}
        """)

        self.SQL_GET_MAX_COMMENT_IDX = """
        SELECT max(comment_idx)
        FROM COMMENT_TABLE
        """

        self.SQL_PUSH_COMMENT = """
        INSERT
        INTO COMMENT_TABLE (
            comment_idx,
            content_idx,
            user_idx,
            created_time,
            comment
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """

        

        self.SQL_DELETE_COMMENT = jinja2.Template("""
        DELETE 
        FROM COMMENT_TABLE
        WHERE 1=1
            AND comment_idx = {{comment_idx}}
        """)

        self.SQL_DELETE_COMMENT_WITH_CONTENT_IDX = jinja2.Template("""
        DELETE
        FROM COMMENT_TABLE
        WHERE 1=1
             AND content_idx = {{content_idx}}
        """)



    def init_db(self,db_path:Path|str):
        self.db_path:Path = Path(db_path)

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute(self.SQL_INIT_CONTENT_TABLE)
            cursor.execute(self.SQL_INIT_COMMENT_TABLE)
            cursor.execute(self.SQL_INIT_USER_TABLE)
            cursor.execute(self.SQL_INIT_IMAGE_TABLE)

            conn.commit()

    def copy_to_tmp(self,db_path_tmp:Path|str):
        with open(str(db_path_tmp),'wb') as tmp:
            with open(str(self.db_path),'rb') as base:
                tmp.write(base.read())

    def push_to_base(self,db_path_tmp:Path|str):
        with open(str(db_path_tmp),'rb') as tmp:
            with open(str(self.db_path),'wb') as base:
                base.write(tmp.read())

    def delete_tmp(self,db_path_tmp:Path|str):
        os.remove(str(db_path_tmp))
    
    def push_content(self,
                    content_idx:int, 
                    user_idx:int,
                    title:str, 
                    category:str,
                    created_time:str,
                    updated_time:str,
                    content:str):
        SQL = self.SQL_PUSH_CONTENT
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            view_cnt = 0
            cursor.execute(SQL,(content_idx,
                                user_idx,
                                title,
                                category,
                                created_time,
                                updated_time,
                                content,
                                view_cnt))
            conn.commit()

    def update_content(self, 
                       content_idx:int,
                       title:str,
                       category:str,
                       updated_time:str,
                       content:str):
        SQL = self.SQL_UPDATE_CONTENT
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(title,
                                category,
                                updated_time,
                                content,
                                content_idx))
            conn.commit()

    def get_max_content_idx(self)->int:
        ''' 
        return integer
        if content table is empty, return -1
        '''
        SQL = self.SQL_MAX_CONTENT_IDX
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
            
    def get_content_count(self,category:str)->int:
        SQL = self.SQL_GET_CONTENT_COUNT.render(**{"category":category})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            for i in cursor.execute(SQL):
                return i[0]
            
    def get_content_list(self,category:str=None,page:int|None=None,row_cnt:int|None=None)->list[dict]:
        '''
        page 1 / row cnt 5  -> get 1,2,3,4,5
        page 3 / row cnt 10 -> get 21~30
        '''
        start_cnt = (page-1)*row_cnt + 1
        end_cnt = page*row_cnt
        SQL = self.SQL_GET_CONTENT_LIST.render(**{'limit':end_cnt,'category':category})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = []
            indexer = 0
            for content_idx,user_idx,title,category,created_time,updated_time,content,view_count,user_id in cursor.execute(SQL):
                indexer += 1
                if indexer >= start_cnt:
                    rst.append({
                                'content_idx':content_idx,
                                'user_idx':user_idx,
                                'title':title,
                                'category':category,
                                'created_time':created_time,
                                'updated_time':updated_time,
                                'content':content,
                                'view_count':view_count,
                                'user_id':user_id
                                })
                if indexer > end_cnt:
                    break
            return rst
        
                   
    def get_content(self,content_idx:int)->dict:
        """
        return {
                    'content_idx':content_idx,
                    'user_idx':user_idx,
                    'title':title,
                    'category':category,
                    'created_time':created_time,
                    'updated_time':created_time,
                    'content':content,
                    'user_id':user_id
                }
        """
        SQL = self.SQL_GET_CONTENT.render(**{"content_idx":content_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = []
            for content_idx,user_idx,title,category,created_time,updated_time,content,view_count,user_id in cursor.execute(SQL):
                rst.append({
                            'content_idx':content_idx,
                            'user_idx':user_idx,
                            'title':title,
                            'category':category,
                            'created_time':created_time,
                            'updated_time':updated_time,
                            'content':content,
                            'view_count':view_count,
                            'user_id':user_id
                        })
            NO_CONTENT = len(rst) == 0
            if NO_CONTENT:
                return None
            else:
                return rst[0]
            
    def delete_content(self,content_idx:int):
        SQL = self.SQL_DELETE_CONTENT.render(**{"content_idx":content_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL)
            conn.commit()

    def get_content_view_count(self,content_idx:int)->int:
        SQL = self.SQL_GET_CONTENT_VIEW_COUNT.render(**{'content_idx':content_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = None
            for row in cursor.execute(SQL):
                rst = row[0]
            if rst is None:
                rst = -1
            return rst
        
    def add_one_content_view_count(self,content_idx:int):
        SQL = self.SQL_UPDATE_CONTENT_VIEW_COUNT.render(**{'content_idx':content_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL)
            conn.commit()
               
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
        print(SQL)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cnt = 0
            for i in cursor.execute(SQL):
               cnt += 1
        return cnt > 0
    
    def get_user_with_id_password(self,user_id:str,user_password:str):
        '''
        this function makes user_info in session
        '''
        SQL = self.SQL_FIND_USER_WITH_ID_PW.render({'user_id':user_id,'user_password':user_password})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()  
            rst = None
            for user_idx,user_id, user_password, user_password_question, user_password_answer,created_time,previlage  in cursor.execute(SQL):
                rst = {
                            'user_idx':user_idx,
                            'user_id':user_id,
                            'user_password':user_password,
                            'user_password_question':user_password_question,
                            'user_password_answer':user_password_answer,
                            'created_time':created_time,
                            'previlage':previlage
                            }
                break
            return rst      
        
    def get_user_with_user_idx(self,user_idx:int):
        SQL = self.SQL_GET_USER_WITH_USER_IDX.render(**{'user_idx':user_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()  
            rst = []
            for user_idx, user_id, user_password, user_password_question, user_password_answer, created_time, previlage in cursor.execute(SQL):
                rst.append({
                            'user_idx':user_idx,
                            'user_id':user_id,
                            'user_password':user_password,
                            'user_password_question':user_password_question,
                            'user_password_answer':user_password_answer,
                            'created_time':created_time,
                            'previlage':previlage
                            })
            if len(rst) == 0:
                return None
            else:
                return rst[0]
              
    def get_user_list(self,init_row_idx=None,row_count=None):
        SQL = self.SQL_GET_ALL_USER
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = []
            for user_idx,user_id, user_password, user_password_question, user_password_answer,created_time,previlage in cursor.execute(SQL):
                rst.append({
                            'user_idx':user_idx,
                            'user_id':user_id,
                            'user_password':user_password,
                            'user_password_question':user_password_question,
                            'user_password_answer':user_password_answer,
                            'created_time':created_time,
                            'previlage':previlage
                            })
            return rst

    def push_user(self,user_idx:int,user_id:str, user_password:str,user_password_question:str, user_password_answer:str, created_time:datetime, previlage:str):
        SQL = self.SQL_PUSH_USER
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(user_idx,
                                user_id,
                                user_password,
                                user_password_question,
                                user_password_answer,
                                created_time,
                                previlage
                                )
                            )
            conn.commit()

    def update_user(self, 
                    user_idx:int, 
                    user_id:str,
                    user_password:str, 
                    user_password_question:str, 
                    user_password_answer:str):
        SQL = self.SQL_UPDATE_USER
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(
                                user_id,
                                user_password,
                                user_password_question,
                                user_password_answer,
                                user_idx,
                                )
                            )
            conn.commit()

    def get_user_password_question_with_user_id(self,user_id:str)->str|None:
        SQL= self.SQL_GET_USER_PASSWORD_QUESTSION_WITH_USER_ID.render(**{'user_id':user_id})
        rtn = None
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            for (user_idx, 
                 user_id, 
                 user_password, 
                 user_password_question, 
                 user_password_answer, 
                 created_time, 
                 previlage) in cursor.execute(SQL):
                rtn = user_password_question
        return rtn

    def check_user_id_and_user_password_answer(self,user_id:str,user_password_answer:str)->bool:
        SQL= self.SQL_CHECK_USER_ID_AND_USER_PASSWORD_ANSWER.render(**{'user_id':user_id,'user_password_answer':user_password_answer})
        rtn = False
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            for (user_idx, 
                 user_id, 
                 user_password, 
                 user_password_question,
                 user_password_answer,
                 created_time, 
                 previlage) in cursor.execute(SQL):
                rtn = True
                break
        return rtn
    
    def get_user_idx_with_user_id(self,user_id:str)->int:
        '''
        if user_id does not exists, return -1
        else, return positive integer
        '''
        SQL = self.SQL_FIND_USER_WITH_ID.render(**{'user_id':user_id})
        rtn = -1
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            for (user_idx,
                user_id,
                user_password,
                user_password_question,
                user_password_answer,
                created_time,
                previlage) in cursor.execute(SQL):
                rtn = user_idx
        return rtn  
    
    def update_user_password(self,user_idx:int, user_password:str)->int:
        SQL = self.SQL_UPDATE_USER_PASSWORD
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(user_password,user_idx))
            conn.commit()

    def get_image_all(self)->list[str]:
        SQL = self.SQL_GET_IMAGE_ALL
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            return [filename[0] for filename in cursor.execute(SQL)]

    def get_image_with_content_idx(self,content_idx:int)->list[str]:
        SQL = self.SQL_FIND_IMAGE_WITH_CONTENT_IDX.render(**{'content_idx':content_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            return [filename[0] for filename in cursor.execute(SQL)]

    def delete_image_with_content_idx(self,content_idx:int)->list[str]:
        SQL = self.SQL_DELETE_IMAGE_WITH_CONTENT_IDX.render(**{'content_idx':content_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL)
            conn.commit()

    def push_image(self,filename:str,content_idx:int):
        SQL = self.SQL_PUSH_IMAGE
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(filename, content_idx))
            conn.commit()    

    def delete_comment(self, comment_idx:int):
        SQL = self.SQL_DELETE_COMMENT.render(**{'comment_idx':comment_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL)
            conn.commit() 

    def get_max_comment_idx(self)->int:
        SQL = self.SQL_GET_MAX_COMMENT_IDX
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
            
    def get_comment(self,comment_idx:int)->dict|None:
        SQL = self.SQL_GET_COMMENT.render(**{'comment_idx':comment_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = []
            for comment_idx, content_idx, user_idx, created_time, comment in cursor.execute(SQL):
                rst.append({'comment_idx':comment_idx,
                            'content_idx':content_idx,
                            'user_idx':user_idx,
                            'created_time':created_time,
                            'comment':comment
                           })
            if len(rst) == 0:
                return None
            else:
                return rst[0]
            
    def get_comment_with_content_idx(self,content_idx:int)->list[dict]:
        SQL = self.SQL_GET_COMMENT_LIST_WITH_CONTENT_IDX.render(**{'content_idx':content_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = []
            for comment_idx, content_idx, user_idx, created_time, comment in cursor.execute(SQL):
                rst.append({'comment_idx':comment_idx,
                            'content_idx':content_idx,
                            'user_idx':user_idx,
                            'created_time':created_time,
                            'comment':comment
                           })
            return rst

    def delete_comment_with_content_idx(self, content_idx:int):
        SQL = self.SQL_DELETE_COMMENT_WITH_CONTENT_IDX.render(**{'content_idx':content_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL)
            conn.commit()

    def push_comment(self,
                     comment_idx:int,
                     content_idx:int,
                     user_idx:int,
                     created_time:str,
                     comment:str):
        SQL = self.SQL_PUSH_COMMENT
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(comment_idx, 
                                content_idx,
                                user_idx,
                                created_time,
                                comment))
            conn.commit()  

    def run_sql(self,db_path:str|Path,sql:str,limit:int)->tuple[bool,float,list]:
        SQL = sql
        rtn = []
        rtn_column = []
        run_success = False
        run_time = 0
        try:
            start = time.time()
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                for idx, row in enumerate(cursor.execute(SQL)):
                    rtn.append(row)
                    if idx > limit:
                        break

                for description in cursor.description:
                    colunm_name = description[0]
                    rtn_column.append(colunm_name)

                conn.commit()
            run_success = True
            end = time.time()
            run_time = end-start
        finally:
            return (run_success,run_time,rtn,rtn_column)
            

            




