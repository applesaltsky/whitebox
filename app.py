#get global config
from global_config import global_config
from global_db_control import DBController
from session_control import SessionController

from fastapi import FastAPI, Response, Request, Form, Query, Cookie
from fastapi.responses import RedirectResponse
import uvicorn, jinja2, psutil

from uuid import uuid4
from datetime import datetime
import time
from pathlib import Path

#init session control
session_controller = SessionController()

#init db, and db control
db_controller = DBController()
db_controller.init_db(db_path=global_config.PATH_DB)

#push one admin to user db
empty_user_db = db_controller.get_max_user_idx() == -1
if empty_user_db:
    admin_user_info = {
        'user_idx':0,
        'user_id':global_config.admin_id,
        'user_password':global_config.admin_pw,
        'user_find_password_questsion':'-',
        'user_find_password_answer':'-',
        'user_email':'aer0700@naver.com'
    }
    db_controller.push_user(user_idx=admin_user_info['user_idx'],
                    user_id=admin_user_info['user_id'],
                    user_password=admin_user_info['user_password'],
                    user_find_password_question=admin_user_info['user_find_password_questsion'],
                    user_find_password_answer=admin_user_info['user_find_password_answer'],
                    user_email=admin_user_info['user_email'],
                    created_time=datetime.now(),
                    previlage='admin')    

#create fastapi application instance
app = FastAPI()

#set middleware
@app.middleware('http')
def add_logger(request:Request, call_next):
    start_time = time.time()
    response = call_next(request)
    process_time = time.time() - start_time
    memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)
    print(datetime.now(), ' url : ', request.url, ' method :', request.method, f' proc_time : {process_time:.4f} sec', f' memory_usage : {memory_usage_mb:.2f} MB')
    return response

@app.middleware('http')
def del_old_session(request:Request, call_next):
    print(session_controller.session_db)
    session_controller.del_old_session(max_age=global_config.max_session_age)
    response = call_next(request)
    return response


@app.middleware('http')
async def confirm_valid_client_session(request:Request, call_next):
    session_id = request.cookies.get('session_id')
    login_client = session_id is not None
    invalid_session = session_controller.get_session(session_id) is None
    if login_client and invalid_session:
        print(f'invalid client session : {session_id}')
        response = RedirectResponse(url = '/')
        response.set_cookie(key='session_id',
                            value='-',
                            max_age=0
                            )
        return response
    
    response = await call_next(request)
    return response


@app.middleware('http')
async def confirm_admin_client_session(request:Request, call_next):
    url_path = request.url.path
    admin_path = r'/admin/' in url_path
    if not admin_path:
        response = await call_next(request)
        return response

    session_id = request.cookies.get('session_id')
    login_client = session_id is not None
    if not login_client:
        response = RedirectResponse(url = '/')
        return response

    user_info = session_controller.get_session(session_id)
    invalid_session = user_info is None
    if invalid_session:
        response = RedirectResponse(url = '/')
        response.set_cookie(key='session_id',
                            value='-',
                            max_age=0
                            )
        return response
    
    user_previlage = user_info['previlage']
    admin_previlage = user_previlage == 'admin'
    if not admin_previlage:
        response = RedirectResponse(url = '/')
        return response
        
    response = await call_next(request)
    return response



