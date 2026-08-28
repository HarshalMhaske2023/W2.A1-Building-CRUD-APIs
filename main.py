"""
FastAPI Task Management REST API

A production-ready REST API built with FastAPI and Uvicorn.
Uses an in-memory data store for managing tasks, complete with
validation, query filtering, stats, reset functionality, and precise
REST status codes.
"""

import copy
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Path, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Initialize FastAPI app with OpenAPI metadata
app = FastAPI(
    title="Task API",
    version="1.0",
    description=(
        "A complete FastAPI REST API for task management with "
        "in-memory storage."
    ),
)

# ------------------------------------------------------------------------------
# In-Memory Storage & Initial Data
# ------------------------------------------------------------------------------
INITIAL_TASKS: List[Dict[str, Any]] = [
    {"id": 1, "title": "Complete Week 2 backend assignment", "done": False},
    {"id": 2, "title": "Review REST status codes", "done": True},
    {"id": 3, "title": "Push 6 commits to GitHub", "done": False},
]

# Mutable in-memory database and auto-increment counter
tasks_db: List[Dict[str, Any]] = copy.deepcopy(INITIAL_TASKS)
next_id: int = 4


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
    description="Returns list of tasks with optional query filters.",
)
async def get_tasks(
    done: Optional[bool] = Query(
        None, description="Filter tasks by completion status"
    ),
    search: Optional[str] = Query(
        None, description="Case-insensitive search string for task title"
    ),
) -> List[Dict[str, Any]]:
    """GET /tasks with optional filters ?done=... and ?search=..."""
    results = tasks_db

    if done is not None:
        results = [t for t in results if t["done"] == done]

    if search is not None:
        search_lower = search.lower()
        results = [t for t in results if search_lower in t["title"].lower()]

    return results


@app.get(
    "/stats",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Task Statistics",
    description="Returns aggregate statistics on total, done, and open tasks.",
)
async def get_stats() -> Dict[str, int]:
    """GET /stats -> 200 OK"""
    total = len(tasks_db)
    completed = sum(1 for t in tasks_db if t["done"])
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
    """GET /tasks/{id}"""
    task = next((t for t in tasks_db if t["id"] == id), None)
    if not task:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"},
        )
    return task


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Task created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid input"},
    },
    summary="Create Task",
    description="Create a new task with auto-incremented ID.",
)
async def create_task(request: Request) -> JSONResponse:
    """POST /tasks -> Accepts {"title": str}"""
    global next_id

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

    new_task = {
        "id": next_id,
        "title": raw_title.strip(),
        "done": False,
    }
    next_id += 1
    tasks_db.append(new_task)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=new_task,
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
    description="Update an existing task's title and/or done status.",
)
async def update_task(
    id: int,
    request: Request,
) -> Union[Dict[str, Any], JSONResponse]:
    """PUT /tasks/{id}"""
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

    task = next((t for t in tasks_db if t["id"] == id), None)
    if not task:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"},
        )

    if has_title:
        task["title"] = body["title"].strip()
    if has_done:
        task["done"] = body["done"]

    return task


@app.delete(
    "/tasks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Task deleted successfully"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
    summary="Delete Task by ID",
    description="Deletes a task by ID.",
)
async def delete_task(
    id: int = Path(..., description="The ID of the task to delete")
) -> Response:
    """DELETE /tasks/{id}"""
    task = next((t for t in tasks_db if t["id"] == id), None)
    if not task:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"},
        )

    tasks_db.remove(task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/reset",
    response_model=ResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset Data Store",
    description="Resets the in-memory task database back to initial state.",
)
async def reset_tasks() -> Dict[str, Any]:
    """POST /reset"""
    global tasks_db, next_id
    tasks_db = copy.deepcopy(INITIAL_TASKS)
    next_id = 4
    return {
        "message": "Database reset to initial state",
        "total": len(tasks_db),
    }
