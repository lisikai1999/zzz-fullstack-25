import sqlite3
from typing import List, Dict


def update_priority_scores(db: sqlite3.Connection) -> None:
    db.execute(
        """
        UPDATE tasks SET priority = (
            SELECT i.uncertainty_score * (1.0 + 0.2 * (julianday('now') - julianday(i.created_at)))
            FROM images i WHERE i.id = tasks.image_id
        )
        WHERE status = 'pending'
        """
    )
    db.commit()


def get_prioritized_queue(limit: int, db: sqlite3.Connection) -> List[Dict]:
    rows = db.execute(
        """
        SELECT t.id, t.image_id, t.priority, i.uncertainty_score, i.filename
        FROM tasks t
        JOIN images i ON i.id = t.image_id
        WHERE t.status = 'pending' AND t.assignee_id IS NULL
        ORDER BY t.priority DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def simulate_uncertainty_scores(image_ids: List[int], db: sqlite3.Connection) -> None:
    import random
    for image_id in image_ids:
        score = random.uniform(0.1, 1.0)
        db.execute(
            "UPDATE images SET uncertainty_score = ? WHERE id = ?",
            (score, image_id),
        )
    db.commit()
