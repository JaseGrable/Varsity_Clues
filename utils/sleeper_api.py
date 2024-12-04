import requests
import pymysql
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

BASE_URL = "https://api.sleeper.app/v1"

# Database configuration loaded from environment variables
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def get_user(username):
    """
    Fetch user details from the Sleeper API.
    """
    try:
        response = requests.get(f"{BASE_URL}/user/{username}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def get_user_leagues(user_id, sport="nfl", season="2024"):
    """
    Fetch leagues for a user from the Sleeper API.
    """
    try:
        response = requests.get(f"{BASE_URL}/user/{user_id}/leagues/{sport}/{season}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching leagues: {e}")
        return None

def get_league_details(league_id):
    """
    Fetch league details by league ID.
    """
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching league details: {e}")
        return None

def get_league_rosters(league_id):
    """
    Fetch rosters for a league by league ID.
    """
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching rosters: {e}")
        return None

def get_league_users(league_id):
    """
    Fetch users in a league by league ID.
    """
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching users: {e}")
        return None

def get_league_matchups(league_id, week):
    """
    Fetch matchups for a league and a specific week.
    """
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/matchups/{week}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching matchups: {e}")
        return None

def get_current_week():
    """
    Fetch the current NFL week.
    """
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

    # Fetch player stats from the Sleeper API
    try:
        response = requests.get(f"{BASE_URL}/players/stats/nfl")
        response.raise_for_status()
        stats = response.json()  # Assuming the structure {player_id: {"pts_ppr": value, ...}}
    except Exception as e:
        print(f"Error fetching player stats: {e}")
        stats = {}

    try:
        # Connect to the database
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Format player IDs for SQL query safely
        query = f"SELECT player_id, first_name, last_name, position, team FROM players WHERE player_id IN ({','.join(['%s'] * len(player_ids))})"
        cursor.execute(query, player_ids)

        # Fetch player data and create a mapping
        player_data = {row["player_id"]: row for row in cursor.fetchall()}
        mapped_players = []

        for player_id in player_ids:
            player = player_data.get(player_id)
            points = stats.get(player_id, {}).get("pts_ppr", 0)  # Default to 0 if no points
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

def get_previous_league_id(current_league):
    """
    Retrieve the ID of the previous year's league.
    """
    try:
        return current_league.get("previous_league_id")
    except Exception as e:
        print(f"Error fetching previous league ID: {e}")
        return None

def get_playoff_bracket(league_id, bracket_type):
    """
    Fetch the playoff bracket for a league.

    Parameters:
        league_id (str): The league ID.
        bracket_type (str): Either "winners" or "losers".

    Returns:
        list: A list of playoff bracket matchups.
    """
    if bracket_type not in ["winners", "losers"]:
        raise ValueError("Invalid bracket type. Use 'winners' or 'losers'.")

    url = f"{BASE_URL}/league/{league_id}/{bracket_type}_bracket"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {bracket_type} bracket: {e}")
        return []

def get_previous_year_data(previous_league_id):
    """
    Fetch all data for the previous year's league, including rosters and matchups.
    """
    try:
        rosters = get_league_rosters(previous_league_id)
        previous_year_matchups = {}
        league_details = get_league_details(previous_league_id)

        # Fetch matchups by week
        total_weeks = league_details.get("settings", {}).get("playoff_week_start", 15) - 1
        for week in range(1, total_weeks + 1):
            previous_year_matchups[week] = get_league_matchups(previous_league_id, week)

        return league_details, rosters, previous_year_matchups
    except Exception as e:
        print(f"Error fetching previous year data: {e}")
        return None, None, None
