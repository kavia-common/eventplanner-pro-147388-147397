"""
Utility script to initialize the DB schema.
Run:  python -m src.api.init_db
"""

from .database import engine, Base
from . import models  # Import models module to ensure all models are loaded (to register tables with metadata)

# PUBLIC_INTERFACE
def init_db():
    """
    PUBLIC_INTERFACE
    Initializes all tables defined in models.

    Usage:
        import and call init_db() or run as standalone script.
    """
    _ = models  # Ensure imported and not marked as unused (for linter + table registration)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

if __name__ == "__main__":
    init_db()
