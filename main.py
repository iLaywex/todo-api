from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
from datetime import datetime

app = FastAPI()

tasks = []

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

@app.get("/tasks")
def get_all_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Задача не найдена")

@app.post("/tasks", status_code=201)
def create_task(data: TaskCreate):
    new_task = {
        "id": str(uuid4()),
        "title": data.title,
        "description": data.description,
        "completed": False,
        "createdAt": datetime.now().isoformat()
    }
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: str, data: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if data.title is not None:
                task["title"] = data.title
            if data.description is not None:
                task["description"] = data.description
            if data.completed is not None:
                task["completed"] = data.completed
            return task
    raise HTTPException(status_code=404, detail="Задача не найдена")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(index)
            return {"message": "Задача удалена"}
    raise HTTPException(status_code=404, detail="Задача не найдена")