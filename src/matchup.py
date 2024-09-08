"""
Matchup Module
--------------
This module defines the Matchup class, which represents a matchup between two teams.
It provides methods to calculate projected points and win percentages based on various factors.
"""

import csv
import logging
from typing import Dict, List, Tuple
import pandas as pd
from colorama import Fore, Back, Style, init

from team import Team
from weather import WeatherConditions

import config

logger = logging.getLogger(__name__)


class Matchup:
    """Represents a matchup between two teams."""

    __slots__ = [
        'dvoa', 'home_team', 'away_team', 'field_type', 'dome', 'weather_temp',
        'weather_wind', 'weather_rain', 'betting_data', 'pass_rates_data',
        'weather_obj', 'home_adv'
    ]

    def __init__(self, matchup_json_data: Dict, projections: object,
                 dvoa: Dict, dave: Dict, pass_rates: Dict):
        self.dvoa = dvoa
        self.home_team = Team(matchup_json_data['home'], projections, dvoa, dave)
        self.away_team = Team(matchup_json_data['away'], projections, dvoa, dave)
        self.field_type = matchup_json_data['field']
        self.dome = matchup_json_data['dome']
        self.weather_temp = matchup_json_data['temp']
        self.weather_wind = matchup_json_data['wind']
        self.weather_rain = matchup_json_data['weather']
        self.betting_data = matchup_json_data['betting_lines']
        self.pass_rates_data = pass_rates
        if self.dome == "yes":
            self.weather_temp = 72.5
            self.weather_rain = 0
            self.weather_wind = 0
        self.weather_obj = WeatherConditions(self.weather_temp,
                                             self.weather_wind,
                                             self.weather_rain)
        self.home_adv = self._load_home_field_advantage()

    def _load_home_field_advantage(self) -> Dict[str, List[str]]:
        """Load home field advantage data from a CSV file."""
        team_data = {}
        with open(config.HOME_ADV_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                team = row['Team']
                home_adv = row['Adv']
                team_data.setdefault(team, []).append(home_adv)
        return team_data

    def project_outcome(self) -> Tuple[float, float]:
        """Project the outcome of the matchup."""
        home_team_points, away_team_points = self._calculate_projected_points()
        return home_team_points, away_team_points

    def _calculate_projected_points(self) -> Tuple[float, float]:
        """Calculate projected points for home and away teams."""
        # Set home team values
        home_pass_offensive_value = self.home_team.get_total_passing_value()
        home_rush_offensive_value = self.home_team.get_total_rushing_value()
        home_pass_defensive_value = self.home_team.get_total_passing_value_def()
        home_rush_defensive_value = self.home_team.get_total_rushing_value_def()

        # Set away team values
        away_pass_offensive_value = self.away_team.get_total_passing_value()
        away_rush_offensive_value = self.away_team.get_total_rushing_value()
        away_pass_defensive_value = self.away_team.get_total_passing_value_def()
        away_rush_defensive_value = self.away_team.get_total_rushing_value_def()

        # Set DAVE values
        home_dave_def_val = self.home_team.get_def_dave_normalized()
        away_dave_def_val = self.away_team.get_def_dave_normalized()
        home_dave_off_val = self.home_team.get_off_dave_normalized()
        away_dave_off_val = self.away_team.get_off_dave_normalized()

        # Adjust defensive values using DAVE
        home_pass_defensive_value = (home_pass_defensive_value +
                                     home_dave_def_val) / 2
        home_rush_defensive_value = (home_rush_defensive_value +
                                     home_dave_def_val) / 2
        away_pass_defensive_value = (away_pass_defensive_value +
                                     away_dave_def_val) / 2
        away_rush_defensive_value = (away_rush_defensive_value +
                                     away_dave_def_val) / 2

        # Adjust offensive values using DAVE
        home_pass_offensive_value = (home_pass_offensive_value +
                                     home_dave_off_val) / 2
        home_rush_offensive_value = (home_rush_offensive_value +
                                     home_dave_off_val) / 2
        away_pass_offensive_value = (away_pass_offensive_value +
                                     away_dave_off_val) / 2
        away_rush_offensive_value = (away_rush_offensive_value +
                                     away_dave_off_val) / 2

        # Define adjusted play rates
        home_pass_rate_offense, home_pass_rate_defense = self.home_team.get_pass_rates(
            self.pass_rates_data)
        away_pass_rate_offense, away_pass_rate_defense = self.away_team.get_pass_rates(
            self.pass_rates_data)

        home_pass_rate_adjusted = (home_pass_rate_offense +
                                   away_pass_rate_defense) / 2
        away_pass_rate_adjusted = (away_pass_rate_offense +
                                   home_pass_rate_defense) / 2

        home_rush_rate_adjusted = 100 - home_pass_rate_adjusted
        away_rush_rate_adjusted = 100 - away_pass_rate_adjusted

        # Adjust offensive values based on defensive values
        home_pass_offensive_value_adjusted = (home_pass_offensive_value -
                                              away_pass_defensive_value)
        home_rush_offensive_value_adjusted = (home_rush_offensive_value -
                                              away_rush_defensive_value)
        away_pass_offensive_value_adjusted = (away_pass_offensive_value -
                                              home_pass_defensive_value)
        away_rush_offensive_value_adjusted = (away_rush_offensive_value -
                                              home_rush_defensive_value)

        # Adjust home pass offensive value based on precipitation
        home_pass_offensive_value_adjusted -= self.weather_obj.calculate_precipitation_impact(
        )

        # Calculate offensive values
        home_offensive_value = (
            home_pass_offensive_value_adjusted * home_pass_rate_adjusted / 100 +
            home_rush_offensive_value_adjusted * home_rush_rate_adjusted / 100)
        away_offensive_value = (
            away_pass_offensive_value_adjusted * away_pass_rate_adjusted / 100 +
            away_rush_offensive_value_adjusted * away_rush_rate_adjusted / 100)

        # Calculate projected points based on field type
        if self.field_type == "grass":
            home_projected_points = self._calculate_points_grass(
                home_offensive_value)
            away_projected_points = self._calculate_points_grass(
                away_offensive_value)
        elif self.field_type == "turf":
            home_projected_points = self._calculate_points_turf(
                home_offensive_value)
            away_projected_points = self._calculate_points_turf(
                away_offensive_value)

        # Adjust projected points based on home field advantage
        home_projected_points += float(
            self.home_adv[self.home_team.team_name][0]) / 2
        away_projected_points -= float(
            self.home_adv[self.away_team.team_name][0]) / 2

        # Pretty output
        self._print_game_header()
        self._print_game_details()
        self._print_starting_lineups()
        self._print_projected_scores(home_projected_points, away_projected_points)
        self._print_win_percentages(home_projected_points, away_projected_points)
        self._print_betting_info(home_projected_points, away_projected_points)

        return home_projected_points, away_projected_points

    def _print_game_header(self):
        print("\n" + "=" * 60)
        print(f"{Fore.CYAN}{Style.BRIGHT}Game Analysis: {self.away_team.team_name} vs {self.home_team.team_name}{Style.RESET_ALL}")
        print("=" * 60)

    def _print_game_details(self):
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Game Details:{Style.RESET_ALL}")
        print(f"{'Home Team:':<15} {self.home_team.team_name}")
        print(f"{'Away Team:':<15} {self.away_team.team_name}")
        print(f"{'Field Type:':<15} {self.field_type}")
        print(f"{'Dome:':<15} {self.dome}")
        print(f"{'Temperature:':<15} {self.weather_temp}°F")
        print(f"{'Wind:':<15} {self.weather_wind} mph")
        print(f"{'Precipitation:':<15} {self.weather_rain}")

    def _print_starting_lineups(self):
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Starting Lineups:{Style.RESET_ALL}")
        print(f"\n{self.home_team.team_name}:")
        for player, position, _ in self.home_team.team_projections:
            print(f"{player:<20} ({position})")
        
        print(f"\n{self.away_team.team_name}:")
        for player, position, _ in self.away_team.team_projections:
            print(f"{player:<20} ({position})")

    def _print_projected_scores(self, home_score, away_score):
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Projected Scores:{Style.RESET_ALL}")
        print(f"{self.home_team.team_name:<20} {home_score:.2f}")
        print(f"{self.away_team.team_name:<20} {away_score:.2f}")

    def _print_win_percentages(self, home_score, away_score):
        home_win_pct = self._calculate_win_percentage(away_score - home_score)
        away_win_pct = 100 - home_win_pct
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Win Percentages:{Style.RESET_ALL}")
        print(f"{self.home_team.team_name:<20} {home_win_pct:.2f}%")
        print(f"{self.away_team.team_name:<20} {away_win_pct:.2f}%")

    def _print_betting_info(self, home_score, away_score):
        if not self.betting_data:
            return

        print(f"\n{Fore.GREEN}{Style.BRIGHT}Betting Lines:{Style.RESET_ALL}")
        print(f"{'Home Team Spread:':<20} {self.betting_data['home_spread']}")
        print(f"{'Away Team Spread:':<20} {self.betting_data['away_spread']}")
        print(f"{'Over/Under:':<20} {self.betting_data['total']}")
        print(f"{'Home Team Moneyline:':<20} {self.betting_data['home_ml']}")
        print(f"{'Away Team Moneyline:':<20} {self.betting_data['away_ml']}")

        home_implied_win_pct = self._calculate_implied_win_pct(self.betting_data["home_ml"])
        away_implied_win_pct = 100 - home_implied_win_pct

        home_win_pct_edge = self._calculate_win_percentage(away_score - home_score) - home_implied_win_pct
        away_win_pct_edge = 100 - self._calculate_win_percentage(away_score - home_score) - away_implied_win_pct

        projected_point_diff = home_score - away_score
        spread_edge = projected_point_diff - self.betting_data["home_spread"]

        projected_total = home_score + away_score
        total_edge = projected_total - self.betting_data["total"]

         
        bet_recommendations = []
        if home_win_pct_edge > 5:
            ml_factor = 5 if self.betting_data['home_spread'] > 0 else 10
            bet_recommendations.append(f"Bet on {self.home_team.team_name} to win | {abs(home_win_pct_edge/ml_factor):.2f}u")
        if away_win_pct_edge > 5:
            ml_factor = 5 if self.betting_data['away_spread'] > 0 else 10
            bet_recommendations.append(f"Bet on {self.away_team.team_name} to win | {abs(away_win_pct_edge/ml_factor):.2f}u")
        if spread_edge > 2:
            bet_recommendations.append(f"Bet on {self.home_team.team_name} to cover the spread | {abs(spread_edge):.2f}u")
        if spread_edge < -2:
            bet_recommendations.append(f"Bet on {self.away_team.team_name} to cover the spread | {abs(spread_edge):.2f}u")
        if total_edge > 2:
            bet_recommendations.append(f"Bet on the Over | {abs(total_edge):.2f}u")
        if total_edge < -2:
            bet_recommendations.append(f"Bet on the Under | {abs(total_edge):.2f}u")

        print(f"\n{Fore.GREEN}{Style.BRIGHT}Bet Recommendations:{Style.RESET_ALL}")
        if bet_recommendations:
            for recommendation in bet_recommendations:
                print(f"{Fore.YELLOW}{recommendation}")
        else:
            print(f"{Fore.YELLOW}No strong betting recommendations for this game.")

        print("\n" + "=" * 60)

    @staticmethod
    def _calculate_points_grass(offense_value: float) -> float:
        """Calculate projected points on grass field."""
        return (21 + 1.23 * offense_value + 0.0692 * offense_value**2 +
                0.0242 * offense_value**3 + 0.000665 * offense_value**4)

    @staticmethod
    def _calculate_points_turf(offense_value: float) -> float:
        """Calculate projected points on turf field."""
        return (23 + 1.23 * offense_value + 0.0692 * offense_value**2 +
                0.0242 * offense_value**3 + 0.000665 * offense_value**4)

    @staticmethod
    def _calculate_win_percentage(point_difference: float) -> float:
        """Calculate win percentage based on point difference."""
        win_pct = (-0.0303 * point_difference + 0.5) * 100
        return max(min(win_pct, 99.9), 0.1)

    @staticmethod
    def _calculate_implied_win_pct(money_line: int) -> float:
        """Calculate implied win percentage from money line odds."""
        if money_line < 0:
            return (-1 * money_line) / ((-1 * money_line) + 100) * 100
        else:
            return 100 / (money_line + 100) * 100