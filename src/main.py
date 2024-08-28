from typing import Dict, List, Tuple, Optional
from data_loader import load_all_position_data, load_csv_data, load_json_data
from team import Team
from utils import get_impact_from_precipitation, get_passing_impact_from_wind, get_impact_from_temperature_delta, create_linear_function
import config
import pandas as pd
import logging
import pprint as pp


# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
# Set up logging
logger = logging.getLogger(__name__)

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
    matchups = load_json_data(config.MATCHUPS_FILE)
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
            play_rates, home_field_adv, home_field_avg_tmp, dvoa, matchups, oline_delta)

def create_function_dict() -> Dict:
    """
    Create a dictionary of linear functions used in the projection model.
    """
    return {
        "Pass": create_linear_function(-42.5, 0, 40, 10),
        "Rush": create_linear_function(-12.5, 0, 25, 10),
        "Rec": create_linear_function(-10, 0, 17.5, 10),
        "OLPF": create_linear_function(15, 0, 5, 10),
        "OLRF": create_linear_function(3.5, 0, 5, 10),
        "DPF": create_linear_function(.35, 0, -.30, 10),
        "DRF": create_linear_function(.07, 0, -.20, 10)
    }

def safe_float(value, default=0.0):
    """Safely convert a value to float, returning a default if conversion fails."""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except ValueError:
        return default

def format_dvoa(dvoa_value):
    """Format DVOA value, handling 'N/A' case."""
    if dvoa_value == 'N/A':
        return 'N/A'  # Pad with spaces to align with float format
    return f"{dvoa_value:>6.1f}%"

def get_normalized_dvoa(num, dvoa_value, linear_func):
    """Get normalized DVOA value using the provided linear function."""
    if dvoa_value == 'N/A':
        return 'N/A'
    try:
        return round(num * linear_func(float(dvoa_value)),1)
    except ValueError:
        return 'N/A'

def format_normalized_dvoa(value):
    """Format normalized DVOA value, handling 'N/A' case."""
    if value == 'N/A':
        return 'N/A  '  # Pad with spaces to align with float format
    return f"{value:>4.1f}"

def win_pct_from_spread(in_spread: float) -> float:
    """
    Calculate the implied win percentage from a point spread.
    
    Args:
        spread (float): The point spread (negative for favorite, positive for underdog)
    
    Returns:
        float: The implied win percentage
    """
    spread = -1*in_spread if in_spread < 0 else 1
    win_pct = (0.00187033*(spread**4))-(0.0613893*(spread**3))+(0.568552*(spread**2))+(1.96375*spread) + 49.9791
    if in_spread < 0:
        return win_pct
    else:
        return 100 - win_pct

def calc_fantasy_pts_pass(yds, td, intc, fd):
    return ((yds/25) + (td*4) + (fd/5)) - (intc)
    
def calc_fantasy_pts_rush(yds, td, fd):
    return (yds/10) + (td*6) + (fd/2)

def calc_fantasy_pts_rec(rec, yds, td, fd):
    return (rec/2) + (yds/10) + (td*6) + (fd*0.3)

def calc_special_teams(yds, td):
    return (yds/25) + (td*6)


