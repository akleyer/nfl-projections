"""
DVOA Module
-----------
This module defines the DVOA class, which loads and manages DVOA (Defense-adjusted Value Over Average) data
for NFL teams and players across multiple years and categories.
"""

import csv
from typing import Dict, List, Tuple
import config
import utils

class DVOA:
    """Manages DVOA data for NFL teams and players."""

    def __init__(self):
        """Initialize DVOA instance with all DVOA data and DAVE data."""
        self.data = self._load_all_dvoa_data()
        self.dave = self._load_dave_data()

    def get_data(self) -> Dict:
        """Return all DVOA data."""
        return self.data

    def get_dave(self) -> Dict:
        """Return DAVE (DVOA Adjusted for Variation Early) data."""
        return self.dave

    def _load_dave_data(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """Load DAVE data from CSV file."""
        team_data = {}
        file_path = "../data/raw/dvoa/dave.csv"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                team = row['TEAM']
                dave_values = (row['OFF DAVE'], row['DEF DAVE'], row['ST DAVE'])
                team_data.setdefault(team, []).append(dave_values)
        return team_data 

    def _load_all_dvoa_data(self) -> Dict[int, Dict[str, Dict]]:
        """Load all DVOA data for configured years."""
        data = {}
        for year in config.YEARS:
            data[year] = {
                "Passing": self._get_passing_dvoa(year),
                "Rushing": self._get_rush_dvoa(year),
                "Receiving": self._get_rec_dvoa(year),
                "OL Pass": self._get_ol_dvoa(year, "Pass"),
                "OL Run": self._get_ol_dvoa(year, "Rush"),
                "Defense Pass": self._get_def_dvoa(year, "Pass"),
                "Defense Rush": self._get_def_dvoa(year, "Rush")
            }
        return data

    def _get_def_dvoa(self, year: int, group: str) -> Dict[str, List[float]]:
        """Load defensive DVOA data for a specific year and group (Pass/Rush)."""
        team_data = {}
        file_path = f"../data/raw/dvoa/{year}/team_defense_dvoa.csv"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    team = row['TEAM']
                except:
                    continue
                if group == "Pass":
                    def_dvoa = self._convert_strpct_to_float(row['PASS'])
                elif group == "Rush":
                    def_dvoa = self._convert_strpct_to_float(row['RUSH'])
                else:
                    raise ValueError(f"Invalid group type for DEF: {group}")
                team_data.setdefault(team, []).append(def_dvoa)
        return team_data 

    def _get_ol_dvoa(self, year: int, group: str) -> Dict[str, List[float]]:
        """Load offensive line DVOA data for a specific year and group (Pass/Rush)."""
        team_data = {}
        file_path = f"../data/raw/dvoa/{year}/dvoa_adjusted_line_yards.csv"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                team = row['Team']
                if group == "Pass":
                    ol_dvoa = utils.safe_float(row['Adj Sack %']) / 100
                elif group == "Rush":
                    ol_dvoa = utils.safe_float(row['ALYards'])
                else:
                    raise ValueError(f"Invalid group type for OL: {group}")
                team_data.setdefault(team, []).append(ol_dvoa)
        return team_data 

    def _get_rec_dvoa(self, year: int) -> Dict[str, List[Tuple[float, float]]]:
        """Load receiving DVOA data for a specific year."""
        return self._load_player_dvoa(year, "receiving_dvoa.csv", 'DVOA', 'TAR')

    def _get_rush_dvoa(self, year: int) -> Dict[str, List[Tuple[float, float]]]:
        """Load rushing DVOA data for a specific year."""
        return self._load_player_dvoa(year, "rushing_dvoa.csv", 'DVOA', 'ATT')

    def _get_passing_dvoa(self, year: int) -> Dict[str, List[Tuple[float, float]]]:
        """Load passing DVOA data for a specific year."""
        return self._load_player_dvoa(year, "passing_dvoa.csv", 'DVOA', 'ATT')

    def _load_player_dvoa(self, year: int, filename: str, dvoa_col: str, att_col: str) -> Dict[str, List[Tuple[float, float]]]:
        """Generic method to load player DVOA data."""
        player_data = {}
        file_path = f"../data/raw/dvoa/{year}/{filename}"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                player_name = row['Player'].lower()
                try:
                    dvoa = self._convert_strpct_to_float(row[dvoa_col])
                    attempts = float(row[att_col])
                except ValueError:
                    dvoa, attempts = 0, 1
                player_data.setdefault(player_name, []).append((dvoa, attempts))
        return player_data

    @staticmethod
    def _convert_strpct_to_float(str_pct: str) -> float:
        """Convert string percentage to float."""
        return float(str_pct.strip('%"\'')) / 100