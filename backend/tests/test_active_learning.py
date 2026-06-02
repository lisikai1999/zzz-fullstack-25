import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3
import pytest
from database import init_db
from services.active_learning import (
    update_priority_scores,
    get_prioritized_queue,
)
from services.assignment import create_tasks_for_images


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    conn.execute("INSERT INTO users (username, role) VALUES ('alice', 'annotator')")

    conn.execute(
        "INSERT INTO images (filename, filepath, width, height, uncertainty_score, is_key_image) "
        "VALUES ('low.png', '/imgs/low.png', 512, 512, 0.1, 0)"
    )
    conn.execute(
        "INSERT INTO images (filename, filepath, width, height, uncertainty_score, is_key_image) "
        "VALUES ('med.png', '/imgs/med.png', 512, 512, 0.5, 0)"
    )
    conn.execute(
        "INSERT INTO images (filename, filepath, width, height, uncertainty_score, is_key_image) "
        "VALUES ('high.png', '/imgs/high.png', 512, 512, 0.95, 0)"
    )
    conn.commit()
    yield conn
    conn.close()


class TestPriorityScoring:
    def test_higher_uncertainty_gets_higher_priority(self, db):
        create_tasks_for_images([1, 2, 3], redundancy=3, db=db)
        update_priority_scores(db)

        queue = get_prioritized_queue(limit=10, db=db)
        assert len(queue) == 3
        # Should be ordered: high (0.95), med (0.5), low (0.1)
        assert queue[0]["image_id"] == 3
        assert queue[1]["image_id"] == 2
        assert queue[2]["image_id"] == 1

    def test_priority_values_are_positive(self, db):
        create_tasks_for_images([1, 2, 3], redundancy=3, db=db)
        update_priority_scores(db)

        queue = get_prioritized_queue(limit=10, db=db)
        for item in queue:
            assert item["priority"] > 0

    def test_empty_queue_when_all_assigned(self, db):
        create_tasks_for_images([1], redundancy=3, db=db)
        db.execute("UPDATE tasks SET status = 'assigned', assignee_id = 1")
        db.commit()

        queue = get_prioritized_queue(limit=10, db=db)
        assert len(queue) == 0

    def test_limit_parameter(self, db):
        create_tasks_for_images([1, 2, 3], redundancy=3, db=db)
        update_priority_scores(db)

        queue = get_prioritized_queue(limit=2, db=db)
        assert len(queue) == 2
        # Still ordered by priority
        assert queue[0]["uncertainty_score"] >= queue[1]["uncertainty_score"]

    def test_only_updates_pending_tasks(self, db):
        create_tasks_for_images([1, 2], redundancy=3, db=db)
        # Mark one as completed
        db.execute("UPDATE tasks SET status = 'completed' WHERE image_id = 1")
        db.commit()

        update_priority_scores(db)
        row = db.execute("SELECT priority FROM tasks WHERE image_id = 1").fetchone()
        # Priority of completed task should remain as initial (0.1 from creation)
        assert row["priority"] == 0.1
