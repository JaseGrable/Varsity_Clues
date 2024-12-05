from flask import Blueprint, render_template
from utils.sleeper_api import (
    get_user_leagues,
    get_league_details,
    get_league_matchups,
    get_current_week,
    get_league_rosters,
    get_league_users,
    get_user_league_history,
)
from utils.helpers import map_players

# Define the Blueprint
leagues_bp = Blueprint("leagues", __name__, url_prefix="/leagues")

# Route to display leagues for a user
@leagues_bp.route("/<string:user_id>")
def leagues(user_id):
    leagues = get_user_leagues(user_id)
    if not leagues:
        return render_template("leagues/leagues.html", error="No leagues found.")
    return render_template("leagues/leagues.html", leagues=leagues, user_id=user_id)

# Route to display league details
@leagues_bp.route("/<string:user_id>/details/<string:league_id>", methods=["GET"])
def league_details(user_id, league_id):
    league = get_league_details(league_id)
    rosters = get_league_rosters(league_id)
    users = get_league_users(league_id)

    if not league or not rosters or not users:
        return render_template(
            "leagues/league_details.html",
            error="League details, rosters, or users not found.",
            rosters=[],
            matchups=[],
            user_id=user_id,
        )

    # Map user IDs to team names and usernames
    user_map = {
        user["user_id"]: {
            "team_name": user["metadata"].get("team_name", f"Roster {user['user_id']}"),
            "username": user["display_name"],
        }
        for user in users
    }

    # Add team details to rosters and calculate rankings
    for roster in rosters:
        owner_info = user_map.get(
            roster["owner_id"],
            {"team_name": f"Roster {roster['roster_id']}", "username": "Unknown User"},
        )
        roster["team_name"] = owner_info["team_name"]
        roster["username"] = owner_info["username"]

    # Sort rosters for standings: by wins, then PF (descending order)
    rosters = sorted(rosters, key=lambda r: (-r["settings"]["wins"], -r["settings"]["fpts"]))

    # Assign rank to each roster
    for index, roster in enumerate(rosters, start=1):
        roster["rank"] = index

    # Fetch current matchups
    current_week = get_current_week()
    matchups_data = get_league_matchups(league_id, current_week)

    # Process matchups
    matchups = []
    processed_matchup_ids = set()

    for matchup in matchups_data:
        team1 = next((r for r in rosters if r["roster_id"] == matchup["roster_id"]), None)
        matchup_id = matchup.get("matchup_id")

        if matchup_id in processed_matchup_ids:
            continue

        team2_matchup = next((m for m in matchups_data if m["matchup_id"] == matchup_id and m["roster_id"] != matchup["roster_id"]), None)
        team2 = next((r for r in rosters if r["roster_id"] == team2_matchup["roster_id"]), None) if team2_matchup else None

        processed_matchup_ids.add(matchup_id)

        matchups.append(
            {
                "team1": {"name": team1["team_name"] if team1 else "Unknown Team", "points": matchup.get("points", 0)},
                "team2": {"name": team2["team_name"] if team2 else "Unknown Team", "points": team2_matchup.get("points", 0) if team2_matchup else 0},
            }
        )

    return render_template(
        "leagues/league_details.html",
        league=league,
        rosters=rosters,
        matchups=matchups,
        week=current_week,
        user_id=user_id,
    )

@leagues_bp.route("/<string:user_id>/history", methods=["GET"])
def league_history(user_id):
    history = get_user_league_history(user_id)
    current_league = get_user_leagues(user_id)  # Fetch the current league details
    
    if not history:
        return render_template(
            "leagues/league_history.html",
            error="No historical leagues found.",
            history=[],
            user_id=user_id,
            current_league_id=None,
        )

    # Extract the most recent league ID for the "Back to Current Season" link
    current_league_id = current_league[0]['league_id'] if current_league else None

    # Sort history by year, descending
    sorted_history = sorted(history.items(), key=lambda x: x[0], reverse=True)

    return render_template(
        "leagues/league_history.html",
        history=sorted_history,
        user_id=user_id,
        current_league_id=current_league_id,
    )