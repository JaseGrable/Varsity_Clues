from flask import Flask, render_template, request, redirect, url_for, session
import requests
import datetime

app = Flask(__name__)
app.secret_key = "random_string_here"

BASE_URL = "https://api.sleeper.app/v1"

# Fetch user details by username
def get_user(username):
    try:
        response = requests.get(f"{BASE_URL}/user/{username}")
        response.raise_for_status()
        return response.json()
    except:
        return None

# Fetch leagues for a user by user_id
def get_user_leagues(user_id, sport="nfl", season="2024"):
    try:
        response = requests.get(f"{BASE_URL}/user/{user_id}/leagues/{sport}/{season}")
        response.raise_for_status()
        return response.json()
    except:
        return None

# Fetch league details by league_id
def get_league_details(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}")
        response.raise_for_status()
        return response.json()
    except:
        return None

# Fetch rosters for a league by league_id
def get_league_rosters(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/rosters")
        response.raise_for_status()
        return response.json()
    except:
        return None

# Fetch users in a league by league_id
def get_league_users(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/users")
        response.raise_for_status()
        return response.json()
    except:
        return None

# Fetch traded picks for a league
def get_traded_picks(league_id):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/traded_picks")
        response.raise_for_status()
        return response.json()
    except:
        return None

# Home page for entering Sleeper username
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form['username']
        user_data = get_user(username)
        if not user_data:
            return render_template('home.html', error="User not found.")
        session['user_id'] = user_data['user_id']
        return redirect(url_for('leagues'))
    return render_template('home.html')

# Display leagues for the logged-in user
@app.route('/leagues', methods=['GET'])
def leagues():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('home'))
    leagues = get_user_leagues(user_id)
    if not leagues:
        return render_template('leagues.html', error="No leagues found.")
    return render_template('leagues.html', leagues=leagues)

# Display league details and roster links
@app.route('/league/<string:league_id>', methods=['GET'])
def league_details(league_id):
    league = get_league_details(league_id)
    if not league:
        return render_template('league_details.html', error="League details not found.")

    rosters = get_league_rosters(league_id)
    users = get_league_users(league_id)

    # Map roster_id to team_name and username
    user_map = {
        roster['roster_id']: {
            'team_name': user['metadata'].get('team_name', f"Roster {roster['roster_id']}"),
            'username': user['display_name']
        }
        for roster, user in zip(rosters, users)
    }

    for roster in rosters:
        roster['team_name'] = user_map.get(roster['roster_id'], {}).get('team_name', f"Roster {roster['roster_id']}")
        roster['username'] = user_map.get(roster['roster_id'], {}).get('username', 'Unknown User')

    return render_template('league_details.html', league=league, rosters=rosters)

# Display detailed roster information
@app.route('/league/<string:league_id>/roster/<int:roster_id>', methods=['GET'])
def roster_details(league_id, roster_id):
    rosters = get_league_rosters(league_id)
    if not rosters:
        return render_template('roster_details.html', error="Roster details not found.")

    # Find the specific roster by roster_id
    roster = next((r for r in rosters if r['roster_id'] == roster_id), None)
    if not roster:
        return render_template('roster_details.html', error="Roster not found.")

    # Get owner info (team name and username)
    users = get_league_users(league_id)
    user_map = {
        roster['roster_id']: user['metadata'].get('team_name', f"Roster {roster['roster_id']}")
        for roster, user in zip(rosters, users)
    }

    team_name = user_map.get(roster_id, f"Roster {roster_id}")

    # Fetch starters, bench, and additional details
    starters = roster.get('starters', [])
    bench = [player for player in roster.get('players', []) if player not in starters]
    taxi = roster.get('taxi', [])

    # Fetch traded picks and filter for this roster
    traded_picks = get_traded_picks(league_id)
    draft_picks = []
    if traded_picks:
        draft_picks = [
            f"{pick['season']} Round {pick['round']} ({user_map.get(pick['roster_id'], 'Roster ' + str(pick['roster_id']))})"
            for pick in traded_picks if pick['owner_id'] == roster_id
        ]

    return render_template(
        'roster_details.html',
        team_name=team_name,
        starters=starters,
        bench=bench,
        taxi=taxi,
        draft_picks=draft_picks
    )

if __name__ == '__main__':
    app.run(debug=True)
