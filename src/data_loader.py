"""
This module handles data loading and processing for the NFL projection model.

It provides functions to:

* Load CSV and JSON data
* Process player data for specific positions
* Load and process data for all positions, merging weekly and season projections

"""

import csv
import json
from typing import Dict, List, Callable, Tuple, Any
import logging
import config
import pprint as pp

logger = logging.getLogger(__name__)

def load_csv_data(file_path: str, process_func: Callable) -> Any:
    """
    Load data from a CSV file and apply a processing function.
    """
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)
        return process_func(data)

def load_json_data(file_path: str) -> Dict:
    """
    Load JSON data from a file.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
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
            team_data.setdefault(team, {pos: []
                for pos in config.POSITIONS
            })[position].append((name, row))
    return team_data

def load_position_data(file_path: str) -> Dict[str, List[Tuple[str, Dict]]]:
    """
    Load and process data for a specific position from a CSV file.
    """
    team_data = {}
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            team = row['team']
            player = row['player']
            team_data.setdefault(team, []).append((player, row))
    return team_data

def load_ftn_data(file_path: str) -> Dict[str, List[Tuple[str, Dict]]]:
    """
    Load and process data for all positions from the 'ftn' CSV file.
    """
    team_data = {}
    with open(file_path, newline='', encoding='utf-8') as csvfile:
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
        logger.info("Loading data for position: %s", pos)
        file_path = getattr(config, f"{pos}_PROJECTIONS_FILE")
        pos_data = load_position_data(file_path)

        for team, players in pos_data.items():
            if team not in all_data:
                all_data[team] = {p: [] for p in config.POSITIONS}
            all_data[team][pos] = players

    # Load and merge season projections for QBs (from 'ftn' file)
    season_data = load_ftn_data(config.PROJECTIONS_FILE_SEASON)
    for team, players in season_data.items():
        for pos, pos_data in all_data[team].items():
            for player, player_data in pos_data:
                for p, p_data in players:
                    if p == player or config.get_dvoa_player_map(player) == p:
                        player_data['PaFD'] = float(p_data['PaFD']) / 17
                        player_data['RuFD'] = float(p_data['RuFD']) / 17
                        player_data['ReFD'] = float(p_data['ReFD']) / 17

    # Load and merge ftn weekly projections for all positions
    ftn_weekly_data = load_ftn_data(config.FTN_PROJECTIONS_FILE)
    for team, players in ftn_weekly_data.items():
        if not team: continue
        for pos, pos_data in all_data[team].items():
            for player, player_data in pos_data:
                for p, p_data in players:
                    if p == player or config.get_ftn_player_map(player) == p:
                        if pos == "QB":
                            player_data['pass_att'] = avg(player_data['pass_att'], p_data['PaAtt'])
                            player_data['pass_cmp'] = avg(player_data['pass_cmp'], p_data['PaCom'])
                            player_data['pass_int'] = avg(player_data['pass_int'], p_data['INT'])
                            player_data['pass_td'] = avg(player_data['pass_td'], p_data['PaTDs'])
                            player_data['pass_yds'] = avg(player_data['pass_yds'], p_data['PaYds'])
                        player_data['rush_att'] = avg(player_data['rush_att'], p_data['RuAtt'])
                        player_data['rush_td'] = avg(player_data['rush_td'], p_data['RuTDs'])
                        player_data['rush_yds'] = avg(player_data['rush_yds'], p_data['RuYds'])
                        if pos in ["WR", "RB", "TE"]:
                            player_data['rec_tgt'] = avg(player_data['rec_tgt'], p_data['Tar'])
                            player_data['rec'] = avg(player_data['rec'], p_data['Rec'])
                            player_data['rec_yds'] = avg(player_data['rec_yds'], p_data['ReYds'])
                            player_data['rec_td'] = avg(player_data['rec_td'], p_data['ReTDs'])
    logger.info("Total teams loaded: %d", len(all_data))
    return all_data

def avg(num1, num2) -> float:
    num1=float(num1)
    num2=float(num2)
    return (num1 + num2) / 2