# """
# This module centralizes configuration settings and constants for the NFL projection model.

# It includes:

# * File paths for various data sources (projections, DVOA, play rates, etc.)
# * Constants like positions and years for historical data
# * Team abbreviation mappings
# * Player mappings for DVOA data
# * Functions for processing DVOA and other data

# """
# from typing import Dict, List, Tuple

# Data directory
DATA_DIR = "../data/raw/"

# Define Week
WEEK_NUM = 2

# File paths
FTN_PROJECTIONS_FILE = f"{DATA_DIR}projections/2024/week{WEEK_NUM}/ftn_all_projections.csv"
PLAY_RATES_FILE = f"{DATA_DIR}misc/play_rates.csv"
HOME_ADV_FILE = f"{DATA_DIR}misc/home_adv.csv"
# AVERAGE_TEMPERATURE_FILE = f"{DATA_DIR}misc/avg_tmp.csv"
MATCHUPS_FILE = f"{DATA_DIR}matchups/2024/matchups_week_{WEEK_NUM}.yaml"
# PROJECTED_OLINE_VALUE_FILE = f"{DATA_DIR}dvoa/oline_delta.csv"

# Constants
# POSITIONS = ['QB', 'WR', 'RB', 'TE']
YEARS = ["2024", "2023", "2022", "2021"]

