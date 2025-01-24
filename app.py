#import internal class
from config import Config
from db_control import DBController
from session_control import SessionController
from util import Checker

#import external package
from fastapi import FastAPI, Response, Request, Form, Query, Cookie, UploadFile
from fastapi.responses import RedirectResponse
from PIL import Image
import uvicorn, jinja2, psutil


#import standard package
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from io import BytesIO
from threading import Lock
import time,re,os


#set config and utility func
config = Config()
checker = Checker()

#init session control
session_controller = SessionController()

#init db, and db control
db_controller = DBController()
db_controller.init_db(db_path=config.PATH_DB)

#push one admin to user db
empty_user_db = db_controller.get_max_user_idx() == -1
if empty_user_db:
    admin_user_info = {
        'user_idx':0,
        'user_id':config.admin_id,
        'user_password':config.admin_pw,
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
def delete_old_session(request:Request, call_next):
    #print(session_controller.session_db)
    session_controller.delete_old_session(max_age=config.max_session_age)
    response = call_next(request)
    return response


@app.middleware('http')
async def confirm_valid_client_session(request:Request, call_next):
    session_id = request.cookies.get('session_id')
    is_login_client = checker.is_login_client(session_id)
    is_valid_session_id = checker.is_valid_session_id(session_controller,session_id)
    
    if is_login_client:
        if not is_valid_session_id:
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
    is_admin_url = checker.is_admin_url(request.url)
    if not is_admin_url:
        response = await call_next(request)
        return response

    session_id = request.cookies.get('session_id')
    is_login_client = checker.is_login_client(session_id)
    if not is_login_client:
        response = RedirectResponse(url = '/')
        return response

    is_valid_session_id = checker.is_valid_session_id(session_controller,session_id)
    if not is_valid_session_id:
        response = RedirectResponse(url = '/')
        response.set_cookie(key='session_id',
                            value='-',
                            max_age=0
                            )
        return response
    
    user_info = session_controller.get_session(session_id)
    is_admin = checker.is_admin(user_info)
    if not is_admin:
        response = RedirectResponse(url = '/')
        return response
        
    response = await call_next(request)
    return response

request_counter = 0
lock = Lock()
def delete_unused_image():
    list_used_image = db_controller.get_image_all()
    list_stored_image = os.listdir(config.PATH_IMAGE)
    for image in list_stored_image:
        if image not in list_used_image:
            os.remove(Path(config.PATH_IMAGE,image))
    
@app.middleware('http')
async def request_counter_middleware(request:Request, call_next):
    global request_counter
    MAX_REQUEST_COUNTER = 1024 * 1024

    response = await call_next(request)

    with lock:
        request_counter += 1
        if request_counter % config.cycle_delete_unused_image == 0:
            delete_unused_image()

        if request_counter >= MAX_REQUEST_COUNTER:
            request_counter = 0
    return response


#set routing
@app.get('/')
def home_handler(session_id:str = Cookie(default='-'),
                 category:str|None=Query(default=None),
                 page:int=Query(default=1),
                 row_cnt:int=Query(default=5)
                 ):
    template = 'home.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()

    user_info = session_controller.get_session(session_id)

    content_list = db_controller.get_content_list(category=category,
                                                  page=page,
                                                  row_cnt=row_cnt
                                                  )
    content_count = db_controller.get_content_count(category=category)

    page_list = []
    for i in range(config.max_page_count):
        if i * row_cnt < content_count:
            page_list.append(i+1)

    body = jinja2.Template(body).render(**{"content_list":content_list,
                                           "user_info":user_info,
                                           "category_list":config.category_list,
                                           'category':category,
                                           'page_list':page_list,
                                           'page':page,
                                           "row_cnt_list":config.row_cnt_list,
                                           "row_cnt":row_cnt,
                                           "global_title":config.global_title
                                           })
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)


