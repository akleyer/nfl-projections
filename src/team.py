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

    __slots__ = ['team_name', 'dvoa', 'team_projections', 'dave_off', 'dave_def', 'dave_st']

    def __init__(self, team_name: str, projections: Projections, dvoa: Dict, dave: Dict):
        self.team_name = team_name
        self.dvoa = dvoa
        self.team_projections = projections.get_team_projections(self.team_name)
        self.dave_off, self.dave_def, self.dave_st = self._get_dave_values(dave)

    @staticmethod
    def _create_function_dict() -> Dict[str, Callable[[float], float]]:
        """Create a dictionary of linear functions used in the projection model."""
        def create_linear_function(x1: float, y1: float, x2: float, y2: float) -> Callable[[float], float]:
            slope = (y2 - y1) / (x2 - x1)
            return lambda x: slope * x + (y1 - slope * x1)

        return {
            "Pass": create_linear_function(-.60, 0, .40, 10),
            "Rush": create_linear_function(-.10, 0, .20, 10),
            "Rec": create_linear_function(-.15, 0, .30, 10),
            "OLPF": create_linear_function(.15, 0, .04, 10),
            "OLRF": create_linear_function(3.3, 0, 4.75, 10),
            "DPF": create_linear_function(.35, 0, -.30, 10),
            "DRF": create_linear_function(.07, 0, -.30, 10),
            "DAVE DEF": create_linear_function(9, 0, -9, 10),
            "DAVE OFF": create_linear_function(-17, 0, 17, 10)
        }

    def get_total_passing_value(self) -> float:
        """Calculate the total passing value based on QB, receiving, OL pass, and rushing values."""
        qb_value = self._get_passing_value()
        receiving_value = self._get_receiving_value()
        ol_pass_value = self._get_offensive_line_pass_value()
        rushing_value = self._get_rushing_value()

        weights = {'qb': 0.50, 'rec': 0.30, 'ol': 0.15, 'rush': 0.05}
        offensive_pass_value = sum(
            value * weights[key] for key, value in {
                'qb': qb_value, 'rec': receiving_value, 'ol': ol_pass_value, 'rush': rushing_value
            }.items()
        )

        return offensive_pass_value

    def get_total_rushing_value(self) -> float:
        """Calculate the total rushing value based on rushing and OL rush values."""
        ol_rush_value = self._get_offensive_line_rush_value()
        rushing_value = self._get_rushing_value()

        weights = {'rushing': 0.65, 'ol_rush': 0.35}
        offensive_rush_value = sum(
            value * weights[key] for key, value in {
                'rushing': rushing_value, 'ol_rush': ol_rush_value
            }.items()
        )

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
        return self._create_function_dict()["Pass"](total_contribution / total_passing_att)

    def get_total_passing_value_def(self) -> float:
        """Get the defensive pass value with potential multiplier."""
        return self._create_function_dict()["DPF"](self.dvoa["2023"]["Defense Pass"][self.team_name][0])

    def get_total_rushing_value_def(self) -> float:
        """Get the defensive rush value with potential multiplier."""
        return self._create_function_dict()["DRF"](self.dvoa["2023"]["Defense Pass"][self.team_name][0])


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
        return self._create_function_dict()["Rec"](total_contribution / total_targets)

    def _get_offensive_line_pass_value(self) -> float:
        """Get the offensive line pass value based on DVOA."""
        return self._create_function_dict()["OLPF"](self.dvoa["2023"]["OL Pass"][self.team_name][0])

    def _get_offensive_line_rush_value(self) -> float:
        """Get the offensive line rush value based on DVOA."""
        return self._create_function_dict()["OLRF"](self.dvoa["2023"]["OL Run"][self.team_name][0])

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
        return self._create_function_dict()["Rush"](total_contribution / total_attempts)

    def get_total_passing_value_def(self) -> float:
        """Get the defensive pass value with potential multiplier."""
        return self._create_function_dict()["DPF"](self.dvoa["2023"]["Defense Pass"][self.team_name][0])

    def get_total_rushing_value_def(self) -> float:
        """Get the defensive rush value with potential multiplier."""
        return self._create_function_dict()["DRF"](self.dvoa["2023"]["Defense Pass"][self.team_name][0])

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