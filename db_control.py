from db_control_sql import db_control_sql

from pathlib import Path
from datetime import datetime, timedelta
import os, time, sqlite3

class DBController(db_control_sql):
    def __init__(self):
        self.db_path:Path = Path()
        super().__init__()

    def init_db(self,db_path:Path|str):
        self.db_path:Path = Path(db_path)

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()

            cursor.execute(self.SQL_INIT_CONTENT_TABLE)
            cursor.execute(self.SQL_INIT_COMMENT_TABLE)
            cursor.execute(self.SQL_INIT_USER_TABLE)
            cursor.execute(self.SQL_INIT_IMAGE_TABLE)
            cursor.execute(self.SQL_INIT_LOGGING_TABLE)
            cursor.execute(self.SQL_INIT_CATEGORY_TABLE)

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
                    category_idx:int,
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
                                category_idx,
                                created_time,
                                updated_time,
                                content,
                                view_cnt))
            conn.commit()

    def update_content(self, 
                       content_idx:int,
                       title:str,
                       category_idx:int,
                       updated_time:str,
                       content:str):
        SQL = self.SQL_UPDATE_CONTENT
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(title,
                                category_idx,
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
            
    def get_content_count(self,category_idx:str)->int:
        SQL = self.SQL_GET_CONTENT_COUNT.render(**{"category_idx":category_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            for i in cursor.execute(SQL):
                return i[0]
            
    def get_content_list(self,category:str=None,
                         page:int|None=None,
                         row_cnt:int|None=None,
                         search_pattern:str|None=None
                        )->list[dict]:
        '''
        page 1 / row cnt 5  -> get 1,2,3,4,5
        page 3 / row cnt 10 -> get 21~30
        '''
        start_cnt = (page-1)*row_cnt + 1
        end_cnt = page*row_cnt
        SQL = self.SQL_GET_CONTENT_LIST.render(**{'limit':end_cnt,'category':category,'search_pattern':search_pattern})
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
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cnt = 0
            for i in cursor.execute(SQL):
               cnt += 1
        return cnt > 0
    
    def get_user_with_id_password(self,user_id:str,user_password:str,encrypter):
        '''
        this function makes user_info in session
        '''
        SQL = self.SQL_FIND_USER_WITH_ID_PW.render({'user_id':user_id,'user_password':encrypter.encrypt(user_password)})
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

    def push_user(self,user_idx:int,user_id:str, user_password:str,user_password_question:str, user_password_answer:str, created_time:datetime, previlage:str, encrypter):
        SQL = self.SQL_PUSH_USER
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(user_idx,
                                user_id,
                                encrypter.encrypt(user_password),
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
                    user_password_answer:str,
                    encrypter):
        SQL = self.SQL_UPDATE_USER
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(
                                user_id,
                                encrypter.encrypt(user_password),
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
    
    def update_user_password(self,user_idx:int, user_password:str, encrypter)->int:
        SQL = self.SQL_UPDATE_USER_PASSWORD
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL,(encrypter.encrypt(user_password),user_idx))
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

    def run_sql(self,db_path:str|Path,sql:str,limit:int)->tuple[bool,float,list,list,bool]:
        SQL = sql
        run_success = False
        run_time = 0
        rtn = []
        rtn_column = []
        error_message = None
        try:
            start = time.time()
            with sqlite3.connect(str(db_path)) as conn:
                cursor = conn.cursor()
                c = cursor.execute(SQL)
                for idx, row in enumerate(c):
                    rtn.append(row)
                    if idx > limit:
                        break

                if cursor.description is not None:
                    for description in cursor.description:
                        colunm_name = description[0]
                        rtn_column.append(colunm_name)

                conn.commit()

            run_success = True
            end = time.time()
            run_time = end-start
        except Exception as e:
            error_message = e
        finally:
            return (run_success,run_time,rtn,rtn_column,error_message)
        
    def push_log(self, 
                 log_idx:int, 
                 timekey:int, 
                 url:str, 
                 method:str, 
                 proc_time:float, 
                 memory_usage:float, 
                 success:bool, 
                 error_message:str):
        SQL = self.SQL_PUSH_LOGGING
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL, (log_idx, 
                                timekey, 
                                url, 
                                method, 
                                proc_time, 
                                memory_usage, 
                                success, 
                                error_message
                                ))
            conn.commit() 

    def get_max_log_idx(self)->int:
        SQL = self.SQL_GET_LOG_INX_MAX
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
        
    def delete_old_log(self,log_expiration_date:int,log_timekey_format:str)->int:
        timekey = (datetime.now() - timedelta(days=log_expiration_date)).strftime(log_timekey_format)
        SQL = self.SQL_DELETE_OLD_LOG.render(**{'timekey':timekey})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL)
            conn.commit()

    def push_category(self,category_idx:int, category:str):
        SQL = self.SQL_PUSH_CATEGORY.render(**{'category_idx':category_idx,
                                               'category':category})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL)
            conn.commit()    

    def update_category(self,category_idx:int, category:str):
        SQL = self.SQL_UPDATE_CATEGORY.render(**{'category':category,
                                                 'category_idx':category_idx})
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(SQL)
            conn.commit()  

    def get_max_category_idx(self)->int:
        ''' 
        return integer
        if category table is empty, return -1
        '''

        SQL = self.SQL_MAX_CATEGORY_IDX
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
            
    def get_category_list(self)->list[dict]:
        SQL = self.SQL_GET_CATEGORY_ALL
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            rst = []
            for category_idx, category in cursor.execute(SQL):
                rst.append({'category_idx':category_idx,
                            'category':category})
        return rst

    def get_category_idx_with_category(self,category:str|None)->int|None:
        if category is None:
            return None
        SQL = self.SQL_GET_CATEGORY_IDX_WITH_CATEGORY.render(**{'category':category})
        rtn = None
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            for category_idx in cursor.execute(SQL):
                rtn = category_idx[0]
                break
        return rtn
