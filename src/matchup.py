"""
Matchup Module
--------------
This module defines the Matchup class, which represents a matchup between two teams.
It provides methods to calculate projected points and win percentages based on various factors.
"""

import csv
import logging
from typing import Dict, List, Tuple
from colorama import Fore, Style

from team import Team
from weather import WeatherConditions
import config

logger = logging.getLogger(__name__)

class Matchup:
    """Represents a matchup between two teams."""

    def __init__(self, matchup_data: Dict, projections: object, dvoa: Dict, dave: Dict, pass_rates: Dict):
        """Initialize a Matchup instance with game data and team statistics."""
        self.home_team = Team(matchup_data['home'], projections, dvoa, dave)
        self.away_team = Team(matchup_data['away'], projections, dvoa, dave)
        self.field_type = matchup_data['field']
        self.dome = matchup_data['dome']
        self.betting_data = matchup_data['betting_lines']
        self.pass_rates_data = pass_rates
        self.weather_obj = self._init_weather(matchup_data)
        self.home_adv = self._load_home_field_advantage()

    def _init_weather(self, matchup_data: Dict) -> WeatherConditions:
        """Initialize weather conditions, adjusting for dome if necessary."""
        if self.dome == "yes":
            return WeatherConditions(72.5, 0, 0)
        return WeatherConditions(matchup_data['temp'], matchup_data['wind'], matchup_data['weather'])

    def _load_home_field_advantage(self) -> Dict[str, List[str]]:
        """Load home field advantage data from a CSV file."""
        with open(config.HOME_ADV_FILE, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            return {row['Team']: [row['Adv']] for row in reader}

    def project_outcome(self) -> Tuple[float, float]:
        """Project the outcome of the matchup."""
        home_points, away_points = self._calculate_projected_points()
        self._print_game_analysis(home_points, away_points)
        return home_points, away_points

    def _calculate_projected_points(self) -> Tuple[float, float]:
        """Calculate projected points for home and away teams."""
        home_off, home_def = self._get_adjusted_team_values(self.home_team)

        print()
        away_off, away_def = self._get_adjusted_team_values(self.away_team)
        # print(f"{self.home_team.team_name} Off: {home_off}")
        # print(f"{self.away_team.team_name} Off: {away_off}")
        # print("-")
        # print(f"{self.home_team.team_name} Def: {home_def}")
        # print(f"{self.away_team.team_name} Def: {away_def}")
        # print("-")

        home_pass_rate, away_pass_rate = self._get_adjusted_pass_rates()

        home_adv = float(self.home_adv[self.home_team.team_name][0])

        home_off_value = self._calculate_offensive_value(home_off, away_def, home_pass_rate)
        # home_off_value += home_adv / 2
        #print(f"Home Off Value: {home_off_value}")
        away_off_value = self._calculate_offensive_value(away_off, home_def, away_pass_rate)
        # away_off_value -= home_adv / 2
        #print(f"Away Off Value: {away_off_value}")

        home_points = self._calculate_points(home_off_value) + (home_adv / 2)
        away_points = self._calculate_points(away_off_value) - (home_adv / 2)

        return home_points, away_points

    def _get_adjusted_team_values(self, team: Team) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Get adjusted offensive and defensive values for a team."""
        off_values = {
            'pass': (team.get_total_passing_value()),# + team.get_off_dave_normalized()) / 2,
            'rush': (team.get_total_rushing_value()),# + team.get_off_dave_normalized()) / 2
        }
        def_values = {
            'pass': (team.get_total_passing_value_def()),# + team.get_def_dave_normalized()) / 2,
            'rush': (team.get_total_rushing_value_def()),# + team.get_def_dave_normalized()) / 2
        }
        #print(team.get_total_rushing_value_def())
        return off_values, def_values

    def _get_adjusted_pass_rates(self) -> Tuple[float, float]:
        """Calculate adjusted pass rates for home and away teams."""
        home_pass_off, home_pass_def = self.home_team.get_pass_rates(self.pass_rates_data)
        away_pass_off, away_pass_def = self.away_team.get_pass_rates(self.pass_rates_data)
        return (home_pass_off + away_pass_def) / 2, (away_pass_off + home_pass_def) / 2

    def _calculate_offensive_value(self, off_values: Dict[str, float], def_values: Dict[str, float], pass_rate: float) -> float:
        """Calculate the overall offensive value considering pass and rush components."""
        pass_value = (off_values['pass'] - def_values['pass']) * pass_rate / 100
        rush_value = (off_values['rush'] - def_values['rush']) * (100 - pass_rate) / 100
        return pass_value + rush_value - self.weather_obj.calculate_precipitation_impact()

    def _calculate_points(self, offensive_value: float) -> float:
        """Calculate projected points based on offensive value and field type."""
        if self.field_type == 'turf':
            return 2.5 * offensive_value + 24.333
        else:
            return 2.5 * offensive_value + 23.667

    def _print_game_analysis(self, home_points: float, away_points: float):
        """Print comprehensive game analysis including projections and betting recommendations."""
        self._print_game_header()
        self._print_game_details()
        self._print_starting_lineups()
        self._print_projected_scores(home_points, away_points)
        self._print_win_percentages(home_points, away_points)
        self._print_betting_info(home_points, away_points)

    def _print_game_header(self):
        """Print the game header."""
        print("\n" + "=" * 60)
        print(f"{Fore.CYAN}{Style.BRIGHT}Game Analysis: {self.away_team.team_name} vs {self.home_team.team_name}{Style.RESET_ALL}")
        print("=" * 60)

    def _print_game_details(self):
        """Print game details including weather and field conditions."""
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Game Details:{Style.RESET_ALL}")
        details = [
            ('Home Team:', self.home_team.team_name),
            ('Away Team:', self.away_team.team_name),
            ('Field Type:', self.field_type),
            ('Dome:', self.dome),
            ('Temperature:', f"{self.weather_obj.temperature}°F"),
            ('Wind:', f"{self.weather_obj.wind_speed} mph"),
            ('Precipitation:', self.weather_obj.precipitation_chance)
        ]
        for label, value in details:
            print(f"{label:<15} {value}")

    def _print_starting_lineups(self):
        """Print starting lineups for both teams."""
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Starting Lineups:{Style.RESET_ALL}")
        for team in [self.home_team, self.away_team]:
            print(f"\n{team.team_name}:")
            for player, position, _ in team.team_projections:
                print(f"{player:<20} ({position})")

    def _print_projected_scores(self, home_score: float, away_score: float):
        """Print projected scores for both teams."""
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Projected Scores:{Style.RESET_ALL}")
        print(f"{self.home_team.team_name:<20} {home_score:.0f}")
        print(f"{self.away_team.team_name:<20} {away_score:.0f}")

    def _print_win_percentages(self, home_score: float, away_score: float):
        """Print win percentages for both teams."""
        home_win_pct = self._calculate_win_percentage(away_score - home_score)
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Win Percentages:{Style.RESET_ALL}")
        print(f"{self.home_team.team_name:<20} {home_win_pct:.0f}%")
        print(f"{self.away_team.team_name:<20} {100 - home_win_pct:.0f}%")

    def _print_betting_info(self, home_score: float, away_score: float):
        """Print betting information and recommendations."""
        if not self.betting_data:
            return

        print(f"\n{Fore.GREEN}{Style.BRIGHT}Betting Lines:{Style.RESET_ALL}")
        for label, key in [
            ('Home Team Spread:', 'home_spread'),
            ('Away Team Spread:', 'away_spread'),
            ('Over/Under:', 'total'),
            ('Home Team Moneyline:', 'home_ml'),
            ('Away Team Moneyline:', 'away_ml')
        ]:
            print(f"{label:<20} {self.betting_data[key]}")

        home_implied_win_pct = self._calculate_implied_win_pct(self.betting_data["home_ml"])
        home_win_pct = self._calculate_win_percentage(away_score - home_score)
        
        edges = {
            'home_ml': home_win_pct - home_implied_win_pct,
            'away_ml': (100 - home_win_pct) - (100 - home_implied_win_pct),
            'spread': (home_score - away_score) - self.betting_data["home_spread"],
            'total': (home_score + away_score) - self.betting_data["total"]
        }

        self._print_bet_recommendations(edges)

    def _print_bet_recommendations(self, edges: Dict[str, float]):
        """Print bet recommendations based on calculated edges."""
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Bet Recommendations:{Style.RESET_ALL}")
        recommendations = []

        if edges['home_ml'] > 5:
            ml_factor = 5 if self.betting_data['home_spread'] > 0 else 10
            recommendations.append(f"Bet on {self.home_team.team_name} to win | {abs(edges['home_ml']/ml_factor):.2f}u")
        if edges['away_ml'] > 5:
            ml_factor = 5 if self.betting_data['away_spread'] > 0 else 10
            recommendations.append(f"Bet on {self.away_team.team_name} to win | {abs(edges['away_ml']/ml_factor):.2f}u")
        if edges['spread'] > 2:
            recommendations.append(f"Bet on {self.home_team.team_name} to cover the spread | {abs(edges['spread']):.2f}u")
        if edges['spread'] < -2:
            recommendations.append(f"Bet on {self.away_team.team_name} to cover the spread | {abs(edges['spread']):.2f}u")
        if edges['total'] > 2:
            recommendations.append(f"Bet on the Over | {abs(edges['total']):.2f}u")
        if edges['total'] < -2:
            recommendations.append(f"Bet on the Under | {abs(edges['total']):.2f}u")

        if recommendations:
            for recommendation in recommendations:
                print(recommendation)
        else:
            print("No strong betting recommendations for this game.")

        print("\n" + "=" * 60)

    @staticmethod
    def _calculate_win_percentage(point_difference: float) -> float:
        """Calculate win percentage based on point difference."""
        return max(min((-0.0303 * point_difference + 0.5) * 100, 99.9), 0.1)

    @staticmethod
    def _calculate_implied_win_pct(money_line: int) -> float:
        """Calculate implied win percentage from money line odds."""
        if money_line < 0:
            return (-money_line) / (-money_line + 100) * 100
        return 100 / (money_line + 100) * 100