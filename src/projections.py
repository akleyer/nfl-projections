import config
import csv
from player import Player

class Projections:
    def __init__(self):
        self.projections_data = self._load_projections()

    def _load_projections(self):
        ftn_projections = self._load_ftn_projections()
        return ftn_projections

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