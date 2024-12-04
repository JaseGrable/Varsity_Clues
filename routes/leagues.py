from flask import Blueprint, render_template
from utils.sleeper_api import (
    get_user_leagues,
    get_league_details,
    get_league_matchups,
    get_current_week,
    get_league_rosters,
    get_league_users,
)
from utils.helpers import map_players
from utils.db import fetch_previous_league_data

# Define the Blueprint
leagues_bp = Blueprint("leagues", __name__, url_prefix="/leagues")

# Route to display leagues for a user
@leagues_bp.route("/<string:user_id>")
def leagues(user_id):
    leagues = get_user_leagues(user_id)
    if not leagues:
        return render_template("leagues/leagues.html", error="No leagues found.")
    return render_template("leagues/leagues.html", leagues=leagues)

# Route to display league details
@leagues_bp.route("/<string:league_id>/details", methods=["GET"])
def league_details(league_id):
    league = get_league_details(league_id)
    rosters = get_league_rosters(league_id)
    users = get_league_users(league_id)

    if not league or not rosters or not users:
        return render_template(
            "leagues/league_details.html",
            error="League details, rosters, or users not found.",
            rosters=[],
            matchups=[],
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
    processed_matchups = set()  # Track processed matchup IDs

    for matchup in matchups_data:
        # Get team1 and opponent_id
        team1 = next((r for r in rosters if r["roster_id"] == matchup["roster_id"]), None)
        opponent_id = matchup.get("matchup_id")
        team2 = next((r for r in rosters if r["roster_id"] == opponent_id), None)

        # Generate a unique key for the matchup
        matchup_key = frozenset([
            team1["roster_id"] if team1 else "Unknown_Team1",
            team2["roster_id"] if team2 else "Unknown_Team2"
        ])

        # Skip if this matchup has already been processed
        if matchup_key in processed_matchups:
            continue

        # Add the matchup to the processed set
        processed_matchups.add(matchup_key)

        # Append the matchup details
        matchups.append(
            {
                "team1": {
                    "name": team1["team_name"] if team1 else "Unknown Team",
                    "points": matchup.get("points", 0),
                },
                "team2": {
                    "name": team2["team_name"] if team2 else "Unknown Team",
                    "points": matchup.get("points_against", 0),  # Use correct key for opponent points
                },
            }
        )

    return render_template(
        "leagues/league_details.html",
        league=league,
        rosters=rosters,
        matchups=matchups,
        week=current_week,
    )

# Route to display league history
@leagues_bp.route("/<string:league_id>/history", methods=["GET"])
def league_history(league_id):
    league, standings = fetch_previous_league_data(league_id)
    if not league:
        return render_template(
            "leagues/league_history.html",
            error="League history not found.",
            standings=[],
            winners_bracket=[],
            losers_bracket=[],
        )
    winners_bracket = []  # Replace with actual playoff bracket logic
    losers_bracket = []  # Replace with actual playoff bracket logic
    return render_template(
        "leagues/league_history.html",
        league=league,
        standings=standings,
        winners_bracket=winners_bracket,
        losers_bracket=losers_bracket,
    )

