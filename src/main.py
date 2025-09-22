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

import os
from pathlib import Path

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

@app.get("/logout", tags="Выход")
async def logout(request: Request):
    # Создаем редирект-ответ
    redirect = RedirectResponse(url="/login", status_code=303)
    # Устанавливаем куки
    redirect.delete_cookie(key="id")
    redirect.delete_cookie(key="username")
    return redirect

@app.get("/register", tags="Регистрация")
async def register(request: Request):
    if request.cookies.get("id"):
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse("register.html", {"request": request})

@app.post("/doregister", tags="Регистрация")
async def doregister(
    request: Request,
    name: str = Form(...),
    login: str = Form(...),
    password: str = Form(...),
):
    with Session(init.engine) as conn:
        stmt = select(init.User).where(init.User.username == login)
        data = conn.execute(stmt).fetchall()
        if data:
            error_msg = "Пользователь с таким именем уже есть"
            return RedirectResponse(url="/register", status_code=303)
        else:
            user = init.User(
                name=name,
                username=login,
                password=function.hash_password(password)
            )
            conn.add(user)
            conn.commit()
    conn = Session(init.engine)
    stmt = select(init.User).where(init.User.username == login)
    id = conn.execute(stmt).fetchall()[0][0].id
    conn.commit()
    conn.close()
    redirect = RedirectResponse(url="/", status_code=303)
    # Устанавливаем куки
    redirect.set_cookie(key="id", value=str(id))
    redirect.set_cookie(key="username", value=function.encrypt(login))
    return redirect

@app.get("/login", tags="Логин")
async def login(request: Request):
    if request.cookies.get("id"):
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse("auth.html", {"request": request})

@app.post("/dologin", tags="Логин")
async def dologin(
    request: Request,
    auth: str = Form(...),
    password: str = Form(...)
):
    with Session(init.engine) as conn:
        stmt = select(init.User).where(init.User.username == auth)
        data = conn.execute(stmt).fetchall()
        if data and data[0][0].password == function.hash_password(password):
            # Создаем редирект-ответ
            redirect = RedirectResponse(url="/", status_code=303)
            # Устанавливаем куки
            redirect.set_cookie(key="id", value=str(data[0][0].id))
            redirect.set_cookie(key="username", value=function.encrypt(data[0][0].username))
            return redirect
        else:
            print("Неверный логин или пароль")
            return RedirectResponse(url="/login", status_code=303)

@app.get("/add", tags="Добавить вопрос")
async def add(request: Request):
    if request.cookies.get("id"):
        return templates.TemplateResponse("add_question.html", {"request": request})
    else:
        return RedirectResponse(url="/login", status_code=303)

@app.post("/doadd", tags="Добавить вопрос")
async def doadd(
    request: Request,
    subject: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
):
    with Session(init.engine) as conn:
        stmt = select(init.Question).where(init.Question.title == title, init.Question.description == description)
        data = conn.execute(stmt).fetchall()
        if data:
            print("Такой вопрос уже есть!")
        else:
            question = init.Question(
                owner=function.decrypt(request.cookies.get("username")),
                subject=subject,
                title=title,
                description=description,
            )
            conn.add(question)
        conn.commit()
        return RedirectResponse(url="/", status_code=303)

@app.get("/", tags="Главная")
async def main(request: Request):
    if request.cookies.get("id"):
        with Session(init.engine) as conn:
            stmt = select(
                init.Question.id,
                init.Question.owner,
                init.Question.subject,
                init.Question.title,
                init.Question.description
            ).order_by(init.Question.id.desc())
            data = conn.execute(stmt).fetchall()
            result = []
            for row in data:
                result.append({
                    "id": row.id,
                    "owner": row.owner,
                    "subject": row.subject,
                    "title": row.title,
                    "description": row.description
                })
            return templates.TemplateResponse("main.html", {"request": request,
                                                            "username": function.decrypt(request.cookies.get("username")),
                                                            "result": result})
    else:
        return RedirectResponse(url="/login", status_code=303)
    
@app.get("/question/{note_id}")
async def question_page(request: Request, note_id: int):
    if request.cookies.get("id"):
        with Session(init.engine) as conn:
            stmt = select(
                init.Question.owner,
                init.Question.subject,
                init.Question.title,
                init.Question.description
            ).where(init.Question.id == note_id)
            data = conn.execute(stmt).fetchall()
            result = [data[0].owner, data[0].subject, data[0].title, data[0].description]
            conn.commit()
            return templates.TemplateResponse("question.html", {"request": request,
                                                                "result": result})
    else:
        return RedirectResponse(url="/login", status_code=303)


if __name__ == "__main__":
    init.Base.metadata.create_all(init.engine)
    uvicorn.run("main:app", reload=True)