def calculate_projected_points(off_value: float) -> float:
    """Calculate projected points based on offensive value."""
    return 22.5 + (1.23 * off_value) + (0.0692 * (off_value ** 2)) + (0.0242 * (off_value ** 3)) + (0.000665 * (off_value ** 4))


def calculate_win_percentage(point_difference: float) -> float:
    """Calculate win percentage based on point difference."""
    win_pct = (-0.0303 * point_difference + 0.5) * 100
    return max(min(win_pct, 99.9), 0.1)


def calc_fantasy_pts_pass(yds, td, intc, fd):
    return ((yds/25) + (td*4) + (fd/5)) - (intc)
    
def calc_fantasy_pts_rush(yds, td, fd):
    return (yds/10) + (td*6) + (fd/2)

def calc_fantasy_pts_rec(rec, yds, td, fd):
    return (rec/2) + (yds/10) + (td*6) + (fd*0.3)

def calc_special_teams(yds, td):
    return (yds/25) + (td*6)