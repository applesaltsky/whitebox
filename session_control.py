from datetime import datetime,timedelta
import time

class SessionController:
    def __init__(self):
        #in memory session
        self.session_db = []


    def push_session(self,session_id:str,user_info:dict):
        new_session = {
                        'session_id':session_id,
                        'user_info':user_info,
                        'created_time':datetime.now()
                      }
        self.session_db.append(new_session)

    def delete_old_session(self,max_age:int):
        def is_alived_session(session):
            expired_time = session['created_time'] + timedelta(seconds=max_age)
            return expired_time > datetime.now()
        self.session_db = list(filter(is_alived_session,self.session_db))

    def get_session(self,session_id:str)->dict|None:
        for session in self.session_db:
            if session['session_id'] == session_id:
                return session['user_info']
        return None
    
    def delete_session(self,session_id:str):
        filter_session = lambda session:session['session_id']!=session_id
        self.session_db = list(filter(filter_session,self.session_db))




        
