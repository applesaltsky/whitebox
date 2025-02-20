#import internal class
from controller.config import Config
from controller.db_control import DBController
from controller.session_control import SessionController
from controller.checker import Checker
from controller.fs_control import FSController
from controller.encrypter import Encrypter

#import external package
from fastapi import FastAPI, Response, Request, Form, Query, Cookie, UploadFile
from fastapi.responses import RedirectResponse
from PIL import Image
import uvicorn, jinja2, psutil

#import standard package
from uuid import uuid4
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO
from threading import Lock
import time, re, math


#set config and utility func
PATH_APP_PY = Path(__file__)
config = Config(PATH_APP_PY)
checker = Checker()

#init session control
session_controller = SessionController()

#init fs control
fs_controller = FSController()

#init db, and db control
db_controller = DBController()
db_controller.init_db(db_path=config.PATH_DB)

#init encrypter
encrypter = Encrypter()
encrypter.init_encrypter(PATH_BCRYPT_SALT=config.PATH_BCRYPT_SALT)

#push admin to user table
empty_user_db = checker.is_empty_user_db(db_controller)
if empty_user_db:
    admin_user_info = {
        'user_idx':0,
        'user_id':config.admin_id,
        'user_password':config.admin_pw,
        'user_password_question':'-',
        'user_password_answer':'-'
    }
    db_controller.push_user(user_idx=admin_user_info['user_idx'],
                    user_id = admin_user_info['user_id'],
                    user_password = admin_user_info['user_password'],
                    user_password_question = admin_user_info['user_password_question'],
                    user_password_answer = admin_user_info['user_password_answer'],
                    created_time=datetime.now(),
                    previlage='admin',
                    encrypter=encrypter)  



#push default category to category table  
empty_category_db = checker.is_empty_category_db(db_controller)
if empty_category_db:
    for idx, category in enumerate(config.default_category_list):
        default_category_info = {
            'category_idx': idx,
            'category':category
        }
        db_controller.push_category(category_idx = default_category_info['category_idx'],
                                    category = default_category_info['category']
                                    )

#create fastapi application instance
app = FastAPI()

#set middleware
@app.middleware('http')
def add_logger(request:Request, call_next):
    start_time = time.time()
    success = True
    error_message = ''
    try:
        response = call_next(request)
    except Exception as e:
        success = False
        error_message = str(e)
    finally:
        process_time = time.time() - start_time
        memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)
        log_idx = db_controller.get_max_log_idx() + 1

        logging_timekey = datetime.now()
        
        db_controller.push_log(log_idx=log_idx,
                               timekey=int(logging_timekey.strftime(config.log_timekey_format)),
                               url=str(request.url),
                               method=request.method,
                               proc_time=round(process_time,4),
                               memory_usage=round(memory_usage_mb,2),
                               success=success,
                               error_message=error_message)

        print(logging_timekey, ' url : ', request.url, ' method :', request.method, f' proc_time : {process_time:.4f} sec', f' memory_usage : {memory_usage_mb:.2f} MB')
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
   
@app.middleware('http')
async def request_counter_middleware(request:Request, call_next):
    global request_counter
    MAX_REQUEST_COUNTER = 1024 * 1024

    response = await call_next(request)

    with lock:
        request_counter += 1
        if request_counter % config.cycle_delete_unused_image == 0:
            fs_controller.delete_unused_image(db_controller,config.PATH_IMAGE)
        
        if request_counter % config.cycle_delete_old_log == 0:
            db_controller.delete_old_log(config.log_expiration_date,config.log_timekey_format)

        if request_counter >= MAX_REQUEST_COUNTER:
            request_counter = 0
    return response


