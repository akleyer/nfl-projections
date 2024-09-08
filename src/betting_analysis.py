from typing import Dict, List, Tuple, Optional


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
def calculate_implied_win_percentage(money_line: int) -> float:
    """Calculate implied win percentage from money line odds."""
    if money_line < 0:
        return (-1 * money_line) / ((-1 * money_line) + 100) * 100
    else:
        return 100 / (money_line + 100) * 100
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