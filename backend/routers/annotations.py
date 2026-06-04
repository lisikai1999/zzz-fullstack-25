from fastapi import APIRouter, HTTPException
from database import get_db
from models import AnnotationCreate, AnnotationUpdate, AnnotationResponse
from datetime import datetime

router = APIRouter()


@router.post("", response_model=AnnotationResponse)
def create_annotation(ann: AnnotationCreate):
    with get_db() as db:
        now = datetime.utcnow().isoformat()
        cursor = db.execute(
            """
            INSERT INTO annotations (task_id, image_id, user_id, annotation_type, label, data_json, layer_index, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ann.task_id,
                ann.image_id,
                ann.user_id,
                ann.annotation_type.value,
                ann.label,
                ann.data_json,
                ann.layer_index,
                now,
                now,
            ),
        )
        db.commit()
        row = db.execute(
            "SELECT * FROM annotations WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return dict(row)


@router.get("/{task_id}")
def get_annotations_for_task(task_id: int, page: int = 1, page_size: int = 20):
    with get_db() as db:
        total = db.execute(
            "SELECT COUNT(*) as cnt FROM annotations WHERE task_id = ?", (task_id,)
        ).fetchone()["cnt"]

        offset = (page - 1) * page_size
        rows = db.execute(
            "SELECT * FROM annotations WHERE task_id = ? LIMIT ? OFFSET ?",
            (task_id, page_size, offset),
        ).fetchall()

        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }


@router.get("/image/{image_id}")
def get_annotations_for_image(image_id: int, page: int = 1, page_size: int = 20):
    with get_db() as db:
        total = db.execute(
            "SELECT COUNT(*) as cnt FROM annotations WHERE image_id = ?", (image_id,)
        ).fetchone()["cnt"]

        offset = (page - 1) * page_size
        rows = db.execute(
            "SELECT * FROM annotations WHERE image_id = ? ORDER BY user_id, layer_index LIMIT ? OFFSET ?",
            (image_id, page_size, offset),
        ).fetchall()

        return {
            "items": [dict(row) for row in rows],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }


@router.put("/{annotation_id}", response_model=AnnotationResponse)
def update_annotation(annotation_id: int, update: AnnotationUpdate):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM annotations WHERE id = ?", (annotation_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Annotation not found")

        updates = []
        params = []
        if update.label is not None:
            updates.append("label = ?")
            params.append(update.label)
        if update.data_json is not None:
            updates.append("data_json = ?")
            params.append(update.data_json)
        if update.layer_index is not None:
            updates.append("layer_index = ?")
            params.append(update.layer_index)

        if updates:
            updates.append("updated_at = ?")
            params.append(datetime.utcnow().isoformat())
            params.append(annotation_id)
            db.execute(
                f"UPDATE annotations SET {', '.join(updates)} WHERE id = ?", params
            )
            db.commit()

        row = db.execute(
            "SELECT * FROM annotations WHERE id = ?", (annotation_id,)
        ).fetchone()
        return dict(row)


@router.delete("/{annotation_id}")
def delete_annotation(annotation_id: int):
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM annotations WHERE id = ?", (annotation_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Annotation not found")
        db.execute("DELETE FROM annotations WHERE id = ?", (annotation_id,))
        db.commit()
        return {"deleted": annotation_id}