def generate_game_analysis(matchup: Dict, home_team: Team, away_team: Team, betting_data: Dict, functions_dict: Dict) -> str:
    """
    Generate a detailed game analysis for a single matchup with formatted stats including DVOA
    """
    analysis = []

    # Game details
    analysis.append(f"Game Analysis: {home_team.abbreviation} vs {away_team.abbreviation}")
    analysis.append(f"Venue: {matchup['home']} ({'Dome' if matchup.get('dome') == 'yes' else 'Outdoor'})")
    analysis.append(f"Field: {matchup.get('field', 'Unknown')}")
    analysis.append(f"Weather: {'N/A (Dome)' if matchup.get('dome') == 'yes' else f'Temp: {matchup.get('temp', 'N/A')}°F, Wind: {matchup.get('wind', 'N/A')} mph, Precipitation: {matchup.get('weather', 'N/A')}%'}")

    # Win probabilities
    analysis.append(f"\nWin Probabilities:")
    analysis.append(f"{home_team.abbreviation}: {betting_data['home_win_pct']:.1f}%")
    analysis.append(f"{away_team.abbreviation}: {betting_data['away_win_pct']:.1f}%")

    for team, name in [(home_team, "Home"), (away_team, "Away")]:
        analysis.append(f"\n{name} Team: {team.abbreviation}")
        analysis.append(f"Projected Offensive Plays: {team.get_offensive_plays_per_60():.1f}")
        analysis.append(f"Pass/Rush Split: {team.get_offensive_pass_rate():.1f}% / {team.get_offensive_rush_rate():.1f}%")
        
        # Full lineup
        analysis.append("\nProjected Lineup:")
        for pos in ['QB', 'RB', 'WR', 'TE']:
            if pos in team.team_data:
                analysis.append(f"  {pos}:")
                for player, player_data in sorted(team.team_data[pos], key=lambda x: safe_float(x[1].get('fpts_ppr', 0)), reverse=True):
                    if pos == 'QB':
                        pass_att = safe_float(player_data.get('pass_att', 0))
                        pass_yds = safe_float(player_data.get('pass_yds', 0))
                        pass_tds = safe_float(player_data.get('pass_td', 0))
                        pass_int = safe_float(player_data.get('pass_int', 0))
                        pass_fds = safe_float(player_data.get('PaFD', 0)) / 17
                        rush_att = safe_float(player_data.get('rush_att', 0))
                        rush_yds = safe_float(player_data.get('rush_yds', 0))
                        rush_fds = safe_float(player_data.get('RuFD', 0)) / 17
                        rush_tds = safe_float(player_data.get('rush_td', 0))
                        fntsy_pts_pass = calc_fantasy_pts_pass(pass_yds, pass_tds, pass_int, pass_fds)
                        fntsy_pts_rush = calc_fantasy_pts_rush(rush_yds, rush_tds, rush_fds)
                        tot_fntsy_pts = round(fntsy_pts_pass + fntsy_pts_rush, 2)
                        mapped_player = config.get_dvoa_player_map(player)
                        pass_dvoa = safe_float(team.pass_dvoa.get(mapped_player, 0))
                        rush_dvoa = safe_float(team.qb_rush_dvoa.get(mapped_player, 0))
                        norm_pass_dvoa = get_normalized_dvoa(pass_att, pass_dvoa, functions_dict['Pass'])
                        norm_rush_dvoa = get_normalized_dvoa(rush_att, rush_dvoa, functions_dict['Rush'])
                        if pass_att > 3 or rush_att > 0.5:
                            analysis.append(f"{' '*5}{player} ({tot_fntsy_pts})")
                            analysis.append(f"{' '*7}[Pass] Att: {pass_att:>4.1f} | Yds: {pass_yds:>5.1f} | TDs: {pass_tds:>4.1f} | FD: {pass_fds:>4.1f} | DVOA: {pass_dvoa:>4.1f} | Norm: {norm_pass_dvoa:>5.1f}")
                            analysis.append(f"{' '*7}[Rush] Att: {rush_att:>4.1f} | Yds: {rush_yds:>5.1f} | TDs: {rush_tds:>4.1f} | FD: {rush_fds:>4.1f} | DVOA: {rush_dvoa:>4.1f} | Norm: {norm_rush_dvoa:>5.1f}")
                    elif pos == 'RB':
                        rush_att = safe_float(player_data.get('rush_att', 0))
                        rush_yds = safe_float(player_data.get('rush_yds', 0))
                        rush_tds = safe_float(player_data.get('rush_td', 0))
                        rush_fds = safe_float(player_data.get('RuFD',     0)) / 17
                        rec_rec = safe_float(player_data.get('rec', 0))
                        rec_tgt = safe_float(player_data.get('rec_tgt', 0))
                        rec_yds = safe_float(player_data.get('rec_yds', 0))
                        rec_tds = safe_float(player_data.get('rec_td', 0))
                        rec_fds = safe_float(player_data.get('ReFD', 0)) / 17
                        rush_dvoa = safe_float(team.rb_rush_dvoa.get(player, 0))
                        rec_dvoa = safe_float(team.rb_rec_dvoa.get(player, 0))
                        fntsy_pts_rush = calc_fantasy_pts_rush(rush_yds, rush_tds, rush_fds)
                        fntsy_pts_rec = calc_fantasy_pts_rec(rec_rec, rec_yds, rec_tds, rec_fds)
                        tot_fntsy_pts = round(fntsy_pts_rush + fntsy_pts_rec, 2)
                        norm_rec_dvoa = get_normalized_dvoa(rec_tgt, rec_dvoa, functions_dict['Rec'])
                        norm_rush_dvoa = get_normalized_dvoa(rush_att, rush_dvoa, functions_dict['Rush'])
                        if rush_att > 0.5 or rec_tgt > 0.1:
                            analysis.append(f"{' '*5}{player} ({tot_fntsy_pts})")
                            analysis.append(f"{' '*7}[Rush] Att: {rush_att:>4.1f} |{' '*11}| Yds: {rush_yds:>5.1f} | TDs: {rush_tds:>4.1f} | FD: {rush_fds:>4.1f} | DVOA: {rush_dvoa:>4.1f} | Norm: {norm_rush_dvoa:>5.1f}")
                            analysis.append(f"{' '*7}[Rec]  Tgt: {rec_tgt:>4.1f} | Rec: {rec_rec:>4.1f} | Yds: {rec_yds:>5.1f} | TDs: {rec_tds:>4.1f} | FD: {rec_fds:>4.1f} | DVOA: {rec_dvoa:>4.1f} | Norm: {norm_rec_dvoa:>5.1f}")
                            analysis.append("")
                    elif pos == 'WR':
                        rush_att = safe_float(player_data.get('rush_att', 0))
                        rush_yds = safe_float(player_data.get('rush_yds', 0))
                        rush_tds = safe_float(player_data.get('rush_td', 0))
                        rush_fds = safe_float(player_data.get('RuFD',     0)) / 17
                        rec_rec = safe_float(player_data.get('rec', 0))
                        rec_tgt = safe_float(player_data.get('rec_tgt', 0))
                        rec_yds = safe_float(player_data.get('rec_yds', 0))
                        rec_tds = safe_float(player_data.get('rec_td', 0))
                        rec_fds = safe_float(player_data.get('ReFD', 0)) / 17
                        rush_dvoa = safe_float(team.rb_rush_dvoa.get(player, 0))
                        rec_dvoa = safe_float(team.rb_rec_dvoa.get(player, 0))
                        fntsy_pts_rush = calc_fantasy_pts_rush(rush_yds, rush_tds, rush_fds)
                        fntsy_pts_rec = calc_fantasy_pts_rec(rec_rec, rec_yds, rec_tds, rec_fds)
                        tot_fntsy_pts = round(fntsy_pts_rush + fntsy_pts_rec, 2)
                        norm_rec_dvoa = get_normalized_dvoa(rec_tgt, rec_dvoa, functions_dict['Rec'])
                        norm_rush_dvoa = get_normalized_dvoa(rush_att, rush_dvoa, functions_dict['Rush'])
                        if rush_att > 0.5 or rec_tgt > 0.1:
                            analysis.append(f"{' '*5}{player} ({tot_fntsy_pts})")
                            analysis.append(f"{' '*7}[Rec]  Tgt: {rec_tgt:>4.1f} | Rec: {rec_rec:>4.1f} | Yds: {rec_yds:>5.1f} | TDs: {rec_tds:>4.1f} | FD: {rec_fds:>4.1f} | DVOA: {rec_dvoa:>4.1f} | Norm: {norm_rec_dvoa:>5.1f}")
                            analysis.append(f"{' '*7}[Rush] Att: {rush_att:>4.1f} |{' '*11}| Yds: {rush_yds:>5.1f} | TDs: {rush_tds:>4.1f} | FD: {rush_fds:>4.1f} | DVOA: {rush_dvoa:>4.1f} | Norm: {norm_rush_dvoa:>5.1f}")
                            analysis.append("")
                    else:  # TE
                        rec_rec = safe_float(player_data.get('rec', 0))
                        rec_tgt = safe_float(player_data.get('rec_tgt', 0))
                        rec_yds = safe_float(player_data.get('rec_yds', 0))
                        rec_tds = safe_float(player_data.get('rec_td', 0))
                        rec_fds = safe_float(player_data.get('ReFD', 0)) / 17
                        rec_dvoa = safe_float(team.rb_rec_dvoa.get(player, 0))
                        fntsy_pts_rec = calc_fantasy_pts_rec(rec_rec, rec_yds, rec_tds, rec_fds)
                        tot_fntsy_pts = round(fntsy_pts_rec, 2)
                        norm_rec_dvoa = get_normalized_dvoa(rec_tgt, rec_dvoa, functions_dict['Rec'])
                        if rec_tgt > 0.1:
                            analysis.append(f"{' '*5}{player} ({tot_fntsy_pts})")
                            analysis.append(f"{' '*7}[Rec]  Tgt: {rec_tgt:>4.1f} | Rec: {rec_rec:>4.1f} | Yds: {rec_yds:>5.1f} | TDs: {rec_tds:>4.1f} | FD: {rec_fds:>4.1f} | DVOA: {rec_dvoa:>4.1f} | Norm: {norm_rec_dvoa:>5.1f}")
                            analysis.append("")                    

    # Betting analysis
    analysis.append("\nBetting Analysis:")
    analysis.append(f"Projected Score: {home_team.abbreviation} {betting_data['h_pts']:.1f} - {away_team.abbreviation} {betting_data['a_pts']:.1f}")
    analysis.append(f"Spread: {home_team.abbreviation} {betting_data['h_spread']} ({betting_data['h_ml']})")
    analysis.append(f"Total: {betting_data['bet_total']} (O/U)")
    
    # Calculate implied win percentages from the spread
    implied_home_win_pct = win_pct_from_spread(betting_data['h_spread'])
    implied_away_win_pct = 100 - implied_home_win_pct

    # Calculate edges
    home_ml_edge = betting_data['home_win_pct'] - implied_home_win_pct
    away_ml_edge = betting_data['away_win_pct'] - implied_away_win_pct
    spread_edge = betting_data['h_spread_delta']
    total_edge = betting_data['total_delta']

    # Display detailed edge calculations
    analysis.append("\nDetailed Edge Calculations:")
    
    analysis.append(f"{home_team.abbreviation} Moneyline Edge:")
    analysis.append(f"  Projected Win%: {betting_data['home_win_pct']:.1f}%")
    analysis.append(f"  Implied Win% from Spread: {implied_home_win_pct:.1f}%")
    analysis.append(f"  Edge: {home_ml_edge:.1f}% ({home_team.abbreviation} {'overvalued' if home_ml_edge < 0 else 'undervalued'})")

    analysis.append(f"\n{away_team.abbreviation} Moneyline Edge:")
    analysis.append(f"  Projected Win%: {betting_data['away_win_pct']:.1f}%")
    analysis.append(f"  Implied Win% from Spread: {implied_away_win_pct:.1f}%")
    analysis.append(f"  Edge: {away_ml_edge:.1f}% ({away_team.abbreviation} {'overvalued' if away_ml_edge < 0 else 'undervalued'})")

    analysis.append(f"\nSpread Edge:")
    analysis.append(f"  Projected Spread: {betting_data['spread']:.1f}")
    analysis.append(f"  Actual Spread: {betting_data['h_spread']}")
    analysis.append(f"  Edge: {spread_edge:.1f} points ({'favoring ' + home_team.abbreviation if spread_edge > 0 else 'favoring ' + away_team.abbreviation})")

    analysis.append(f"\nTotal Edge:")
    analysis.append(f"  Projected Total: {betting_data['proj_total']:.1f}")
    analysis.append(f"  Actual Total: {betting_data['bet_total']}")
    analysis.append(f"  Edge: {total_edge:.1f} points ({'Over' if total_edge > 0 else 'Under'})")

    # Betting recommendations with explanations
    analysis.append("\nBetting Recommendations:")
    recommendations = []

    # Moneyline recommendation
    if abs(home_ml_edge) > 3 or abs(away_ml_edge) > 3:
        if home_ml_edge > away_ml_edge:
            rec_team = home_team.abbreviation
            edge = home_ml_edge
        else:
            rec_team = away_team.abbreviation
            edge = away_ml_edge
        recommendations.append(f"Moneyline: Consider {rec_team}")
        analysis.append(f"- Moneyline on {rec_team}: The model projects a {edge:.1f}% edge, which is significant (>3%). This suggests value in the {rec_team} moneyline bet.")
    else:
        analysis.append("- Moneyline: No strong recommendation. The projected edge is not significant enough (<3%).")

    # Spread recommendation
    if abs(spread_edge) > 1.5:
        rec_team = f"{home_team.abbreviation} {betting_data['h_spread']}" if spread_edge > 0 else f"{away_team.abbreviation} {betting_data['a_spread']}"
        recommendations.append(f"Spread: Consider {rec_team}")
        analysis.append(f"- Spread on {rec_team}: The model projects a {abs(spread_edge):.1f} point edge, which is significant (>1.5 points). This suggests value in this spread bet.")
    else:
        analysis.append("- Spread: No strong recommendation. The projected edge is not significant enough (<1.5 points).")

    # Total recommendation
    if abs(total_edge) > 3:
        rec = "Over" if total_edge > 0 else "Under"
        recommendations.append(f"Total: Consider {rec}")
        analysis.append(f"- Total {rec}: The model projects the total to be {abs(total_edge):.1f} points {'higher' if rec == 'Over' else 'lower'} than the line, which is significant (>3 points). This suggests value in the {rec} bet.")
    else:
        analysis.append("- Total: No strong recommendation. The projected difference from the line is not significant enough (<3 points).")

    if recommendations:
        analysis.append("\nSummary of Recommendations:")
        for rec in recommendations:
            analysis.append(f"- {rec}")
    else:
        analysis.append("\nNo strong betting recommendations for this game based on the model's projections.")

    return "\n".join(analysis)

