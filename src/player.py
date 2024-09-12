"""
Player Module
-------------
This module defines the Player class, which represents an NFL player
and provides methods to calculate various DVOA statistics and load player projections.
"""

from typing import Dict, Any
import config
import utils

class Player:
    """Represents an NFL player with associated statistics and projections."""

    def __init__(self, name: str, pos: str, team: str):
        """Initialize a Player instance."""
        self.name = name.lower()
        self.position = pos
        self.team = team
        self.yearly_weights = {
            "2024": 1,
            "2023": 2,
            "2022": 4,
            "2021": 8
        }
        self.projections: Dict[str, float] = {}
        self.dvoa_player_map = {
            "tank dell": "nathaniel dell",
            "velus jones jr.": "velus jones",
            "scotty miller": "scott miller",
            "calvin austin iii": "calvin austin",
            "marvin mims jr.": "marvin mims",
            "pierre strong jr.": "pierre strong",
            "gabe davis": "gabriel davis",
            "travis etienne jr.": "travis etienne",
            "joshua palmer": "josh palmer",
            "brian robinson jr.": "brian robinson",
            "dk metcalf": "d.k. metcalf",
            "kenneth walker iii": "kenneth walker",
            "nick westbrook-ikhine": "nick westbrook",
            "chig okonkwo": "chigoziem okonkwo",
            "michael pittman jr.": "michael pittman",
            "de'von achane": "devon achane",

        }

    def get_passing_dvoa(self, dvoa: Dict[str, Dict[str, Dict[str, Any]]]) -> float:
        """Calculate weighted passing DVOA across years."""
        # print(f"QB: {self.name}")
        # print(f"Weighted DVOA: {round(self._calculate_weighted_dvoa(dvoa, "Passing", "pass_attempts") * 100)}%")
        return self._calculate_weighted_dvoa(dvoa, "Passing", "pass_attempts")

    def get_receiving_dvoa(self, dvoa: Dict[str, Dict[str, Dict[str, Any]]]) -> float:
        """Calculate weighted receiving DVOA across years."""
        #print(f"{self.name} Weighted DVOA: {round(self._calculate_weighted_dvoa(dvoa, "Receiving", "targets") * 100)}%")
        # if self._calculate_weighted_dvoa(dvoa, "Receiving", "targets") == 0:
        #     print(f"\n=== Couln't find {self.name}\n")
        return self._calculate_weighted_dvoa(dvoa, "Receiving", "targets")

    def get_rushing_dvoa(self, dvoa: Dict[str, Dict[str, Dict[str, Any]]]) -> float:
        """Calculate weighted rushing DVOA across years."""
        # if self._calculate_weighted_dvoa(dvoa, "Rushing", "attempts") == 0 and self.position == "RB":
        #     print(f"\n=== Couln't find {self.name}\n")
        return self._calculate_weighted_dvoa(dvoa, "Rushing", "attempts")

    def _calculate_weighted_dvoa(self, dvoa: Dict[str, Dict[str, Dict[str, Any]]], 
                                 category: str, attempt_type: str) -> float:
        """Generic method to calculate weighted DVOA for a given category."""
        total_attempts = 0
        total_contribution = 0
        for year in config.YEARS:
            yearly_dvoa = dvoa[year][category]
            mapped_name = self.dvoa_player_map.get(self.name, self.name)
            try:
                player_dvoa, player_attempts = yearly_dvoa[mapped_name][0]
            except KeyError:
                player_dvoa, player_attempts = 0, 0

            weighted_attempts = player_attempts / self.yearly_weights[year]
            yearly_contribution = player_dvoa * weighted_attempts
            total_attempts += weighted_attempts
            total_contribution += yearly_contribution

        return total_contribution / total_attempts if total_attempts else 0

    def get_proj_passing_att(self) -> float:
        """Get projected passing attempts."""
        return self.projections.get("PassAtt", 0)

    def get_proj_targets(self) -> float:
        """Get projected targets."""
        #print(f"{self.name} proj targets: {self.projections.get("Targets", 0)}")
        return self.projections.get("Targets", 0)

    def get_proj_attempts(self) -> float:
        """Get projected rushing attempts."""
        return self.projections.get("RushAtt", 0)

    def load_ftn_data(self, player_data: Dict[str, str]):
        """Load player projections from FTN data."""
        projection_mappings = {
            "PassAtt": "PaAtt",
            "PassComp": "PaCom",
            "PassTDs": "PaTDs",
            "PassYds": "PaYds",
            "PassInt": "INT",
            "RushAtt": "RuAtt",
            "RushYds": "RuYds",
            "RushTDs": "RuTDs",
            "Targets": "Tar",
            "Receptions": "Rec",
            "RecYards": "ReYds",
            "RecTDs": "ReTDs",
            "Fumbles": "Fum"
        }

        self.projections = {
            proj_key: utils.safe_float(player_data[ftn_key])
            for proj_key, ftn_key in projection_mappings.items()
        }