from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime
from database import SessionLocal, TaskModel

app = FastAPI()

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

@app.get("/tasks")
def get_all_tasks():
    db = SessionLocal()
    tasks = db.query(TaskModel).all()
    db.close()
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    db = SessionLocal()
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    db.close()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task

@app.post("/tasks", status_code=201)
def create_task(data: TaskCreate):
    db = SessionLocal()
    new_task = TaskModel(
        id=str(uuid4()),
        title=data.title,
        description=data.description,
        completed=False,
        createdAt=datetime.now().isoformat()
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    db.close()
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: str, data: TaskUpdate):
    db = SessionLocal()
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        db.close()
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.completed is not None:
        task.completed = data.completed
    db.commit()
    db.refresh(task)
    db.close()
    return task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    db = SessionLocal()
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        db.close()
        raise HTTPException(status_code=404, detail="Задача не найдена")
    db.delete(task)
    db.commit()
    db.close()
    return {"message": "Задача удалена"}