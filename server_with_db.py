import os
import sqlite3
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

# Инициализация приложения
app = FastAPI()

# Конфигурация базы данных
DATABASE_FILE = "core_system.db"
LOG_FILE = "core_log.txt"
ARCHIVE_FOLDER = "Archive"

# Функция для создания таблиц, если их нет
def initialize_database():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content TEXT NOT NULL
        )
        """
        )
        conn.commit()

# Проверка и создание архива и логов
def initialize_environment():
    if not os.path.exists(ARCHIVE_FOLDER):
        os.makedirs(ARCHIVE_FOLDER)
        print(f"Создана архивная папка: {ARCHIVE_FOLDER}")
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as log:
            log.write("Лог файл создан\n")
        print(f"Создан лог файл: {LOG_FILE}")

# Запускается при старте сервера
@app.on_event("startup")
def startup_event():
    if not os.path.exists(DATABASE_FILE):
        print(f"Создание базы данных: {DATABASE_FILE}")
    initialize_database()
    initialize_environment()

# Модель для файлов
class FileModel(BaseModel):
    name: str
    content: str

# Эндпоинт для добавления файла
@app.post("/add-file/")
def add_file(file: FileModel):
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (name, content) VALUES (?, ?)",
            (file.name, file.content),
        )
        conn.commit()
    return {"status": "Файл добавлен", "file": file.name}

# Эндпоинт для получения списка файлов
@app.get("/list-files/")
def list_files():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM files")
        files = cursor.fetchall()
    if not files:
        return {"status": "Файлов нет"}
    return {"files": files}

# Эндпоинт для получения содержимого файла по ID
@app.get("/get-file/{file_id}/")
def get_file(file_id: int):
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, content FROM files WHERE id = ?", (file_id,))
        file = cursor.fetchone()
    if not file:
        raise HTTPException(status_code=404, detail="Файл не найден")
    return {"name": file[0], "content": file[1]}

# Эндпоинт для удаления файла по ID
@app.delete("/delete-file/{file_id}/")
def delete_file(file_id: int):
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
        conn.commit()
    return {"status": "Файл удалён", "file_id": file_id}

# Эндпоинт для загрузки нового ядра
@app.post("/upload-core/")
def upload_core(file: FileModel):
    archive_path = os.path.join(ARCHIVE_FOLDER, f"{file.name}")
    with open(archive_path, "w", encoding="utf-8") as core_file:
        core_file.write(file.content)
    return {"status": "Ядро загружено", "path": archive_path}

# Эндпоинт для перестроения проекта
@app.get("/rebuild-project/")
def rebuild_project():
    return {"status": "Проект перестроен"}

# Новый эндпоинт для управления задачами
@app.post("/api-control/")
async def api_control(request: Request):
    try:
        data = await request.json()
        action = data.get("action")
        payload = data.get("payload")

        if action == "update_file":
            filename = payload.get("filename")
            content = payload.get("content")
            with open(filename, "w", encoding="utf-8") as file:
                file.write(content)
            return {"status": "File updated successfully", "filename": filename}

        elif action == "execute_task":
            task = payload.get("task")
            return {"status": "Task executed", "task": task}

        elif action == "log_message":
            message = payload.get("message")
            with open(LOG_FILE, "a", encoding="utf-8") as log_file:
                log_file.write(f"{message}\n")
            return {"status": "Message logged", "message": message}

        else:
            return {"status": "Unknown action", "action": action}

    except Exception as e:
        return {"status": "Error", "detail": str(e)}
