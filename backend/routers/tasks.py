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


@router.get("")
def list_tasks(status: str = None, assignee_id: int = None, page: int = 1, page_size: int = 20):
    with get_db() as db:
        base_where = " WHERE 1=1"
        params = []
        if status:
            base_where += " AND status = ?"
            params.append(status)
        if assignee_id:
            base_where += " AND assignee_id = ?"
            params.append(assignee_id)

        total = db.execute(
            "SELECT COUNT(*) as cnt FROM tasks" + base_where, params
        ).fetchone()["cnt"]

        offset = (page - 1) * page_size
        query = "SELECT * FROM tasks" + base_where + " ORDER BY priority DESC LIMIT ? OFFSET ?"
        rows = db.execute(query, params + [page_size, offset]).fetchall()

        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }


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
