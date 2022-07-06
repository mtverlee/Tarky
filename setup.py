import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()


def setupDatabase():
    connection = psycopg2.connect(database=os.getenv('POSTGRES_DATABASE'),
                                  user=os.getenv('POSTGRES_USER'),
                                  password=os.getenv('POSTGRES_PASSWORD'),
                                  host=os.getenv('POSTGRES_HOST'),
                                  port=os.getenv('POSTGRES_PORT'))  # Connect to the database
    cursor = connection.cursor()  # Get database cursor
    # Set database table schema
    cursor.execute(
        "CREATE TABLE patchnotes (id serial, patch_id text, url text, date timestamp)")
    connection.commit()  # Write changes to database
    cursor.execute(
        "CREATE TABLE guilds (id serial, guild_id text, name text, date timestamp)")
    connection.commit()
    cursor.execute(
        "CREATE TABLE channels (id serial, channel_id text, date timestamp)")
    connection.commit()
    connection.close()  # Close connection to databbase


if __name__ == "__main__":
    setupDatabase()
