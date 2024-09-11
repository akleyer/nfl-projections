import config
import utils

class Player:
    def __init__(self, name, pos, team):
        self.name = name
        self.position = pos
        self.team = team
        self.yearly_weights = {
            "2024" : 1,
            "2023" : 2,
            "2022" : 4,
            "2021" : 8
        }

    def get_passing_dvoa(self, dvoa):
        total_pass_attempts = 0
        total_contribution = 0
        for year in config.YEARS:
            yearly_passing_dvoa = dvoa[year]["Passing"]
            try:
                player_dvoa, player_pass_attempts = yearly_passing_dvoa[self.name][0]
            except KeyError:
                player_dvoa, player_pass_attempts = (0, 1)
            weighted_pass_attempts = player_pass_attempts / self.yearly_weights[year]
            yearly_contribution = player_dvoa * weighted_pass_attempts
            total_pass_attempts += weighted_pass_attempts
            total_contribution += yearly_contribution
        return total_contribution / total_pass_attempts

    def get_receiving_dvoa(self, dvoa):
        total_targets = 0
        total_contribution = 0
        for year in config.YEARS:
            yearly_receiving_dvoa = dvoa[year]["Receiving"]
            try:
                player_dvoa, player_targets = yearly_receiving_dvoa[self.name][0]
            except KeyError:
                player_dvoa = 0
                player_targets = 0
            weighted_targets = player_targets / self.yearly_weights[year]
            yearly_contribution = player_dvoa * weighted_targets
            total_targets += weighted_targets
            total_contribution += yearly_contribution
        try:
            return total_contribution / total_targets
        except ZeroDivisionError:
            return 0

    def get_rushing_dvoa(self, dvoa):
        total_attempts = 0
        total_contribution = 0
        for year in config.YEARS:
            yearly_rushing_dvoa = dvoa[year]["Rushing"]
            try:
                player_dvoa, player_attempts = yearly_rushing_dvoa[self.name][0]
            except KeyError:
                player_dvoa = 0
                player_attempts = 0
            weighted_attempts = player_attempts / self.yearly_weights[year]
            yearly_contribution = player_dvoa * weighted_attempts
            total_attempts += weighted_attempts
            total_contribution += yearly_contribution
        try:
            return total_contribution / total_attempts
        except ZeroDivisionError:
            return 0

    def get_proj_passing_att(self):
        return self.projections["PassAtt"]

    def get_proj_targets(self):
        return self.projections["Targets"]

    def get_proj_attempts(self):
        return self.projections["RushAtt"]

    def load_ftn_data(self, player_data):
        self.projections = {
            "PassAtt" : utils.safe_float(player_data['PaAtt']),
            "PassComp" : utils.safe_float(player_data['PaCom']),
            "PassTDs" : utils.safe_float(player_data['PaTDs']),
            "PassYds" : utils.safe_float(player_data['PaYds']),
            "PassInt" : utils.safe_float(player_data['INT']),
            "RushAtt" : utils.safe_float(player_data['RuAtt']),
            "RushYds" : utils.safe_float(player_data['RuYds']),
            "RushTDs" : utils.safe_float(player_data['RuTDs']),
            "Targets" : utils.safe_float(player_data['Tar']),
            "Receptions" : utils.safe_float(player_data['Rec']),
            "RecYards" : utils.safe_float(player_data['ReYds']),
            "RecTDs" : utils.safe_float(player_data['ReTDs']),
            "Fumbles" : utils.safe_float(player_data['Fum']),
        }