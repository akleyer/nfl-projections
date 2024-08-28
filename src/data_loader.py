import csv
import json
from typing import Dict, List, Callable, Tuple, Any
import config
import logging

logger = logging.getLogger(__name__)

def load_csv_data(file_path: str, process_func: Callable) -> Any:
    """
    Load data from a CSV file and apply a processing function.
    """
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
        return process_func(data)

def load_json_data(file_path: str) -> Dict:
    """
    Load JSON data from a file.
    """
    with open(file_path, 'r') as file:
        return json.load(file)

def process_position_data(data: List[Dict]) -> Dict[str, Dict[str, List[Tuple]]]:
    """
    Process player data for a specific position.
    """
    team_data = {}
    for row in data:
        team = row['team']
        position = row['pos']
        name = row['player']
        if position in config.POSITIONS:
            team_data.setdefault(team, {pos: [] for pos in config.POSITIONS})[position].append((name, row))
    return team_data

def load_position_data(file_path: str) -> Dict[str, List[Tuple[str, Dict]]]:
    """
    Load and process data for a specific position from a CSV file.
    """
    team_data = {}
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            team = row['team']
            player = row['player']
            team_data.setdefault(team, []).append((player, row))
    return team_data

def load_ftn_position_data(file_path: str) -> Dict[str, List[Tuple[str, Dict]]]:
    """
    Load and process data for all positions from the 'ftn' CSV file.
    """
    team_data = {}
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            team = row['Tm']
            player = row['Player']
            team_data.setdefault(team, []).append((player, row))
    return team_data

def load_all_position_data() -> Dict[str, Dict[str, List[Tuple[str, Dict]]]]:
    """
    Load and process data for all positions, merging weekly and season projections.
    """
    all_data = {}
    for pos in config.POSITIONS:
        logger.info(f"Loading data for position: {pos}")
        file_path = getattr(config, f"{pos}_PROJECTIONS_FILE")
        pos_data = load_position_data(file_path)
        
        for team, players in pos_data.items():
            if team not in all_data:
                all_data[team] = {p: [] for p in config.POSITIONS}
            all_data[team][pos] = players

    # Load and merge season projections for QBs (from 'ftn' file)
    season_qb_data = load_ftn_position_data(config.QB_PROJECTIONS_FILE_SEASON)
    for team, players in season_qb_data.items():
        for player, player_data in all_data[team]['QB']:
            for p, p_data in players:
                if p == player or config.get_dvoa_player_map(player) == p:
                    player_data['PaFD'] = p_data['PaFD']
                    player_data['RuFD'] = p_data['RuFD']
                    player_data['ReFD'] = p_data['ReFD']

    logger.info(f"Total teams loaded: {len(all_data)}")
    for team, positions in all_data.items():
        logger.debug(f"Team {team}: {', '.join(f'{pos}: {len(players)}' for pos, players in positions.items())}")

    return all_data

