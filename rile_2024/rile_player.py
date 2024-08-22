import numpy as np

class NFLPlayerProjector:
    def __init__(self):
        self.positions = ['QB', 'RB', 'WR', 'TE', 'OL', 'DL', 'LB', 'DB', 'K']
        self.stats = {
            'QB': ['pass_attempts', 'pass_completions', 'pass_yards', 'pass_tds', 'interceptions', 'rush_attempts', 'rush_yards', 'rush_tds'],
            'RB': ['rush_attempts', 'rush_yards', 'rush_tds', 'targets', 'receptions', 'rec_yards', 'rec_tds'],
            'WR': ['targets', 'receptions', 'rec_yards', 'rec_tds'],
            'TE': ['targets', 'receptions', 'rec_yards', 'rec_tds'],
            'OL': ['pass_block_win_rate', 'run_block_win_rate'],
            'DL': ['sacks', 'tackles_for_loss', 'qb_pressures'],
            'LB': ['tackles', 'sacks', 'interceptions', 'passes_defended'],
            'DB': ['interceptions', 'passes_defended', 'tackles'],
            'K': ['fg_attempts', 'fg_made', 'fg_percentage', 'xp_attempts', 'xp_made', 'xp_percentage']
        }

    def project_player(self, name, position, past_3_years_stats, projected_snaps):
        if position not in self.positions:
            raise ValueError(f"Invalid position: {position}")
        
        # Calculate weighted average of past 3 years (most recent year weighted highest)
        weights = [0.5, 0.3, 0.2]
        projected_stats = {}
        
        for stat in self.stats[position]:
            if stat in past_3_years_stats:
                weighted_avg = sum(w * s for w, s in zip(weights, past_3_years_stats[stat]))
                projected_stats[stat] = weighted_avg * (projected_snaps / 1000)  # Adjust for projected snaps
        
        return projected_stats