def process_matchup(matchup: Dict, nfl_teams: Dict, def_pass_dvoa: Dict, dvoa: Dict,
                    adjusted_rush_yards: Dict, adjusted_sack_rate: Dict, def_rush_dvoa: Dict,
                    play_rates: Dict, functions_dict: Dict, home_field_advantage: Dict,
                    average_home_temperature: Dict, oline_delta: Dict) -> Tuple[Dict, Dict, Dict, Dict]:
    """
    Process a single matchup and calculate various statistics and projections
    """
    logger.info(f"Processing matchup: {matchup['home']} vs {matchup['away']}")

    home_team = Team(matchup['home'], nfl_teams[matchup['home']], def_pass_dvoa, dvoa,
                     adjusted_rush_yards, adjusted_sack_rate, def_rush_dvoa, play_rates, functions_dict, oline_delta)
    away_team = Team(matchup['away'], nfl_teams[matchup['away']], def_pass_dvoa, dvoa,
                     adjusted_rush_yards, adjusted_sack_rate, def_rush_dvoa, play_rates, functions_dict, oline_delta)

    # Calculate various metrics for both teams
    home_pass_offense = home_team.get_offensive_pass_value()
    away_pass_offense = away_team.get_offensive_pass_value()
    home_pass_defense = home_team.get_defensive_pass_value()
    away_pass_defense = away_team.get_defensive_pass_value()
    home_rush_offense = home_team.get_offensive_rush_value()
    away_rush_offense = away_team.get_offensive_rush_value()
    home_rush_defense = home_team.get_defensive_rush_value()
    away_rush_defense = away_team.get_defensive_rush_value()
    
    # Apply weather effects
    precipitation_impact = get_impact_from_precipitation(matchup.get("weather"))
    wind_impact = get_passing_impact_from_wind(matchup.get("wind"))

    home_pass_offense -= home_pass_offense * precipitation_impact
    away_pass_offense -= away_pass_offense * precipitation_impact

    # Calculate offensive and defensive deltas
    home_pass_delta = home_pass_offense - away_pass_defense
    home_rush_delta = home_rush_offense - away_rush_defense
    away_pass_delta = away_pass_offense - home_pass_defense
    away_rush_delta = away_rush_offense - home_rush_defense

    # Calculate pass and rush rate deltas
    home_pass_rate_delta = (home_team.get_offensive_pass_rate() + away_team.get_defensive_pass_rate()) / 2
    home_rush_rate_delta = (home_team.get_offensive_rush_rate() + away_team.get_defensive_rush_rate()) / 2
    away_pass_rate_delta = (away_team.get_offensive_pass_rate() + home_team.get_defensive_pass_rate()) / 2
    away_rush_rate_delta = (away_team.get_offensive_rush_rate() + home_team.get_defensive_rush_rate()) / 2

    # Calculate offensive values
    home_offense_value = ((home_pass_delta * home_pass_rate_delta) + (home_rush_delta * home_rush_rate_delta)) / 100
    away_offense_value = ((away_pass_delta * away_pass_rate_delta) + (away_rush_delta * away_rush_rate_delta)) / 100

    # Calculate projected points
    home_projected_points = calculate_projected_points(home_offense_value)
    away_projected_points = calculate_projected_points(away_offense_value)

    # Apply weather and temperature effects
    game_temp = matchup.get("temp")
    if game_temp is not None:
        home_temp_delta = abs(average_home_temperature[matchup['home']] - game_temp)
        away_temp_delta = abs(average_home_temperature[matchup['away']] - game_temp)

        home_temp_effect = get_impact_from_temperature_delta(home_temp_delta)
        away_temp_effect = get_impact_from_temperature_delta(away_temp_delta)

        home_projected_points = (home_projected_points * wind_impact) * home_temp_effect
        away_projected_points = (away_projected_points * wind_impact) * away_temp_effect
    else:
        home_projected_points *= wind_impact
        away_projected_points *= wind_impact
    
    # Apply home field advantage
    home_advantage_offense, home_advantage_defense = home_field_advantage[matchup['home']]
    away_advantage_offense, away_advantage_defense = home_field_advantage[matchup['away']]

    home_projected_points *= (1 + home_advantage_offense + away_advantage_defense)
    away_projected_points *= (1 + (away_advantage_offense * -1) + (home_advantage_defense * -1))

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

