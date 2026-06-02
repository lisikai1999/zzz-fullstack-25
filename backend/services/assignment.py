import sqlite3
import uuid
from typing import List, Optional, Dict
from datetime import datetime


def assign_next_task(user_id: int, db: sqlite3.Connection) -> Optional[Dict]:
    row = db.execute(
        """
        SELECT t.id, t.image_id, t.priority, t.redundancy_group
        FROM tasks t
        WHERE t.status = 'pending'
          AND t.assignee_id IS NULL
          AND t.image_id NOT IN (
              SELECT image_id FROM tasks WHERE assignee_id = ?
          )
        ORDER BY t.priority DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()

    if row is None:
        return None

    now = datetime.utcnow().isoformat()
    db.execute(
        "UPDATE tasks SET assignee_id = ?, status = 'assigned', assigned_at = ? WHERE id = ?",
        (user_id, now, row["id"]),
    )
    db.commit()

    return {
        "id": row["id"],
        "image_id": row["image_id"],
        "priority": row["priority"],
        "redundancy_group": row["redundancy_group"],
    }


def create_tasks_for_images(
    image_ids: List[int], redundancy: int, db: sqlite3.Connection
) -> List[int]:
    created_ids = []
    for image_id in image_ids:
        row = db.execute(
            "SELECT is_key_image, uncertainty_score FROM images WHERE id = ?",
            (image_id,),
        ).fetchone()
        if row is None:
            continue

        is_key = row["is_key_image"]
        priority = row["uncertainty_score"]
        num_tasks = redundancy if is_key else 1
        group_id = str(uuid.uuid4()) if is_key else None

        for _ in range(num_tasks):
            cursor = db.execute(
                """
                INSERT INTO tasks (image_id, status, priority, redundancy_group)
                VALUES (?, 'pending', ?, ?)
                """,
                (image_id, priority, group_id),
            )
            created_ids.append(cursor.lastrowid)

    db.commit()
    return created_ids


def get_tasks_by_status(db: sqlite3.Connection) -> Dict[str, List[Dict]]:
    rows = db.execute(
        "SELECT * FROM tasks ORDER BY priority DESC"
    ).fetchall()

    result = {
        "pending": [],
        "assigned": [],
        "in_progress": [],
        "completed": [],
        "arbitration": [],
    }

    for row in rows:
        task = dict(row)
        status = task["status"]
        if status in result:
            result[status].append(task)

    return result


def get_available_annotators(exclude_image_id: int, db: sqlite3.Connection) -> List[int]:
    rows = db.execute(
        """
        SELECT u.id FROM users u
        WHERE u.role = 'annotator'
          AND u.id NOT IN (
              SELECT assignee_id FROM tasks
              WHERE image_id = ? AND assignee_id IS NOT NULL
          )
        """,
        (exclude_image_id,),
    ).fetchall()
    return [row["id"] for row in rows]
