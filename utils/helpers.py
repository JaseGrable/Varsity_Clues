import pymysql
from flask import jsonify
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def map_players(player_ids):
    """
    Map player IDs to player names using the database.
    """
    if not player_ids:
        return []
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        formatted_ids = ','.join([f"'{player_id}'" for player_id in player_ids])
        query = f"SELECT player_id, first_name, last_name, position, team FROM players WHERE player_id IN ({formatted_ids})"
        cursor.execute(query)

        player_data = {row['player_id']: row for row in cursor.fetchall()}
        return [
            f"{player_data[player_id]['first_name']} {player_data[player_id]['last_name']} ({player_data[player_id]['position']})"
            if player_id in player_data else player_id
            for player_id in player_ids
        ]
    except Exception as e:
        print(f"Error mapping players: {e}")
        return player_ids
    finally:
        if 'connection' in locals():
            connection.close()

def format_rosters(rosters):
    """
    Sort rosters by wins and points, then assign rankings.
    """
    rosters = sorted(rosters, key=lambda r: (-r['settings']['wins'], -r['settings']['fpts']))
    for index, roster in enumerate(rosters, start=1):
        roster['rank'] = index
    return rosters

def error_response(message, status_code=400):
    """
    Standardized error response for JSON APIs.
    """
    response = jsonify({'error': message})
    response.status_code = status_code
    return response