@app.get('/content')
def submit_content_form_handler(session_id:str = Cookie(default='-'),
                                content_idx:int|None = Query(default=None)):
    
    is_login_client = checker.is_login_client(session_id)
    if not is_login_client:
        return RedirectResponse(url='/')
    
    with open(Path(config.PATH_TEMPLATES,'content_edit.html'),'rt',encoding='utf-8') as f:
        body = f.read()


    user_info = session_controller.get_session(session_id)

    create_content = content_idx is None
    update_content = content_idx is not None

    if create_content:
        content_idx = None
        content = None
        view_count = 0
        created_time = datetime.now().strftime(config.time_format) 
        updated_time = created_time

    #to update content, user is author or admin. else, user cannot update content.
    if update_content:
        content_idx = content_idx
        content = db_controller.get_content(content_idx)

        is_author = checker.is_author(content,user_info)
        is_admin = checker.is_admin(user_info)
        if is_author or is_admin:
            view_count = content['view_count']
            created_time = content['created_time']
            updated_time = datetime.now().strftime(config.time_format) 
        else:  
            return RedirectResponse(url='/')

    body = jinja2.Template(body).render(**{
                                           "content_idx":content_idx,
                                           'content':content,
                                           "user_info":user_info,
                                           'category_list':config.category_list,
                                           'view_count':view_count,
                                           'created_time':created_time,
                                           'updated_time':updated_time,
                                           'global_title':config.global_title
                                           }
                                        )
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/content')
def submit_content_request_handler(title:str = Form(default='test'), 
                                   category:str=Form(default='test'), 
                                   content:str = Form(default='test'),
                                   session_id:str = Cookie(default='-'),
                                   content_idx:int|None = Form(default=None)):
    
    is_login_client = checker.is_login_client(session_id)
    if not is_login_client:
        return RedirectResponse(url='/')
    
    
    def get_image_list(content:str)->list[str]:
        pattern = '<img src="/image/.*/>'
        img_files = []
        for i in re.compile(pattern).findall(content):
            f:str = len('<img src="/image/')
            e:str = '.webp"'
            i:str = i[f:]
            i:str = i[:i.find(e)]
            i:str = i + '.webp'
            img_files.append(i)
        return img_files
    
    user_info = session_controller.get_session(session_id)

    create_content = content_idx is None
    update_content = content_idx is not None
    
    if create_content:  
        content_idx = db_controller.get_max_content_idx()+1
        img_list = get_image_list(content)

        for img in img_list:
            db_controller.push_image(img,content_idx)

        created_time = datetime.now().strftime(config.time_format)
        db_controller.push_content(content_idx = content_idx, 
                               user_idx = user_info['user_idx'], 
                               title = title, 
                               category = category,
                               created_time = created_time,
                               updated_time = created_time,
                               content = content)

    if update_content:  #update content
        content_idx = content_idx
        img_list = get_image_list(content)

        db_controller.delete_image_with_content_idx(content_idx)
        for img in img_list:
            db_controller.push_image(img,content_idx)

        updated_time = datetime.now().strftime(config.time_format)
        db_controller.update_content(content_idx=content_idx,
                                     title=title,
                                     category=category,
                                     updated_time=updated_time,
                                     content=content)

    
    status_code = 303  #see other
    return RedirectResponse(url='/', status_code=status_code)

@app.get('/content/{content_idx:int}')
def serve_content(content_idx:int,session_id:str = Cookie(default='-')):
    db_controller.add_one_content_view_count(content_idx)

    template = 'content_view.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()

    content = db_controller.get_content(content_idx)
    content['content'] = content['content'].replace("`","\`")
    user_info = session_controller.get_session(session_id)
    comment_list = db_controller.get_comment_with_content_idx(content_idx)

    comment_list_tmp = []
    for comment in comment_list:
        comment_user_info = db_controller.get_user_with_user_idx(comment['user_idx'])
        comment['user_id'] = comment_user_info['user_id'] #push user id to each comment
        comment_list_tmp.append(comment)

    comment_list = comment_list_tmp
    body = jinja2.Template(body).render(**{'content':content,
                                           'user_info':user_info,
                                           'comment_list':comment_list,
                                           'global_title':config.global_title
                                           })
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/delete/content/{content_idx:int}')
def delete_content(content_idx:int,session_id:str|None=Cookie(default=None)):
    
    is_login_client = checker.is_login_client(session_id)
    if not is_login_client:
        status_code = 303 #see other
        return RedirectResponse(f'/content/{content_idx}', status_code=status_code)

    content = db_controller.get_content(content_idx)

    user_info = session_controller.get_session(session_id)
    is_admin = checker.is_admin(user_info)
    is_author = checker.is_author(content,user_info)
    if not is_author and not is_admin:
        status_code = 303 #see other
        return RedirectResponse(f'/content/{content_idx}', status_code=status_code)

    db_controller.delete_comment_with_content_idx(content_idx)
    db_controller.delete_image_with_content_idx(content_idx)
    db_controller.delete_content(content_idx)
    status_code = 303 #see other
    return RedirectResponse('/',status_code=status_code)
    
@app.post('/delete/comment/{comment_idx:int}')
def delete_comment(comment_idx:int,session_id:str|None=Cookie(default=None)):
    comment = db_controller.get_comment(comment_idx)
    user_info = session_controller.get_session(session_id)
    content_idx = comment['content_idx']

    is_author = checker.is_author_comment(comment,user_info)
    if not is_author:
        status_code = 303 #see other
        return RedirectResponse(f'/content/{content_idx}', status_code=status_code)

    db_controller.delete_comment(comment_idx)
    status_code = 303 #see other
    return RedirectResponse(f'/content/{content_idx}', status_code=status_code)



@app.get('/user')
def submit_user_form_handler(error_message:str = Query(default=' ')):
    '''
    serve create account form
    '''
    with open(Path(config.PATH_TEMPLATES,'user.html'),'rt',encoding='utf-8') as f:
        body = f.read()
    body = jinja2.Template(body).render(**{'error_message':error_message.replace('_',' '),
                                           'global_title':config.global_title
                                           })
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

