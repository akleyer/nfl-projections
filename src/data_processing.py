from typing import Dict, List, Tuple, Optional
from team import Team
from data_loader import load_all_position_data, load_csv_data, load_json_data
import config
import logging
logger = logging.getLogger(__name__)
from utils import get_impact_from_precipitation, get_passing_impact_from_wind, get_impact_from_temperature_delta, create_linear_function, safe_float, get_normalized_dvoa, win_pct_from_spread
from betting_analysis import calculate_betting_data, calculate_bet
from game_analysis import generate_game_analysis
from projection_calculations import calc_fantasy_pts_pass, calc_fantasy_pts_rec, calc_fantasy_pts_rush, calculate_win_percentage, calculate_projected_points




def format_normalized_dvoa(value):
    """Format normalized DVOA value, handling 'N/A' case."""
    if value == 'N/A':
        return 'N/A  '  # Pad with spaces to align with float format
    return f"{value:>4.1f}"




def load_and_process_data() -> Tuple[Dict, Dict, Dict, Dict, Dict, Dict, Dict, List]:
    """
    Load and process all necessary data for the NFL projection model.
    
    Returns:
        Tuple containing processed data for teams, DVOA, adjusted yards, play rates,
        home field advantage, average temperature, and matchups.
    """
    nfl_teams = load_all_position_data()
    def_pass_dvoa, def_rush_dvoa = load_csv_data(config.DVOA_TEAM_DEFENSE_FILE, config.process_dvoa_data)
    adjusted_rush_yards, adjusted_sack_rate = load_csv_data(config.DVOA_ADJUSTED_LINE_YARDS_FILE, config.process_dvoa_data_ol)
    play_rates = load_csv_data(config.PLAY_RATES_FILE, config.create_play_rate_entry)
    home_field_adv = load_csv_data(config.HOME_ADVANTAGE_FILE, config.process_home_field_adv)
    home_field_avg_tmp = load_csv_data(config.AVERAGE_TEMPERATURE_FILE, config.process_avg_temp)
    oline_delta = load_csv_data(config.PROJECTED_OLINE_VALUE_FILE, config.process_proj_oline)
    
    dvoa = {
        "Passing": {year: load_csv_data(f"../data/raw/dvoa/{year}/passing_dvoa.csv", config.process_dvoa_yearly)
                    for year in config.YEARS},
        "Rushing": {
            pos: {year: load_csv_data(f"../data/raw/dvoa/{year}/{pos.lower()}_rushing_dvoa.csv", config.process_dvoa_yearly)
                  for year in config.YEARS}
            for pos in ["RB", "QB", "WR"]
        },
        "Receiving": {
            pos: {year: load_csv_data(f"../data/raw/dvoa/{year}/{pos.lower()}_receiving_dvoa.csv", config.process_dvoa_yearly)
                  for year in config.YEARS}
            for pos in ["WR", "RB", "TE"]
        }
    }
    
    return (nfl_teams, def_pass_dvoa, def_rush_dvoa, adjusted_rush_yards, adjusted_sack_rate,
            play_rates, home_field_adv, home_field_avg_tmp, dvoa, oline_delta)

