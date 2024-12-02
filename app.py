from flask import Flask, render_template, request, redirect, url_for
import requests
import pymysql
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Base URL for Sleeper API
BASE_URL = "https://api.sleeper.app/v1"

# Database configuration loaded from environment variables
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Fetch user details from the Sleeper API
def get_user(username):
    try:
        response = requests.get(f"{BASE_URL}/user/{username}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

# Fetch leagues for a user from the Sleeper API
def get_user_leagues(user_id, sport="nfl", season="2024"):
    try:
        response = requests.get(f"{BASE_URL}/user/{user_id}/leagues/{sport}/{season}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching leagues: {e}")
        return None

# Fetch league details by league ID
def get_league_details(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching league details: {e}")
        return None

# Fetch rosters for a league by league ID
def get_league_rosters(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching rosters: {e}")
        return None

# Fetch users in a league
def get_league_users(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching users: {e}")
        return None

# Fetch the current NFL week
def get_current_week():
    try:
        response = requests.get(f"{BASE_URL}/state/nfl")
        response.raise_for_status()
        return response.json().get('week', 1)
    except Exception as e:
        print(f"Error fetching current week: {e}")
        return 1

# Function to map player IDs to player names using the database
def map_players(player_ids):
    if not player_ids:
        return []
    try:
        # Connect to the database
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # Format player IDs for SQL query
        formatted_ids = ','.join([f"'{player_id}'" for player_id in player_ids])
        query = f"SELECT player_id, first_name, last_name, position, team FROM players WHERE player_id IN ({formatted_ids})"
        cursor.execute(query)

        # Fetch player data and create a mapping
        player_data = {row['player_id']: row for row in cursor.fetchall()}
        return [
            f"{player_data[player_id]['first_name']} {player_data[player_id]['last_name']} ({player_data[player_id]['position']})"
            if player_id in player_data else player_id
            for player_id in player_ids
        ]
    except Exception as e:
        print(f"Error mapping players: {e}")
        return player_ids  # Return player IDs as fallback
    finally:
        if 'connection' in locals():
            connection.close()

# Route for the home page
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        user_data = get_user(username)
        if not user_data:
            return render_template('home.html', error="User not found.")
        return redirect(url_for('leagues', user_id=user_data['user_id']))
    return render_template('home.html')

# Route to display leagues
@app.route('/leagues/<string:user_id>', methods=['GET'])
def leagues(user_id):
    leagues = get_user_leagues(user_id)
    if not leagues:
        return render_template('leagues.html', error="No leagues found.")
    return render_template('leagues.html', leagues=leagues)

# Route to display league details
@app.route('/league/<string:league_id>', methods=['GET'])
def league_details(league_id):
    league = get_league_details(league_id)
    rosters = get_league_rosters(league_id)
    users = get_league_users(league_id)

    if not league or not rosters or not users:
        return render_template('league_details.html', error="League details, rosters, or users not found.")

    # Map user IDs to team names and usernames
    user_map = {
        user['user_id']: {
            'team_name': user['metadata'].get('team_name', f"Roster {user['user_id']}"),
            'username': user['display_name']
        }
        for user in users
    }

    # Add team details to rosters
    for roster in rosters:
        owner_info = user_map.get(roster['owner_id'], {'team_name': f"Roster {roster['roster_id']}", 'username': 'Unknown User'})
        roster['team_name'] = owner_info['team_name']
        roster['username'] = owner_info['username']

    return render_template('league_details.html', league=league, rosters=rosters)

# Route to display roster details
@app.route('/league/<string:league_id>/roster/<int:roster_id>', methods=['GET'])
def roster_details(league_id, roster_id):
    rosters = get_league_rosters(league_id)
    users = get_league_users(league_id)

    if not rosters or not users:
        return render_template('roster_details.html', error="Roster or user data not found.")

    # Find specific roster
    roster = next((r for r in rosters if r['roster_id'] == roster_id), None)
    if not roster:
        return render_template('roster_details.html', error="Roster not found.")

    # Get owner info
    user_info = next((u for u in users if u['user_id'] == roster['owner_id']), {})
    team_name = user_info.get('metadata', {}).get('team_name', f"Roster {roster_id}")
    username = user_info.get('display_name', "Unknown User")

    # Map players to names
    starters = map_players(roster.get('starters', []))
    bench = map_players([player for player in roster.get('players', []) if player not in roster.get('starters', [])])
    taxi = map_players(roster.get('taxi', []))

    return render_template(
        'roster_details.html',
        team_name=team_name,
        username=username,
        starters=starters,
        bench=bench,
        taxi=taxi
    )

if __name__ == '__main__':
    app.run(debug=True)





