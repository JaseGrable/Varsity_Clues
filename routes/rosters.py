from flask import Blueprint, render_template
from utils.sleeper_api import get_league_rosters, get_league_users
from utils.helpers import map_players

# Define the Blueprint
rosters_bp = Blueprint("rosters", __name__, url_prefix="/rosters")


# Route to display roster details
@rosters_bp.route("/<string:league_id>/roster/<int:roster_id>", methods=["GET"])
def roster_details(league_id, roster_id):
    rosters = get_league_rosters(league_id)
    users = get_league_users(league_id)

    if not rosters or not users:
        return render_template(
            "rosters/roster_details.html", error="Roster or user data not found."
        )

    # Find specific roster
    roster = next((r for r in rosters if r["roster_id"] == roster_id), None)
    if not roster:
        return render_template(
            "rosters/roster_details.html", error="Roster not found."
        )

    # Get owner info
    user_info = next((u for u in users if u["user_id"] == roster["owner_id"]), {})
    team_name = user_info.get("metadata", {}).get("team_name", f"Roster {roster_id}")
    username = user_info.get("display_name", "Unknown User")

    # Map players to names
    starters = map_players(roster.get("starters", []))
    bench = map_players(
        [player for player in roster.get("players", []) if player not in roster.get("starters", [])]
    )
    taxi = map_players(roster.get("taxi", []))
    draft_picks = roster.get("draft_picks", [])

    return render_template(
        "rosters/roster_details.html",
        team_name=team_name,
        username=username,
        starters=starters,
        bench=bench,
        taxi=taxi,
        draft_picks=draft_picks,
    )
