from app.database.session import SessionLocal
from app.seed import run_all

if __name__ == "__main__":
    with SessionLocal() as session:
        run_all(session)
