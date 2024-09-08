"""
NFL Projection Model
--------------------
This module contains the main logic for the NFL projection model.
It loads and processes data, creates matchups, and runs projections.
"""

import csv
import logging
from typing import Dict, List, Tuple

from data_loader import load_json_data
from dvoa import DVOA
from matchup import Matchup
from projections import Projections
from utils import safe_float

import config

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def _load_pass_rates() -> Dict[str, List[Tuple[float, float]]]:
    """Load pass rates for each team from a CSV file."""
    team_data = {}
    with open(config.PLAY_RATES_FILE, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                team = row['Team']
                off_pass_rate = safe_float(row['OffPassRate'])
                def_pass_rate = safe_float(row['DefPassRate'])
                team_data.setdefault(team, []).append(
                    (off_pass_rate, def_pass_rate))
            except KeyError:
                continue
    return team_data

def main():
    """Main function to run the NFL projection model."""
    projections = Projections()
    dvoa = DVOA()
    pass_rates = _load_pass_rates()
    matchups = [
        Matchup(matchup, projections, dvoa.get_data(), dvoa.get_dave(),
                pass_rates).project_outcome()
        for matchup in load_json_data(config.MATCHUPS_FILE)
    ]


if __name__ == "__main__":
    main()