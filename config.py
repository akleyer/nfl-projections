from typing import Dict, List, Tuple

# File paths
QB_FILE = "projections/2024/week1/qb.csv"
WR_FILE = "projections/2024/week1/wr.csv"
RB_FILE = "projections/2024/week1/rb.csv"
TE_FILE = "projections/2024/week1/te.csv"
DVOA_FILE = "dvoa/2023/team_defense_dvoa.csv"
ADJUSTED_LINE_YARDS_FILE = "dvoa/2023/dvoa_adjusted_line_yards.csv"
PLAY_RATES_FILE = "misc/play_rates.csv"
HOME_ADV_FILE = "misc/home_adv.csv"
AVG_TEMP_FILE = "misc/avg_tmp.csv"
MATCHUPS_FILE = "misc/matchups_week_1.json"
PROJ_OLINE_VAL_FILE = "dvoa/oline_delta.csv"

# Constants
POSITIONS = ['QB', 'WR', 'RB', 'TE']
YEARS = ["2023_playoffs", "2023", "2022", "2021", "2020"]

# Team abbreviation mapping
TEAM_ABBR_MAPPING = {
   
    # Add any other necessary mappings here
}

def get_standard_team_abbr(abbr: str) -> str:
    """
    Get the standard team abbreviation.
    
    Args:
        abbr (str): The team abbreviation to standardize.
    
    Returns:
        str: The standardized team abbreviation.
    """
    return TEAM_ABBR_MAPPING.get(abbr, abbr)

def process_dvoa_data(data: List[List[str]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Process DVOA data from a list of rows.

    Args:
        data (List[List[str]]): A list of rows containing DVOA data.

    Returns:
        Tuple[Dict[str, float], Dict[str, float]]: A tuple containing pass DVOA and rush DVOA dictionaries.
    """
    pass_dvoa, rush_dvoa = {}, {}
    for row in data[1:]:  # Skip header
        pass_dvoa[row[0]] = float(row[7])
        rush_dvoa[row[0]] = float(row[9])
    return pass_dvoa, rush_dvoa

def process_dvoa_data_ol(data: List[List[str]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Process DVOA data from a list of rows.

    Args:
        data (List[List[str]]): A list of rows containing DVOA data.

    Returns:
        Tuple[Dict[str, float], Dict[str, float]]: A tuple containing pass DVOA and rush DVOA dictionaries.
    """
    pass_dvoa, rush_dvoa = {}, {}
    for row in data[1:]:  # Skip header
        pass_dvoa[row[0]] = float(row[9])
        rush_dvoa[row[0]] = float(row[3])
    return rush_dvoa, pass_dvoa

def create_play_rate_entry(data: List[List[str]]) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Create play rate entries for all teams based on the data.

    Args:
        data (List[List[str]]): A list of rows containing play rate data.

    Returns:
        Dict[str, Dict[str, Dict[str, float]]]: A dictionary of play rate information for each team.
    """
    play_rates = {}
    for row in data[1:]:  # Skip header
        team = row[0]
        play_rates[team] = {
            "OFF": {
                "PlayPer60": float(row[2]),
                "PassRate": float(row[1]),
                "RushRate": 100 - float(row[1]),
            },
            "DEF": {
                "PlayPer60": float(row[4]),
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