from flask import Blueprint, render_template
from utils.sleeper_api import get_league_rosters, get_league_users, map_players_with_points

# Define the Blueprint
rosters_bp = Blueprint("rosters", __name__, url_prefix="/rosters")

@rosters_bp.route("/<string:league_id>/roster/<int:roster_id>", methods=["GET"])
def roster_details(league_id, roster_id):
    try:
        # Fetch rosters and users
        rosters = get_league_rosters(league_id)
        users = get_league_users(league_id)

        if not rosters or not users:
            return render_template('rosters/roster_details.html', error="Roster or user data not found.")

        # Find specific roster
        roster = next((r for r in rosters if r['roster_id'] == roster_id), None)
        if not roster:
            return render_template('rosters/roster_details.html', error="Roster not found.")

        # Get owner info
        user_info = next((u for u in users if u['user_id'] == roster['owner_id']), {})
        team_name = user_info.get('metadata', {}).get('team_name', f"Roster {roster_id}")
        username = user_info.get('display_name', "Unknown User")

        # Map players to names and calculate points
        starters = map_players_with_points(roster.get('starters', []))
        bench = map_players_with_points([player for player in roster.get('players', []) if player not in roster.get('starters', [])])
        taxi = map_players_with_points(roster.get('taxi', []))

        return render_template(
            'rosters/roster_details.html',
            team_name=team_name,
            username=username,
            starters=starters,
            bench=bench,
            taxi=taxi
        )
    except Exception as e:
        return render_template('rosters/roster_details.html', error=str(e))