#set routing
@app.get('/')
def home_handler(session_id:str = Cookie(default='-')):
    template = 'home.html'
    with open(Path(global_config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()
    user_info = session_controller.get_session(session_id)
    content_list = db_controller.get_content_list()
    content_list = sorted(content_list, key=lambda content : content['created_time'], reverse=True)
    body = jinja2.Template(body).render(**{"content_list":content_list,"user_info":user_info})
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)


@app.get('/content')
def submit_content_form_handler(session_id:str = Cookie(default='-')):
    user_info = session_controller.get_session(session_id)
    if user_info is None:
        return RedirectResponse(url='/')
    
    with open(Path(global_config.PATH_TEMPLATES,'content.html'),'rt',encoding='utf-8') as f:
        body = f.read()
    body = jinja2.Template(body).render(**{
                                           "user_info":user_info,
                                           'category_list':global_config.category_list
                                           }
                                        )
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/content')
def submit_content_request_handler(title:str = Form(default='test'), 
                                   category:str=Form(default='test'), 
                                   content:str = Form(default='test'),
                                   session_id:str = Cookie(default='-')):
    user_info = session_controller.get_session(session_id)
    if user_info is None:
        return RedirectResponse(url='/')
    new_content_idx = db_controller.get_max_content_idx()+1
    db_controller.push_content(content_idx = new_content_idx, 
                               user_idx = user_info['user_idx'], 
                               title = title, 
                               category = category,
                               created_time = datetime.now(),
                               content=content)
    status_code = 303  #see other
    return RedirectResponse(url='/', status_code=status_code)

@app.get('/content/{content_idx}')
def serve_content(content_idx:int,session_id:str = Cookie(default='-')):
    template = 'content__content_idx.html'
    with open(Path(global_config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()
    content = db_controller.get_content(content_idx)
    content['content'] = content['content'].replace("`","\`")
    user_info = session_controller.get_session(session_id)
    body = jinja2.Template(body).render(**{'content':content,'user_info':user_info})
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/user')
def submit_user_form_handler(error_message:str = Query(default=' ')):
    '''
    serve create account form
    '''
    with open(Path(global_config.PATH_TEMPLATES,'user.html'),'rt',encoding='utf-8') as f:
        body = f.read()
    body = jinja2.Template(body).render(**{'error_message':error_message.replace('_',' ')})
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/user')
def submit_user_request_handler(user_id:str=Form(default='-'),
                                user_password:str=Form(default='-'),
                                user_password_confirm:str=Form(default='-'),
                                user_find_password_question:str=Form(default='-'),
                                user_find_password_answer:str=Form(default='-'),
                                user_email:str=Form(default='-')
                                ):
    '''
    handle create account request
    '''
    
    def valid_user_id(user_id:str):
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
    
    def valid_user_password(user_password:str, user_password_confirm:str):
        too_short_user_password = len(user_id) < 5
        if too_short_user_password:
            error_message = 'user_password must be longer then 5.'
            return (False, error_message)
        
        double_confirm_fail = user_password != user_password_confirm
        if double_confirm_fail:
            error_message = 'double confirm password fail. please check your input.'
            return (False, error_message)
        
        error_message = None
        return (True, error_message)

    for validation, error_message in [valid_user_id(user_id),valid_user_password(user_password,user_password_confirm)]:
        if validation is not True:
            status_code = 303  #see other
            error_message = error_message.replace(' ','_')
            return RedirectResponse(url=f'/user?error_message={error_message}', status_code=status_code)
        
    new_user_idx = db_controller.get_max_user_idx() + 1
    db_controller.push_user(user_idx=new_user_idx,
                            user_id=user_id,
                            user_password=user_password,
                            user_find_password_question=user_find_password_question,
                            user_find_password_answer=user_find_password_answer,
                            user_email=user_email,
                            created_time=datetime.now(),
                            previlage='user')
    status_code = 303  #see other
    return RedirectResponse(url='/login', status_code=status_code)

@app.get('/login')
def serve_user_login_form(error_message:str = Query(default=' ')):
    template = 'login.html'
    with open(Path(global_config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()
    body = jinja2.Template(body).render(**{'error_message':error_message.replace("_"," ")})
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/login')
def user_login_requests_handler(user_id:str=Form(default='-'),user_password:str=Form(default='-')):
    user_info = db_controller.get_user_with_id_password(user_id,user_password)
    invalid_user_info = user_info is None
    if invalid_user_info:
        status_code = 303
        error_message = 'user id or password is not correct. please check your input.'.replace(' ','_')
        return RedirectResponse(url=f'/login?error_message={error_message}', status_code=status_code)
        
    status_code = 303  #see other
    response = RedirectResponse(url='/', status_code=status_code)

    max_age_session = global_config.max_session_age  #sec
    session_id = str(uuid4())
    response.set_cookie(key='session_id',
                        value=session_id,
                        max_age=max_age_session
                        )
    session_controller.push_session(session_id,user_info)
    return response

@app.post('/logout')
def user_logout_requests_handler(session_id:str = Cookie(default='-')):
    status_code = 303  #see other
    response =  RedirectResponse(url='/', status_code=status_code)
    response.set_cookie(key='session_id',
                        value="-",
                        max_age=0)
    session_controller.del_session(session_id)
    return response

@app.get('/admin/user')
def serve_user_list_page(session_id:str = Cookie(default='-')):
    template = 'admin__user.html'
    with open(Path(global_config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()
    user_list = db_controller.get_user_list(init_row_idx=None,row_count=None)
    body = jinja2.Template(body).render(**{'user_list':user_list})
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)


if __name__ == "__main__":
    print(f"server started : {global_config.time_server_started}")
    uvicorn.run("__main__:app",port=5000,reload=global_config.reload)