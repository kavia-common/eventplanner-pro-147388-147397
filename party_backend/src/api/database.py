import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PUBLIC_INTERFACE
def get_database_url():
    """
    Returns the database URL from environment variables.

    Raises:
        RuntimeError: If the database URL is not set.
    """
    # Conventional variable names you may need to update depending on actual .env
    url = os.getenv('DATABASE_URL')
    if not url:
        raise RuntimeError("DATABASE_URL environment variable is not set!")
    return url

# Set up the SQLAlchemy Base
Base = declarative_base()

# Create engine and session factory using DATABASE_URL
DATABASE_URL = get_database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