#set routing
@app.get('/')
def home_handler(session_id:str = Cookie(default='-'),
                 category:str|None=Query(default=None),
                 page:int=Query(default=1),
                 row_cnt:int=Query(default=5),
                 search_pattern:str|None=Query(default=None)
                 ):
    
    if page <= 0 or row_cnt <=0:
        return RedirectResponse('/')

    def batch(iter,n:int=2):
        '''
        for i in batch([1,2,3,4,5,6,7],n=3):
            print(i)

        [1, 2, 3] [4, 5, 6] [7]
        '''
        rst = []
        total_batch_cnt = math.ceil(len(iter)/n)
        yield_batch_cnt = 1

        for idx, item in enumerate(iter):
            rst.append(item)
            if (idx + 1) % n == 0:
                yield rst
                rst = []
                yield_batch_cnt += 1
            if ((idx + 1) == len(iter)) and (total_batch_cnt == yield_batch_cnt):
                yield rst

    template = 'home.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()

    user_info = session_controller.get_session(session_id)

    content_list = db_controller.get_content_list(category=category,
                                                  page=page,
                                                  row_cnt=row_cnt,
                                                  search_pattern=search_pattern
                                                  )
    
    category_idx = db_controller.get_category_idx_with_category(category)
    content_count = db_controller.get_content_count(category_idx=category_idx)

    total_page_count = max(math.ceil(content_count/row_cnt),1)
    page_batch_list = [i for i in batch(list(map(lambda item : item+1,range(total_page_count))),n=config.max_page_count)]
    
    page_list = []
    page_batch_idx = 0
    for page_batch in page_batch_list:
        if page in page_batch:
            page_list = page_batch
            break
        page_batch_idx += 1
    
    is_page_in_first_batch = page in page_batch_list[0]
    prev_button_page = -1
    if not is_page_in_first_batch:
        prev_button_page = page_batch_list[page_batch_idx - 1][-1]

    
    is_page_in_last_batch = page in page_batch_list[-1]
    next_button_page = -1
    if not is_page_in_last_batch:
        next_button_page = page_batch_list[page_batch_idx + 1][0]
    
    category_list = db_controller.get_category_list()
    body = jinja2.Template(body).render(**{"content_list":content_list,
                                           "user_info":user_info,
                                           "category_list":category_list,
                                           'category':category,
                                           'page_list':page_list,
                                           'page':page,
                                           "row_cnt_list":config.row_cnt_list,
                                           "row_cnt":row_cnt,
                                           "global_title":config.global_title,
                                           'write_content_previlage':config.write_content_previlage,
                                           'is_page_in_first_batch':is_page_in_first_batch,
                                           'is_page_in_last_batch':is_page_in_last_batch,
                                           'prev_button_page':prev_button_page,
                                           'next_button_page':next_button_page,
                                           'ADMIN_ID':config.admin_id,
                                           'ADMIN_EMAIL':config.admin_email,
                                           'global_description':config.global_description
                                           })
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)


@app.post('/')
def redirect_to_get():
    status_code = 303 #see other
    response = RedirectResponse('/',status_code=status_code)
    return response

