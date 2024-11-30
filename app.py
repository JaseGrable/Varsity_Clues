from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

BASE_URL = "https://api.sleeper.app/v1"

# Fetch user details by username
def get_user(username):
    try:
        response = requests.get(f"{BASE_URL}/user/{username}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

# Fetch leagues for a user by user_id
def get_user_leagues(user_id, sport="nfl", season="2024"):
    try:
        response = requests.get(f"{BASE_URL}/user/{user_id}/leagues/{sport}/{season}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching leagues: {e}")
        return None

# Fetch league details by league_id
def get_league_details(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching league details: {e}")
        return None

# Fetch rosters for a league by league_id
def get_league_rosters(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching rosters: {e}")
        return None

# Fetch users in a league by league_id
def get_league_users(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching users: {e}")
        return None

# Fetch traded picks for a league
def get_traded_picks(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/traded_picks")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching traded picks: {e}")
        return None

# Home page for entering Sleeper username
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        user_data = get_user(username)
        if not user_data:
            return render_template('home.html', error="User not found.")
        return redirect(url_for('leagues', user_id=user_data['user_id']))
    return render_template('home.html')

# Display leagues for the logged-in user
@app.route('/leagues/<string:user_id>', methods=['GET'])
def leagues(user_id):
    leagues = get_user_leagues(user_id)
    if not leagues:
        return render_template('leagues.html', error="No leagues found.")
    return render_template('leagues.html', leagues=leagues)

# Display league details with team and standings
@app.route('/league/<string:league_id>', methods=['GET'])
def league_details(league_id):
    league = get_league_details(league_id)
    rosters = get_league_rosters(league_id)
    users = get_league_users(league_id)

    if not rosters or not users:
        return render_template('league_details.html', error="Rosters or users not found.")

    # Map roster_id to team_name and username
    user_map = {
        user['user_id']: {
            'team_name': user['metadata'].get('team_name', f"Roster {user['user_id']}"),
            'username': user['display_name']
        }
        for user in users
    }

    for roster in rosters:
        user_info = user_map.get(roster['owner_id'], {'team_name': f"Roster {roster['roster_id']}", 'username': 'Unknown User'})
        roster['team_name'] = user_info['team_name']
        roster['username'] = user_info['username']

    return render_template('league_details.html', league=league, rosters=rosters)

# Display detailed roster information
@app.route('/league/<string:league_id>/roster/<int:roster_id>', methods=['GET'])
def roster_details(league_id, roster_id):
    rosters = get_league_rosters(league_id)
    users = get_league_users(league_id)
    traded_picks = get_traded_picks(league_id)

    if not rosters or not users:
        return render_template('roster_details.html', error="Roster or user data not found.")

    # Find the specific roster
    roster = next((r for r in rosters if r['roster_id'] == roster_id), None)
    if not roster:
        return render_template('roster_details.html', error="Roster not found.")

    # Get team and owner info
    user_info = next((u for u in users if u['user_id'] == roster['owner_id']), {})
    team_name = user_info.get('metadata', {}).get('team_name', f"Roster {roster_id}")
    username = user_info.get('display_name', "Unknown User")

    # Build draft picks list
    draft_picks = []
    for pick in traded_picks or []:
        if pick['owner_id'] == roster_id:
            original_team = next((u['metadata'].get('team_name', f"Roster {pick['roster_id']}") for u in users if u['user_id'] == pick['roster_id']), f"Roster {pick['roster_id']}")
            draft_picks.append(f"{pick['season']} Round {pick['round']} ({original_team})")

    # Add untraded picks
    for year in range(2025, 2028):
        for round_num in range(1, 5):
            if not any(int(p['season']) == year and int(p['round']) == round_num for p in traded_picks or []):
                draft_picks.append(f"{year} Round {round_num}")

    return render_template('roster_details.html', team_name=team_name, username=username, draft_picks=sorted(draft_picks))

if __name__ == '__main__':
    app.run(debug=True)

