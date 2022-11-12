import databases
import sqlalchemy

from settings import DATABASE_URL

metadata = sqlalchemy.MetaData()
database = databases.Database(DATABASE_URL)
engine = sqlalchemy.create_engine(DATABASE_URL)


class Base:
    def __init__(self, database: databases.Database):
        self.database = database