@app.post('/comment/{content_idx:int}')
def push_comment(content_idx:int, 
                 user_idx:int|None=Form(default=None),
                 comment:str|None=Form(default=None),
                 session_id:str=Cookie(default='-')
                 ):
    is_login_client = checker.is_login_client(session_id)
    if not is_login_client:
        status_code = 303 #see other
        return RedirectResponse('/content/{content_idx:int}', status_code=status_code)
    created_time = datetime.now().strftime(config.time_format)
    comment_idx = db_controller.get_max_comment_idx() + 1
    db_controller.push_comment(comment_idx=comment_idx, 
                               content_idx=content_idx,
                               user_idx=user_idx,
                               created_time=created_time,
                               comment=comment)
    status_code = 303 #see other
    return RedirectResponse(f'/content/{content_idx}', status_code=status_code)

@app.get('/login')
def serve_user_login_form(error_message:str = Query(default=' ')):
    template = 'login.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()
    body = jinja2.Template(body).render(**{'error_message':error_message.replace("_"," "),
                                           'global_title':config.global_title
                                           })
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/login')
def user_login_requests_handler(user_id:str=Form(default='-'),user_password:str=Form(default='-')):
    user_info = db_controller.get_user_with_id_password(user_id,user_password)
    is_valid_user_info = checker.is_valid_user_info(user_info)
    if not is_valid_user_info:
        status_code = 303
        error_message = 'user id or password is not correct. please check your input.'.replace(' ','_')
        return RedirectResponse(url=f'/login?error_message={error_message}', status_code=status_code)
        
    status_code = 303  #see other
    response = RedirectResponse(url='/', status_code=status_code)

    max_age_session = config.max_session_age  #sec
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
    session_controller.delete_session(session_id)
    return response

@app.post('/fs/upload/image')
def upload_image(image:UploadFile|None = Form(default=None)):
    '''
    this function save image file on folder and return filename
    return '20250119190633_73cfb64d-88ce-419f-b112-c357f3c22a4d.png'

    '''
    if image is None:
        body = 'no image contained on upload image request.'
        status_code = 400 #bad request
        headers = {'Content-Type':'text/plain'}
        return Response(content=body, status_code=status_code, headers=headers)
    
    accept = ['.jpg','.png','.jpeg','.webp','.gif']
    not_acceptable_extension = len(list(filter(lambda extension:extension in image.filename,accept))) == 0
    if not_acceptable_extension:
        body = 'image extension should be .'
        for a in accept:
            body += a
            body += ';'
        status_code = 400 #bad request
        headers = {'Content-Type':'text/plain'}
        return Response(content=body, status_code=status_code, headers=headers)
    
    def convert_to_webp(image_bytes:bytes)->bytes:
        imageBytesIO_webp = BytesIO()
        with Image.open(BytesIO(image_bytes),'r') as img:
            img.save(imageBytesIO_webp,'webp')
        imageBytesIO_webp.seek(0)
        return imageBytesIO_webp.read()

    imageBytes:bytes= image.file.read()
    extension_is_webp = '.webp' in image.filename
    if not extension_is_webp:
        imageBytes = convert_to_webp(imageBytes)
        
    upload_time = datetime.now().strftime("%Y%m%d%H%M%S")
    random = str(uuid4())
    file_name = f"{upload_time}_{random}.webp"
    file_path = Path(config.PATH_IMAGE,file_name)
    with open(file_path,'wb') as f:
        f.write(imageBytes)

    body = file_name
    status_code = 200
    headers = {'Content-Type':'text/plain'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/js/{file_name:str}')
def serve_javascript(file_name:str):
    file_path = Path(config.PATH_JAVASCRIPT,file_name)
    with open(file_path,'rt',encoding='utf-8') as f:
        body = f.read()
    status_code = 200  #see other
    headers = {'Content-Type':'text/javascript'}
    return Response(content=body, status_code=status_code, headers=headers)
 
@app.get('/css/{file_name:str}')
def serve_css(file_name:str):
    file_path = Path(config.PATH_CSS,file_name)
    with open(file_path,'rt',encoding='utf-8') as f:
        body = f.read()
    status_code = 200  #see other
    headers = {'Content-Type':'text/css'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/image/{file_name:str}')
def serve_image(file_name:str):
    file_path = Path(config.PATH_IMAGE,file_name)
    with open(file_path,'rb') as f: 
        body = f.read()
    status_code = 200  #see other
    headers = {'Content-Type':'image/webp'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/admin/user')
def serve_admin_panel(session_id:str = Cookie(default='-')):
    template = 'admin_panel.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()
    user_list = db_controller.get_user_list(init_row_idx=None,row_count=None)
    body = jinja2.Template(body).render(**{'user_list':user_list,
                                           'global_title':config.global_title})
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)


if __name__ == "__main__":
    print(f"server started : {config.time_server_started}")
    uvicorn.run("__main__:app",port=config.PORT,reload=config.reload)