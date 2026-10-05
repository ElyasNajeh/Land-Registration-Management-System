# Land Registration

A workflow-driven land registration system for managing applicants, parcel applications, supporting documents, surveys, registrar decisions, certificates, maps, and operational analytics.

## Features

- Applicant profiles with verification state and linked applications
- Land application submission with parcel details, GeoJSON location, document metadata, and idempotency
- Server-side application search, filtering, sorting, and pagination
- Validated registration workflow, interruptions, notes, objections, document review, and certificate issuance
- Workload-aware surveyor assignment, ordered field milestones, survey reports, and registrar review
- Server-side KPI/aggregation endpoints and a filtered Leaflet parcel map
- Responsive React staff dashboard with loading, empty, error, and pagination states

## Technologies & Tools

- React and Vite — component-based frontend and development/build tooling
- FastAPI and Pydantic — typed HTTP API and request validation
- MongoDB and PyMongo — document persistence, indexes, aggregation, and GeoJSON queries
- Leaflet and OpenStreetMap — interactive parcel/application map
- Pytest, Mongomock, and HTTPX — isolated API workflow tests

## Prerequisites

- Python 3.10 or newer
- Node.js 20 or newer with npm
- MongoDB 6 or newer, locally or through MongoDB Atlas

## Environment Variables

Backend variables are documented in `LandRegistrationAPI/.env.example`:

- `APP_NAME` — API display name
- `API_PREFIX` — API route prefix; defaults to `/api`
- `DATABASE_NAME` — MongoDB database name
- `MONGODB_URL` — MongoDB connection URI
- `CORS_ORIGINS` — comma-separated permitted frontend origins
- `STAFF_API_KEY` — optional staff endpoint protection key

The frontend accepts `VITE_API_URL`; `/api` uses the included Vite development proxy. Do not place secrets in frontend variables.

## Getting Started

```bash
git clone <repository-url>
cd Land-Registration-Management-System
python -m venv .venv
```

Activate the virtual environment (`.venv\Scripts\Activate.ps1` on PowerShell or `source .venv/bin/activate` on macOS/Linux), then configure and run the backend:

```bash
pip install -r requirements.txt
cp LandRegistrationAPI/.env.example LandRegistrationAPI/.env
cd LandRegistrationAPI
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Set `MONGODB_URL` and `DATABASE_NAME` in `LandRegistrationAPI/.env`. Required indexes are created automatically when the API starts. In another terminal, run the frontend:

```bash
cd LandRegistrationUI
cp .env.example .env
npm install
npm run dev
```

Open `http://127.0.0.1:5173`. API documentation is available at `http://127.0.0.1:8000/docs`. Run verification with:

```bash
pip install -r requirements-dev.txt
pytest
cd LandRegistrationUI
npm run lint
npm run build
```

On PowerShell, use `Copy-Item` instead of `cp` if preferred.

## Project Structure

- `LandRegistrationAPI/app/` — FastAPI configuration, MongoDB integration, feature routers, schemas, and services
- `LandRegistrationUI/src/` — React pages, reusable components, hooks, and API client
- `LandRegistrationUI/css/` — preserved visual system and responsive layout
- `COMP4382_Land_Registration_Final_Project2nd2025-2026.pdf` — original project specification


## Team Members

- [Elyas Najeh](https://github.com/ElyasNajeh).
- [Hareth Shoman](https://github.com/Hareth5).
- [Ahmad Omariyeh](https://github.com/Ahmad-Omaryeh).
