from fastapi import APIRouter, HTTPException
from database import get_db
from models import (
    TaskResponse,
    TaskStatusUpdate,
    BulkTaskCreate,
    TaskAssignRequest,
    KanbanResponse,
)
from services.assignment import assign_next_task, create_tasks_for_images, get_tasks_by_status

router = APIRouter()


@router.get("", response_model=list[TaskResponse])
def list_tasks(status: str = None, assignee_id: int = None):
    with get_db() as db:
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if assignee_id:
            query += " AND assignee_id = ?"
            params.append(assignee_id)
        query += " ORDER BY priority DESC"
        rows = db.execute(query, params).fetchall()
        return [dict(row) for row in rows]


@router.get("/kanban", response_model=KanbanResponse)
def get_kanban():
    with get_db() as db:
        return get_tasks_by_status(db)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        return dict(row)


@router.post("/assign")
def assign_task(req: TaskAssignRequest):
    with get_db() as db:
        task = assign_next_task(req.user_id, db)
        if task is None:
            raise HTTPException(status_code=404, detail="No tasks available")
        return task


@router.post("/bulk-create")
def bulk_create_tasks(req: BulkTaskCreate):
    with get_db() as db:
        ids = create_tasks_for_images(req.image_ids, req.redundancy, db)
        return {"created_task_ids": ids, "count": len(ids)}


@router.patch("/{task_id}/status")
def update_task_status(task_id: int, req: TaskStatusUpdate):
    with get_db() as db:
        row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")

        updates = "status = ?"
        params = [req.status.value]

        if req.status.value == "completed":
            from datetime import datetime
            updates += ", completed_at = ?"
            params.append(datetime.utcnow().isoformat())

        params.append(task_id)
        db.execute(f"UPDATE tasks SET {updates} WHERE id = ?", params)
        db.commit()
        return {"id": task_id, "status": req.status.value}
