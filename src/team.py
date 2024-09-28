"""
Team Module
-----------
This module defines the Team class, which represents a football team and provides methods
to calculate various offensive and defensive values based on player projections and DVOA data.
"""

from typing import Callable, Dict, Tuple

from projections import Projections

class Team:
    """Represents a football team."""

    __slots__ = ['team_name', 'dvoa', 'pff', 'team_projections', 'dave_off', 'dave_def', 'dave_st']

    def __init__(self, team_name: str, projections: Projections, dvoa: Dict, dave: Dict, pff_data: Dict):
        self.team_name = team_name
        self.dvoa = dvoa
        self.pff = pff_data
        self.team_projections = projections.get_team_projections(self.team_name)
        self.dave_off, self.dave_def, self.dave_st = self._get_dave_values(dave)

    @staticmethod
    def _create_function_dict() -> Dict[str, Callable[[float], float]]:
        """Create a dictionary of linear functions used in the projection model."""
        def create_linear_function(x1: float, y1: float, x2: float, y2: float) -> Callable[[float], float]:
            slope = (y2 - y1) / (x2 - x1)
            return lambda x: slope * x + (y1 - slope * x1)

        return {
            "Pass": create_linear_function(-.80, 0, .55, 10),
            "Rush": create_linear_function(-.20, 0, .25, 10),
            "Rec": create_linear_function(-.20, 0, .30, 10),
            "OLPF": create_linear_function(.85, 0, .25, 10),
            "OLRF": create_linear_function(22.5, 0, 35.75, 10),
            "DPF": create_linear_function(3.55, 0, -1.6, 10),
            "DRF": create_linear_function(0.85, 0, -2, 10),
            "DAVE DEF": create_linear_function(9.5, 0, -10.5, 10),
            "DAVE OFF": create_linear_function(-17, 0, 17, 10),
            "PFF Pass": create_linear_function(30,0,95,10)
        }

    def get_total_passing_value(self) -> float:
        """Calculate the total passing value based on QB, receiving, OL pass, and rushing values."""
        qb_value = self._get_passing_value()
        receiving_value = self._get_receiving_value()
        ol_pass_value = self._get_offensive_line_pass_value()
        # print(f"{self.team_name} QB Value: {round(qb_value,1)}")
        # print(f"{self.team_name} Rec Value: {round(receiving_value,1)}")
        # print(f"{self.team_name} OL Pass Value: {round(ol_pass_value,1)}")

        weights = {'qb': 0.50, 'rec': 0.30, 'ol': 0.20}
        offensive_pass_value = sum(
            value * weights[key] for key, value in {
                'qb': qb_value, 'rec': receiving_value, 'ol': ol_pass_value
            }.items()
        )

        # print(f"  O: {self.team_name} P: {round(offensive_pass_value,1)}")

        return offensive_pass_value

    def get_total_rushing_value(self) -> float:
        """Calculate the total rushing value based on rushing and OL rush values."""
        ol_rush_value = self._get_offensive_line_rush_value()
        rushing_value = self._get_rushing_value()
        # print(f"{self.team_name} Rush Value: {round(rushing_value,1)}")
        # print(f"{self.team_name} OL Rush Value: {round(ol_rush_value,1)}")
        

        weights = {'rushing': 0.60, 'ol_rush': 0.40}
        offensive_rush_value = sum(
            value * weights[key] for key, value in {
                'rushing': rushing_value, 'ol_rush': ol_rush_value
            }.items()
        )
        #print(f"  O: {self.team_name} R: {round(offensive_rush_value,1)}")
        return offensive_rush_value

    def _get_passing_value(self) -> float:
        """Calculate the passing value based on QB projections and DVOA."""
        total_passing_att = sum(
            player_data.get_proj_passing_att() for _, player_position, player_data in self.team_projections
            if player_position == "QB"
        )
        total_contribution = sum(
            player_data.get_passing_dvoa(self.dvoa) * player_data.get_proj_passing_att()
            for _, player_position, player_data in self.team_projections if player_position == "QB"
        )

        normalized_dvoa_value = self._create_function_dict()["Pass"](total_contribution / total_passing_att)
        # import pprint
        # pprint.pprint(self.pff)
        pff_passing_data = self.pff["2024"]["Passing"]

        total_pff_player_grade = 0
        total_passes = 0
        total_cont = 0
        for _, player_position, player_data in self.team_projections:
            if player_position == "QB":
                total_pff_player_grade += pff_passing_data[player_data.name][0][0]
                total_passes += pff_passing_data[player_data.name][0][1]
                total_cont = pff_passing_data[player_data.name][0][0] * pff_passing_data[player_data.name][0][1]

        pff_player_grade = self._create_function_dict()["PFF Pass"](total_cont / total_passes)
        # print(normalized_dvoa_value)
        # print(pff_player_grade)

        return (normalized_dvoa_value + pff_player_grade) / 2

    def _get_receiving_value(self) -> float:
        """Calculate the receiving value based on WR, RB, and TE projections and DVOA."""
        total_targets = sum(
            player_data.get_proj_targets() for _, player_position, player_data in self.team_projections
            if player_position in ["WR", "RB", "TE"]
        )
        total_contribution = sum(
            player_data.get_receiving_dvoa(self.dvoa) * player_data.get_proj_targets()
            for _, player_position, player_data in self.team_projections if player_position in ["WR", "RB", "TE"]
        )
        #print(f"Total REC DVOA: {round(total_contribution / total_targets,2)}")
        return self._create_function_dict()["Rec"](total_contribution / total_targets)

    def _get_offensive_line_pass_value(self) -> float:
        """Get the offensive line pass value based on DVOA."""
        _weighted_avg = (
            ((self.dvoa["2021"]["OL Pass"][self.team_name][0]) / 8) + \
            ((self.dvoa["2022"]["OL Pass"][self.team_name][0]) / 4) + \
            ((self.dvoa["2023"]["OL Pass"][self.team_name][0]) / 2) + \
            (self.dvoa["2024"]["OL Pass"][self.team_name][0])
        ) * 15 / 4
        #print(_weighted_avg)
        return self._create_function_dict()["OLPF"](_weighted_avg)

    def _get_offensive_line_rush_value(self) -> float:
        """Get the offensive line rush value based on DVOA."""
        _weighted_avg = (
            ((self.dvoa["2021"]["OL Run"][self.team_name][0]) / 8) + \
            ((self.dvoa["2022"]["OL Run"][self.team_name][0]) / 4) + \
            ((self.dvoa["2023"]["OL Run"][self.team_name][0]) / 2) + \
            (self.dvoa["2024"]["OL Run"][self.team_name][0])
        ) * 15 / 4
        #print(_weighted_avg)
        return self._create_function_dict()["OLRF"](_weighted_avg)

    def _get_rushing_value(self) -> float:
        """Calculate the rushing value based on RB and WR projections and DVOA."""
        total_attempts = sum(
            player_data.get_proj_attempts() for _, player_position, player_data in self.team_projections
            if player_position in ["QB", "WR", "RB"]
        )
        total_contribution = sum(
            player_data.get_rushing_dvoa(self.dvoa) * player_data.get_proj_attempts()
            for _, player_position, player_data in self.team_projections if player_position in ["WR", "RB"]
        )
        #print(f"Total RUSH DVOA: {round(total_contribution / total_attempts,2)}")
        return self._create_function_dict()["Rush"](total_contribution / total_attempts)

    def get_total_passing_value_def(self) -> float:
        """Get the defensive pass value with potential multiplier."""
        _weighted_avg = (
            ((self.dvoa["2021"]["Defense Pass"][self.team_name][0]) / 8) + \
            ((self.dvoa["2022"]["Defense Pass"][self.team_name][0]) / 4) + \
            ((self.dvoa["2023"]["Defense Pass"][self.team_name][0]) / 2) + \
            (self.dvoa["2024"]["Defense Pass"][self.team_name][0])
        ) * 15 / 4
        # print(_weighted_avg)
        # print(f"  D: {self.team_name} P: {round(self._create_function_dict()["DPF"](_weighted_avg),1)}")
        return self._create_function_dict()["DPF"](_weighted_avg)

    def get_total_rushing_value_def(self) -> float:
        """Get the defensive rush value with potential multiplier."""
        _weighted_avg = (
            ((self.dvoa["2021"]["Defense Rush"][self.team_name][0]) / 8) + \
            ((self.dvoa["2022"]["Defense Rush"][self.team_name][0]) / 4) + \
            ((self.dvoa["2023"]["Defense Rush"][self.team_name][0]) / 2) + \
            (self.dvoa["2024"]["Defense Rush"][self.team_name][0])
        ) * 15 / 4
        print(round(_weighted_avg,3))
        print(f"  D: {self.team_name} R: {round(self._create_function_dict()["DRF"](_weighted_avg),1)}")
        return self._create_function_dict()["DRF"](_weighted_avg)

    def get_def_dave_normalized(self) -> float:
        """Get the normalized defensive DAVE value."""
        return self._create_function_dict()["DAVE DEF"](float(self.dave_def))

    def get_off_dave_normalized(self) -> float:
        """Get the normalized offensive DAVE value."""
        return self._create_function_dict()["DAVE OFF"](float(self.dave_off))

    def _get_dave_values(self, dave_data: Dict) -> Tuple[float, float, float]:
        """Get the DAVE values for the team."""
        return dave_data[self.team_name][0]

    def get_pass_rates(self, pass_rate_data: Dict) -> Tuple[float, float]:
        """Get the pass rates for the team."""
        return pass_rate_data[self.team_name][0]