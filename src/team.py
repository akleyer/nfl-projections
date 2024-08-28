import logging
from typing import Dict, List, Tuple, Callable, Optional
from config import get_standard_team_abbr, get_dvoa_player_map

logger = logging.getLogger(__name__)

class Team:
    def __init__(self,
                 team_abbreviation: str,
                 team_data: Dict[str, List[Tuple[str, Dict]]],
                 defensive_pass_dvoa: Dict[str, float],
                 dvoa_data: Dict[str, Dict],
                 adjusted_rush_yards: Dict[str, float],
                 adjusted_sack_rate: Dict[str, float],
                 defensive_rush_dvoa: Dict[str, float],
                 play_rates: Dict[str, Dict],
                 functions: Dict[str, Callable],
                 oline_delta: Dict[str, float]
                 ):
        """
        Initialize a Team object representing an NFL team.
        """
        self.abbreviation = get_standard_team_abbr(team_abbreviation)
        self.team_data = team_data
        self.dvoa_data = dvoa_data
        self.pass_dvoa = self._get_weighted_dvoa(dvoa_data["Passing"])
        self.rb_rush_dvoa = self._get_weighted_dvoa(dvoa_data["Rushing"]["RB"])
        self.qb_rush_dvoa = self._get_weighted_dvoa(dvoa_data["Rushing"]["QB"])
        self.wr_rush_dvoa = self._get_weighted_dvoa(dvoa_data["Rushing"]["WR"])
        self.te_rec_dvoa = self._get_weighted_dvoa(dvoa_data["Receiving"]["TE"])
        self.rb_rec_dvoa = self._get_weighted_dvoa(dvoa_data["Receiving"]["RB"])
        self.wr_rec_dvoa = self._get_weighted_dvoa(dvoa_data["Receiving"]["WR"])
        self.offensive_line_pass_efficiency = adjusted_sack_rate
        self.offensive_line_rush_efficiency = adjusted_rush_yards
        self.defensive_pass_dvoa = defensive_pass_dvoa
        self.defensive_rush_dvoa = defensive_rush_dvoa
        self.play_rates = play_rates
        self.qb_function = functions["Pass"]
        self.rush_function = functions["Rush"]
        self.rec_function = functions["Rec"]
        self.ol_pass_function = functions["OLPF"]
        self.ol_rush_function = functions["OLRF"]
        self.defensive_pass_function = functions["DPF"]
        self.defensive_rush_function = functions["DRF"]
        self.oline_delta = oline_delta

    @staticmethod
    def _get_weighted_dvoa(dvoa_tmp: Dict[str, Dict[str, Tuple[float, float]]]) -> Dict[str, float]:
        """
        Calculate weighted DVOA for players based on historical data.
        """
        final_dvoa = {}
        final_dvoa_tracker = {}
        years = ["2024", "2023", "2022", "2021", "2020"]
        weight_factors = [1, 2, 4, 8, 16]

        for year, players in dvoa_tmp.items():
            for player, stats in players.items():
                mapped_player = get_dvoa_player_map(player)
                dvoa_val, num_plays = stats
                if mapped_player not in final_dvoa_tracker:
                    final_dvoa_tracker[mapped_player] = [0, 0]
                for i, target_year in enumerate(years):
                    if year == target_year:
                        weighted_dvoa = dvoa_val * (num_plays / weight_factors[i])
                        final_dvoa_tracker[mapped_player][0] += weighted_dvoa
                        final_dvoa_tracker[mapped_player][1] += (num_plays / weight_factors[i])

        for player, values in final_dvoa_tracker.items():
            mapped_player = get_dvoa_player_map(player)
            weighted_dvoa, num_plays = values
            final_dvoa[mapped_player] = weighted_dvoa / num_plays if num_plays else 0

        return final_dvoa

    def generate_qb_value(self) -> float:
        """Generate the quarterback value based on DVOA."""
        if "QB" in self.team_data and self.team_data["QB"]:
            qb_name = self.team_data["QB"][0][0]
            mapped_player = get_dvoa_player_map(qb_name)
            return self.pass_dvoa.get(mapped_player, 0.0)
        return 0.0

    def get_qb_value(self) -> float:
        """Get the quarterback value considering a threshold."""
        dvoa_tmp = self.generate_qb_value()
        qb_val = self.qb_function(dvoa_tmp)
        return max(0, qb_val) if qb_val <= -5 else qb_val

    def get_offensive_line_pass_value(self) -> float:
        """Get the offensive line pass value."""
        resting_starters = []  # Add logic for resting starters if needed
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        avg_val = (self.ol_pass_function(self.offensive_line_pass_efficiency[self.abbreviation]) + self.oline_delta[self.abbreviation]) / 2
        return avg_val * multiplier

    def get_offensive_line_rush_value(self) -> float:
        """Get the offensive line rush value."""
        resting_starters = []  # Add logic for resting starters if needed
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        avg_val = (self.ol_rush_function(self.offensive_line_rush_efficiency[self.abbreviation]) + self.oline_delta[self.abbreviation]) / 2
        return avg_val * multiplier

    def get_defensive_pass_value(self) -> float:
        """Get the defensive pass value with potential multiplier."""
        resting_starters = []  # Add logic for resting starters if needed
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0

        std_abbr = get_standard_team_abbr(self.abbreviation)
        def_pass_value = self.defensive_pass_dvoa.get(std_abbr, 0.0)

        return self.defensive_pass_function(def_pass_value) * multiplier

    def get_defensive_rush_value(self) -> float:
        """Get the defensive rush value with potential multiplier."""
        resting_starters = []  # Add logic for resting starters if needed
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0

        std_abbr = get_standard_team_abbr(self.abbreviation)
        def_rush_value = self.defensive_rush_dvoa.get(std_abbr, 0.0)

        return self.defensive_rush_function(def_rush_value) * multiplier

    def get_offensive_pass_value(self) -> float:
        """Get the offensive pass value combining various factors."""
        qb_value = self.get_qb_value()
        receiving_value = self.get_receiving_value()
        ol_pass_value = self.get_offensive_line_pass_value()
        rushing_value = self.get_rushing_value()
        return (qb_value * 0.55) + (receiving_value * 0.30) + (ol_pass_value * 0.1) + (rushing_value * 0.05)

    def get_offensive_rush_value(self) -> float:
        """Get the offensive rush value combining rushing and OL factors."""
        rushing_value = self.get_rushing_value()
        ol_rush_value = self.get_offensive_line_rush_value()
        return (rushing_value * 0.65) + (ol_rush_value * 0.35)

    def get_play_rates(self) -> Dict[str, Dict[str, float]]:
        """Get the play rates for the team."""
        return self.play_rates[self.abbreviation]

    def get_offensive_plays_per_60(self) -> float:
        """Get the offensive plays per 60 minutes."""
        return self.get_play_rates()["OFFENSE"]["PlaysPer60"]

    def get_defensive_plays_per_60(self) -> float:
        """Get the defensive plays per 60 minutes."""
        return self.get_play_rates()["DEFENSE"]["PlaysPer60"]

    def get_offensive_pass_rate(self) -> float:
        """Get the offensive pass rate."""
        return self.get_play_rates()["OFFENSE"]["PassRate"]

    def get_defensive_pass_rate(self) -> float:
        """Get the defensive pass rate."""
        return self.get_play_rates()["DEFENSE"]["PassRate"]

    def get_offensive_rush_rate(self) -> float:
        """Get the offensive rush rate."""
        return self.get_play_rates()["OFFENSE"]["RushRate"]

    def get_defensive_rush_rate(self) -> float:
        """Get the defensive rush rate."""
        return self.get_play_rates()["DEFENSE"]["RushRate"]

    def safe_float(self, value: Optional[str], default: float = 0.0) -> float:
        """Safely convert a value to float, returning a default if conversion fails."""
        if value is None or value == '':
            return default
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Could not convert '{value}' to float. Using default value {default}")
            return default

    def generate_rushing_value(self) -> float:
        """Generate the total rushing value for the team."""
        total_dvoa, total_attempts = 0, 0
        for position, dvoa_dict in [('RB', self.rb_rush_dvoa), ('WR', self.wr_rush_dvoa), ('QB', self.qb_rush_dvoa)]:
            if position in self.team_data:
                for player, data in self.team_data[position]:
                    attempts = self.safe_float(data.get('rush_att', '0'))
                    player_dvoa = dvoa_dict.get(player, 0.0)
                    total_dvoa += attempts * player_dvoa
                    total_attempts += attempts
        result = total_dvoa / total_attempts if total_attempts else 0
        return result

    def get_rushing_value(self) -> float:
        """Get the rushing value for the team."""
        total_dvoa = self.generate_rushing_value()
        return self.rush_function(total_dvoa)

    def generate_receiving_value(self) -> float:
        """Generate the total receiving value for the team."""
        total_dvoa, total_targets = 0, 0
        for position, dvoa_dict in [('RB', self.rb_rec_dvoa), ('WR', self.wr_rec_dvoa), ('TE', self.te_rec_dvoa)]:
            if position in self.team_data:
                for player, data in self.team_data[position]:
                    targets = self.safe_float(data.get('rec_tgt', '0'))
                    player_dvoa = dvoa_dict.get(player, 0.0)
                    total_dvoa += targets * player_dvoa
                    total_targets += targets
        result = total_dvoa / total_targets if total_targets else 0
        return result

    def get_receiving_value(self) -> float:
        """Get the receiving value for the team."""
        total_dvoa = self.generate_receiving_value()
        return self.rec_function(total_dvoa)

    @staticmethod
    def _calculate_total_dvoa(players: List[Tuple[str, Dict]], dvoa_dict: Dict[str, float], 
                              total_dvoa: float, total: float, att_or_targets_index: int) -> Tuple[float, float]:
        """
        Calculate the total DVOA for a group of players.
        """
        for player, data in players:
            att_or_targets = float(data[att_or_targets_index])
            player_dvoa = dvoa_dict.get(player, 0.0)
            total_dvoa += att_or_targets * player_dvoa
            total += att_or_targets
        return total_dvoa, total

    def print_lineup(self):
        """Print the team's lineup."""
        print(self.abbreviation)
        for pos, players in self.team_data.items():
            for player, data in players:
                if float(data.get('att', 0)) or float(data.get('targets', 0)):
                    print(f"{pos:<5}{player:<15}")