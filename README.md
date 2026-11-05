# Smart Waste Management & Recycling Operations System

FastAPI backend for waste collection, vehicles and crews, recycling centres, processing, disposal, complaints, analytics and audit - with **OAuth2 (password flow) + JWT** authentication and **Google OAuth2 sign-up**.

**Stack:** Python 3.11+ · FastAPI · Pydantic v2 · SQLAlchemy 2 · PostgreSQL / MySQL (SQLite for quick start) · JWT · Authlib (Google) · Alembic · Pytest · Docker

## Quick start
```bash
cp .env.example .env
docker compose up --build            # API on http://localhost:8000/docs
```
or without Docker:
```bash
pip install -r requirements.txt
cp .env.example .env                 # defaults to SQLite; for PostgreSQL/MySQL see docs/deployment.md
alembic upgrade head && python -m app.seed
python run.py
```
Default login (change it!): `admin@example.com` / `Admin@12345`

In Swagger (`/docs`) click **Authorize**, enter the e-mail as *username*, and every protected endpoint works.

## Authentication in one minute
| Goal | Call |
|---|---|
| Register (customer) | `POST /api/v1/auth/register` |
| Log in (OAuth2 password flow) | `POST /api/v1/auth/login` form `username`, `password` |
| Register / log in with Google | open `GET /api/v1/auth/google/login` in a browser |
| Renew / log out | `POST /auth/refresh`, `POST /auth/logout` |
| Who am I | `GET /auth/me` |

Google setup (client ID/secret, redirect URI) is in [docs/api_documentation.md](docs/api_documentation.md).

## Project layout
`app/api` HTTP endpoints · `app/services` business rules · `app/repositories` queries · `app/models` tables · `app/schemas` Pydantic · `app/core` config/JWT/OAuth/errors · `app/enums` · `app/seed` · `app/tasks` · `alembic/` · `tests/` (unit, integration, security) · `postman/` · `docs/`

## Tests
```bash
pytest        # 133 tests, in-memory SQLite, no external services
```
Covers authentication (incl. Google flow with a fake provider), role permissions, pickup creation, vehicle assignment, **capacity validation**, collection tracking, waste transfer, recycling calculations, disposal approval and dashboard metrics.

## Docs
[architecture](docs/architecture.md) · [database schema](docs/database_schema.md) · [business rules](docs/business_rules.md) · [calculation formulas](docs/calculation_formulas.md) · [API](docs/api_documentation.md) · [deployment](docs/deployment.md)

## Scope notes
* Password-reset tokens are returned in the API response only outside `production`; connect a mail provider before going live.
* Photo evidence is stored as reference URLs (no binary upload), as specified.
* Redis is optional and not required by any feature; `REDIS_URL` is reserved for caching/queues.
