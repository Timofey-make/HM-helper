import uuid
from pathlib import Path
import uvicorn
from fastapi import FastAPI, Request, Form, UploadFile, File, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
import function
import init

app = FastAPI()
UPLOAD_DIR = Path("static/uploads")
templates = Jinja2Templates(directory="templates")

@app.get("/register", tags="Регистрация")
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/doregister", tags="Регистрация")
async def doregister(
    request: Request,
    Login: str = Form(...),
    Password: str = Form(...),
    Teacher: str = Form(None)
):
    if Teacher is None:
        teacher = False
    else:
        teacher = True
    with Session(init.engine) as conn:
        stmt = select(init.User).where(init.User.username == Login)
        data = conn.execute(stmt).fetchall()
        if data:
            print("Пользователь с таким именем уже есть")
            return RedirectResponse(url="/register", status_code=303)
        else:
            user = init.User(
                teacher=teacher,
                username=Login,
                password=function.hash_password(Password),
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
    redirect.set_cookie(key="teacher", value=str(teacher))
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
        print(data[0][0].teacher)
        if data and data[0][0].password == function.hash_password(Password):
            # Создаем редирект-ответ
            redirect = RedirectResponse(url="/", status_code=303)
            # Устанавливаем куки
            redirect.set_cookie(key="teacher", value=str(data[0][0].teacher))
            redirect.set_cookie(key="id", value=str(data[0][0].id))
            redirect.set_cookie(key="username", value=function.encrypt(data[0][0].username))
            return redirect
        else:
            print("Неверный логин или пароль")
            return RedirectResponse(url="/login", status_code=303)

@app.get("/", tags="Каталог")
async def main(request: Request):
    user_id = request.cookies.get("id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    with Session(init.engine) as conn:
        stmt = select(init.Section)
        result = conn.execute(stmt)
        sections = result.scalars().all()
        notes = []
        for section in sections:
            notes.append(section.name)
    return templates.TemplateResponse("main.html", {"request": request, "notes": notes, "teacher": request.cookies.get("teacher")})

@app.get("/add", tags="Добавить секцию")
async def add(request: Request):
    user_id = request.cookies.get("id")
    teacher = request.cookies.get("teacher")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    elif not teacher:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("add.html", {"request": request})

@app.post("/doadd", tags="Добавить секцию")
async def doadd(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...),
):
    unique_filename = f"{uuid.uuid4()}_{image.filename}"
    file_path = UPLOAD_DIR / unique_filename
    with open(file_path, "wb") as buffer:
        buffer.write(await image.read())
    await image.close()
    with Session(init.engine) as conn:
        section = init.Section(
            owner=function.decrypt(request.cookies.get("username")),
            name=name,
            description=description,
            image_path=unique_filename,
        )
        conn.add(section)
        conn.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/section_page", tags="Страница секции")
async def section_page(
    request: Request,
    section_name: str = Query(..., description="Название секции")
):
    user_id = request.cookies.get("id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    

if __name__ == "__main__":
    init.Base.metadata.create_all(init.engine)
    uvicorn.run("main:app", reload=True)