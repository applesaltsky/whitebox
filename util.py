class Checker:
    """
    all method of checker should return boolean
    """
    def is_admin_url(self,url:str)->bool:
        return r'/admin' in str(url)

    def is_login_client(self,session_id:str)->bool:
        return session_id is not None

    def is_valid_session_id(self,
                                session_controller, 
                                session_id:dict|None)->bool:
        user_info = session_controller.get_session(session_id)
        return user_info is not None
    
    def is_admin(self,user_info:dict|None)->bool:
        if user_info is None:
            raise ValueError("user_info is None. you should call checker.is_valid_session_id() before call checker.is_admin()")
        return user_info['previlage'] == 'admin'
    
    def is_admin_session(self,session_controller,session_id:str)->bool:
        user_info = session_controller.get_session(session_id)
        if user_info is None:
            return False
        return user_info['previlage'] == 'admin'

    
    def is_author(self,content:dict,user_info:dict)->bool:
        return content['user_idx'] == user_info['user_idx']
    
    def is_author_comment(self,comment:dict, user_info:dict)->bool:
        return comment['user_idx'] == user_info['user_idx']
    
    def is_valid_user_info(self,user_info:dict|None)->bool:
        return user_info is not None
    
    def is_same_user_info_db_and_session(self, user_info_in_db, user_info_in_session):
        if user_info_in_db is None or user_info_in_session is None:
            return False
        return user_info_in_db['user_idx'] == user_info_in_session['user_idx']
    
    def valid_user_id(self, db_controller, user_id:str):
        too_short_user_id = len(user_id) < 5
        if too_short_user_id:
            error_message = 'user_id must be longer then 5.'
            return (False, error_message)
        
        exist_user_id = db_controller.exist_user_id(user_id)
        if exist_user_id:
            error_message = f'user_id({user_id}) already exists.'
            return (False, error_message)
        
        error_message = None
        return (True, error_message)
    
    def valid_user_password(self, user_password:str, user_password_confirm:str):
        too_short_user_password = len(user_password) < 8
        if too_short_user_password:
            error_message = 'user_password must be longer then 8.'
            return (False, error_message)
        
        double_confirm_fail = user_password != user_password_confirm
        if double_confirm_fail:
            error_message = 'double confirm password fail. please check your input.'
            return (False, error_message)
        
        error_message = None
        return (True, error_message)


class Logger:
    def logging(self,message):
        return message