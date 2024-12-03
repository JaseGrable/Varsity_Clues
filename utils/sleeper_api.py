import requests

BASE_URL = "https://api.sleeper.app/v1"

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