def calculate_projected_points(off_value: float) -> float:
    """Calculate projected points based on offensive value."""
    return 22.5 + (1.23 * off_value) + (0.0692 * (off_value ** 2)) + (0.0242 * (off_value ** 3)) + (0.000665 * (off_value ** 4))

def calculate_win_percentage(point_difference: float) -> float:
    """Calculate win percentage based on point difference."""
    win_pct = (-0.0303 * point_difference + 0.5) * 100
    return max(min(win_pct, 99.9), 0.1)

def calculate_betting_data(matchup: Dict, h_pts: float, a_pts: float, home_win_pct: float, away_win_pct: float) -> Dict:
    """Calculate various betting-related data for the matchup."""
    h_ml, a_ml = matchup['betting_lines']['home_ml'], matchup['betting_lines']['away_ml']
    h_spread, a_spread = matchup['betting_lines']['home_spread'], matchup['betting_lines']['away_spread']
    bet_total = matchup['betting_lines']['total']

    proj_total = h_pts + a_pts
    spread = a_pts - h_pts

    implied_h_win_pct = calculate_implied_win_percentage(h_ml)
    implied_a_win_pct = calculate_implied_win_percentage(a_ml)

    h_win_pct_delta = home_win_pct - implied_h_win_pct
    a_win_pct_delta = away_win_pct - implied_a_win_pct

    h_spread_delta = h_spread - spread
    a_spread_delta = a_spread + spread

    total_delta = proj_total - bet_total

    return {
        'h_ml': h_ml, 'a_ml': a_ml, 'h_spread': h_spread, 'a_spread': a_spread,
        'bet_total': bet_total, 'proj_total': proj_total, 'spread': spread,
        'implied_h_win_pct': implied_h_win_pct, 'implied_a_win_pct': implied_a_win_pct,
        'h_win_pct_delta': h_win_pct_delta, 'a_win_pct_delta': a_win_pct_delta,
        'h_spread_delta': h_spread_delta, 'a_spread_delta': a_spread_delta,
        'total_delta': total_delta, 'h_pts': h_pts, 'a_pts': a_pts,
        'home_win_pct': home_win_pct, 'away_win_pct': away_win_pct  # Added these two lines
    }

