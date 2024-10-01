import config
import csv
from player import Player

import pprint as pp

class Projections:
    def __init__(self):
        self.projections_data = self._load_projections()

    def _load_projections(self):
        projections = self._load_fantasydata_projections()
        #ftn_projections = self._load_ftn_projections()
        #fantasy_data_projections = self._load_fantasydata_projections(ftn_projections)
        return projections

    def _load_fantasydata_projections(self):
        team_data = {}
        positions = ["QB", "WR", "RB", "TE"]
        for position in positions:
            with open(f"../data/raw/projections/2024/week{config.WEEK_NUM}/projections_{position.lower()}.csv", newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    team = row['team']
                    player_name = row['player']
                    player_position = row['pos']
                    player_obj = Player(player_name, player_position, team)
                    player_obj.load_fd_data(row)
                    team_data.setdefault(team, []).append((player_name, player_position, player_obj))
        return team_data

    # def _load_ftn_projections(self):
    #     team_data = {}
    #     for position in ["qb","rb","wr","te"]:
    #         with open(f"../data/raw/projections/2024/week4/ftn_projections_{position}.csv", newline='', encoding='utf-8') as csvfile:
    #             reader = csv.DictReader(csvfile)
    #             for row in reader:
    #                 team = row['Team']
    #                 player_name = row['Player']
    #                 player_position = row['Position']
    #                 player_obj = Player(player_name, player_position, team)
    #                 player_obj.load_ftn_data(row)
    #                 team_data.setdefault(team, []).append((player_name, player_position, player_obj))
    #     return team_data

    def get_team_projections(self, team_name):
        return self.projections_data[team_name]