class NFLTeamProjector:
    def __init__(self):
        self.player_projector = NFLPlayerProjector()

    def project_team_stats(self, roster):
        team_stats = {
            'qb_rating': 0,
            'qb_epa_per_play': 0,
            'rb_ypc': 0,
            'rec_ypr': 0,
            'ol_pbwr': 0,
            'ol_rbwr': 0,
            'third_down_rate': 0,
            'rz_efficiency': 0,
            'pace_of_play': 0,
            'kicker_accuracy': 0,
            'def_dvoa': 0,
            'def_pressure_rate': 0,
            'def_coverage_rating': 0
        }

        total_pass_attempts = sum(player['projected_stats'].get('pass_attempts', 0) for player in roster if player['position'] == 'QB')
        total_rush_attempts = sum(player['projected_stats'].get('rush_attempts', 0) for player in roster if player['position'] in ['QB', 'RB'])
        total_targets = sum(player['projected_stats'].get('targets', 0) for player in roster if player['position'] in ['WR', 'RB', 'TE'])

        # Calculate QB rating and EPA
        qb_stats = [player for player in roster if player['position'] == 'QB']
        if qb_stats:
            completions = sum(qb['projected_stats'].get('pass_completions', 0) for qb in qb_stats)
            pass_yards = sum(qb['projected_stats'].get('pass_yards', 0) for qb in qb_stats)
            pass_tds = sum(qb['projected_stats'].get('pass_tds', 0) for qb in qb_stats)
            interceptions = sum(qb['projected_stats'].get('interceptions', 0) for qb in qb_stats)
            
            team_stats['qb_rating'] = self.calculate_passer_rating(completions, total_pass_attempts, pass_yards, pass_tds, interceptions)
            team_stats['qb_epa_per_play'] = self.estimate_epa_per_play(pass_yards, pass_tds, interceptions, total_pass_attempts)

        # Calculate RB yards per carry
        total_rush_yards = sum(player['projected_stats'].get('rush_yards', 0) for player in roster if player['position'] in ['QB', 'RB'])
        team_stats['rb_ypc'] = total_rush_yards / total_rush_attempts if total_rush_attempts > 0 else 0

        # Calculate receiver yards per reception
        total_rec_yards = sum(player['projected_stats'].get('rec_yards', 0) for player in roster if player['position'] in ['WR', 'RB', 'TE'])
        total_receptions = sum(player['projected_stats'].get('receptions', 0) for player in roster if player['position'] in ['WR', 'RB', 'TE'])
        team_stats['rec_ypr'] = total_rec_yards / total_receptions if total_receptions > 0 else 0

        # Calculate OL stats
        ol_stats = [player for player in roster if player['position'] == 'OL']
        if ol_stats:
            team_stats['ol_pbwr'] = np.mean([ol['projected_stats'].get('pass_block_win_rate', 0) for ol in ol_stats])
            team_stats['ol_rbwr'] = np.mean([ol['projected_stats'].get('run_block_win_rate', 0) for ol in ol_stats])

        # Calculate defensive stats
        dl_stats = [player for player in roster if player['position'] == 'DL']
        lb_stats = [player for player in roster if player['position'] == 'LB']
        db_stats = [player for player in roster if player['position'] == 'DB']

        if dl_stats and lb_stats and db_stats:
            total_sacks = sum(player['projected_stats'].get('sacks', 0) for player in dl_stats + lb_stats)
            total_pressures = sum(player['projected_stats'].get('qb_pressures', 0) for player in dl_stats)
            total_passes_defended = sum(player['projected_stats'].get('passes_defended', 0) for player in lb_stats + db_stats)
            total_interceptions = sum(player['projected_stats'].get('interceptions', 0) for player in lb_stats + db_stats)

            team_stats['def_pressure_rate'] = (total_sacks + total_pressures) / total_pass_attempts if total_pass_attempts > 0 else 0
            team_stats['def_coverage_rating'] = (total_passes_defended + total_interceptions * 2) / total_pass_attempts if total_pass_attempts > 0 else 0

        # Calculate kicker accuracy
        kicker_stats = [player for player in roster if player['position'] == 'K']
        if kicker_stats:
            fg_made = sum(k['projected_stats'].get('fg_made', 0) for k in kicker_stats)
            fg_attempts = sum(k['projected_stats'].get('fg_attempts', 0) for k in kicker_stats)
            xp_made = sum(k['projected_stats'].get('xp_made', 0) for k in kicker_stats)
            xp_attempts = sum(k['projected_stats'].get('xp_attempts', 0) for k in kicker_stats)
            
            team_stats['kicker_accuracy'] = (fg_made + xp_made) / (fg_attempts + xp_attempts) if (fg_attempts + xp_attempts) > 0 else 0

        # Placeholder for more complex stats (would require more detailed play-by-play data)
        team_stats['third_down_rate'] = 40  # League average placeholder
        team_stats['rz_efficiency'] = 55  # League average placeholder
        team_stats['pace_of_play'] = 28  # League average placeholder
        team_stats['def_dvoa'] = 0  # League average placeholder

        return team_stats

    def calculate_passer_rating(self, completions, attempts, yards, tds, ints):
        a = (completions / attempts - 0.3) * 5
        b = (yards / attempts - 3) * 0.25
        c = (tds / attempts) * 20
        d = 2.375 - (ints / attempts * 25)
        return ((a + b + c + d) / 6) * 100

    def estimate_epa_per_play(self, yards, tds, ints, attempts):
        # This is a simplified estimation and would need to be refined with actual EPA data
        return (yards * 0.05 + tds * 4 - ints * 5) / attempts if attempts > 0 else 0

# Example usage
player_projector = NFLPlayerProjector()
team_projector = NFLTeamProjector()

# Example player projection
patrick_mahomes_stats = {
    'pass_attempts': [600, 580, 550],
    'pass_completions': [400, 385, 360],
    'pass_yards': [5000, 4800, 4500],
    'pass_tds': [40, 38, 35],
    'interceptions': [10, 12, 15],
    'rush_attempts': [60, 55, 50],
    'rush_yards': [300, 280, 250],
    'rush_tds': [3, 2, 2]
}

mahomes_projection = player_projector.project_player("Patrick Mahomes", "QB", patrick_mahomes_stats, 1000)

# Example team projection
chiefs_roster = [
    {'name': "Patrick Mahomes", 'position': "QB", 'projected_stats': mahomes_projection},
    # Add more players here...
]

chiefs_team_stats = team_projector.project_team_stats(chiefs_roster)
print(chiefs_team_stats)