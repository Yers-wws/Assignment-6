"""Database storage module providing backward compatibility and database integration."""

import os
from database import engine, SessionLocal, Base, get_db
from scripts.seed import seed_database


class DatabaseStorage:
    """Storage bridge interfacing with the relational database."""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self.Base = Base

    def seed_data(self):
        """Populates the database tables with seed data."""
        seed_database()

    def get_session(self):
        """Returns a new database session."""
        return self.SessionLocal()


# Global database storage instance
db = DatabaseStorage()
