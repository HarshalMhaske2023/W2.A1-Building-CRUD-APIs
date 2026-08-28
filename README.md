# FastAPI To-Do CRUD API

A production-ready, performant REST API built using **Python**, **FastAPI**, and **Uvicorn** with in-memory state management.

🔗 **GitHub Repository**: [https://github.com/HarshalMhaske2023/W2.A1-Building-CRUD-APIs](https://github.com/HarshalMhaske2023/W2.A1-Building-CRUD-APIs)

---

## Project Overview

This project implements a complete CRUD (Create, Read, Update, Delete) REST API for managing tasks. It utilizes Pydantic for schema validation, FastAPI for route definition and interactive OpenAPI documentation, and Uvicorn as the ASGI server.

### Key Features
- **In-Memory Data Store**: Fast, lightweight task management pre-filled with initial tasks.
- **Auto-Incrementing IDs**: Unique sequential IDs for newly created items.
- **Validation**: Enforces non-empty, non-whitespace titles and valid update payloads.
- **Query Filters**: Optional filtering by completion status (`?done=true|false`) and substring title search (`?search=query`).
- **Statistics & State Reset**: Aggregate statistics endpoint (`/stats`) and database reset endpoint (`/reset`).

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

3. Access the interactive documentation in your browser:
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

---

## Swagger UI Screenshots

Below is the visual overview of the interactive OpenAPI documentation generated at `http://localhost:8000/docs`:

```text
+-------------------------------------------------------------------------+
|                        SWAGGER UI DOCUMENTATION                         |
|                     http://localhost:8000/docs                          |
+-------------------------------------------------------------------------+
| [GET]    /               Root API Information                           |
| [GET]    /health         Health Status Check                            |
| [GET]    /tasks          List All Tasks (Query filtering)               |
| [POST]   /tasks          Create New Task                                |
| [GET]    /tasks/{id}     Get Task by Unique ID                          |
| [PUT]    /tasks/{id}     Update Task Title / Completion Status          |
| [DELETE] /tasks/{id}     Delete Task by Unique ID                       |
| [GET]    /stats          Task Analytics & Summary                       |
| [POST]   /reset          Reset Data Store to Default State              |
+-------------------------------------------------------------------------+
```

![Swagger UI Screenshot](./docs/swagger_ui.png)
![Endpoints Overview](./docs/swagger_endpoints.png)

> *(Swagger UI screenshot placeholders attached above. Save your screenshots to `docs/swagger_ui.png` to render automatically).*

---

## Mocked Terminal Output (`curl -i`)

Here is an example execution of a `curl -i` request fetching the task list:

```text
$ curl -i http://localhost:8000/tasks

HTTP/1.1 200 OK
date: Fri, 28 Aug 2026 14:08:30 GMT
server: uvicorn
content-length: 226
content-type: application/json

[
  {
    "id": 1,
    "title": "Complete Week 2 backend assignment",
    "done": false
  },
  {
    "id": 2,
    "title": "Review REST status codes",
    "done": true
  },
  {
    "id": 3,
    "title": "Push 6 commits to GitHub",
    "done": false
  }
]
```

---

## AI vs Me

> *Note: Detailed side-by-side code diff analysis between `main.py` and `ai-version/main.py` will be added shortly after running `git diff --no-index main.py ai-version/main.py`.*
