import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3
import pytest
from database import init_db, SCHEMA
from services.assignment import (
    assign_next_task,
    create_tasks_for_images,
    get_available_annotators,
)


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")

    # Seed users
    conn.execute("INSERT INTO users (username, role) VALUES ('alice', 'annotator')")
    conn.execute("INSERT INTO users (username, role) VALUES ('bob', 'annotator')")
    conn.execute("INSERT INTO users (username, role) VALUES ('carol', 'annotator')")
    # Seed images
    conn.execute(
        "INSERT INTO images (filename, filepath, width, height, uncertainty_score, is_key_image) "
        "VALUES ('img1.png', '/imgs/img1.png', 512, 512, 0.9, 0)"
    )
    conn.execute(
        "INSERT INTO images (filename, filepath, width, height, uncertainty_score, is_key_image) "
        "VALUES ('img2.png', '/imgs/img2.png', 512, 512, 0.3, 0)"
    )
    conn.execute(
        "INSERT INTO images (filename, filepath, width, height, uncertainty_score, is_key_image) "
        "VALUES ('key1.png', '/imgs/key1.png', 512, 512, 0.8, 1)"
    )
    conn.commit()
    yield conn
    conn.close()


class TestCreateTasks:
    def test_normal_image_creates_one_task(self, db):
        ids = create_tasks_for_images([1], redundancy=3, db=db)
        assert len(ids) == 1

    def test_key_image_creates_redundant_tasks(self, db):
        ids = create_tasks_for_images([3], redundancy=3, db=db)
        assert len(ids) == 3
        # All should have same redundancy_group
        rows = db.execute(
            "SELECT redundancy_group FROM tasks WHERE id IN ({})".format(
                ",".join(str(i) for i in ids)
            )
        ).fetchall()
        groups = set(row["redundancy_group"] for row in rows)
        assert len(groups) == 1
        assert None not in groups

    def test_mixed_images(self, db):
        ids = create_tasks_for_images([1, 2, 3], redundancy=2, db=db)
        # img1: 1 task, img2: 1 task, key1: 2 tasks = 4 total
        assert len(ids) == 4

    def test_nonexistent_image_skipped(self, db):
        ids = create_tasks_for_images([999], redundancy=3, db=db)
        assert len(ids) == 0


class TestAssignNextTask:
    def test_assigns_highest_priority(self, db):
        create_tasks_for_images([1, 2], redundancy=3, db=db)
        # img1 has uncertainty=0.9, img2 has uncertainty=0.3
        task = assign_next_task(user_id=1, db=db)
        assert task is not None
        assert task["image_id"] == 1  # highest priority

    def test_no_duplicate_assignment(self, db):
        create_tasks_for_images([1], redundancy=3, db=db)
        task1 = assign_next_task(user_id=1, db=db)
        assert task1 is not None
        # Same user should not get same image again
        task2 = assign_next_task(user_id=1, db=db)
        # Only one task for img1 (non-key), so should be None or different image
        if task2 is not None:
            assert task2["image_id"] != task1["image_id"]

    def test_returns_none_when_empty(self, db):
        task = assign_next_task(user_id=1, db=db)
        assert task is None

    def test_key_image_assigned_to_different_annotators(self, db):
        create_tasks_for_images([3], redundancy=3, db=db)
        t1 = assign_next_task(user_id=1, db=db)
        t2 = assign_next_task(user_id=2, db=db)
        t3 = assign_next_task(user_id=3, db=db)
        assert t1 is not None
        assert t2 is not None
        assert t3 is not None
        assert t1["image_id"] == t2["image_id"] == t3["image_id"] == 3

    def test_assignment_updates_status(self, db):
        create_tasks_for_images([1], redundancy=3, db=db)
        task = assign_next_task(user_id=1, db=db)
        row = db.execute("SELECT status, assignee_id FROM tasks WHERE id = ?", (task["id"],)).fetchone()
        assert row["status"] == "assigned"
        assert row["assignee_id"] == 1


class TestAvailableAnnotators:
    def test_excludes_already_assigned(self, db):
        create_tasks_for_images([3], redundancy=3, db=db)
        assign_next_task(user_id=1, db=db)
        available = get_available_annotators(exclude_image_id=3, db=db)
        assert 1 not in available
        assert 2 in available
        assert 3 in available