def calculate_implied_win_percentage(money_line: int) -> float:
    """Calculate implied win percentage from money line odds."""
    if money_line < 0:
        return (-1 * money_line) / ((-1 * money_line) + 100) * 100
    else:
        return 100 / (money_line + 100) * 100

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

def create_team_data_dict(team_name: str, team: Team) -> Dict:
    """Create a dictionary of team data for DataFrame 3."""
    return {
        "Team": team_name,
        "QB DVOA": round(team.generate_qb_value(), 1),
        "QB Val": round(team.get_qb_value(), 1),
        "Rush DVOA": round(team.generate_rushing_value(), 1),
        "Rush Val": round(team.get_rushing_value(), 1),
        "Rec DVOA": round(team.generate_receiving_value(), 1),
        "Rec Val": round(team.get_receiving_value(), 1),
        "OL Pass Val": round(team.get_offensive_line_pass_value(), 1),
        "OL Rush Val": round(team.get_offensive_line_rush_value(), 1),
        "Off Pass Val": round(team.get_offensive_pass_value(), 1),
        "Off Rush Val": round(team.get_offensive_rush_value(), 1),
        "Def Pass Val": round(team.get_defensive_pass_value(), 1),
        "Def Rush Val": round(team.get_defensive_rush_value(), 1)
    }

