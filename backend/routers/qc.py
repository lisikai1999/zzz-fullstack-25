from fastapi import APIRouter, HTTPException
from database import get_db
from models import ConsistencyResult, ArbitrationCreate, ArbitrationResponse
from services.arbitration import assess_consistency, get_flagged_items
from datetime import datetime

router = APIRouter()


@router.get("/consistency/{image_id}")
def compute_consistency(image_id: int):
    with get_db() as db:
        image = db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        results = assess_consistency(image_id, db)
        return results


@router.get("/comparison/{image_id}")
def get_comparison(image_id: int):
    with get_db() as db:
        image = db.execute("SELECT * FROM images WHERE id = ?", (image_id,)).fetchone()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")

        annotations = db.execute(
            """
            SELECT a.*, u.username
            FROM annotations a
            JOIN users u ON u.id = a.user_id
            WHERE a.image_id = ?
            ORDER BY a.user_id
            """,
            (image_id,),
        ).fetchall()

        consistency = db.execute(
            "SELECT * FROM consistency_results WHERE image_id = ?", (image_id,)
        ).fetchall()

        annotators = {}
        for ann in annotations:
            ann = dict(ann)
            uid = ann["user_id"]
            if uid not in annotators:
                annotators[uid] = {"user_id": uid, "username": ann["username"], "annotations": []}
            annotators[uid]["annotations"].append(ann)

        return {
            "image": dict(image),
            "annotators": list(annotators.values()),
            "consistency_results": [dict(r) for r in consistency],
        }


@router.post("/arbitrate", response_model=ArbitrationResponse)
def submit_arbitration(req: ArbitrationCreate):
    with get_db() as db:
        now = datetime.utcnow().isoformat()
        # If updating an existing pending arbitration, resolve it
        existing = db.execute(
            "SELECT id FROM arbitrations WHERE consistency_result_id = ? AND status = 'pending'",
            (req.consistency_result_id,),
        ).fetchone()

        if existing:
            db.execute(
                """
                UPDATE arbitrations
                SET reviewer_id = ?, resolution_json = ?, status = 'resolved', resolved_at = ?
                WHERE id = ?
                """,
                (req.reviewer_id, req.resolution_json, now, existing["id"]),
            )
            db.commit()
            row = db.execute("SELECT * FROM arbitrations WHERE id = ?", (existing["id"],)).fetchone()
        else:
            cursor = db.execute(
                """
                INSERT INTO arbitrations (image_id, consistency_result_id, reviewer_id, resolution_json, status, resolved_at)
                VALUES (?, ?, ?, ?, 'resolved', ?)
                """,
                (req.image_id, req.consistency_result_id, req.reviewer_id, req.resolution_json, now),
            )
            db.commit()
            row = db.execute("SELECT * FROM arbitrations WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)


@router.get("/flagged")
def list_flagged(page: int = 1, page_size: int = 20):
    with get_db() as db:
        total = db.execute(
            "SELECT COUNT(*) as cnt FROM consistency_results WHERE flagged = 1"
        ).fetchone()["cnt"]

        offset = (page - 1) * page_size
        items = get_flagged_items(db, limit=page_size, offset=offset)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }


@router.get("/pending-arbitrations")
def list_pending_arbitrations(page: int = 1, page_size: int = 20):
    """Get all pending arbitration items with full context for the arbitration UI."""
    with get_db() as db:
        total = db.execute(
            "SELECT COUNT(*) as cnt FROM arbitrations WHERE status = 'pending'"
        ).fetchone()["cnt"]

        offset = (page - 1) * page_size
        rows = db.execute(
            """
            SELECT
                arb.id as arbitration_id,
                arb.image_id,
                arb.consistency_result_id,
                arb.status as arbitration_status,
                cr.metric_type,
                cr.score,
                cr.annotation_id_a,
                cr.annotation_id_b,
                i.filename,
                i.width,
                i.height
            FROM arbitrations arb
            JOIN consistency_results cr ON cr.id = arb.consistency_result_id
            JOIN images i ON i.id = arb.image_id
            WHERE arb.status = 'pending'
            ORDER BY cr.score ASC
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        ).fetchall()

        # Batch load all referenced annotations
        ann_ids = set()
        for row in rows:
            ann_ids.add(row["annotation_id_a"])
            ann_ids.add(row["annotation_id_b"])

        ann_map = {}
        if ann_ids:
            ann_rows = db.execute(
                """
                SELECT a.*, u.username
                FROM annotations a
                JOIN users u ON u.id = a.user_id
                WHERE a.id IN ({})
                """.format(",".join("?" * len(ann_ids))),
                list(ann_ids),
            ).fetchall()
            ann_map = {a["id"]: dict(a) for a in ann_rows}

        results = []
        for row in rows:
            row = dict(row)
            row["annotation_a"] = ann_map.get(row["annotation_id_a"])
            row["annotation_b"] = ann_map.get(row["annotation_id_b"])
            results.append(row)

        return {
            "items": results,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }


@router.get("/arbitration/{arbitration_id}")
def get_arbitration_detail(arbitration_id: int):
    """Get full detail of a single arbitration case for the resolution UI."""
    with get_db() as db:
        arb = db.execute(
            """
            SELECT arb.*, cr.metric_type, cr.score, cr.annotation_id_a, cr.annotation_id_b
            FROM arbitrations arb
            JOIN consistency_results cr ON cr.id = arb.consistency_result_id
            WHERE arb.id = ?
            """,
            (arbitration_id,),
        ).fetchone()
        if not arb:
            raise HTTPException(status_code=404, detail="Arbitration not found")

        arb = dict(arb)

        image = db.execute("SELECT * FROM images WHERE id = ?", (arb["image_id"],)).fetchone()
        arb["image"] = dict(image)

        ann_a = db.execute(
            "SELECT a.*, u.username FROM annotations a JOIN users u ON u.id = a.user_id WHERE a.id = ?",
            (arb["annotation_id_a"],),
        ).fetchone()
        ann_b = db.execute(
            "SELECT a.*, u.username FROM annotations a JOIN users u ON u.id = a.user_id WHERE a.id = ?",
            (arb["annotation_id_b"],),
        ).fetchone()

        arb["annotation_a"] = dict(ann_a) if ann_a else None
        arb["annotation_b"] = dict(ann_b) if ann_b else None

        # Also fetch all annotations for this image for full context
        all_anns = db.execute(
            "SELECT a.*, u.username FROM annotations a JOIN users u ON u.id = a.user_id WHERE a.image_id = ?",
            (arb["image_id"],),
        ).fetchall()
        arb["all_annotations"] = [dict(a) for a in all_anns]

        return arb
