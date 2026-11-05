# Deployment

## Docker Compose (recommended)
```bash
cp .env.example .env          # set SECRET_KEY, SESSION_SECRET, SUPER_ADMIN_PASSWORD (and Google keys if used)
docker compose up --build
```
The `api` container waits for PostgreSQL, runs `alembic upgrade head`, seeds the super admin and the 7 waste categories (idempotent), then serves on **http://localhost:8000** (`/docs`, `/health`). Optional Redis: `docker compose --profile redis up`.

## Local (no Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt            # SQLite needs nothing more
# PostgreSQL: pip install -r requirements-postgres.txt   |   MySQL: pip install -r requirements-mysql.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
python run.py                 # or: uvicorn app.main:app --reload
```
MySQL: `DATABASE_URL=mysql+pymysql://user:pass@host:3306/db`. PostgreSQL: `postgresql+psycopg2://user:pass@host:5432/db`.

## Tests
```bash
pytest                         # uses an in-memory SQLite database, no setup needed
```

## Production checklist
* `ENVIRONMENT=production` (enforces a non-default `SECRET_KEY`, secure session cookie, hides the reset token from API responses).
* Strong random `SECRET_KEY` and `SESSION_SECRET` (`openssl rand -hex 32`); change `SUPER_ADMIN_PASSWORD` immediately.
* Terminate TLS in front of the API; the Google redirect URI must be `https://`.
* Restrict `CORS_ORIGINS` to your front-end origin(s).
* Wire `/auth/forgot-password` to a mail provider (currently the token is returned only outside production).
* Schedule `python -c "from app.database.session import SessionLocal; from app.tasks import maintenance_tasks as t; print(t.run(SessionLocal()))"` (and `notification_tasks.run`) daily via cron / a job runner for maintenance-due and pending-approval alerts.
