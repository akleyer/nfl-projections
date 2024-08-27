import logging
from typing import Dict, List, Tuple, Callable, Optional
from config import get_standard_team_abbr

# Set up logging
logger = logging.getLogger(__name__)

class Team:
    def __init__(self,
                 team_abbreviation: str,
                 team_data: Dict[str, List[Tuple[str, Dict]]],
                 def_pass: Dict[str, float],
                 dvoa_obj: Dict[str, Dict],
                 ary: Dict[str, float],
                 asr: Dict[str, float],
                 def_rush: Dict[str, float],
                 pr: Dict[str, Dict],
                 functions: Dict[str, Callable],
                 oline_delta: Dict[str, float]
                 ):
        """
        Initialize a Team object.

        Args:
            team_abbreviation (str): The abbreviation of the team.
            team_data (Dict[str, List[Tuple[str, Dict]]]): Data related to the team's players.
            def_pass (Dict[str, float]): Defensive passing data.
            dvoa_obj (Dict[str, Dict]): DVOA data.
            ary (Dict[str, float]): Offensive line rushing data.
            asr (Dict[str, float]): Offensive line passing data.
            def_rush (Dict[str, float]): Defensive rushing data.
            pr (Dict[str, Dict]): Play rate data.
            functions (Dict[str, Callable]): Functions for calculating values.
        """
        self.abbreviation = get_standard_team_abbr(team_abbreviation)
        self.team_data = team_data
        self.dvoa = dvoa_obj
        self.pass_dvoa = self._get_weighted_dvoa(dvoa_obj["Passing"])
        self.rb_rush_dvoa = self._get_weighted_dvoa(dvoa_obj["Rushing"]["RB"])
        self.qb_rush_dvoa = self._get_weighted_dvoa(dvoa_obj["Rushing"]["QB"])
        self.wr_rush_dvoa = self._get_weighted_dvoa(dvoa_obj["Rushing"]["WR"])
        self.te_rec_dvoa = self._get_weighted_dvoa(dvoa_obj["Receiving"]["TE"])
        self.rb_rec_dvoa = self._get_weighted_dvoa(dvoa_obj["Receiving"]["RB"])
        self.wr_rec_dvoa = self._get_weighted_dvoa(dvoa_obj["Receiving"]["WR"])
        self.ol_pass = asr
        self.ol_rush = ary
        self.def_pass = def_pass
        self.def_rush = def_rush
        self.play_rates = pr
        self.qb_func = functions["Pass"]
        self.rush_func = functions["Rush"]
        self.rec_func = functions["Rec"]
        self.ol_pass_func = functions["OLPF"]
        self.ol_rush_func = functions["OLRF"]
        self.dpf = functions["DPF"]
        self.drf = functions["DRF"]
        self.oline_delta = oline_delta

    @staticmethod
    def _get_weighted_dvoa(dvoa_tmp: Dict[str, Dict[str, Tuple[float, float]]]) -> Dict[str, float]:
        """
        Calculate weighted DVOA (Defense-adjusted Value Over Average) for players.

        Args:
            dvoa_tmp (Dict[str, Dict[str, Tuple[float, float]]]): DVOA data for players, organized by year.

        Returns:
            Dict[str, float]: Weighted DVOA values for players.
        """
        final_dvoa = {}
        final_dvoa_tracker = {}
        years = ["2024", "2023", "2022", "2021", "2020"]
        weight_factors = [1, 2, 4, 8, 16]

        for year, players in dvoa_tmp.items():
            for player, stats in players.items():
                dvoa_val, num = stats
                if player not in final_dvoa_tracker:
                    final_dvoa_tracker[player] = [0, 0]
                for i, target_year in enumerate(years):
                    if year == target_year:
                        weighted_dvoa = dvoa_val * (num / weight_factors[i])
                        final_dvoa_tracker[player][0] += weighted_dvoa
                        final_dvoa_tracker[player][1] += (num / weight_factors[i])

        for player, values in final_dvoa_tracker.items():
            weighted_dvoa, num = values
            final_dvoa[player] = weighted_dvoa / num if num else 0

        return final_dvoa

    def generate_qb_value(self) -> float:
        """Generate the quarterback value based on DVOA."""
        if "QB" in self.team_data and self.team_data["QB"]:
            qb_name = self.team_data["QB"][0][0]
            return self.pass_dvoa.get(qb_name, 0.0)
        return 0.0

    def get_qb_value(self) -> float:
        """Get the quarterback value considering a threshold."""
        dvoa_tmp = self.generate_qb_value()
        qb_val = self.qb_func(dvoa_tmp)
        return max(0, qb_val) if qb_val <= -5 else qb_val

    def get_ol_pass_value(self) -> float:
        """Get the offensive line pass value."""
        resting_starters = []  # Add logic for resting starters if needed
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        avg_val = (self.ol_pass_func(self.ol_pass[self.abbreviation]) + self.oline_delta[self.abbreviation]) / 2
        return avg_val * multiplier

    def get_ol_rush_value(self) -> float:
        """Get the offensive line rush value."""
        resting_starters = []  # Add logic for resting starters if needed
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        avg_val = (self.ol_rush_func(self.ol_rush[self.abbreviation]) + self.oline_delta[self.abbreviation]) / 2
        return avg_val * multiplier

    def get_def_pass_value(self) -> float:
        """Get the defensive pass value with potential multiplier."""
        resting_starters = []  # Add logic for resting starters if needed
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        
        std_abbr = get_standard_team_abbr(self.abbreviation)
        def_pass_value = self.def_pass.get(std_abbr, 0.0)
        
        return self.dpf(def_pass_value) * multiplier

    def get_def_rush_value(self) -> float:
        """Get the defensive rush value with potential multiplier."""
        resting_starters = []  # Add logic for resting starters if needed
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        
        std_abbr = get_standard_team_abbr(self.abbreviation)
        def_rush_value = self.def_rush.get(std_abbr, 0.0)
        
        return self.drf(def_rush_value) * multiplier


    def get_off_pass_value(self) -> float:
        """Get the offensive pass value combining various factors."""
        qb_value = self.get_qb_value()
        rec_value = self.get_rec_value()
        ol_pass_value = self.get_ol_pass_value()
        rushing_value = self.get_rushing_value()
        return (qb_value * 0.55) + (rec_value * 0.30) + (ol_pass_value * 0.1) + (rushing_value * 0.05)

    def get_off_rush_value(self) -> float:
        """Get the offensive rush value combining rushing and OL factors."""
        rushing_value = self.get_rushing_value()
        ol_rush_value = self.get_ol_rush_value()
        return (rushing_value * 0.65) + (ol_rush_value * 0.35)

    def get_play_rates(self) -> Dict[str, Dict[str, float]]:
        """Get the play rates for the team."""
        return self.play_rates[self.abbreviation]

    def get_off_plays_per_60(self) -> float:
        """Get the offensive plays per 60 minutes."""
        return self.get_play_rates()["OFF"]["PlayPer60"]

    def get_def_plays_per_60(self) -> float:
        """Get the defensive plays per 60 minutes."""
        return self.get_play_rates()["DEF"]["PlayPer60"]

    def get_off_pass_rate(self) -> float:
        """Get the offensive pass rate."""
        return self.get_play_rates()["OFF"]["PassRate"]

    def get_def_pass_rate(self) -> float:
        """Get the defensive pass rate."""
        return self.get_play_rates()["DEF"]["PassRate"]

    def get_off_rush_rate(self) -> float:
        """Get the offensive rush rate."""
        return self.get_play_rates()["OFF"]["RushRate"]

    def get_def_rush_rate(self) -> float:
        """Get the defensive rush rate."""
        return self.get_play_rates()["DEF"]["RushRate"]

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
        return self.rush_func(total_dvoa)

    def generate_rec_value(self) -> float:
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

    def get_rec_value(self) -> float:
        """Get the receiving value for the team."""
        total_dvoa = self.generate_rec_value()
        return self.rec_func(total_dvoa)

    @staticmethod
    def _calculate_total_dvoa(players: List[Tuple[str, Dict]], dvoa_dict: Dict[str, float], 
                              total_dvoa: float, total: float, att_or_targets_index: int) -> Tuple[float, float]:
        """
        Calculate the total DVOA for a group of players.

        Args:
            players (List[Tuple[str, Dict]]): List of player data.
            dvoa_dict (Dict[str, float]): DVOA values for players.
            total_dvoa (float): Running total of DVOA values.
            total (float): Running total of attempts or targets.
            att_or_targets_index (int): Index of attempts or targets in player data.

        Returns:
            Tuple[float, float]: Updated total DVOA and total attempts/targets.
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