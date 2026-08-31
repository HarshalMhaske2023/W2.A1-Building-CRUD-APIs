"""
AI-Generated Alternate Version of FastAPI Task Management REST API (Stage 6 Bonus)

Architectural Approach:
- Utilizes SQLAlchemy ORM instead of raw sqlite3 string queries.
- Manages connection lifecycle via FastAPI Dependency Injection (`Depends(get_db)` generator pattern).
- Defines a declarative ORM mapping (`TaskModel`) cleanly decoupled from Pydantic schemas.
- Handles database transactions safely with automatic rollback on errors.
"""

from contextlib import asynccontextmanager
from typing import Generator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = "sqlite:///./tasks.db"

# Create SQLAlchemy engine & SessionLocal factory
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Declarative Base for ORM Models
class Base(DeclarativeBase):
    pass


class TaskModel(Base):
    """SQLAlchemy ORM Task entity mapping to 'tasks' table."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    done = Column(Boolean, default=False, nullable=False)


# ------------------------------------------------------------------------------
# Dependency Injection for Database Session
# ------------------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """Provides transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initializes tables and seeds initial tasks if empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(TaskModel).count() == 0:
            initial_tasks = [
                TaskModel(id=1, title="Complete Week 2 backend assignment", done=False),
                TaskModel(id=2, title="Review REST status codes", done=True),
                TaskModel(id=3, title="Push 6 commits to GitHub", done=False),
            ]
            db.add_all(initial_tasks)
            db.commit()
    finally:
        db.close()


# ------------------------------------------------------------------------------
# FastAPI Lifespan Handler
# ------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to ensure database setup on startup."""
    init_db()
    yield


app = FastAPI(
    title="Task API - AI ORM Edition",
    version="2.0",
    description="Alternative FastAPI implementation utilizing SQLAlchemy ORM and Dependency Injection.",
    lifespan=lifespan,
)


# ------------------------------------------------------------------------------
# Pydantic Schemas for API Requests & Responses
# ------------------------------------------------------------------------------
class TaskRead(BaseModel):
    id: int
    title: str
    done: bool

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None)
    done: Optional[bool] = Field(None)


class StatsResponse(BaseModel):
    total: int
    done: int
    open: int


class ResetResponse(BaseModel):
    message: str
    total: int


# ------------------------------------------------------------------------------
# REST API Endpoints
# ------------------------------------------------------------------------------
@app.get("/", status_code=status.HTTP_200_OK)
def read_root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", status_code=status.HTTP_200_OK)
def check_health():
    return {"status": "ok"}


@app.get("/tasks", response_model=List[TaskRead], status_code=status.HTTP_200_OK)
def list_tasks(
    done: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(TaskModel)
    if done is not None:
        query = query.filter(TaskModel.done == done)
    if search is not None:
        query = query.filter(TaskModel.title.ilike(f"%{search}%"))
    return query.all()


@app.get("/stats", response_model=StatsResponse, status_code=status.HTTP_200_OK)
def get_stats(db: Session = Depends(get_db)):
    total = db.query(TaskModel).count()
    completed = db.query(TaskModel).filter(TaskModel.done == True).count()
    return {"total": total, "done": completed, "open": total - completed}


@app.get("/tasks/{id}", response_model=TaskRead, status_code=status.HTTP_200_OK)
def get_task(
    id: int = Path(...),
    db: Session = Depends(get_db),
):
    task = db.query(TaskModel).filter(TaskModel.id == id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Task {id} not found"},
        )
    return task


@app.post("/tasks", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
):
    clean_title = payload.title.strip()
    if not clean_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Title is required and cannot be empty"},
        )
    new_task = TaskModel(title=clean_title, done=False)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.put("/tasks/{id}", response_model=TaskRead, status_code=status.HTTP_200_OK)
def update_task(
    id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
):
    task = db.query(TaskModel).filter(TaskModel.id == id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Task {id} not found"},
        )

    has_title = payload.title is not None
    has_done = payload.done is not None

    if not has_title and not has_done:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid update payload"},
        )

    if has_title:
        clean_title = payload.title.strip()
        if not clean_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid update payload"},
            )
        task.title = clean_title

    if has_done:
        task.done = payload.done

    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    id: int,
    db: Session = Depends(get_db),
):
    task = db.query(TaskModel).filter(TaskModel.id == id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Task {id} not found"},
        )
    db.delete(task)
    db.commit()
    return None


@app.post("/reset", response_model=ResetResponse, status_code=status.HTTP_200_OK)
def reset_database(db: Session = Depends(get_db)):
    db.query(TaskModel).delete()
    db.commit()

    initial_tasks = [
        TaskModel(id=1, title="Complete Week 2 backend assignment", done=False),
        TaskModel(id=2, title="Review REST status codes", done=True),
        TaskModel(id=3, title="Push 6 commits to GitHub", done=False),
    ]
    db.add_all(initial_tasks)
    db.commit()
    total = db.query(TaskModel).count()
    return {"message": "Database reset to initial state", "total": total}
