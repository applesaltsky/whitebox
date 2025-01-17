#get global config
from global_config import global_config
from global_db_control import DBController

from fastapi import FastAPI, Response, Request, Form, Query, APIRouter, Depends
from fastapi.responses import RedirectResponse
import uvicorn, jinja2

from datetime import datetime
import time

db_controller = DBController()
db_controller.init_db(db_path=global_config.PATH_DB, init=False)
app = FastAPI()

@app.middleware('http')
def add_process_time_logger(request:Request, call_next):
    start_time = time.time()
    response = call_next(request)
    process_time = time.time() - start_time
    print(' time : ',datetime.now(), ' url : ', request.url, ' proc_time : ', process_time, 'sec')
    return response


user = APIRouter()
admin = APIRouter()

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
    return RedirectResponse(url='/login', status_code=status_code)

@app.post('/logout')
def user_logout_requests_handler():
    status_code = 303  #see other
    response =  RedirectResponse(url='/login', status_code=status_code)
    response.set_cookie(key="user_id",
                        value="-",
                        max_age=0)
    response.set_cookie(key='session_id',
                        value="-",
                        max_age=0)
    return response

@admin.get('/admin/user')
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

app.include_router(user)
app.include_router(admin)

if __name__ == "__main__":
    print(f"server started : {global_config.time_server_started}")
    uvicorn.run("__main__:app",port=5000,reload=global_config.reload)