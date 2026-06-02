import json
from fastapi import APIRouter, HTTPException
from database import get_db
from models import AnnotatorStats, OverviewStats
from services.metrics import (
    compute_iou_bbox,
    compute_dice_bbox,
    compute_iou_mask,
    compute_dice_mask,
    polygon_to_mask,
    rle_to_mask,
)

router = APIRouter()


def _compute_gold_deviation(user_id: int, db) -> dict:
    """
    Compute per-annotator deviation from gold standards.
    Returns { avg_iou, avg_dice, count } comparing the user's annotations
    against gold standards on the same images.
    """
    user_annotations = db.execute(
        """
        SELECT a.image_id, a.annotation_type, a.label, a.data_json
        FROM annotations a
        WHERE a.user_id = ?
        """,
        (user_id,),
    ).fetchall()

    if not user_annotations:
        return {"avg_iou": None, "avg_dice": None, "count": 0}

    iou_scores = []
    dice_scores = []

    for ann in user_annotations:
        ann = dict(ann)
        gold = db.execute(
            """
            SELECT gs.data_json, gs.annotation_type
            FROM gold_standards gs
            WHERE gs.image_id = ? AND gs.annotation_type = ? AND gs.label = ?
            LIMIT 1
            """,
            (ann["image_id"], ann["annotation_type"], ann["label"]),
        ).fetchone()

        if not gold:
            continue

        gold = dict(gold)
        ann_data = json.loads(ann["data_json"])
        gold_data = json.loads(gold["data_json"])

        image = db.execute(
            "SELECT width, height FROM images WHERE id = ?", (ann["image_id"],)
        ).fetchone()
        width, height = image["width"], image["height"]

        try:
            if ann["annotation_type"] == "bbox":
                iou = compute_iou_bbox(ann_data["coords"], gold_data["coords"])
                dice = compute_dice_bbox(ann_data["coords"], gold_data["coords"])
                iou_scores.append(iou)
                dice_scores.append(dice)
            elif ann["annotation_type"] == "polygon":
                mask_ann = polygon_to_mask(
                    [(p[0], p[1]) for p in ann_data["points"]], width, height
                )
                mask_gold = polygon_to_mask(
                    [(p[0], p[1]) for p in gold_data["points"]], width, height
                )
                iou = compute_iou_mask(mask_ann, mask_gold)
                dice = compute_dice_mask(mask_ann, mask_gold)
                iou_scores.append(iou)
                dice_scores.append(dice)
            elif ann["annotation_type"] == "mask":
                mask_ann = rle_to_mask(ann_data["rle"], width, height)
                mask_gold = rle_to_mask(gold_data["rle"], width, height)
                iou = compute_iou_mask(mask_ann, mask_gold)
                dice = compute_dice_mask(mask_ann, mask_gold)
                iou_scores.append(iou)
                dice_scores.append(dice)
            elif ann["annotation_type"] == "classification":
                # For classification, 1.0 if match, 0.0 if not
                match = 1.0 if ann_data.get("class") == gold_data.get("class") else 0.0
                iou_scores.append(match)
                dice_scores.append(match)
        except (KeyError, TypeError, ValueError):
            continue

    if not iou_scores:
        return {"avg_iou": None, "avg_dice": None, "count": 0}

    return {
        "avg_iou": sum(iou_scores) / len(iou_scores),
        "avg_dice": sum(dice_scores) / len(dice_scores),
        "count": len(iou_scores),
    }


@router.get("/annotators")
def list_annotators():
    """List all annotators with basic stats."""
    with get_db() as db:
        users = db.execute(
            "SELECT id, username, role, created_at FROM users WHERE role = 'annotator' ORDER BY id"
        ).fetchall()
        return [dict(u) for u in users]


@router.get("/annotator/{user_id}")
def get_annotator_stats(user_id: int):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        total = db.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE assignee_id = ?", (user_id,)
        ).fetchone()["cnt"]

        completed = db.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE assignee_id = ? AND status = 'completed'",
            (user_id,),
        ).fetchone()["cnt"]

        avg_score = db.execute(
            """
            SELECT AVG(cr.score) as avg_score
            FROM consistency_results cr
            JOIN annotations a ON (a.id = cr.annotation_id_a OR a.id = cr.annotation_id_b)
            WHERE a.user_id = ?
            """,
            (user_id,),
        ).fetchone()["avg_score"]

        # Compute actual gold standard deviation
        gold_result = _compute_gold_deviation(user_id, db)
        gold_deviation = None
        if gold_result["avg_dice"] is not None:
            gold_deviation = 1.0 - gold_result["avg_dice"]

        return {
            "user_id": user_id,
            "username": user["username"],
            "total_tasks": total,
            "completed_tasks": completed,
            "avg_consistency_score": avg_score,
            "gold_standard_deviation": gold_deviation,
            "gold_detail": gold_result,
        }


@router.get("/overview", response_model=OverviewStats)
def get_overview():
    with get_db() as db:
        total_images = db.execute("SELECT COUNT(*) as cnt FROM images").fetchone()["cnt"]
        total_tasks = db.execute("SELECT COUNT(*) as cnt FROM tasks").fetchone()["cnt"]
        pending_tasks = db.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'pending'"
        ).fetchone()["cnt"]
        completed_tasks = db.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'completed'"
        ).fetchone()["cnt"]
        flagged_items = db.execute(
            "SELECT COUNT(*) as cnt FROM consistency_results WHERE flagged = 1"
        ).fetchone()["cnt"]
        total_annotators = db.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE role = 'annotator'"
        ).fetchone()["cnt"]

        return {
            "total_images": total_images,
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "completed_tasks": completed_tasks,
            "flagged_items": flagged_items,
            "total_annotators": total_annotators,
        }
