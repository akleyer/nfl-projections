"""
This module handles data loading and processing for the NFL projection model.

It provides functions to:

* Load CSV and JSON data
* Process player data for specific positions
* Load and process data for all positions, merging weekly and season projections

"""

import csv
from typing import Dict, List, Callable, Tuple
import config
import yaml


def load_yaml_data(file_path: str) -> List[Dict]:
    """
    Load YAML data from a file.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        List[Dict]: A list of dictionaries containing the YAML data.

    Raises:
        FileNotFoundError: If the specified file is not found.
        yaml.YAMLError: If there's an error parsing the YAML file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise


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
