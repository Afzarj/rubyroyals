import os
import re
import subprocess
import sys
from pathlib import Path

from sqlalchemy import inspect, text

from app import app, db


MIGRATION_DIR = Path(__file__).parent / "migrations" / "versions"


def migration_revisions():
    revisions = set()
    for path in MIGRATION_DIR.glob("*.py"):
        match = re.search(r"revision\s*=\s*[\"']([^\"']+)", path.read_text(encoding="utf-8"))
        if match:
            revisions.add(match.group(1))
    return revisions


def reset_orphaned_database_revision():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = set(inspector.get_table_names())
        if "alembic_version" not in table_names:
            return False

        current_revision = db.session.execute(
            text("SELECT version_num FROM alembic_version LIMIT 1")
        ).scalar()
        if not current_revision or current_revision in migration_revisions():
            return False

        print(f"Unknown Alembic revision {current_revision}; resetting pledge schema.")
        with db.engine.begin() as connection:
            if db.engine.dialect.name == "postgresql":
                connection.execute(text("DROP TABLE IF EXISTS pledge CASCADE"))
            else:
                connection.execute(text("DROP TABLE IF EXISTS pledge"))
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
        return True


if __name__ == "__main__":
    reset_orphaned_database_revision()
    subprocess.run([sys.executable, "-m", "flask", "db", "upgrade"], check=True)

    port = os.environ.get("PORT", "10000")
    os.execvp(
        "gunicorn",
        ["gunicorn", "--bind", f"0.0.0.0:{port}", "app:app"],
    )
