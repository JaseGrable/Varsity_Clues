import pymysql
from dotenv import load_dotenv
import os
import json

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def fetch_previous_league_data(league_id):
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM previous_leagues WHERE league_id = %s", (league_id,))
            league = cursor.fetchone()
            cursor.execute("SELECT * FROM previous_rosters WHERE league_id = %s", (league_id,))
            rosters = cursor.fetchall()
        return league, rosters
    finally:
        connection.close()

