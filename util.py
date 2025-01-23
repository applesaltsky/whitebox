class Checker:
    """
    all method of checker should return boolean
    """
    def is_admin_url(self,url:str)->bool:
        return r'/admin/' in str(url)

    def is_login_client(self,session_id:dict|None)->bool:
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
    
    def is_author(self,content:dict,user_info:dict)->bool:
        return content['user_idx'] == user_info['user_idx']
    
    def is_author_comment(self,comment:dict, user_info:dict)->bool:
        return comment['user_idx'] == user_info['user_idx']
    
    def is_valid_user_info(self,user_info:dict|None)->bool:
        return user_info is not None
    
