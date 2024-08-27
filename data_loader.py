import csv
import json
from typing import Dict, List, Callable, Tuple, Any
import config
import logging

logger = logging.getLogger(__name__)

def load_csv_data(file_path: str, process_func: Callable) -> Any:
    """
    Load data from a CSV file and apply a processing function to it.

    Args:
        file_path (str): The path to the CSV file.
        process_func (Callable): A function to process the CSV data.

    Returns:
        Any: The result of applying the processing function to the data.
    """
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
        return process_func(data)


def load_json_data(file_path: str) -> Dict:
    """
    Load JSON data from a file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data as a dictionary.
    """
    with open(file_path, 'r') as file:
        return json.load(file)

def process_position_data(data: List[Dict]) -> Dict[str, Dict[str, List[Tuple]]]:
    """
    Process player data for a specific position.

    Args:
        data (List[Dict]): List of player data dictionaries.

    Returns:
        Dict[str, Dict[str, List[Tuple]]]: Processed data organized by team and position.
    """
    team_db = {}
    for row in data:
        team = row['team']
        pos = row['pos']
        name = row['player']
        if pos in config.POSITIONS:
            team_db.setdefault(team, {pos: [] for pos in config.POSITIONS})[pos].append((name, row))
    return team_db

def load_position_data(file_path: str) -> Dict[str, List[Tuple[str, Dict]]]:
    """
    Load and process data for a specific position from a CSV file.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        Dict[str, List[Tuple[str, Dict]]]: Processed position data.
    """
    team_data = {}
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            team = row['team']
            player = row['player']
            if team not in team_data:
                team_data[team] = []
            team_data[team].append((player, row))
    return team_data

def load_all_position_data() -> Dict[str, Dict[str, List[Tuple[str, Dict]]]]:
    """
    Load and process data for all positions.

    Returns:
        Dict[str, Dict[str, List[Tuple[str, Dict]]]]: Processed data for all positions.
    """
    all_data = {}
    for pos in config.POSITIONS:
        logger.info(f"Loading data for position: {pos}")
        file_path = getattr(config, f"{pos}_FILE")
        pos_data = load_position_data(file_path)
        
        for team, players in pos_data.items():
            if team not in all_data:
                all_data[team] = {p: [] for p in config.POSITIONS}
            all_data[team][pos] = players
        
        logger.info(f"Loaded {sum(len(players) for players in pos_data.values())} players for position {pos}")

    logger.info(f"Total teams loaded: {len(all_data)}")
    for team, positions in all_data.items():
        logger.debug(f"Team {team}: {', '.join(f'{pos}: {len(players)}' for pos, players in positions.items())}")

    return all_data

