import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from fastapi.testclient import TestClient

# Override DB path before importing main
import database
TEST_DB = "/tmp/test_annotation_api.db"
database.DB_PATH = TEST_DB

from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    database.init_db(TEST_DB)
    # Seed data
    with database.get_db(TEST_DB) as db:
        db.execute("INSERT INTO users (username, role) VALUES ('alice', 'annotator')")
        db.execute("INSERT INTO users (username, role) VALUES ('bob', 'annotator')")
        db.execute("INSERT INTO users (username, role) VALUES ('reviewer1', 'reviewer')")
        db.execute(
            "INSERT INTO images (filename, filepath, width, height, uncertainty_score, is_key_image) "
            "VALUES ('ct1.png', '/uploads/ct1.png', 512, 512, 0.9, 1)"
        )
        db.execute(
            "INSERT INTO images (filename, filepath, width, height, uncertainty_score, is_key_image) "
            "VALUES ('ct2.png', '/uploads/ct2.png', 512, 512, 0.3, 0)"
        )
    yield
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


class TestFullWorkflow:
    def test_health(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_bulk_create_tasks(self):
        resp = client.post("/api/tasks/bulk-create", json={"image_ids": [1, 2], "redundancy": 2})
        assert resp.status_code == 200
        data = resp.json()
        # image 1 is key: 2 tasks, image 2 is normal: 1 task = 3
        assert data["count"] == 3

    def test_assign_and_annotate_workflow(self):
        # Create tasks
        client.post("/api/tasks/bulk-create", json={"image_ids": [1], "redundancy": 2})

        # Assign to alice
        resp = client.post("/api/tasks/assign", json={"user_id": 1})
        assert resp.status_code == 200
        task_alice = resp.json()

        # Assign to bob
        resp = client.post("/api/tasks/assign", json={"user_id": 2})
        assert resp.status_code == 200
        task_bob = resp.json()

        assert task_alice["image_id"] == task_bob["image_id"] == 1

        # Alice submits annotation
        ann_data = {
            "task_id": task_alice["id"],
            "image_id": 1,
            "user_id": 1,
            "annotation_type": "bbox",
            "label": "tumor",
            "data_json": json.dumps({"coords": [100, 100, 200, 200]}),
        }
        resp = client.post("/api/annotations", json=ann_data)
        assert resp.status_code == 200

        # Bob submits annotation (slightly different)
        ann_data2 = {
            "task_id": task_bob["id"],
            "image_id": 1,
            "user_id": 2,
            "annotation_type": "bbox",
            "label": "tumor",
            "data_json": json.dumps({"coords": [110, 105, 210, 205]}),
        }
        resp = client.post("/api/annotations", json=ann_data2)
        assert resp.status_code == 200

        # Compute consistency
        resp = client.get("/api/qc/consistency/1")
        assert resp.status_code == 200
        results = resp.json()
        assert len(results) > 0
        # Should have IoU and Dice results
        metrics = [r["metric_type"] for r in results]
        assert "iou" in metrics
        assert "dice" in metrics

    def test_kanban_view(self):
        client.post("/api/tasks/bulk-create", json={"image_ids": [1, 2], "redundancy": 2})
        resp = client.get("/api/tasks/kanban")
        assert resp.status_code == 200
        data = resp.json()
        assert "pending" in data
        assert "completed" in data
        assert len(data["pending"]) == 3

    def test_comparison_view(self):
        client.post("/api/tasks/bulk-create", json={"image_ids": [1], "redundancy": 2})
        client.post("/api/tasks/assign", json={"user_id": 1})
        client.post("/api/tasks/assign", json={"user_id": 2})

        # Submit annotations
        tasks = client.get("/api/tasks?assignee_id=1").json()
        client.post("/api/annotations", json={
            "task_id": tasks[0]["id"], "image_id": 1, "user_id": 1,
            "annotation_type": "bbox", "label": "nodule",
            "data_json": json.dumps({"coords": [50, 50, 150, 150]}),
        })

        tasks = client.get("/api/tasks?assignee_id=2").json()
        client.post("/api/annotations", json={
            "task_id": tasks[0]["id"], "image_id": 1, "user_id": 2,
            "annotation_type": "bbox", "label": "nodule",
            "data_json": json.dumps({"coords": [60, 55, 155, 145]}),
        })

        resp = client.get("/api/qc/comparison/1")
        assert resp.status_code == 200
        data = resp.json()
        assert "annotators" in data
        assert len(data["annotators"]) == 2

    def test_stats_overview(self):
        resp = client.get("/api/stats/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_images"] == 2
        assert data["total_annotators"] == 2

    def test_update_task_status(self):
        client.post("/api/tasks/bulk-create", json={"image_ids": [2], "redundancy": 1})
        resp = client.post("/api/tasks/assign", json={"user_id": 1})
        task_id = resp.json()["id"]

        resp = client.patch(f"/api/tasks/{task_id}/status", json={"status": "completed"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_no_tasks_available(self):
        resp = client.post("/api/tasks/assign", json={"user_id": 1})
        assert resp.status_code == 404


class TestArbitrationWorkflow:
    def _setup_flagged_annotations(self):
        """Create two very different annotations that will be flagged."""
        client.post("/api/tasks/bulk-create", json={"image_ids": [1], "redundancy": 2})
        client.post("/api/tasks/assign", json={"user_id": 1})
        client.post("/api/tasks/assign", json={"user_id": 2})

        tasks_alice = client.get("/api/tasks?assignee_id=1").json()
        tasks_bob = client.get("/api/tasks?assignee_id=2").json()

        # Very different annotations -> low IoU -> flagged
        client.post("/api/annotations", json={
            "task_id": tasks_alice[0]["id"], "image_id": 1, "user_id": 1,
            "annotation_type": "bbox", "label": "tumor",
            "data_json": json.dumps({"coords": [10, 10, 100, 100]}),
        })
        client.post("/api/annotations", json={
            "task_id": tasks_bob[0]["id"], "image_id": 1, "user_id": 2,
            "annotation_type": "bbox", "label": "tumor",
            "data_json": json.dumps({"coords": [200, 200, 400, 400]}),
        })

        # Trigger consistency check
        client.get("/api/qc/consistency/1")

    def test_pending_arbitrations_listed(self):
        self._setup_flagged_annotations()
        resp = client.get("/api/qc/pending-arbitrations")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) > 0
        item = items[0]
        assert item["arbitration_status"] == "pending"
        assert item["annotation_a"] is not None
        assert item["annotation_b"] is not None
        assert "username" in item["annotation_a"]
        assert "username" in item["annotation_b"]

    def test_arbitration_detail(self):
        self._setup_flagged_annotations()
        pending = client.get("/api/qc/pending-arbitrations").json()
        arb_id = pending[0]["arbitration_id"]

        resp = client.get(f"/api/qc/arbitration/{arb_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert "image" in detail
        assert "annotation_a" in detail
        assert "annotation_b" in detail
        assert "all_annotations" in detail
        assert detail["image"]["width"] == 512

    def test_submit_arbitration_resolves(self):
        self._setup_flagged_annotations()
        pending = client.get("/api/qc/pending-arbitrations").json()
        assert len(pending) > 0
        item = pending[0]

        resp = client.post("/api/qc/arbitrate", json={
            "image_id": item["image_id"],
            "consistency_result_id": item["consistency_result_id"],
            "reviewer_id": 3,
            "resolution_json": json.dumps({
                "chosen": "annotation_a",
                "annotation_id": item["annotation_id_a"],
                "comment": "Alice's annotation is more accurate",
            }),
        })
        assert resp.status_code == 200
        result = resp.json()
        assert result["status"] == "resolved"
        assert result["reviewer_id"] == 3

        # Verify it's no longer in pending
        pending_after = client.get("/api/qc/pending-arbitrations").json()
        resolved_ids = [p["arbitration_id"] for p in pending_after]
        assert item["arbitration_id"] not in resolved_ids

    def test_arbitration_not_found(self):
        resp = client.get("/api/qc/arbitration/9999")
        assert resp.status_code == 404


class TestStatsWithGoldStandard:
    def test_list_annotators_dynamic(self):
        resp = client.get("/api/stats/annotators")
        assert resp.status_code == 200
        annotators = resp.json()
        assert len(annotators) == 2
        usernames = [a["username"] for a in annotators]
        assert "alice" in usernames
        assert "bob" in usernames

    def test_gold_deviation_no_gold_standard(self):
        """When no gold standard exists, deviation is None."""
        resp = client.get("/api/stats/annotator/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["gold_standard_deviation"] is None
        assert data["gold_detail"]["count"] == 0

    def test_gold_deviation_with_gold_standard(self):
        """When gold standard exists, compute actual IoU/Dice deviation."""
        # Insert gold standard
        with database.get_db(TEST_DB) as db:
            db.execute(
                "INSERT INTO gold_standards (image_id, annotation_type, label, data_json, created_by) "
                "VALUES (1, 'bbox', 'tumor', ?, 3)",
                (json.dumps({"coords": [10, 10, 110, 110]}),),
            )

        # Create task and submit annotation from alice
        client.post("/api/tasks/bulk-create", json={"image_ids": [1], "redundancy": 2})
        client.post("/api/tasks/assign", json={"user_id": 1})
        tasks = client.get("/api/tasks?assignee_id=1").json()
        client.post("/api/annotations", json={
            "task_id": tasks[0]["id"], "image_id": 1, "user_id": 1,
            "annotation_type": "bbox", "label": "tumor",
            "data_json": json.dumps({"coords": [15, 15, 105, 105]}),
        })

        resp = client.get("/api/stats/annotator/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["gold_standard_deviation"] is not None
        assert data["gold_standard_deviation"] >= 0
        assert data["gold_standard_deviation"] <= 1.0
        assert data["gold_detail"]["count"] >= 1
        assert data["gold_detail"]["avg_iou"] is not None
        assert data["gold_detail"]["avg_iou"] > 0.5  # Should be high overlap
        assert data["gold_detail"]["avg_dice"] is not None
        assert data["gold_detail"]["avg_dice"] > 0.5

    def test_gold_deviation_low_overlap(self):
        """Annotation far from gold standard should have high deviation."""
        with database.get_db(TEST_DB) as db:
            db.execute(
                "INSERT INTO gold_standards (image_id, annotation_type, label, data_json, created_by) "
                "VALUES (1, 'bbox', 'nodule', ?, 3)",
                (json.dumps({"coords": [0, 0, 50, 50]}),),
            )

        client.post("/api/tasks/bulk-create", json={"image_ids": [1], "redundancy": 2})
        client.post("/api/tasks/assign", json={"user_id": 2})
        tasks = client.get("/api/tasks?assignee_id=2").json()
        client.post("/api/annotations", json={
            "task_id": tasks[0]["id"], "image_id": 1, "user_id": 2,
            "annotation_type": "bbox", "label": "nodule",
            "data_json": json.dumps({"coords": [300, 300, 450, 450]}),
        })

        resp = client.get("/api/stats/annotator/2")
        assert resp.status_code == 200
        data = resp.json()
        assert data["gold_standard_deviation"] is not None
        # No overlap -> deviation should be 1.0 (= 1 - 0 dice)
        assert data["gold_standard_deviation"] >= 0.9
