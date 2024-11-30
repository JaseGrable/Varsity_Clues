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

# Fetch matchups for a given league and week
def get_matchups(league_id, week):
    try:
        response = requests.get(f"{BASE_URL}/league/{league_id}/matchups/{week}")
        response.raise_for_status()
        return response.json()
    except:
        return None

# Fetch current week dynamically
def get_current_week():
    current_date = datetime.datetime.now()
    start_date = datetime.datetime(2024, 9, 5)  # Example NFL season start date
    current_week = ((current_date - start_date).days // 7) + 1
    return max(current_week, 1)

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
        user['user_id']: {
            'team_name': user['metadata'].get('team_name', f"Team {user['user_id']}"),
            'username': user['display_name']
        }
        for user in users
    }

    for roster in rosters:
        user_info = user_map.get(roster['owner_id'], {'team_name': f"Team {roster['roster_id']}", 'username': 'Unknown User'})
        roster['team_name'] = user_info['team_name']
        roster['username'] = user_info['username']

    # Fetch matchups for the current week
    week = get_current_week()
    matchups = get_matchups(league_id, week)

    # Combine matchup data
    roster_map = {
        roster['roster_id']: {
            'team_name': roster['team_name'],
            'starters': roster.get('starters', []),
            'bench': [player for player in roster.get('players', []) if player not in roster.get('starters', [])],
            'record': f"{roster['settings']['wins']}-{roster['settings']['losses']}-{roster['settings']['ties']}",
            'pf': roster['settings']['fpts'] + roster['settings'].get('fpts_decimal', 0) / 100,
            'pa': roster['settings']['fpts_against'] + roster['settings'].get('fpts_against_decimal', 0) / 100
        }
        for roster in rosters
    }
    formatted_matchups = []
    if matchups:
        matchup_pairs = {}
        for team in matchups:
            matchup_id = team['matchup_id']
            if matchup_id not in matchup_pairs:
                matchup_pairs[matchup_id] = [team]
            else:
                matchup_pairs[matchup_id].append(team)

        for matchup in matchup_pairs.values():
            if len(matchup) == 2:
                team1 = roster_map.get(matchup[0]['roster_id'], {})
                team2 = roster_map.get(matchup[1]['roster_id'], {})
                formatted_matchups.append({
                    'team1': {
                        'name': team1.get('team_name'),
                        'starters': team1.get('starters'),
                        'bench': team1.get('bench'),
                        'points': matchup[0].get('points', 0)
                    },
                    'team2': {
                        'name': team2.get('team_name'),
                        'starters': team2.get('starters'),
                        'bench': team2.get('bench'),
                        'points': matchup[1].get('points', 0)
                    }
                })

    return render_template('league_details.html', league=league, rosters=rosters, matchups=formatted_matchups)

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
    user_info = next((u for u in users if u['user_id'] == roster['owner_id']), {})
    team_name = user_info.get('metadata', {}).get('team_name', f"Team {roster_id}")
    username = user_info.get('display_name', "Unknown User")

    # Fetch starters, bench, and additional details
    starters = roster.get('starters', [])
    bench = [player for player in roster.get('players', []) if player not in starters]
    taxi = roster.get('taxi', [])
    draft_picks = roster.get('draft_picks', [])
    record = f"{roster['settings']['wins']}-{roster['settings']['losses']}-{roster['settings']['ties']}"
    pf = roster['settings']['fpts'] + roster['settings'].get('fpts_decimal', 0) / 100
    pa = roster['settings']['fpts_against'] + roster['settings'].get('fpts_against_decimal', 0) / 100

    return render_template(
        'roster_details.html',
        team_name=team_name,
        username=username,
        starters=starters,
        bench=bench,
        taxi=taxi,
        draft_picks=draft_picks,
        record=record,
        pf=pf,
        pa=pa
    )

if __name__ == '__main__':
    app.run(debug=True)