@app.get('/content')
def submit_content_form_handler(session_id:str = Cookie(default='-'),
                                content_idx:int|None = Query(default=None)):
    
    is_login_client = checker.is_login_client(session_id)
    if not is_login_client:
        return RedirectResponse(url='/')
    
    user_info = session_controller.get_session(session_id)
    has_write_content_previlage = checker.has_write_content_previlage(user_info,config)
    if not has_write_content_previlage:
        return RedirectResponse(url='/')
    
    with open(Path(config.PATH_TEMPLATES,'content_edit.html'),'rt',encoding='utf-8') as f:
        body = f.read()

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
        
    category_list = db_controller.get_category_list()

    body = jinja2.Template(body).render(**{
                                           "content_idx":content_idx,
                                           'content':content,
                                           "user_info":user_info,
                                           'category_list':category_list,
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
                                   category_idx:int|None=Form(default=None), 
                                   content:str = Form(default='test'),
                                   session_id:str = Cookie(default='-'),
                                   content_idx:int|None = Form(default=None)):
    
    is_login_client = checker.is_login_client(session_id)
    if not is_login_client:
        return RedirectResponse(url='/')
    
    user_info = session_controller.get_session(session_id)
    has_write_content_previlage = checker.has_write_content_previlage(user_info,config)
    if not has_write_content_previlage:
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
                               category_idx = category_idx,
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
                                     category_idx=category_idx,
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
    content['content'] = content['content'].replace(r"`",r"\`")
    user_info = session_controller.get_session(session_id)
    comment_list = db_controller.get_comment_with_content_idx(content_idx)
    first_image = db_controller.get_image_with_content_idx(content_idx)[0]

    comment_list_tmp = []
    for comment in comment_list:
        comment_user_info = db_controller.get_user_with_user_idx(comment['user_idx'])
        comment['user_id'] = comment_user_info['user_id'] #push user id to each comment
        comment_list_tmp.append(comment)

    comment_list = comment_list_tmp
    body = jinja2.Template(body).render(**{
                                            'content_idx':content_idx,
                                            'content':content,
                                            'user_info':user_info,
                                            'comment_list':comment_list,
                                            'global_title':config.global_title,
                                            'first_image':first_image
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
def serve_create_user_page(session_id:str|None = Cookie(default=None),
                           error_message:str = Query(default=' '),
                           content_idx:int|None = Query(default=None)):
    '''
    serve create account form
    '''
    is_login_client = checker.is_login_client(session_id)
    if is_login_client:
        #logout and redirect to home
        response = RedirectResponse('/')
        response.set_cookie(key='session_id',
                        value="-",
                        max_age=0)
        if session_controller.get_session(session_id):
            session_controller.delete_session(session_id)
        return response

    with open(Path(config.PATH_TEMPLATES,'user.html'),'rt',encoding='utf-8') as f:
        body = f.read()
    body = jinja2.Template(body).render(**{'error_message':error_message.replace('_',' '),
                                           'global_title':config.global_title,
                                           'content_idx':content_idx
                                           })
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/user')
def create_user_request(        
                                content_idx:int|None=Form(default=None),
                                user_id:str=Form(default='-'),
                                user_password:str=Form(default='-'),
                                user_password_confirm:str=Form(default='-'),
                                user_password_question:str=Form(default='-'),
                                user_password_answer:str=Form(default='-'),
                        ):
    '''
    handle create account request
    '''
    
    for validation, error_message in [checker.valid_user_id(db_controller,user_id),checker.valid_user_password(user_password,user_password_confirm)]:
        if validation is not True:
            status_code = 303  #see other
            error_message = error_message.replace(' ','_')
            return RedirectResponse(url=f'/user?error_message={error_message}', status_code=status_code)
        
    new_user_idx = db_controller.get_max_user_idx() + 1
    db_controller.push_user(user_idx=new_user_idx,
                            user_id=user_id,
                            user_password=user_password,
                            user_password_question=user_password_question,
                            user_password_answer=user_password_answer,
                            created_time=datetime.now(),
                            previlage='user',
                            encrypter=encrypter)
    status_code = 303  #see other
    if content_idx is not None:
        return RedirectResponse(url=f'/login?content_idx={content_idx}', status_code=status_code)
    else:
        return RedirectResponse(url='/login', status_code=status_code)

@app.get('/find/user')
def serve_find_user_page(error_message:str|None = Query(None)
                    ):
    
    template = 'user_find.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()

    body = jinja2.Template(body).render(**{
                                           'error_message':error_message,
                                           'user_id':None,
                                           'global_title':config.global_title,
                                           'user_password_question':None,
                                           'temp_user_password':None
                                           })
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/find/user')
def serve_find_user_page(user_id:str|None = Form(default=None),
                         user_password_answer:str|None = Form(default=None)
                    ):
    error_message = None
    template = 'user_find.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()    

    if user_id:
        exist_user_id = db_controller.exist_user_id(user_id)
        if not exist_user_id:
            error_message = f"Can not find user_id={user_id}, please check your input."
            user_id = None
    
    user_password_question = None
    if user_id:
        user_password_question = db_controller.get_user_password_question_with_user_id(user_id)
    
    temp_user_password = None
    if user_password_answer:
        user_id_and_answer_is_correct = db_controller.check_user_id_and_user_password_answer(user_id,user_password_answer)
        
        if not user_id_and_answer_is_correct:
            error_message = "your answer is not correct, please check your input"
        
        if user_id_and_answer_is_correct: 
            user_idx = db_controller.get_user_idx_with_user_id(user_id)
            temp_user_password = str(uuid4())
            db_controller.update_user_password(user_idx, temp_user_password, encrypter)   

    body = jinja2.Template(body).render(**{
                                           'error_message':error_message,
                                           'user_id':user_id,
                                           'global_title':config.global_title,
                                           'user_password_question':user_password_question,
                                           'temp_user_password':temp_user_password
                                           })
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/edit/user')
def serve_edit_user_page(error_message:str|None = Query(default=None),
                         session_id:str = Cookie(default='-')):
    login_client = checker.is_login_client(session_id)
    is_valid_session = checker.is_valid_session_id(session_controller, session_id)
    if not (login_client and is_valid_session):
        #logout and redirect to home
        response = RedirectResponse('/')
        return response
    
    user_info = session_controller.get_session(session_id) 
    
    template = 'user_edit.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()    

    body = jinja2.Template(body).render(**{'global_title':config.global_title,
                                           'user_info':user_info,
                                           'error_message':error_message})
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/edit/user')
def handle_edit_user_request(session_id:str = Cookie(default='-'),
                            user_id:str|None = Form(default=None),
                            user_id_new:str|None = Form(default=None),
                            user_password:str|None = Form(default=None),
                            user_password_new:str|None = Form(default=None),
                            user_password_new_confirm:str|None = Form(default=None),
                            user_password_question:str|None = Form(default=None),
                            user_password_answer:str|None = Form(default=None),

                              ):
    
    user_info_in_session = session_controller.get_session(session_id)
    user_info_in_db = db_controller.get_user_with_id_password(user_id,user_password,encrypter)

    if not checker.is_same_user_info_db_and_session(user_info_in_db,user_info_in_session):
        error_message = 'password confirm failed. please, check your input.'
        status_code = 303 #see other
        response = RedirectResponse(f'/edit/user?error_message={error_message}',status_code=status_code)
        
        return response
    
    updated_user_id = user_id != user_id_new
    if updated_user_id:
        validation, error_message = checker.valid_user_id(db_controller,user_id_new)
        if validation is not True:
            status_code = 303  #see other
            return RedirectResponse(url=f'/edit/user?error_message={error_message}', status_code=status_code)
    
    validation, error_message = checker.valid_user_password(user_password_new,user_password_new_confirm)
    if validation is not True:
        status_code = 303  #see other
        return RedirectResponse(url=f'/edit/user?error_message={error_message}', status_code=status_code)
    
    
    user_info = session_controller.get_session(session_id)
    user_idx = user_info['user_idx']

    #update db
    db_controller.update_user(user_idx,
                              user_id_new,
                              user_password_new,
                              user_password_question,
                              user_password_answer,
                              encrypter)
    
    #update session
    session_controller.delete_session(session_id)

    session_id = session_controller.create_session_id()
    user_info = db_controller.get_user_with_user_idx(user_idx)
    session_controller.push_session(session_id,user_info)
    
    #update client cookie(login again)
    status_code = 303 #see other
    response = RedirectResponse(url='/',status_code=status_code)

    max_age_session = config.max_session_age  #sec
    response.set_cookie(key='session_id',
                        value=session_id,
                        max_age=max_age_session
                        )
    session_controller.push_session(session_id,user_info)
    return response

@app.post('/comment/{content_idx:int}')
def push_comment(content_idx:int, 
                 user_idx:int|None=Form(default=None),
                 comment:str|None=Form(default=None),
                 session_id:str|None=Cookie(default=None)
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
def serve_user_login_form(
                            error_message:str = Query(default=' '),
                            content_idx:int|None = Query(default=None)
                         ):
    template = 'login.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()
    body = jinja2.Template(body).render(**{'error_message':error_message.replace("_"," "),
                                           'global_title':config.global_title,
                                           'content_idx':content_idx
                                           })
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/login')
def user_login_requests_handler(content_idx:int|None = Form(default=None),
                                user_id:str=Form(default='-'),
                                user_password:str=Form(default='-')):
    user_info = db_controller.get_user_with_id_password(user_id,user_password,encrypter)
    is_valid_user_info = checker.is_valid_user_info(user_info)
    if not is_valid_user_info:
        status_code = 303
        error_message = 'user id or password is not correct. please check your input.'.replace(' ','_')
        return RedirectResponse(url=f'/login?error_message={error_message}', status_code=status_code)
        
    status_code = 303  #see other
    if content_idx is not None:
        response = RedirectResponse(url=f'/content/{content_idx}', status_code=status_code)
    else:
        response = RedirectResponse(url='/', status_code=status_code)

    max_age_session = config.max_session_age  #sec
    session_id = session_controller.create_session_id()
    response.set_cookie(key='session_id',
                        value=session_id,
                        max_age=max_age_session
                        )
    session_controller.push_session(session_id,user_info)
    return response

@app.post('/logout')
def user_logout_requests_handler(   
                                    content_idx:int|None = Form(default=None),
                                    session_id:str = Cookie(default='-')
                                 ):
    status_code = 303  #see other
    if content_idx is not None:
        response =  RedirectResponse(url=f'/content/{content_idx}', status_code=status_code)
    else:
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
    status_code = 200  
    headers = {'Content-Type':'text/javascript'}
    return Response(content=body, status_code=status_code, headers=headers)
 
@app.get('/css/{file_name:str}')
def serve_css(file_name:str):
    file_path = Path(config.PATH_CSS,file_name)
    with open(file_path,'rt',encoding='utf-8') as f:
        body = f.read()
    status_code = 200
    headers = {'Content-Type':'text/css'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/image/{file_name:str}')
def serve_image(file_name:str):
    file_path = Path(config.PATH_IMAGE,file_name)
    with open(file_path,'rb') as f: 
        body = f.read()
    status_code = 200  
    headers = {'Content-Type':'image/webp'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/favicon.ico')
def serve_favicon():
    file_path = Path(config.PATH_FAVICON_ICO)
    with open(file_path,'rb') as f: 
        body = f.read()
    status_code = 200  
    headers = {'Content-Type':'image/x-icon'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/admin/panel')
def serve_admin_panel(session_id:str|None = Cookie(default=None)):
    if not checker.is_login_client(session_id):
        status_code = 307
        return RedirectResponse(url='/',status_code=status_code)

    if not checker.is_admin_session(session_controller,session_id):
        response = RedirectResponse('/')
        response.set_cookie(key='session_id',
                        value="-",
                        max_age=0)
        return response

    template = 'admin_panel.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()

    body = jinja2.Template(body).render(**{
                                           'global_title':config.global_title,
                                           'run_rst':False,
                                           'row_cnt':0,
                                           'run_time':0,
                                           'query_result':None})
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/admin/panel')
def serve_admin_panel(session_id:str|None = Cookie(default=None),
                      sql:str|None = Form(default=None)):
    if not checker.is_login_client(session_id):
        status_code = 307
        return RedirectResponse(url='/',status_code=status_code)

    if not checker.is_admin_session(session_controller,session_id):
        response = RedirectResponse('/')
        response.set_cookie(key='session_id',
                        value="-",
                        max_age=0)
        return response
    
    
    db_controller.copy_to_tmp(config.PATH_DB_TMP)

    rst = db_controller.run_sql(
                                db_path = config.PATH_DB_TMP, 
                                sql = sql, 
                                limit = config.limit_admin_panel_view
                                )
    run_success, run_time, query_result, query_column,error_message = rst

    db_controller.push_to_base(config.PATH_DB_TMP)
 
    template = 'admin_panel.html'
    with open(Path(config.PATH_TEMPLATES,template),'rt',encoding='utf-8') as f:
        body = f.read()

    body = jinja2.Template(body).render(**{
                                           'global_title':config.global_title,
                                           'run_success':run_success,
                                           'row_cnt':len(query_result),
                                           'run_time': round(run_time,3),
                                           'query_result':query_result,
                                           'query_column':query_column,
                                           'error_message':error_message
                                           })
    status_code = 200
    headers = {'Content-Type':'text/html;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)


@app.get('/sitemap.xml')
def serve_sitemap():
    content_list = db_controller.get_all_content_list()
    timestamp = (datetime.now()-timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%S%z')
    body = jinja2.Template(r"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {% for idx in content_list %}
  <url>
	<loc>https://whitebox.social/content/{{idx['content_idx']}}</loc>
	<lastmod>{{timestamp}}</lastmod>
	<changefreq>weekly</changefreq>
	<priority>0.8</priority>
  </url>
    {% endfor %}
</urlset>""").render({'timestamp':timestamp, 'content_list':content_list})
    status_code = 200
    headers = {'Content-Type':'text/xml;charset=utf-8'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/thumbnail')
def serve_thumbnail():
    file_path = Path(config.PATH_THUMBNAIL)
    with open(file_path,'rb') as f: 
        body = f.read()
    status_code = 200
    headers = {'Content-Type':'image/png'}
    return Response(content=body, status_code=status_code, headers=headers)

#run fastapi application
if __name__ == "__main__":
    print(f"server started : {config.time_server_started}")
    uvicorn.run("__main__:app",host=config.HOST, port=config.PORT,reload=config.reload)