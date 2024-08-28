from typing import List, Dict, Tuple

def project_season_records(matchups: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    Project season records for all teams based on game-by-game win probabilities.

    Args:
        matchups (List[Dict]): List of dictionaries containing matchup data including
                               'home', 'away', 'week', and 'home_win_pct'.

    Returns:
        Dict[str, Dict[str, float]]: Projected records for each team after each week.
            Format: {team: {week: {'wins': projected_wins, 'losses': projected_losses}}}
    """
    teams = set()
    for matchup in matchups:
        teams.add(matchup['home'])
        teams.add(matchup['away'])

    records = {team: {0: {'wins': 0, 'losses': 0}} for team in teams}

    for matchup in matchups:
        week = int(matchup['week'])
        home_team = matchup['home']
        away_team = matchup['away']
        home_win_prob = matchup['home_win_pct'] / 100  # Assuming home_win_pct is given as a percentage

        # Update home team record
        prev_home_record = records[home_team][week - 1]
        records[home_team][week] = {
            'wins': prev_home_record['wins'] + home_win_prob,
            'losses': prev_home_record['losses'] + (1 - home_win_prob)
        }

        # Update away team record
        prev_away_record = records[away_team][week - 1]
        records[away_team][week] = {
            'wins': prev_away_record['wins'] + (1 - home_win_prob),
            'losses': prev_away_record['losses'] + home_win_prob
        }

        # Fill in records for teams not playing this week
        for team in teams:
            if team not in [home_team, away_team]:
                records[team][week] = records[team][week - 1].copy()

    return records

def print_season_projection(records: Dict[str, Dict[str, Dict[str, float]]]):
    """
    Print the season projection in a readable format.

    Args:
        records (Dict[str, Dict[str, Dict[str, float]]]): Projected records for each team after each week.
    """
    teams = list(records.keys())
    weeks = max(max(team_records.keys()) for team_records in records.values())

    print(f"{'Team':<5} {'Final Record':<15} {'Week-by-Week Projection'}")
    print("-" * 80)

    for team in sorted(teams):
        final_week = max(records[team].keys())
        final_record = records[team][final_week]
        final_wins = final_record['wins']
        final_losses = final_record['losses']
        
        week_by_week = " ".join(f"{records[team][week]['wins']:.1f}-{records[team][week]['losses']:.1f}" for week in range(1, weeks + 1))
        
        print(f"{team:<5} {final_wins:.1f}-{final_losses:.1f} {'':8} {week_by_week}")

def run_season_projection(matchups: List[Dict]):
    """
    Run the season projection based on the provided matchups.

    Args:
        matchups (List[Dict]): List of dictionaries containing matchup data including
                               'home', 'away', 'week', and 'home_win_pct'.
    """
    season_records = project_season_records(matchups)
    print_season_projection(season_records)

# Example usage:
if __name__ == "__main__":
    example_matchups = [
        {'home': 'BAL', 'away': 'CLE', 'week': '1', 'home_win_pct': 70},
        {'home': 'PIT', 'away': 'BAL', 'week': '2', 'home_win_pct': 40},
        # ... add more matchups for the entire season
    ]
    run_season_projection(example_matchups)