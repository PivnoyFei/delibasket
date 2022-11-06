import databases
import sqlalchemy

from settings import DATABASE_SQLITE, DATABASE_URL, USE_SQLITE
from sqlalchemy.orm import sessionmaker

metadata = sqlalchemy.MetaData()

if not USE_SQLITE:
    DATABASE_URL = DATABASE_SQLITE
    database = databases.Database(DATABASE_URL)
    engine = sqlalchemy.create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    database = databases.Database(DATABASE_URL)
    engine = sqlalchemy.create_engine(DATABASE_URL)
