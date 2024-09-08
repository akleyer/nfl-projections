import pprint as pp
import config
import csv
from player import Player

class Projections:
    def __init__(self):
        self.projections_data = self._load_projections()

    def _load_projections(self):
        team_projections = {}
        #fantasydata_projections = self._load_fantasydata_projections()
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

    # def _load_fantasydata_projections(self):
    #     team_projections = {}
    #     for pos in config.POSITIONS:
    #         proj_data = self._load_fantasydata_pos_projections(pos)
    #         for team, players in proj_data.items():
    #             if team not in team_projections:
    #                 team_projections[team] = {}
    #             team_projections[team][pos] = players
    #     return team_projections

    # def _load_fantasydata_pos_projections(self, position):
    #     team_data = {}
    #     file_path = getattr(config, f"{position}_PROJECTIONS_FILE")
    #     with open(file_path, newline='', encoding='utf-8') as csvfile:
    #         reader = csv.DictReader(csvfile)
    #         for row in reader:
    #             team = row['team']
    #             player = row['player']
    #             team_data.setdefault(team, []).append((player, row))
    #     return team_data

    def get_team_projections(self, team_name):
        return self.projections_data[team_name]