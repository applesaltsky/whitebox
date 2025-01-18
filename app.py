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

#init session control
session_controller = SessionController()

#init db and push one admin to user db
db_controller = DBController()
db_controller.init_db(db_path=global_config.PATH_DB, init=False)
empty_user_db = db_controller.get_max_user_idx() == -1
if empty_user_db:
    admin_user_info = {
        'user_idx':0,
        'user_id':'admin',
        'user_password':'admin',
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

#add middleware to app
@app.middleware('http')
def add_logger(request:Request, call_next):
    start_time = time.time()
    response = call_next(request)
    process_time = time.time() - start_time
    memory_usage_mb = psutil.Process().memory_info().rss / (1024 * 1024)
    print(datetime.now(), ' url : ', request.url, ' method :', request.method, f' proc_time : {process_time:.4f} sec', f' memory usage : {memory_usage_mb:.2f} MB')
    return response

@app.middleware('http')
def del_old_session(request:Request, call_next):
    session_controller.del_old_session(max_age=global_config.max_session_age)
    response = call_next(request)
    return response


@app.middleware('http')
def confirm_valid_client_session(request:Request, call_next):
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
    
    response = call_next(request)
    return response


@app.middleware('http')
def confirm_admin_client_session(request:Request, call_next):
    url_path = request.url.path
    admin_path = r'/admin/' in url_path
    if not admin_path:
        response = call_next(request)
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
        
    response = call_next(request)
    return response


@app.get('/')
def home_handler():
    content_list = db_controller.get_content_list()
    body = """
<!DOCTYPE html>
<html lang="ko"> 
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>간단한 양식</title>
</head>
<body>
    <h1> content list </h1>
    {% for row in content_list %}
        <div> {{row['content_idx']}} : {{row['user_idx']}} : {{row['category']}} <a href='/content/{{row['content_idx']}}'> {{row['title']}} </a> : {{row['created_time']}} </div> 
    {% endfor %}
    <div><a href='/'> go to idx </a></div>
    <div><a href='/content'> write content </a></div>
    <div><a href='/user'> create account </a></div>
    <form action="/login" method="get">
         <div>
            <button type="submit">login</button>
        </div>
    </form>
</body>
</html>
    """
    body = jinja2.Template(body).render(**{"content_list":content_list})
    status_code = 200
    headers = {'Content-Type':'text/html'}
    return Response(content=body, status_code=status_code, headers=headers)


@app.get('/content')
def submit_content_form_handler():
    body = """
<!DOCTYPE html>
<html lang="ko"> 
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>간단한 양식</title>
</head>
<body>
    <h1>제목과 내용 입력하기</h1>
    <form action="/content" method="post">
        <div>
            <label for="title">제목:</label>
            <input type="text" id="title" name="title" required>
        </div>
        <div>
            <label for="content">내용:</label><br>
            <textarea id="content" name="content" rows="4" cols="50" required></textarea>
        </div>
        <div>
            <button type="submit">전송</button>
        </div>
    </form>
    <div><a href='/'> go to idx </a></div>
    <div><a href='/user'> create account </a></div>
    <form action="/login" method="get">
         <div>
            <button type="submit">login</button>
        </div>
    </form>
</body>
</html>"""
    status_code = 200
    headers = {'Content-Type':'text/html'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/content')
def submit_content_request_handler(title:str = Form(default='test'), content:str = Form(default='test')):
    new_content_idx = db_controller.get_max_content_idx()+1
    db_controller.push_content(content_idx = new_content_idx, 
                               user_idx = 0, 
                               title = title, 
                               category='main',
                               created_time = datetime.now(),
                               content=content)
    status_code = 303  #see other
    return RedirectResponse(url='/', status_code=status_code)

@app.get('/content/{content_idx}')
def submit_content_form_handler(content_idx:int):
    content = db_controller.get_content(content_idx)
    body = """
<!DOCTYPE html>
<html lang="ko"> 
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>간단한 양식</title>
</head>
<body>
    <h1> TITLE : {{title}} </h1>
    <div> <p> {{user_idx}} </p> <p> {{created_time}} </p> </div>
    <div>    
    {{content}}
    </div>
    <div><a href='/'> go to idx </a></div>
    <div><a href='/content'> write content </a></div>
    <div><a href='/user'> create account </a></div>
    <form action="/login" method="get">
         <div>
            <button type="submit">login</button>
        </div>
    </form>
    <form action="/logout" method="post">
         <div>
            <button type="submit">logout</button>
        </div>
    </form>
</body>
</html>"""
    body = jinja2.Template(body).render(**content)
    status_code = 200
    headers = {'Content-Type':'text/html'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.get('/user')
def submit_user_form_handler(error_message:str = Query(default=' ')):
    body = """
<!DOCTYPE html>
<html lang="ko"> 
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>간단한 양식</title>
</head>
<body>
    <h1>created user page</h1>
    <div> {{error_message}} </div>
    <form action="/user" method="post">
        <div>
            <label for="user_id">id : </label>
            <input type="text" id="user_id" name="user_id" required>
        </div>
        <div>
            <label for="user_password">password : </label>
            <input type="password" id="user_password" name="user_password" required></input>
        </div>
        <div>
            <label for="user_password_confirm">password_confirm : </label>
            <input type="password" id="user_password_confirm" name="user_password_confirm" required></input>
        </div>
        <div>
            <label for="user_email">user_email : </label>
            <input type="email" id="user_email" name="user_email" required></input>
        </div>
        <div>
            <label for="user_find_password_question">user_find_password_question : </label>
            <input type="text" id="user_find_password_question" name="user_find_password_question" value="내가 가장 좋아하는 과자는?" required></input>
        </div>
        <div>
            <label for="user_find_password_answer">user_find_password_answer : </label>
            <input type="text" id="user_find_password_answer" name="user_find_password_answer" value="호두과자" required></input>
        </div>
        <div>
            <button type="submit">전송</button>
        </div>
    </form>
    <div><a href='/'> go to idx </a></div>
    <div><a href='/user'> create account </a></div>
</body>
</html>"""
    body = jinja2.Template(body).render(**{'error_message':error_message.replace('_',' ')})
    status_code = 200
    headers = {'Content-Type':'text/html'}
    return Response(content=body, status_code=status_code, headers=headers)

@app.post('/user')
def submit_user_request_handler(user_id:str=Form(default='-'),
                                user_password:str=Form(default='-'),
                                user_password_confirm:str=Form(default='-'),
                                user_find_password_question:str=Form(default='-'),
                                user_find_password_answer:str=Form(default='-'),
                                user_email:str=Form(default='-')
                                ):
    
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
    return RedirectResponse(url='/user', status_code=status_code)

@app.get('/login')
def serve_user_login_form(error_message:str = Query(default=' ')):
    body = """
<!DOCTYPE html>
<html lang="ko"> 
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>간단한 양식</title>
</head>
<body>
    <h1> login page </h1>
    <div> {{error_message}} </div>
    <form action="/login" method="post">
        <div> 
            <label for="user_id">id : </label>
            <input type="text" id="user_id" name="user_id" required>
        </div>
        <div> 
            <label for="user_password">password : </label>
            <input type="password" id="user_password" name="user_password" required></input>   
        </div>
        <div>
            <button type="submit">전송</button>
        </div>
    </form>
    <div><a href='/'> go to idx </a></div>
    <div><a href='/content'> write content </a></div>
    <div><a href='/user'> create account </a></div>
</body>
</html>    
    """
    body = jinja2.Template(body).render(**{'error_message':error_message.replace("_"," ")})
    status_code = 200
    headers = {'Content-Type':'text/html'}
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
def serve_user_list_page():
    user_list = db_controller.get_user_list(init_row_idx=None,row_count=None)
    body = """
<!DOCTYPE html>
<html lang="ko"> 
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>간단한 양식</title>
    <style>
        table {
            width: 50%;
            border-collapse: collapse;
        }
        table, th, td {
            border: 1px solid black;
        }
        th, td {
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <h1> user list </h1>
    <table>
        <thead>
            <tr>
                <th>previlage</th>
                <th>user_idx</th>
                <th>user_id</th>
                <th>user_password</th>
                <th>user_find_password_question</th>
                <th>user_find_password_answer</th>
                <th>user_email</th>
                <th>created_time</th>
            </tr>
        </thead>
        <tbody>
            {% for row in user_list %}
            <tr>
                <td> {{row['previlage']}} </td>
                <td> {{row['user_idx']}} </td>
                <td> {{row['user_id']}} </td>
                <td> {{row['user_password']}} </td>
                <td> {{row['user_find_password_question']}} </td>
                <td> {{row['user_find_password_answer']}} </td>
                <td> {{row['user_email']}} </td>
                <td> {{row['created_time']}} </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    <div><a href='/'> go to idx </a></div>
    <div><a href='/content'> write content </a></div>
    <div><a href='/user'> create account </a></div>
</body>
</html>
    """
    body = jinja2.Template(body).render(**{'user_list':user_list})
    status_code = 200
    headers = {'Content-Type':'text/html'}
    return Response(content=body, status_code=status_code, headers=headers)


if __name__ == "__main__":
    print(f"server started : {global_config.time_server_started}")
    uvicorn.run("__main__:app",port=5000,reload=global_config.reload)