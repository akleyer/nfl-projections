from typing import Dict, List, Tuple, Optional
from team import Team
from utils import safe_float, get_normalized_dvoa, win_pct_from_spread
from projection_calculations import calc_fantasy_pts_pass, calc_fantasy_pts_rec, calc_fantasy_pts_rush, calculate_win_percentage, calculate_projected_points
import config

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

    scaling_factor = 0.5
    unit_size = 10

    home_ml_bet_size = round(home_ml_edge * scaling_factor, 1)
    away_ml_bet_size = round(away_ml_edge * scaling_factor, 1)
    spread_bet_size = abs(round(spread_edge * scaling_factor, 1))
    total_bet_size = abs(round(total_edge * scaling_factor, 1))

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
            ml = betting_data['h_ml']
            ml_risk = home_ml_bet_size 
            ml_payout = round((ml_risk*100/-betting_data['h_ml']),0) if betting_data['h_ml'] < 0 else round(ml_risk * betting_data['h_ml']/100,0)
        else:
            rec_team = away_team.abbreviation
            edge = away_ml_edge
            ml = betting_data['a_ml']
            ml_risk = away_ml_bet_size
            ml_payout = round((ml_risk*100/-betting_data['a_ml']),0) if betting_data['a_ml'] < 0 else round(ml_risk * betting_data['a_ml']/100)
        risk_dollars = ml_risk * unit_size
        payout_dollars = ml_payout * unit_size
        recommendations.append(f"Moneyline: Consider {rec_team} ({ml}) | Risk {ml_risk}u (${risk_dollars}) to win {ml_payout} units (${payout_dollars})")
        analysis.append(f"- Moneyline on {rec_team}: The model projects a {edge:.1f}% edge, which is significant (>3%). This suggests value in the {rec_team} moneyline bet.")
    else:
        analysis.append("- Moneyline: No strong recommendation. The projected edge is not significant enough (<3%).")

    # Spread recommendation
    if abs(spread_edge) > 1.5:
        rec_team = f"{home_team.abbreviation} {betting_data['h_spread']}" if spread_edge > 0 else f"{away_team.abbreviation} {betting_data['a_spread']}"
        if payout_dollars:
            spread_dollars = unit_size * spread_bet_size
            spread_payout = round(spread_bet_size*100/110,1)
            spread_payout_dollars = unit_size * spread_payout
        recommendations.append(f"Spread: Consider {rec_team} | Risk {spread_bet_size}u (${spread_dollars}) to win {spread_payout}u (${spread_payout_dollars})")
        analysis.append(f"- Spread on {rec_team}: The model projects a {abs(spread_edge):.1f} point edge, which is significant (>1.5 points). This suggests value in this spread bet.")
    else:
        analysis.append("- Spread: No strong recommendation. The projected edge is not significant enough (<1.5 points).")

    # Total recommendation
    if abs(total_edge) > 3:
        rec = "Over" if total_edge > 0 else "Under"
        total_dollars = unit_size * total_bet_size
        total_payout = round(total_bet_size*100/110,1)
        total_payout_dollars = unit_size * total_payout
        recommendations.append(f"Total: Consider {rec} {betting_data['bet_total']} | Risk {total_bet_size}u (${total_dollars}) to win {total_payout}u (${total_payout_dollars})")
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