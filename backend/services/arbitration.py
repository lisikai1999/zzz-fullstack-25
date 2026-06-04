import sqlite3
import json
from typing import List, Dict
from itertools import combinations

from services.metrics import (
    compute_iou_bbox,
    compute_dice_bbox,
    compute_iou_mask,
    compute_dice_mask,
    compute_cohens_kappa,
    polygon_to_mask,
    rle_to_mask,
)

IOU_THRESHOLD = 0.7
DICE_THRESHOLD = 0.7
KAPPA_THRESHOLD = 0.6


def assess_consistency(image_id: int, db: sqlite3.Connection) -> List[Dict]:
    annotations = db.execute(
        "SELECT * FROM annotations WHERE image_id = ?", (image_id,)
    ).fetchall()

    if len(annotations) < 2:
        return []

    image = db.execute(
        "SELECT width, height FROM images WHERE id = ?", (image_id,)
    ).fetchone()
    width, height = image["width"], image["height"]

    results = []
    for ann_a, ann_b in combinations(annotations, 2):
        ann_a = dict(ann_a)
        ann_b = dict(ann_b)

        if ann_a["annotation_type"] != ann_b["annotation_type"]:
            continue

        score = None
        metric_type = None

        if ann_a["annotation_type"] == "bbox":
            data_a = json.loads(ann_a["data_json"])
            data_b = json.loads(ann_b["data_json"])
            iou = compute_iou_bbox(data_a["coords"], data_b["coords"])
            dice = compute_dice_bbox(data_a["coords"], data_b["coords"])
            for mt, sc, threshold in [("iou", iou, IOU_THRESHOLD), ("dice", dice, DICE_THRESHOLD)]:
                flagged = 1 if sc < threshold else 0
                cursor = db.execute(
                    """
                    INSERT INTO consistency_results
                    (image_id, annotation_id_a, annotation_id_b, metric_type, score, flagged)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (image_id, ann_a["id"], ann_b["id"], mt, sc, flagged),
                )
                results.append({
                    "id": cursor.lastrowid,
                    "image_id": image_id,
                    "annotation_id_a": ann_a["id"],
                    "annotation_id_b": ann_b["id"],
                    "metric_type": mt,
                    "score": sc,
                    "flagged": bool(flagged),
                })

        elif ann_a["annotation_type"] == "polygon":
            data_a = json.loads(ann_a["data_json"])
            data_b = json.loads(ann_b["data_json"])
            mask_a = polygon_to_mask(
                [(p[0], p[1]) for p in data_a["points"]], width, height
            )
            mask_b = polygon_to_mask(
                [(p[0], p[1]) for p in data_b["points"]], width, height
            )
            iou = compute_iou_mask(mask_a, mask_b)
            dice = compute_dice_mask(mask_a, mask_b)
            for mt, sc, threshold in [("iou", iou, IOU_THRESHOLD), ("dice", dice, DICE_THRESHOLD)]:
                flagged = 1 if sc < threshold else 0
                cursor = db.execute(
                    """
                    INSERT INTO consistency_results
                    (image_id, annotation_id_a, annotation_id_b, metric_type, score, flagged)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (image_id, ann_a["id"], ann_b["id"], mt, sc, flagged),
                )
                results.append({
                    "id": cursor.lastrowid,
                    "image_id": image_id,
                    "annotation_id_a": ann_a["id"],
                    "annotation_id_b": ann_b["id"],
                    "metric_type": mt,
                    "score": sc,
                    "flagged": bool(flagged),
                })

        elif ann_a["annotation_type"] == "mask":
            data_a = json.loads(ann_a["data_json"])
            data_b = json.loads(ann_b["data_json"])
            mask_a = rle_to_mask(data_a["rle"], width, height)
            mask_b = rle_to_mask(data_b["rle"], width, height)
            iou = compute_iou_mask(mask_a, mask_b)
            dice = compute_dice_mask(mask_a, mask_b)
            for mt, sc, threshold in [("iou", iou, IOU_THRESHOLD), ("dice", dice, DICE_THRESHOLD)]:
                flagged = 1 if sc < threshold else 0
                cursor = db.execute(
                    """
                    INSERT INTO consistency_results
                    (image_id, annotation_id_a, annotation_id_b, metric_type, score, flagged)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (image_id, ann_a["id"], ann_b["id"], mt, sc, flagged),
                )
                results.append({
                    "id": cursor.lastrowid,
                    "image_id": image_id,
                    "annotation_id_a": ann_a["id"],
                    "annotation_id_b": ann_b["id"],
                    "metric_type": mt,
                    "score": sc,
                    "flagged": bool(flagged),
                })

        elif ann_a["annotation_type"] == "classification":
            data_a = json.loads(ann_a["data_json"])
            data_b = json.loads(ann_b["data_json"])
            kappa = compute_cohens_kappa(
                [data_a["class"]], [data_b["class"]]
            )
            flagged = 1 if kappa < KAPPA_THRESHOLD else 0
            cursor = db.execute(
                """
                INSERT INTO consistency_results
                (image_id, annotation_id_a, annotation_id_b, metric_type, score, flagged)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (image_id, ann_a["id"], ann_b["id"], "kappa", kappa, flagged),
            )
            results.append({
                "id": cursor.lastrowid,
                "image_id": image_id,
                "annotation_id_a": ann_a["id"],
                "annotation_id_b": ann_b["id"],
                "metric_type": "kappa",
                "score": kappa,
                "flagged": bool(flagged),
            })

    db.commit()

    # Create arbitration records for flagged results
    for r in results:
        if r["flagged"]:
            db.execute(
                """
                INSERT INTO arbitrations (image_id, consistency_result_id, status)
                VALUES (?, ?, 'pending')
                """,
                (image_id, r["id"]),
            )
    db.commit()

    return results


def get_flagged_items(db: sqlite3.Connection, limit: int = None, offset: int = None) -> List[Dict]:
    query = """
        SELECT cr.*, a.status as arbitration_status, a.id as arbitration_id
        FROM consistency_results cr
        LEFT JOIN arbitrations a ON a.consistency_result_id = cr.id
        WHERE cr.flagged = 1
        ORDER BY cr.computed_at DESC
    """
    params = []
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    if offset is not None:
        query += " OFFSET ?"
        params.append(offset)
    rows = db.execute(query, params).fetchall()
    return [dict(row) for row in rows]
