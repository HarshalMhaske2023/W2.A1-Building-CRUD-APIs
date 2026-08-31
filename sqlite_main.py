"""
FastAPI Task Management REST API with SQLite Database

A production-ready REST API built with FastAPI, Uvicorn, and sqlite3.
Uses persistent SQLite database storage (tasks.db) for task management,
with parameterized SQL queries, schema validation, query filtering,
aggregate stats, state reset, and exact REST status codes.
"""

from contextlib import asynccontextmanager
import sqlite3
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Path, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

DB_FILE = "tasks.db"


# ------------------------------------------------------------------------------
# Database Helpers & Initialization
# ------------------------------------------------------------------------------
def get_db_connection() -> sqlite3.Connection:
    """Connects to SQLite database and configures Row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Creates tasks table if not existing and seeds 3 initial tasks if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM tasks")
    count_row = cursor.fetchone()
    count = count_row[0] if count_row else 0

    if count == 0:
        cursor.executemany(
            "INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)",
            [
                (1, "Complete Week 2 backend assignment", 0),
                (2, "Review REST status codes", 1),
                (3, "Push 6 commits to GitHub", 0),
            ],
        )
        conn.commit()
    conn.close()


def format_task(row: sqlite3.Row) -> Dict[str, Any]:
    """Converts SQLite Row to JSON-serializable task dict with bool status."""
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }


# ------------------------------------------------------------------------------
# FastAPI Lifespan Handler
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize database on startup."""
    init_db()
    yield


# Initialize FastAPI app with OpenAPI metadata and Lifespan
app = FastAPI(
    title="Task API",
    version="1.0",
    description="A complete FastAPI REST API for tasks with SQLite database.",
    lifespan=lifespan,
)


# ------------------------------------------------------------------------------
# Pydantic Schemas for Request/Response Validation & OpenAPI Documentation
# ------------------------------------------------------------------------------
class Task(BaseModel):
    """Schema representing a Task object."""

    id: int = Field(
        ...,
        description="Unique integer ID of the task",
        examples=[1],
    )
    title: str = Field(
        ...,
        description="Title of the task",
        examples=["Complete assignment"],
    )
    done: bool = Field(
        False,
        description="Completion status of the task",
        examples=[False],
    )


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    title: str = Field(
        ...,
        description="Non-empty title for the new task",
        examples=["Build a FastAPI app"],
    )


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    title: Optional[str] = Field(
        None,
        description="Optional new title",
        examples=["Updated title"],
    )
    done: Optional[bool] = Field(
        None,
        description="Optional new completion status",
        examples=[True],
    )


class RootResponse(BaseModel):
    """Schema for root endpoint response."""

    name: str = Field("Task API", description="Name of the API")
    version: str = Field("1.0", description="API version")
    endpoints: List[str] = Field(
        ["/tasks"], description="Available primary endpoints"
    )


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field("ok", description="Operational status")


class StatsResponse(BaseModel):
    """Schema for stats response."""

    total: int = Field(
        ..., description="Total number of tasks", examples=[3]
    )
    done: int = Field(
        ..., description="Number of completed tasks", examples=[1]
    )
    open: int = Field(
        ..., description="Number of open tasks", examples=[2]
    )


class ResetResponse(BaseModel):
    """Schema for reset response."""

    message: str = Field(
        "Database reset to initial state", description="Confirmation message"
    )
    total: int = Field(3, description="Total tasks after reset")


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    error: str = Field(..., description="Error message description")


# ------------------------------------------------------------------------------
# Global Exception Handler for Validation Errors
# ------------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def custom_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Custom validation handler for specific 400 error payloads."""
    _ = exc  # Unused variable placeholder for linter
    path = request.url.path
    if path.startswith("/tasks") and request.method == "POST":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"},
        )
    elif path.startswith("/tasks") and request.method == "PUT":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid update payload"},
        )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Invalid request payload"},
    )


# ------------------------------------------------------------------------------
# REST API Endpoints
# ------------------------------------------------------------------------------

@app.get(
    "/favicon.ico",
    include_in_schema=False,
)
async def favicon() -> Response:
    """Return 204 No Content for browser icon requests to keep logs clean."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/",
    response_model=RootResponse,
    status_code=status.HTTP_200_OK,
    summary="Root Information",
    description="Returns basic information about the API.",
)
async def get_root() -> Dict[str, Any]:
    """GET / -> 200 OK"""
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns system operational status.",
)
async def get_health() -> Dict[str, Any]:
    """GET /health -> 200 OK"""
    return {"status": "ok"}


@app.get(
    "/tasks",
    response_model=List[Task],
    status_code=status.HTTP_200_OK,
    summary="List All Tasks",
    description="Returns list of tasks from SQLite with optional filters.",
)
async def get_tasks(
    done: Optional[bool] = Query(
        None, description="Filter tasks by completion status"
    ),
    search: Optional[str] = Query(
        None, description="Case-insensitive search string for task title"
    ),
) -> List[Dict[str, Any]]:
    """GET /tasks -> SELECT * FROM tasks (with optional filtering)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM tasks WHERE 1=1"
    params: List[Any] = []

    if done is not None:
        query += " AND done = ?"
        params.append(1 if done else 0)

    if search is not None:
        query += " AND LOWER(title) LIKE ?"
        params.append(f"%{search.lower()}%")

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [format_task(row) for row in rows]


