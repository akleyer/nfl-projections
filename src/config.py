from typing import Dict, List, Tuple

# Data directory 
DATA_DIR = "../data/raw/"

# Define Week
WEEK_NUM = 1
# File paths
QB_PROJECTIONS_FILE = f"{DATA_DIR}projections/2024/week{WEEK_NUM}/projections_qb.csv"
QB_PROJECTIONS_FILE_SEASON = f"{DATA_DIR}projections/2024/season/projections_all_positions.csv"
WR_PROJECTIONS_FILE = f"{DATA_DIR}projections/2024/week{WEEK_NUM}/projections_wr.csv"
RB_PROJECTIONS_FILE = f"{DATA_DIR}projections/2024/week{WEEK_NUM}/projections_rb.csv"
TE_PROJECTIONS_FILE = f"{DATA_DIR}projections/2024/week{WEEK_NUM}/projections_te.csv"

DVOA_TEAM_DEFENSE_FILE = f"{DATA_DIR}dvoa/2023/team_defense_dvoa.csv"
DVOA_ADJUSTED_LINE_YARDS_FILE = f"{DATA_DIR}dvoa/2023/dvoa_adjusted_line_yards.csv"
PLAY_RATES_FILE = f"{DATA_DIR}misc/play_rates.csv"
HOME_ADVANTAGE_FILE = f"{DATA_DIR}misc/home_adv.csv"
AVERAGE_TEMPERATURE_FILE = f"{DATA_DIR}misc/avg_tmp.csv"
MATCHUPS_FILE = f"{DATA_DIR}matchups/2024/matchups_week_{WEEK_NUM}.json"
PROJECTED_OLINE_VALUE_FILE = f"{DATA_DIR}dvoa/oline_delta.csv"

# Constants
POSITIONS = ['QB', 'WR', 'RB', 'TE']
YEARS = ["2023_playoffs", "2023", "2022", "2021", "2020"]

TEAM_ABBR_MAPPING = {}

# Player mapping for dvoa
PLAYER_DVOA_MAPPING = {
    'Gardner Minshew II': 'Gardner Minshew'
}

def get_dvoa_player_map(name: str) -> str:
    return PLAYER_DVOA_MAPPING.get(name, name)

def get_standard_team_abbr(abbr: str) -> str:
    """
    Get the standardized team abbreviation.
    """
    return TEAM_ABBR_MAPPING.get(abbr, abbr)

def process_dvoa_data(data: List[List[str]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Process DVOA data, extracting pass and rush DVOA.
    """
    pass_dvoa = {row[0]: float(row[7]) for row in data[1:]}
    rush_dvoa = {row[0]: float(row[9]) for row in data[1:]}
    return pass_dvoa, rush_dvoa

def process_dvoa_data_ol(data: List[List[str]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Process offensive line DVOA data, extracting rush and pass DVOA.
    """
    rush_dvoa = {row[0]: float(row[3]) for row in data[1:]}
    pass_dvoa = {row[0]: float(row[9]) for row in data[1:]}
    return rush_dvoa, pass_dvoa

def create_play_rate_entry(data: List[List[str]]) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Create play rate entries for all teams.
    """
    play_rates = {}
    for row in data[1:]:
        team = row[0]
        play_rates[team] = {
            "OFFENSE": {
                "PlaysPer60": float(row[2]),
                "PassRate": float(row[1]),
                "RushRate": 100 - float(row[1]),
            },
            "DEFENSE": {
                "PlaysPer60": float(row[4]),
                "PassRate": float(row[3]),
                "RushRate": 100 - float(row[3]),
            }
        }
    return play_rates

def process_proj_oline(data: List[List[str]]) -> Dict[str, float]:
    return {row[0]: float(row[1]) for row in data[1:]}

def process_home_field_adv(data: List[List[str]]) -> Dict[str, Tuple[float, float]]:
    return {row[0]: (float(row[1]), float(row[2])) for row in data[1:]}

def process_avg_temp(data: List[List[str]]) -> Dict[str, float]:
    return {row[0]: float(row[1]) for row in data[1:]}

def process_dvoa_yearly(data: List[List[str]]) -> Dict[str, Tuple[float, float]]:
    return {row[0]: (float(row[4]) * 100, float(row[6])) for row in data[1:]}