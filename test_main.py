"""
Comprehensive Test Suite for FastAPI Task Management API

Verifies:
1. GET / -> 200 Root information
2. GET /health -> 200 Health check
3. GET /tasks -> 200 Task list & query parameters (?done=..., ?search=...)
4. GET /tasks/{id} -> 200 OK or 404 Not Found
5. POST /tasks -> 201 Created or 400 Bad Request
6. PUT /tasks/{id} -> 200 OK, 400 Bad Request, 404 Not Found
7. DELETE /tasks/{id} -> 204 No Content or 404 Not Found
8. GET /stats -> 200 Aggregate stats (total, done, open)
9. POST /reset -> 200 In-memory state reset
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db_before_test() -> None:
    """Reset in-memory DB before every test to ensure isolation."""
    client.post("/reset")


def test_get_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


def test_get_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_tasks_initial() -> None:
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3
    assert tasks[0]["id"] == 1
    assert tasks[0]["done"] is False
    assert tasks[1]["id"] == 2
    assert tasks[1]["done"] is True


def test_get_tasks_filtering_done() -> None:
    # Test done=true
    resp_done = client.get("/tasks?done=true")
    assert resp_done.status_code == 200
    tasks_done = resp_done.json()
    assert len(tasks_done) == 1
    assert tasks_done[0]["id"] == 2

    # Test done=false
    resp_open = client.get("/tasks?done=false")
    assert resp_open.status_code == 200
    tasks_open = resp_open.json()
    assert len(tasks_open) == 2
    assert {t["id"] for t in tasks_open} == {1, 3}


def test_get_tasks_filtering_search() -> None:
    resp_search = client.get("/tasks?search=REST")
    assert resp_search.status_code == 200
    tasks = resp_search.json()
    assert len(tasks) == 1
    assert tasks[0]["id"] == 2
    assert "Review REST status codes" in tasks[0]["title"]


def test_get_task_by_id_success() -> None:
    response = client.get("/tasks/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "title": "Complete Week 2 backend assignment",
        "done": False,
    }


def test_get_task_by_id_not_found() -> None:
    response = client.get("/tasks/999")
    assert response.status_code == 404
    assert response.json() == {"error": "Task 999 not found"}


def test_create_task_success() -> None:
    payload = {"title": "Write automated unit tests"}
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    new_task = response.json()
    assert new_task["id"] == 4
    assert new_task["title"] == "Write automated unit tests"
    assert new_task["done"] is False

    # Check list increment
    tasks = client.get("/tasks").json()
    assert len(tasks) == 4


def test_create_task_validation_missing_title() -> None:
    response = client.post("/tasks", json={})
    assert response.status_code == 400
    assert response.json() == {
        "error": "Title is required and cannot be empty"
    }


def test_create_task_validation_whitespace_title() -> None:
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 400
    assert response.json() == {
        "error": "Title is required and cannot be empty"
    }


def test_update_task_success_title_and_done() -> None:
    payload = {"title": "Updated Task 1 Title", "done": True}
    response = client.put("/tasks/1", json=payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == 1
    assert updated["title"] == "Updated Task 1 Title"
    assert updated["done"] is True


def test_update_task_success_partial() -> None:
    payload = {"done": True}
    response = client.put("/tasks/3", json=payload)
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == 3
    assert updated["done"] is True
    assert updated["title"] == "Push 6 commits to GitHub"


def test_update_task_validation_empty_body() -> None:
    response = client.put("/tasks/1", json={})
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid update payload"}


def test_update_task_validation_whitespace_title() -> None:
    response = client.put("/tasks/1", json={"title": "   "})
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid update payload"}


def test_update_task_not_found() -> None:
    response = client.put("/tasks/999", json={"done": True})
    assert response.status_code == 404
    assert response.json() == {"error": "Task 999 not found"}


def test_delete_task_success() -> None:
    response = client.delete("/tasks/1")
    assert response.status_code == 204
    assert response.content == b""  # Empty response body

    # Verify task is deleted
    get_resp = client.get("/tasks/1")
    assert get_resp.status_code == 404
    assert get_resp.json() == {"error": "Task 1 not found"}


def test_delete_task_not_found() -> None:
    response = client.delete("/tasks/999")
    assert response.status_code == 404
    assert response.json() == {"error": "Task 999 not found"}


def test_get_stats() -> None:
    response = client.get("/stats")
    assert response.status_code == 200
    assert response.json() == {"total": 3, "done": 1, "open": 2}


def test_reset() -> None:
    # Modify state
    client.post("/tasks", json={"title": "Temporary Task"})
    client.delete("/tasks/1")

    # Reset
    response = client.post("/reset")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Database reset to initial state",
        "total": 3,
    }

    # Verify initial tasks are back
    tasks = client.get("/tasks").json()
    assert len(tasks) == 3
    assert [t["id"] for t in tasks] == [1, 2, 3]
