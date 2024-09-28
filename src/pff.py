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

class PFF:
    """Manages DVOA data for NFL teams and players."""

    def __init__(self):
        """Initialize DVOA instance with all DVOA data and DAVE data."""
        self.pff = self._load_pff_data()

    def get_data(self) -> Dict:
        """Return all DVOA data."""
        return self.pff

    def _load_pff_data(self) -> Dict[int, Dict[str, Dict]]:
        """Load all DVOA data for configured years."""
        data = {}
        # for year in config.YEARS:
        data["2024"] = {
            "Passing": self._get_passing_grade("2024")
            # "Rushing": self._get_rush_dvoa(year),
            # "Receiving": self._get_rec_dvoa(year),
            # "OL Pass": self._get_ol_dvoa(year, "Pass"),
            # "OL Run": self._get_ol_dvoa(year, "Rush"),
            # "Defense Pass": self._get_def_dvoa(year, "Pass"),
            # "Defense Rush": self._get_def_dvoa(year, "Rush")
        }
        return data

    def _get_passing_grade(self, year: int) -> Dict[str, List[Tuple[float, float]]]:
        """Load passing DVOA data for a specific year."""
        return self._load_player_grade(year, "passing_grades.csv")

    def _load_player_grade(self, year: int, filename: str):
        """Generic method to load player DVOA data."""
        player_data = {}
        file_path = f"../data/raw/pff/{year}/{filename}"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                player_name = row['player'].lower()
                try:
                    dvoa = utils.safe_float(row["grades_pass"])
                    att = utils.safe_float(row["attempts"])
                except ValueError:
                    dvoa = 0
                    att = 1
                player_data.setdefault(player_name, []).append((dvoa, att))
        return player_data