def process_matchup(matchup: Dict, nfl_teams: Dict, def_pass_dvoa: Dict, dvoa: Dict,
                    adjusted_rush_yards: Dict, adjusted_sack_rate: Dict, def_rush_dvoa: Dict,
                    play_rates: Dict, functions_dict: Dict, home_field_advantage: Dict,
                    average_home_temperature: Dict, oline_delta: Dict) -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Process a single matchup and calculate various statistics and projections
    """
    logger.info(f"Processing matchup: {matchup['home']} vs {matchup['away']}")

    
    # Calculate win percentages and betting data
    home_win_pct = calculate_win_percentage(away_projected_points - home_projected_points)
    away_win_pct = 100 - home_win_pct

    betting_data = calculate_betting_data(matchup, home_projected_points, away_projected_points, home_win_pct, away_win_pct)

    # Generate detailed game analysis
    game_analysis = generate_game_analysis(matchup, home_team, away_team, betting_data, functions_dict)

    # Prepare data for DataFrames
    df_data = prepare_df_data(matchup, home_team, away_team, home_offense_value, away_offense_value, 
                              home_projected_points, away_projected_points, home_win_pct, away_win_pct, betting_data)
    df2_data = prepare_df2_data(matchup, home_pass_delta, home_rush_delta, away_pass_delta, away_rush_delta)
    df3_data = prepare_df3_data(matchup, home_team, away_team)
    df4_data = prepare_df4_data(matchup, home_projected_points, away_projected_points)

    logger.info(f"Finished processing matchup: {matchup['home']} vs {matchup['away']}")
    return df_data, df2_data, df3_data, df4_data, game_analysis

def prepare_df_data(matchup: Dict, home_team: Team, away_team: Team, h_off: float, a_off: float,
                    h_pts: float, a_pts: float, home_win_pct: float, away_win_pct: float,
                    betting_data: Dict) -> Dict:
    """Prepare data for the main DataFrame."""
    return {
        "Home": matchup['home'],
        "Away": matchup['away'],
        "H_O": round(h_off, 1),
        "A_O": round(a_off, 1),
        "HP": round(h_pts),
        "AP": round(a_pts),
        "Spread": round(betting_data['spread'], 1),
        "H Win %": round(home_win_pct, 1),
        "A Win %": round(away_win_pct, 1),
        "H ML": betting_data['h_ml'],
        "A ML": betting_data['a_ml'],
        "~H Win %": round(betting_data['implied_h_win_pct'], 1),
        "~A Win %": round(betting_data['implied_a_win_pct'], 1),
        "~HD": round(betting_data['h_win_pct_delta'], 1),
        "~AD": round(betting_data['a_win_pct_delta'], 1),
        "H Spread": betting_data['h_spread'],
        "A Spread": betting_data['a_spread'],
        "~HSD": round(betting_data['h_spread_delta'], 1),
        "~ASD": round(betting_data['a_spread_delta'], 1),
        "PrjTotal": round(betting_data['proj_total'], 1),
        "Total": betting_data['bet_total'],
        "~TD": round(betting_data['total_delta'], 1),
        "O/U": "O" if betting_data['proj_total'] > betting_data['bet_total'] else "U",
        "ML Bet": calculate_bet("ML", betting_data['h_win_pct_delta'], home_win_pct, away_win_pct),
        "Spr Bet": calculate_bet("Spread", betting_data['h_spread_delta']),
        "Tot Bet": calculate_bet("Total", betting_data['total_delta'])
    }


def prepare_df2_data(matchup: Dict, hp_delta: float, hr_delta: float, ap_delta: float, ar_delta: float) -> Dict:
    """Prepare data for the second DataFrame."""
    return {
        "Home": matchup['home'],
        "Away": matchup['away'],
        "H Pass Adv": round(hp_delta, 1) * 10,
        "H Rush Adv": round(hr_delta, 1) * 10,
        "A Pass Adv": round(ap_delta, 1) * 10,
        "A Rush Adv": round(ar_delta, 1) * 10,
    }

def prepare_df3_data(matchup: Dict, home_team: Team, away_team: Team) -> List[Dict]:
    """Prepare data for the third DataFrame."""
    return [
        create_team_data_dict(matchup['home'], home_team),
        create_team_data_dict(matchup['away'], away_team)
    ]

def prepare_df4_data(matchup: Dict, h_pts: float, a_pts: float) -> Dict:
    """Prepare data for the fourth DataFrame."""
    return {
        "Home": matchup['home'],
        "HP": round(h_pts),
        "AP": round(a_pts),
        "Away": matchup['away'],
        "Total": round(h_pts + a_pts, 1)
    }