def prepare_df4_data(matchup: Dict, h_pts: float, a_pts: float) -> Dict:
    """Prepare data for the fourth DataFrame."""
    return {
        "Home": matchup['home'],
        "HP": round(h_pts),
        "AP": round(a_pts),
        "Away": matchup['away'],
        "Total": round(h_pts + a_pts, 1)
    }

def calculate_bet(bet_type: str, delta: float, home_win_pct: float = 0, away_win_pct: float = 0) -> str:
    """Calculate bet recommendation based on delta."""
    if bet_type == "ML":
        if delta > 3:
            return f"H: {5 * round(((delta / 20) * (home_win_pct / 100)) * 100)}"
        elif delta < -3:
            return f"A: {5 * round(((-delta / 20) * (away_win_pct / 100)) * 100)}"
    elif bet_type == "Spread":
        if abs(delta) > 1.5:
            side = "H" if delta > 0 else "A"
            return f"{side}: {5 * round(abs(delta) * 7.5)}"
    elif bet_type == "Total" and abs(delta) >= 3:
        return f"{5 * round(abs(delta) * 15 / 5)}"
    return "~"

def main():
    """Main function to run the NFL projection model."""
    # Load and process all necessary data
    (nfl_teams, def_pass_dvoa, def_rush_dvoa, adjusted_rush_yards, adjusted_sack_rate,
     play_rates, home_field_adv, home_field_avg_tmp, dvoa, matchups, oline_delta) = load_and_process_data()

    # Create function dictionary
    functions_dict = create_function_dict()

    # Initialize lists to store data for DataFrames
    data_for_df = []
    data_for_df_2 = []
    data_for_df_3 = []
    data_for_df_4 = []
    game_analyses = []

    # Process each matchup
    for matchup in matchups:
        df_data, df2_data, df3_data, df4_data, game_analysis = process_matchup(
            matchup, nfl_teams, def_pass_dvoa, dvoa, adjusted_rush_yards, adjusted_sack_rate,
            def_rush_dvoa, play_rates, functions_dict, home_field_adv, home_field_avg_tmp, oline_delta
        )
        
        data_for_df.append(df_data)
        data_for_df_2.append(df2_data)
        data_for_df_3.extend(df3_data)
        data_for_df_4.append(df4_data)
        game_analyses.append(game_analysis)

    # Create DataFrames
    df = pd.DataFrame(data_for_df)
    df2 = pd.DataFrame(data_for_df_2)
    df3 = pd.DataFrame(data_for_df_3)
    df4 = pd.DataFrame(data_for_df_4)

    # Print detailed game analyses
    print("\nDetailed Game Analyses:")
    for analysis in game_analyses:
        print("\n" + "="*50)
        print(analysis)
        print("="*50)

    # Display results
    print("\nDataFrame 1:")
    print(df.to_string(index=False))
    print("\nDataFrame 2:")
    print(df2.to_string(index=False))
    print("\nDataFrame 3:")
    print(df3.to_string(index=False))
    print("\nDataFrame 4:")
    print(df4.to_string(index=False))

if __name__ == "__main__":
    main()