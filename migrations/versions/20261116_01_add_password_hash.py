"""Create missing CRM tables and add password hashes to existing users."""

from alembic import op
from sqlalchemy import Column, String, inspect

from app.database import Base
import app.models  # noqa: F401 - register model metadata


revision = "20261116_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    user_columns = {column["name"] for column in inspect(bind).get_columns("users")}
    if "password_hash" not in user_columns:
        op.add_column("users", Column("password_hash", String(length=255), nullable=True))
    op.execute(
        "UPDATE users SET email = 'legacy-user-' || id || '@invalid.local' "
        "WHERE id NOT IN (SELECT MIN(id) FROM users GROUP BY lower(email))"
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email_lower ON users (lower(email))")
    if "tasks" in inspect(bind).get_table_names():
        op.execute(
            "UPDATE tasks SET status = 'pending' "
            "WHERE status NOT IN ('pending', 'in_progress', 'completed')"
        )


def downgrade() -> None:
    bind = op.get_bind()
    op.execute("DROP INDEX IF EXISTS ix_users_email_lower")
    user_columns = {column["name"] for column in inspect(bind).get_columns("users")}
    if "password_hash" in user_columns:
        op.drop_column("users", "password_hash")