@app.get(
    "/stats",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Task Statistics",
    description="Returns aggregate statistics on total, done, and open tasks.",
)
async def get_stats() -> Dict[str, int]:
    """GET /stats -> 200 OK"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_row = cursor.fetchone()
    total = total_row[0] if total_row else 0

    cursor.execute("SELECT COUNT(*) FROM tasks WHERE done = 1")
    done_row = cursor.fetchone()
    completed = done_row[0] if done_row else 0

    conn.close()
    open_tasks = total - completed
    return {"total": total, "done": completed, "open": open_tasks}


@app.get(
    "/tasks/{id}",
    response_model=Task,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Task found and returned"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
    summary="Get Task by ID",
    description="Retrieve details of a single task by ID.",
)
async def get_task_by_id(
    id: int = Path(..., description="The ID of the task to retrieve")
) -> Union[Dict[str, Any], JSONResponse]:
    """GET /tasks/{id} -> SELECT * FROM tasks WHERE id = ?"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"},
        )
    return format_task(row)


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Task created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
    },
    summary="Create Task",
    description="Create a new task in SQLite database.",
)
async def create_task(request: Request) -> JSONResponse:
    """POST /tasks -> INSERT INTO tasks (title, done) VALUES (?, 0)"""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"},
        )

    if not isinstance(body, dict) or "title" not in body:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"},
        )

    raw_title = body["title"]
    if not isinstance(raw_title, str) or not raw_title.strip():
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Title is required and cannot be empty"},
        )

    title = raw_title.strip()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO tasks (title, done) VALUES (?, 0)", (title,))
    conn.commit()
    new_id = cursor.lastrowid

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to create task"},
        )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=format_task(row),
    )


@app.put(
    "/tasks/{id}",
    response_model=Task,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Task updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid payload"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
    summary="Update Task by ID",
    description="Update task title and/or completion status in SQLite.",
)
async def update_task(
    id: int,
    request: Request,
) -> Union[Dict[str, Any], JSONResponse]:
    """PUT /tasks/{id} -> UPDATE tasks SET title = ?, done = ? WHERE id = ?"""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid update payload"},
        )

    if not isinstance(body, dict):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid update payload"},
        )

    has_title = "title" in body and body["title"] is not None
    has_done = "done" in body and body["done"] is not None

    if not has_title and not has_done:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid update payload"},
        )

    if has_title:
        title_val = body["title"]
        if not isinstance(title_val, str) or not title_val.strip():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid update payload"},
            )

    if has_done:
        if not isinstance(body["done"], bool):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid update payload"},
            )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    existing = cursor.fetchone()

    if not existing:
        conn.close()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"},
        )

    new_title = body["title"].strip() if has_title else existing["title"]
    new_done = (1 if body["done"] else 0) if has_done else existing["done"]

    cursor.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (new_title, new_done, id),
    )
    conn.commit()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    updated_row = cursor.fetchone()
    conn.close()

    if not updated_row:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"},
        )

    return format_task(updated_row)


@app.delete(
    "/tasks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Task deleted successfully"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
    summary="Delete Task by ID",
    description="Deletes a task by ID from SQLite.",
)
async def delete_task(
    id: int = Path(..., description="The ID of the task to delete")
) -> Response:
    """DELETE /tasks/{id} -> DELETE FROM tasks WHERE id = ?"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"},
        )

    cursor.execute("DELETE FROM tasks WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/reset",
    response_model=ResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset Data Store",
    description="Resets SQLite tasks table back to initial 3 example tasks.",
)
async def reset_tasks() -> Dict[str, Any]:
    """POST /reset -> Resets SQLite database back to initial state."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM tasks")
    try:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")
    except Exception:
        pass

    cursor.executemany(
        "INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)",
        [
            (1, "Complete Week 2 backend assignment", 0),
            (2, "Review REST status codes", 1),
            (3, "Push 6 commits to GitHub", 0),
        ],
    )
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM tasks")
    total_row = cursor.fetchone()
    total = total_row[0] if total_row else 3
    conn.close()

    return {
        "message": "Database reset to initial state",
        "total": total,
    }
