"""
Database migrations for the Central Job Coordinator.

Run migrations with:
    psql -d your_database -f migrations/001_initial.sql

Or use a migration tool like Alembic.
"""

MIGRATIONS = [
    "001_initial.sql",
]

__all__ = ["MIGRATIONS"]
