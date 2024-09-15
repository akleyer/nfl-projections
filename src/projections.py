import config
import csv
from player import Player

import pprint as pp

class Projections:
    def __init__(self):
        self.projections_data = self._load_projections()

    def _load_projections(self):
        ftn_projections = self._load_ftn_projections()
        pp.pprint(ftn_projections)
        # quit()
        fantasy_data_projections = self._load_fantasydata_projections(ftn_projections)
        return ftn_projections

    def _load_fantasydata_projections(self, ftn_proj):
        team_data = {}
        positions = ["QB", "WR", "RB", "TE"]
        for position in positions:
            with open(f"../data/raw/projections/2024/week2/projections_{position.lower()}.csv", newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    team = row['team']
                    player_name = row['player']
                    player_position = row['pos']
                    for player in ftn_proj[team]:
                        ftn_player_name, ftn_player_pos, player_obj = player
                        if ftn_player_name == player_name:
                            player_obj.load_fd_data(row)
                        
        return

    def _load_ftn_projections(self):
        team_data = {}
        with open(config.FTN_PROJECTIONS_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                team = row['Tm']
                player_name = row['Player']
                player_position = row['Pos']
                player_obj = Player(player_name, player_position, team)
                player_obj.load_ftn_data(row)
                team_data.setdefault(team, []).append((player_name, player_position, player_obj))
        return team_data

    def get_team_projections(self, team_name):
        return self.projections_data[team_name]