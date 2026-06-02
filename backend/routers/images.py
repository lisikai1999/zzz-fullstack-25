import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from database import get_db
from models import ImageCreate, ImageResponse, UncertaintyUpdate
from services.active_learning import update_priority_scores

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ImageResponse)
async def upload_image(
    file: UploadFile = File(...),
    width: int = 512,
    height: int = 512,
    is_key_image: bool = False,
):
    filepath = os.path.join(UPLOAD_DIR, file.filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    with get_db() as db:
        cursor = db.execute(
            """
            INSERT INTO images (filename, filepath, width, height, is_key_image)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file.filename, filepath, width, height, 1 if is_key_image else 0),
        )
        db.commit()
        row = db.execute("SELECT * FROM images WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)


@router.get("/{image_id}", response_model=ImageResponse)
def get_image(image_id: int):
    with get_db() as db:
        row = db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Image not found")
        return dict(row)


@router.get("/{image_id}/file")
def get_image_file(image_id: int):
    from fastapi.responses import FileResponse

    with get_db() as db:
        row = db.execute("SELECT filepath FROM images WHERE id = ?", (image_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Image not found")
        if not os.path.exists(row["filepath"]):
            raise HTTPException(status_code=404, detail="File not found on disk")
        return FileResponse(row["filepath"])


@router.patch("/{image_id}/uncertainty")
def update_uncertainty(image_id: int, req: UncertaintyUpdate):
    with get_db() as db:
        row = db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Image not found")
        db.execute(
            "UPDATE images SET uncertainty_score = ? WHERE id = ?",
            (req.uncertainty_score, image_id),
        )
        update_priority_scores(db)
        db.commit()
        return {"id": image_id, "uncertainty_score": req.uncertainty_score}
