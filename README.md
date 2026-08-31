# FastAPI To-Do CRUD API (SQLite Persistence)

A production-ready, performant REST API built using **Python**, **FastAPI**, **Uvicorn**, and **SQLite database persistence**.

🔗 **GitHub Repository**: [https://github.com/HarshalMhaske2023/W2.A1-Building-CRUD-APIs](https://github.com/HarshalMhaske2023/W2.A1-Building-CRUD-APIs)

---

## Project Overview

This project implements a complete CRUD (Create, Read, Update, Delete) REST API for managing tasks. It utilizes Pydantic for schema validation, FastAPI for route definition and interactive OpenAPI documentation, Uvicorn as the ASGI server, and an SQLite database for persistent storage.

### Why SQLite Was Chosen
- **Single-File Storage**: Entire database lives in a lightweight single file (`tasks.db`), eliminating the need for complex external database servers (like PostgreSQL or MySQL) for local development.
- **Zero Setup & Zero Configuration**: Requires no installation or background daemon service; Python includes native support via the built-in `sqlite3` module.
- **Data Persistence (Survives Restarts)**: Unlike in-memory data structures, SQLite writes all table state to disk, so tasks persist seamlessly across application restarts.

---

## Database Architecture & Behavior

- **Database File**: [`tasks.db`](file:///c:/Users/HP/OneDrive/Desktop/FlyRank%20Tasks/CRUD%20APIs/tasks.db) located in the project root directory.
- **Automatic Lifecycle**: Initialized automatically on startup via FastAPI `lifespan` handler (`init_db()`). If `tasks.db` does not exist or the `tasks` table is empty, it automatically creates the table schema and seeds the 3 initial tasks.
- **Version Control Safety**: `tasks.db` is explicitly listed in `.gitignore` to prevent local binary database files from being committed to source control.

---

## Run Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the FastAPI development server:
   ```bash
   uvicorn main:app --reload
   ```

3. Access the interactive API documentation:
   - **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Core CRUD Endpoints

| Method | Path | Description | Success Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/tasks` | Retrieve all tasks (supports `?done=` and `?search=` filters) | `200 OK` |
| `GET` | `/tasks/{id}` | Retrieve details of a single task by ID | `200 OK` |
| `POST` | `/tasks` | Create a new task (requires JSON body `{"title": "..."}`) | `201 Created` |
| `PUT` | `/tasks/{id}` | Update task `title` and/or `done` status by ID | `200 OK` |
| `DELETE` | `/tasks/{id}` | Delete task by ID (returns empty response body) | `204 No Content` |
| `GET` | `/stats` | Aggregate stats (`total`, `done`, `open`) | `200 OK` |
| `POST` | `/reset` | Reset database state back to initial 3 seeded tasks | `200 OK` |

---

## Database Verification (DB Browser for SQLite)

The SQLite database structure and seeded dataset were manually inspected and verified using **DB Browser for SQLite**.

### Embedded Screenshot
![DB Browser Screenshot](db_browser.png)

### Manual SQL Verification Query
Executing the following SQL query in DB Browser:
```sql
SELECT * FROM tasks;
```

**Query Result**: Successfully returned the 3 initial seeded tasks from `tasks.db`:
```text
+----+------------------------------------+------+
| id | title                              | done |
+----+------------------------------------+------+
| 1  | Complete Week 2 backend assignment | 0    |
| 2  | Review REST status codes           | 1    |
| 3  | Push 6 commits to GitHub           | 0    |
+----+------------------------------------+------+
```

---

## AI vs Me (Stage 6)

-FastAPI Task Management REST API with SQLite Database
+AI-Generated Alternate Version of FastAPI Task Management REST API (Stage 6 Bonus)

-A production-ready REST API built with FastAPI, Uvicorn, and sqlite3.
-Uses persistent SQLite database storage (tasks.db) for task management,
-with parameterized SQL queries, schema validation, query filtering,
-aggregate stats, state reset, and exact REST status codes.
+Architectural Approach:
+- Utilizes SQLAlchemy ORM instead of raw sqlite3 string queries.
+- Manages connection lifecycle via FastAPI Dependency Injection (`Depends(get_db)` generator pattern).
+- Defines a declarative ORM mapping (`TaskModel`) cleanly decoupled from Pydantic schemas.
+- Handles database transactions safely with automatic rollback on errors.
 """

 Three Major Observations:

1. **Payload Handling & Type Safety vs. Raw Dictionaries**:
   * **Hand-Built Version (`main.py`)**: Utilized direct Pydantic models in endpoint signatures (`task: TaskCreate`, `task: TaskUpdate`), allowing FastAPI to automatically validate schemas, handle type casting, and document request bodies accurately in Swagger UI.
   * **AI Version (`ai-version/main.py`)**: Defined Pydantic models at the top (`TaskItem`, `TaskCreatePayload`) but bypassed them in endpoint function signatures by accepting generic `payload: Dict[str, object]`. It then implemented verbose manual `isinstance()` checks and `.strip()` string validations inside the route handlers.

2. **Error Handling Architecture**:
   * **Hand-Built Version**: Handled error scenarios cleanly using status-code-bound exceptions with concise error dict payloads.
   * **AI Version**: Injected custom nested error dictionaries into `HTTPException(detail={"error": "..."})` across every validation checkpoint, resulting in `{ "detail": { "error": "..." } }` wrapped payloads instead of standard top-level JSON fields.

3. **Data Mutation & State Management**:
   * **Hand-Built Version**: Separated list mutations and indexing cleanly with standard Python list comprehensions and counter management.
   * **AI Version**: Relied on `global id_counter` and `global task_repository` statements within mutable routes like `/reset` and `/tasks` POST, introducing procedural state mutation rather than modular store encapsulation.
>>>>>>> 14e49a586065827727f0936283f8a223549dcffd
