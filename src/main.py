from fastapi import FastAPI, Request, Form, Response, requests
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from urllib.parse import unquote

from requests import session
from sqlalchemy.future import select
from sqlalchemy.orm import Session
from sqlalchemy import update

import init
import function
import sqlite3
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/register", tags="Регистрация")
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/doregister", tags="Регистрация")
async def doregister(
    request: Request,
    Login: str = Form(...),
    Password: str = Form(...),
):
    print(Login, Password)
    with Session(init.engine) as conn:
        stmt = select(init.User).where(init.User.username == Login)
        data = conn.execute(stmt).fetchall()
        if data:
            error_msg = "Пользователь с таким именем уже есть"
            return RedirectResponse(url="/register", status_code=303)
        else:
            user = init.User(
                username=Login,
                password=function.hash_password(Password)
            )
            conn.add(user)
            conn.commit()
    conn = Session(init.engine)
    stmt = select(init.User).where(init.User.username == Login)
    id = conn.execute(stmt).fetchall()[0][0].id
    conn.commit()
    conn.close()
    redirect = RedirectResponse(url="/", status_code=303)
    # Устанавливаем куки
    redirect.set_cookie(key="id", value=str(id))
    redirect.set_cookie(key="username", value=function.encrypt(Login))
    return redirect

@app.get("/login", tags="Логин")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/dologin", tags="Логин")
async def dologin(
    request: Request,
    Login: str = Form(...),
    Password: str = Form(...)
):
    with Session(init.engine) as conn:
        stmt = select(init.User).where(init.User.username == Login)
        data = conn.execute(stmt).fetchall()
        if data and data[0][0].password == function.hash_password(Password):
            # Создаем редирект-ответ
            redirect = RedirectResponse(url="/", status_code=303)
            # Устанавливаем куки
            redirect.set_cookie(key="id", value=str(data[0][0].id))
            redirect.set_cookie(key="username", value=function.encrypt(data[0][0].username))
            return redirect
        else:
            print("Неверный логин или пароль")
            return RedirectResponse(url="/login", status_code=303)

if __name__ == "__main__":
    init.Base.metadata.create_all(init.engine)
    uvicorn.run("main:app", reload=True)