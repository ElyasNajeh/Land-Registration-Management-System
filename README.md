# Land Registration Management System

A simple land registration web service and UI built with FastAPI (backend) and a static frontend (LandRegistrationUI).

## Project structure

- Land-Registration-Management-System-main/
  - LandRegistrationAPI/ - FastAPI backend
    - app/main.py - FastAPI app entrypoint
    - app/core/config.py - configuration and environment settings
    - app/features/ - feature routers and services (applications, assignments, survey assignments, applicants)
    - requirements.txt - Python dependencies
  - LandRegistrationUI/ - Static frontend (HTML/CSS/JS)

## Features

- Create and manage land applications
- Assign surveyors and manage survey milestones and reports
- Applicant management
- Simple UI for interacting with the API

## Prerequisites

- Python 3.10+ (recommended)
- pip
- Node.js (optional, for running `LandRegistrationUI` server if you prefer node)
- A MongoDB instance (Atlas or local)

## Environment variables

Create a `.env` file in `LandRegistrationAPI/` containing at least the following:

```
APP_NAME=Land Registration API
DATABASE_NAME=<your_db_name>
MONGODB_HOST=<host>
MONGODB_USER=<user>
MONGODB_PASSWORD=<password>
MONGODB_APP_NAME=<app_name>
SECRET_KEY=<secret>
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
ALGORITHM=HS256
```

The application reads settings from `app/core/config.py` and loads `.env` automatically.

## Install and run (backend)

1. Create and activate a virtual environment:

On Windows (PowerShell):

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

On macOS / Linux:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the API (from the `LandRegistrationAPI` folder):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## Run the frontend

The UI is a static site in `LandRegistrationUI/`. You can open `index.html` directly in a browser or serve it with a simple static server.

If the project includes `server.cjs`, you can start it with Node.js:

```bash
cd LandRegistrationUI
node server.cjs
```

Or use a simple Python static server for development:

```bash
cd LandRegistrationUI
python -m http.server 3000
# then open http://localhost:3000 in your browser
```

## API Endpoints (overview)

The backend registers several routers. Key endpoints include:

- Applications
  - `POST /applications/` — Create application
  - `GET /applications/` — List applications (supports query params `status`, `application_type`, `skip`, `limit`, `sort_field`, `sort_order`)
  - `GET /applications/{application_id}` — Get application by id
  - `PATCH /applications/{application_id}/transition` — Change application status
  - `POST /applications/{application_id}/hold` — Put application on hold
  - `POST /applications/{application_id}/reject` — Reject application
  - `POST /applications/{application_id}/certificate` — Generate certificate
  - `POST /applications/{application_id}/notes` — Add note
  - `POST /applications/{application_id}/missing-documents` — Mark missing documents
  - `POST /applications/{application_id}/objection` — Mark under objection

- Assignments
  - `POST /applications/{application_id}/auto-assign-surveyor` — Auto assign a surveyor
  - `PATCH /applications/{application_id}/survey-milestone` — Add survey milestone
  - `POST /applications/{application_id}/survey-report` — Add survey report
  - `PATCH /applications/{application_id}/registrar-review` — Registrar review

- Survey Assignments
  - `POST /staff/` — Create staff
  - `GET /staff/{staff_id}` — Get staff by id

- Applicants
  - `POST /applicants/` — Create applicant
  - `GET /applicants/{applicant_id}` — Get applicant
  - `GET /applicants/{applicant_id}/applications` — List applicant's applications

Refer to the router files in `app/features/` for request schemas and more details.

## Notes and next steps

- Update the `.env` with correct MongoDB connection details.
- Add API docs links: when running the server, FastAPI exposes OpenAPI at `/docs` and `/redoc`.
- Consider adding tests and Dockerfile for easy deployment.

## Contact

If you need further help setting up or documenting specific endpoints, open an issue or ask for more details.
