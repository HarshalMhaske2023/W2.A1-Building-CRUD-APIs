"""
AI-Generated Alternate Version of FastAPI Task Management REST API (Stage 7)

This alternate implementation uses a distinct architectural layout, custom exception
handlers, different variable naming conventions, and alternate Pydantic schemas.
"""

from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Initialize FastAPI instance
app = FastAPI(
    title="Task Management System - AI Edition",
    version="2.0.0",
    description="Alternate FastAPI implementation for AI vs Human code comparison.",
)

# ------------------------------------------------------------------------------
# Alternate In-Memory Store & Global Counter
# ------------------------------------------------------------------------------
task_repository: List[Dict[str, object]] = [
    {"id": 1, "title": "Complete Week 2 backend assignment", "done": False},
    {"id": 2, "title": "Review REST status codes", "done": True},
    {"id": 3, "title": "Push 6 commits to GitHub", "done": False},
]

id_counter: int = 4


# ------------------------------------------------------------------------------
# Alternate Pydantic Models
# ------------------------------------------------------------------------------
class TaskItem(BaseModel):
    """Primary task entity model."""
    id: int = Field(..., description="Unique ID assigned by database")
    title: str = Field(..., description="Description of task to be performed")
    done: bool = Field(False, description="Task completion status flag")


class TaskCreatePayload(BaseModel):
    """Payload schema for creating a new task."""
    title: str = Field(..., min_length=1, description="Title string must not be empty")


class TaskUpdatePayload(BaseModel):
    """Payload schema for updating existing task."""
    title: Optional[str] = Field(None, description="Optional updated title string")
    done: Optional[bool] = Field(None, description="Optional updated completion status")


# ------------------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------------------
@app.get("/", status_code=status.HTTP_200_OK)
def read_root() -> Dict[str, object]:
    """Root endpoint detailing service name and version."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", status_code=status.HTTP_200_OK)
def check_health() -> Dict[str, str]:
    """Health check route."""
    return {"status": "ok"}


@app.get("/tasks", status_code=status.HTTP_200_OK)
def fetch_all_tasks(
    done: Optional[bool] = None,
    search: Optional[str] = None,
) -> List[Dict[str, object]]:
    """Retrieve task list with optional filtering by completion status or search term."""
    items = task_repository

    if done is not None:
        items = [item for item in items if item["done"] == done]

    if search is not None:
        term = search.lower()
        items = [item for item in items if term in str(item["title"]).lower()]

    return items


@app.get("/stats", status_code=status.HTTP_200_OK)
def fetch_stats() -> Dict[str, int]:
    """Retrieve summary statistics of tasks."""
    total_count = len(task_repository)
    completed_count = sum(1 for item in task_repository if item["done"] is True)
    pending_count = total_count - completed_count
    return {
        "total": total_count,
        "done": completed_count,
        "open": pending_count,
    }


@app.get("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def fetch_task_by_id(task_id: int) -> Dict[str, object]:
    """Fetch single task by ID or return 404."""
    for item in task_repository:
        if item["id"] == task_id:
            return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": f"Task {task_id} not found"},
    )


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def add_new_task(payload: Dict[str, object]) -> Dict[str, object]:
    """Create a new task with validation."""
    global id_counter

    if "title" not in payload or not isinstance(payload["title"], str) or not payload["title"].strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Title is required and cannot be empty"},
        )

    record = {
        "id": id_counter,
        "title": payload["title"].strip(),
        "done": False,
    }
    id_counter += 1
    task_repository.append(record)
    return record


@app.put("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def update_existing_task(task_id: int, payload: Dict[str, object]) -> Dict[str, object]:
    """Update task fields by ID."""
    has_title = "title" in payload and payload["title"] is not None
    has_done = "done" in payload and payload["done"] is not None

    if not has_title and not has_done:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid update payload"},
        )

    if has_title and (not isinstance(payload["title"], str) or not payload["title"].strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid update payload"},
        )

    if has_done and not isinstance(payload["done"], bool):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid update payload"},
        )

    for item in task_repository:
        if item["id"] == task_id:
            if has_title:
                item["title"] = str(payload["title"]).strip()
            if has_done:
                item["done"] = bool(payload["done"])
            return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": f"Task {task_id} not found"},
    )


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(task_id: int) -> None:
    """Delete task by ID."""
    for index, item in enumerate(task_repository):
        if item["id"] == task_id:
            task_repository.pop(index)
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"error": f"Task {task_id} not found"},
    )


@app.post("/reset", status_code=status.HTTP_200_OK)
def reset_repository() -> Dict[str, object]:
    """Reset repository back to initial state."""
    global task_repository, id_counter
    task_repository = [
        {"id": 1, "title": "Complete Week 2 backend assignment", "done": False},
        {"id": 2, "title": "Review REST status codes", "done": True},
        {"id": 3, "title": "Push 6 commits to GitHub", "done": False},
    ]
    id_counter = 4
    return {
        "message": "Database reset to initial state",
        "total": len(task_repository),
    }
