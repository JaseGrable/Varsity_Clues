import requests
from datetime import datetime
import pymysql
from dotenv import load_dotenv
import os
# Load environment variables
load_dotenv()

BASE_URL = "https://api.sleeper.app/v1"

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def get_user(username):
    try:
        response = requests.get(f"{BASE_URL}/user/{username}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def get_user_leagues(user_id, sport="nfl", season=None):
    if not season:
        season = datetime.now().year
    try:
        response = requests.get(f"{BASE_URL}/user/{user_id}/leagues/{sport}/{season}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching leagues: {e}")
        return None

def get_user_league_history(user_id, sport="nfl", start_year=2021):
    leagues_by_year = {}
    current_year = datetime.now().year
    for year in range(current_year, start_year - 1, -1):
        try:
            response = requests.get(f"{BASE_URL}/user/{user_id}/leagues/{sport}/{year}")
            response.raise_for_status()
            leagues = response.json()
            if leagues:
                leagues_by_year[year] = leagues
        except Exception as e:
            print(f"Error fetching leagues for {year}: {e}")
            continue
    return leagues_by_year

def get_league_details(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching league details: {e}")
        return None

def get_league_rosters(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching rosters: {e}")
        return None

def get_league_users(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching users: {e}")
        return None

def get_league_matchups(league_id, week):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/matchups/{week}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching matchups: {e}")
        return None

def get_current_week():
    try:
        response = requests.get(f"{BASE_URL}/state/nfl")
        response.raise_for_status()
        return response.json().get('week', 1)
    except Exception as e:
        print(f"Error fetching current week: {e}")
        return 1
def map_players_with_points(player_ids):
    """
    Map player IDs to their names and total points.
    """
    if not player_ids:
        return []

    try:
        response = requests.get(f"{BASE_URL}/players/stats/nfl")
        response.raise_for_status()
        stats = response.json()
    except Exception as e:
        print(f"Error fetching player stats: {e}")
        stats = {}

    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        formatted_ids = ','.join([f"'{player_id}'" for player_id in player_ids])
        query = f"SELECT player_id, first_name, last_name, position, team FROM players WHERE player_id IN ({formatted_ids})"
        cursor.execute(query)

        player_data = {row["player_id"]: row for row in cursor.fetchall()}
        mapped_players = []

        for player_id in player_ids:
            player = player_data.get(player_id)
            points = stats.get(player_id, {}).get("pts_ppr", 0)
            if player:
                mapped_players.append(
                    f"{player['first_name']} {player['last_name']} ({player['position']}, {player['team']}) - {points} points"
                )
            else:
                mapped_players.append(f"{player_id} - {points} points")

        return mapped_players
    except Exception as e:
        print(f"Error mapping players: {e}")
        return [f"{player_id} - 0 points" for player_id in player_ids]
    finally:
        if 'connection' in locals():
            connection.close()
