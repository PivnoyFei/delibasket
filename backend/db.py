import databases
import psycopg2
import sqlalchemy

from settings import DATABASE_SQLITE, DATABASE_URL

metadata = sqlalchemy.MetaData()


#def test_connect_db():
#    try:
#        psycopg2.connect(DATABASE_URL)
#        print("Connection to PostgreSQL DB successful.")
#        return DATABASE_URL
#    except psycopg2.OperationalError:
#        print(
#            "An error occurred while connecting to the PostgreSQL database,"
#            "reconnecting to SQLite was successful."
#        )
#        return DATABASE_SQLITE


TEST_DATABASE_URL = DATABASE_SQLITE # test_connect_db()
database = databases.Database(TEST_DATABASE_URL)
engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
