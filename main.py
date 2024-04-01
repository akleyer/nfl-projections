#!/usr/bin/env python3

import csv
import json
import pandas as pd


def load_csv_data(file_path, process_row):
    """
    Load data from a CSV file and apply a processing function to it.

    Args:
        file_path (str): The path to the CSV file.
        process_row (function): A function to process each row of the CSV data.

    Returns:
        Any: The result of applying the processing function to the data.
    """
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        return process_row(reader)


def load_json_data(file_path):
    """
    Load JSON data from a file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data as a dictionary.
    """
    with open(file_path, 'r') as file:
        return json.load(file)


def process_projections(reader):
    """
    Process projection data from a CSV reader.

    Args:
        reader (csv.reader): CSV reader object containing projection data.

    Returns:
        dict: A dictionary containing processed projection data.
    """
    team_db = {}
    for row in reader:
        if row[3] not in ['FB', 'K', 'DST']:
            team_db.setdefault(row[2], {"QB": [], "WR": [], "RB": [], "TE": []})[row[3]].append(
                (row[1], row[11], row[14]))
    return team_db


def process_dvoa_data(reader, pass_col, rush_col):
    """
    Process DVOA (Defense-adjusted Value Over Average) data from a CSV reader.

    Args:
        reader (csv.reader): CSV reader object containing DVOA data.
        pass_col (int): Column index for pass DVOA data.
        rush_col (int): Column index for rush DVOA data.

    Returns:
        tuple: A tuple containing pass DVOA and rush DVOA data as dictionaries.
    """
    pass_dvoa, rush_dvoa = {}, {}
    for row in reader:
        pass_dvoa[row[0]] = float(row[pass_col])
        rush_dvoa[row[0]] = float(row[rush_col])
    return pass_dvoa, rush_dvoa


def get_weighted_dvoa(dvoa_tmp):
    """
    Calculate weighted DVOA (Defense-adjusted Value Over Average) for players.

    Args:
        dvoa_tmp (dict): A dictionary containing DVOA data for players, organized by year.

    Returns:
        dict: A dictionary containing weighted DVOA values for players.
    """
    final_dvoa = {}
    final_dvoa_tracker = {}
    years = ["2023_playoffs", "2023", "2022", "2021", "2020"]

    weight_factors = [1, 2, 4, 8, 16]  # Corresponding weight factors for each year

    for year, players in dvoa_tmp.items():
        for player, stats in players.items():
            dvoa_val, num = stats

            if player not in final_dvoa_tracker:
                final_dvoa_tracker[player] = [0, 0]

            for i, target_year in enumerate(years):
                if year == target_year:
                    weighted_dvoa = dvoa_val * (num / weight_factors[i])
                    final_dvoa_tracker[player][0] += weighted_dvoa
                    final_dvoa_tracker[player][1] += (num / weight_factors[i])

    for player, values in final_dvoa_tracker.items():
        weighted_dvoa, num = values
        final_dvoa[player] = weighted_dvoa / num

    return final_dvoa


def _calculate_total_dvoa(players, dvoa_dict, total_dvoa, total, att_or_targets_index):
    """
    Calculate the total DVOA (Defense-adjusted Value Over Average) for a group of players.

    Args:
        players (list): A list of player data, where each player is represented as a list.
        dvoa_dict (dict): A dictionary containing DVOA values for players.
        total_dvoa (float): The running total of DVOA values.
        total (float): The running total of the attribute (e.g., attempts or targets) values.
        att_or_targets_index (int): The index of the attribute (e.g., attempts or targets) in the player data.

    Returns:
        tuple: A tuple containing the total DVOA and the total attribute value.
    """
    for player in players:
        name = player[0]
        att_or_targets = player[att_or_targets_index]
        player_dvoa = dvoa_dict.get(name, 0.0)
        total_dvoa += float(att_or_targets) * player_dvoa
        total += float(att_or_targets)
    return total_dvoa, total


class Team:
    def __init__(self,
                 team_abbreviation,
                 team_data,
                 def_pass,
                 dvoa_obj,
                 ary,
                 asr,
                 def_rush,
                 pr,
                 functions
                 ):
        """
        Initialize a Team object.

        Args:
            team_abbreviation (str): The abbreviation of the team.
            team_data (dict): Data related to the team's players.
            def_pass (dict): Defensive passing data.
            dvoa_obj (dict): DVOA data.
            ary (dict): Offensive line rushing data.
            asr (dict): Offensive line passing data.
            def_rush (dict): Defensive rushing data.
            pr (dict): Play rate data.
            functions (dict): Functions for calculating values.
        """
        self.abbreviation = team_abbreviation
        self.team_data = team_data
        self.dvoa = dvoa_obj
        self.pass_dvoa = get_weighted_dvoa(dvoa_obj["Passing"])
        self.rb_rush_dvoa = get_weighted_dvoa(dvoa_obj["Rushing"]["RB"])
        self.qb_rush_dvoa = get_weighted_dvoa(dvoa_obj["Rushing"]["QB"])
        self.wr_rush_dvoa = get_weighted_dvoa(dvoa_obj["Rushing"]["WR"])
        self.te_rec_dvoa = get_weighted_dvoa(dvoa_obj["Receiving"]["TE"])
        self.rb_rec_dvoa = get_weighted_dvoa(dvoa_obj["Receiving"]["RB"])
        self.wr_rec_dvoa = get_weighted_dvoa(dvoa_obj["Receiving"]["WR"])
        self.ol_pass = asr
        self.ol_rush = ary
        self.def_pass = def_pass
        self.def_rush = def_rush
        self.play_rates = pr
        self.qb_func = functions["Pass"]
        self.rush_func = functions["Rush"]
        self.rec_func = functions["Rec"]
        self.ol_pass_func = functions["OLPF"]
        self.ol_rush_func = functions["OLRF"]
        self.dpf = functions["DPF"]
        self.drf = functions["DRF"]

    def print_lineup(self):
        print(self.abbreviation)
        for pos, players in self.team_data.items():
            for player in players:
                player_name, att, targets = player
                if float(att) or float(targets):
                    print(f"{pos:<5}{player_name:<15}")
        # print(self.team_data)

    def generate_qb_value(self):
        """
        Generate the quarterback value based on DVOA.

        Returns:
            float: The calculated quarterback value.
        """
        return self.pass_dvoa[self.team_data["QB"][0][0]]

    def get_qb_value(self):
        """
        Get the quarterback value considering a threshold.

        Returns:
            float: The quarterback value.
        """
        dvoa_tmp = self.generate_qb_value()
        qb_val = self.qb_func(dvoa_tmp)
        return max(0, qb_val) if qb_val <= -5 else qb_val

    def get_ol_pass_value(self):
        """
        Get the offensive line pass value.

        Returns:
            float: The offensive line pass value.
        """
        resting_starters = []
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        return self.ol_pass_func(self.ol_pass[self.abbreviation]) * multiplier

    def get_ol_rush_value(self):
        """
        Get the offensive line rush value.

        Returns:
            float: The offensive line rush value.
        """
        resting_starters = []
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        return self.ol_rush_func(self.ol_rush[self.abbreviation]) * multiplier

    def get_def_pass_value(self):
        """
        Get the defensive pass value with potential multiplier.

        Returns:
            float: The defensive pass value.
        """
        resting_starters = []
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        return self.dpf(self.def_pass[self.abbreviation]) * multiplier

    def get_def_rush_value(self):
        """
        Get the defensive rush value with potential multiplier.

        Returns:
            float: The defensive rush value.
        """
        resting_starters = []
        multiplier = 0.70 if self.abbreviation in resting_starters else 1.0
        return self.drf(self.def_rush[self.abbreviation]) * multiplier

    def get_off_pass_value(self):
        """
        Get the offensive pass value combining various factors.

        Returns:
            float: The offensive pass value.
        """
        qb_value = self.get_qb_value()
        rec_value = self.get_rec_value()
        ol_pass_value = self.get_ol_pass_value()
        rushing_value = self.get_rushing_value()
        return (qb_value * 0.55) + (rec_value * 0.30) + (ol_pass_value * 0.1) + (rushing_value * 0.05)

    def get_off_rush_value(self):
        """
        Get the offensive rush value combining rushing and OL factors.

        Returns:
            float: The offensive rush value.
        """
        rushing_value = self.get_rushing_value()
        ol_rush_value = self.get_ol_rush_value()
        return (rushing_value * 0.65) + (ol_rush_value * 0.35)

    def get_play_rates(self):
        """
        Get the play rates for the team.

        Returns:
            dict: The play rates data.
        """
        return self.play_rates[self.abbreviation]

    def get_off_plays_per_60(self):
        """
        Get the offensive plays per 60 minutes.

        Returns:
            float: Offensive plays per 60 minutes.
        """
        return self.get_play_rates()["OFF"]["PlayPer60"]

    def get_def_plays_per_60(self):
        """
        Get the defensive plays per 60 minutes.

        Returns:
            float: Defensive plays per 60 minutes.
        """
        return self.get_play_rates()["DEF"]["PlayPer60"]

    def get_off_pass_rate(self):
        """
        Get the offensive pass rate.

        Returns:
            float: Offensive pass rate.
        """
        return self.get_play_rates()["OFF"]["PassRate"]

    def get_def_pass_rate(self):
        """
        Get the defensive pass rate.

        Returns:
            float: Defensive pass rate.
        """
        return self.get_play_rates()["DEF"]["PassRate"]

    def get_off_rush_rate(self):
        """
        Get the offensive rush rate.

        Returns:
            float: Offensive rush rate.
        """
        return self.get_play_rates()["OFF"]["RushRate"]

    def get_def_rush_rate(self):
        """
        Get the defensive rush rate.

        Returns:
            float: Defensive rush rate.
        """
        return self.get_play_rates()["DEF"]["RushRate"]

    def generate_rushing_value(self):
        """
        Generate the total rushing value for the team.

        Returns:
            float: The total rushing value.
        """
        total_dvoa, total_attempts = 0, 0
        for position, dvoa_dict in [('RB', self.rb_rush_dvoa), ('WR', self.wr_rush_dvoa), ('QB', self.qb_rush_dvoa)]:
            total_dvoa, total_attempts = _calculate_total_dvoa(self.team_data[position], dvoa_dict, total_dvoa,
                                                               total_attempts, 1)
        total_dvoa = total_dvoa / total_attempts if total_attempts else 0
        return total_dvoa

    def get_rushing_value(self):
        """
        Get the rushing value for the team.

        Returns:
            float: The rushing value.
        """
        total_dvoa = self.generate_rushing_value()
        return self.rush_func(total_dvoa)

    def generate_rec_value(self):
        """
        Generate the total receiving value for the team.

        Returns:
            float: The total receiving value.
        """
        total_dvoa, total_targets = 0, 0
        for position, dvoa_dict in [('RB', self.rb_rec_dvoa), ('WR', self.wr_rec_dvoa), ('TE', self.te_rec_dvoa)]:
            total_dvoa, total_targets = _calculate_total_dvoa(self.team_data[position], dvoa_dict, total_dvoa,
                                                              total_targets, 2)
        total_dvoa = total_dvoa / total_targets if total_targets else 0
        return total_dvoa

    def get_rec_value(self):
        """
        Get the receiving value for the team.

        Returns:
            float: The receiving value.
        """
        total_dvoa = self.generate_rec_value()
        return self.rec_func(total_dvoa)


# Load data
nfl_teams = load_csv_data("projections/2023/week18/fantasy-football-weekly-projections.csv", process_projections)
def_pass_dvoa, def_rush_dvoa = load_csv_data('dvoa/2023/team_defense_dvoa.csv',
                                             lambda reader: process_dvoa_data(reader, 7, 9))
adjusted_rush_yards, adjusted_sack_rate = load_csv_data('dvoa/2023/dvoa_adjusted_line_yards.csv',
                                                        lambda reader: process_dvoa_data(reader, 3, 15))


def create_play_rate_entry(row):
    """
    Create a play rate entry based on a row of data.

    Args:
        row (list): A list containing data for play rates, including pass and rush rates.

    Returns:
        dict: A dictionary containing play rate information for both offense (OFF) and defense (DEF).
    """
    return {
        "OFF": {
            "PlayPer60": float(row[2]),
            "PassRate": float(row[1]),
            "RushRate": 100 - float(row[1]),
        },
        "DEF": {
            "PlayPer60": float(row[4]),
            "PassRate": float(row[3]),
            "RushRate": 100 - float(row[3]),
        }
    }


play_rates = load_csv_data('misc/play_rates.csv',
                           lambda reader: {row[0]: create_play_rate_entry(row) for row in reader})
home_field_adv = load_csv_data("misc/home_adv.csv",
                               lambda reader: {row[0]: (float(row[1]), float(row[2])) for row in reader})
home_field_avg_tmp = load_csv_data("misc/avg_tmp.csv", lambda reader: {row[0]: float(row[1]) for row in reader})

dvoa = {
    "Passing": {year: load_csv_data(f"dvoa/{year}/passing_dvoa.csv",
                                    lambda reader: {row[0]: (float(row[4]) * 100, float(row[6])) for row in reader})
                for year in ["2023_playoffs", "2023", "2022", "2021", "2020"]},
    "Rushing": {
        "RB": {year: load_csv_data(f"dvoa/{year}/rb_rushing_dvoa.csv",
                                   lambda reader: {row[0]: (float(row[4]) * 100, float(row[6])) for row in reader})
               for year in ["2023_playoffs", "2023", "2022", "2021", "2020"]},
        "QB": {year: load_csv_data(f"dvoa/{year}/qb_rushing_dvoa.csv",
                                   lambda reader: {row[0]: (float(row[4]) * 100, float(row[6])) for row in reader})
               for year in ["2023_playoffs", "2023", "2022", "2021", "2020"]},
        "WR": {year: load_csv_data(f"dvoa/{year}/wr_rushing_dvoa.csv",
                                   lambda reader: {row[0]: (float(row[4]) * 100, float(row[6])) for row in reader})
               for year in ["2023_playoffs", "2023", "2022", "2021", "2020"]}
    },
    "Receiving": {
        "WR": {year: load_csv_data(f"dvoa/{year}/wr_receiving_dvoa.csv",
                                   lambda reader: {row[0]: (float(row[4]) * 100, float(row[6])) for row in reader})
               for year in ["2023_playoffs", "2023", "2022", "2021", "2020"]},
        "RB": {year: load_csv_data(f"dvoa/{year}/rb_receiving_dvoa.csv",
                                   lambda reader: {row[0]: (float(row[4]) * 100, float(row[6])) for row in reader})
               for year in ["2023_playoffs", "2023", "2022", "2021", "2020"]},
        "TE": {year: load_csv_data(f"dvoa/{year}/te_receiving_dvoa.csv",
                                   lambda reader: {row[0]: (float(row[4]) * 100, float(row[6])) for row in reader})
               for year in ["2023_playoffs", "2023", "2022", "2021", "2020"]}
    }
}


def linear_function(x1, y1, x2, y2):
    """
    Create a linear function given two points on the line.

    Args:
        x1 (float): x-coordinate of the first point.
        y1 (float): y-coordinate of the first point.
        x2 (float): x-coordinate of the second point.
        y2 (float): y-coordinate of the second point.

    Returns:
        function: A lambda function representing the linear equation.
    """
    m = (y2 - y1) / (x2 - x1)
    return lambda x: m * x + (y1 - m * x1)


functions_dict = {
    "Pass": linear_function(-40, 0, 37.5, 10),
    "Rush": linear_function(-15, 0, 22.5, 10),
    "Rec": linear_function(-10, 0, 17.5, 10),
    "OLPF": linear_function(85, 0, 20, 10),
    "OLRF": linear_function(3.3, 0, 4.85, 10),
    "DPF": linear_function(.35, 0, -.30, 10),
    "DRF": linear_function(.07, 0, -.20, 10)
}

matchups = load_json_data('misc/matchups_conference.json')

data_for_df = []
data_for_df_2 = []
data_for_df_3 = []
data_for_df_4 = []


def get_pct_from_wind(wind):
    """
    Calculate a percentage modifier based on wind speed.

    Args:
        wind (float): Wind speed in units (e.g., miles per hour).

    Returns:
        float: A percentage modifier based on the wind speed.
    """
    return 0.999 + (0.00317 * wind) + (-1 * (0.000458 * (wind ** 2)))


def get_pct_from_precip(precip):
    """
    Calculate a percentage modifier based on precipitation.

    Args:
        precip (float): Precipitation level (e.g., inches).

    Returns:
        float: A percentage modifier based on the precipitation level.
    """
    return 0.0025 * precip


def get_pct_from_temp_delta(delta):
    """
    Calculate a percentage modifier based on temperature change.

    Args:
        delta (float): Temperature change in units (e.g., degrees).

    Returns:
        float: A percentage modifier based on the temperature change.
    """
    return 1 - (0.000664 + (0.00148 * delta) + (0.0000375 * (delta ** 2)))


# Process matchups
for matchup in matchups:
    team1 = Team(
        matchup['home'],
        nfl_teams[matchup['home']],
        def_pass_dvoa,
        dvoa,
        adjusted_rush_yards,
        adjusted_sack_rate,
        def_rush_dvoa,
        play_rates,
        functions_dict
    )
    team2 = Team(
        matchup['away'],
        nfl_teams[matchup['away']],
        def_pass_dvoa,
        dvoa,
        adjusted_rush_yards,
        adjusted_sack_rate,
        def_rush_dvoa,
        play_rates,
        functions_dict
    )

    team1.print_lineup()
    print()
    team2.print_lineup()
    print()

    neutral = True if matchup["neutral"] == "yes" else False

    precip_delta = get_pct_from_precip(matchup["weather"]) if matchup["weather"] else 0
    wind_delta = get_pct_from_wind(matchup["wind"]) if matchup["wind"] else 1
    game_temp = 72.5 if not matchup["temp"] else matchup["temp"]
    home_avg_tmp = home_field_avg_tmp[matchup["home"]]
    away_avg_tmp = home_field_avg_tmp[matchup["away"]]

    hp = team1.get_off_pass_value()
    ap = team2.get_off_pass_value()
    hpd = team1.get_def_pass_value()
    apd = team2.get_def_pass_value()
    hr = team1.get_off_rush_value()
    ar = team2.get_off_rush_value()
    hrd = team1.get_def_rush_value()
    ard = team2.get_def_rush_value()

    hp -= hp * precip_delta
    ap -= ap * precip_delta
    hp_delta = hp - apd
    hr_delta = hr - ard
    ap_delta = ap - hpd
    ar_delta = ar - hrd

    home_pass_rate_delta = (team1.get_off_pass_rate() + team2.get_def_pass_rate()) / 2
    home_rush_rate_delta = (team1.get_off_rush_rate() + team2.get_def_rush_rate()) / 2
    away_pass_rate_delta = (team2.get_off_pass_rate() + team1.get_def_pass_rate()) / 2
    away_rush_rate_delta = (team2.get_off_rush_rate() + team1.get_def_rush_rate()) / 2

    h_off = ((hp_delta * home_pass_rate_delta) + (hr_delta * home_rush_rate_delta)) / 100
    a_off = ((ap_delta * away_pass_rate_delta) + (ar_delta * away_rush_rate_delta)) / 100

    h_pts = 22.5 + (1.23 * h_off) + (0.0692 * (h_off ** 2)) + (0.0242 * (h_off ** 3)) + (0.000665 * (h_off ** 4))
    a_pts = 22.5 + (1.23 * a_off) + (0.0692 * (a_off ** 2)) + (0.0242 * (a_off ** 3)) + (0.000665 * (a_off ** 4))

    h_pts = (h_pts * wind_delta) * get_pct_from_temp_delta(abs(home_avg_tmp - game_temp))
    a_pts = (a_pts * wind_delta) * get_pct_from_temp_delta(abs(away_avg_tmp - game_temp))

    if neutral:
        f_h_pts = h_pts
        f_a_pts = a_pts

    else:
        h_adv, h_adv_def = home_field_adv[matchup['home']]
        a_adv, a_adv_def = home_field_adv[matchup['away']]
        a_adv = a_adv * -1
        a_adv_def = a_adv_def * -1

        h_adv = h_adv + a_adv_def
        a_adv = a_adv + h_adv_def

        f_h_pts = h_pts * (1 + h_adv)
        f_a_pts = a_pts * (1 + a_adv)

    home_win_pct = (-0.0303 * (f_a_pts - f_h_pts) + 0.5) * 100
    if home_win_pct >= 100:
        home_win_pct = 99.9
    if home_win_pct <= 0:
        home_win_pct = 0.1
    away_win_pct = 100 - home_win_pct

    h_ml = matchup['betting_lines']['home_ml']
    a_ml = matchup['betting_lines']['away_ml']
    h_spread = matchup['betting_lines']['home_spread']
    a_spread = matchup['betting_lines']['away_spread']

    proj_total = (f_h_pts + f_a_pts)
    bet_total = matchup['betting_lines']['total']
    over_under_bet = "O" if proj_total > bet_total else "U"

    implied_h_win_pct = (-1 * h_ml) / ((-1 * h_ml) + 100) * 100 if h_ml < 0 else (100 / (h_ml + 100) * 100)
    implied_a_win_pct = (-1 * a_ml) / ((-1 * a_ml) + 100) * 100 if a_ml < 0 else (100 / (a_ml + 100) * 100)

    spread = f_a_pts - f_h_pts

    h_spread_delta = h_spread - spread
    a_spread_delta = a_spread + spread

    h_win_pct_delta = home_win_pct - implied_h_win_pct
    a_win_pct_delta = away_win_pct - implied_a_win_pct

    ml_bet = "~"
    spread_bet = "~"
    total_bet = "~"

    if h_win_pct_delta > 3:
        ml_bet = f"H: {5 * round(((h_win_pct_delta / 20) * (home_win_pct / 100)) * 100)}"
    elif a_win_pct_delta > 3:
        ml_bet = f"A: {5 * round(((a_win_pct_delta / 20) * (away_win_pct / 100)) * 100)}"

    if h_spread_delta > 1.5:
        spread_bet = f"H: {5 * round(h_spread_delta * 7.5)}"
    elif a_spread_delta > 1.5:
        spread_bet = f"A: {5 * round(a_spread_delta * 7.5)}"

    total_delta = proj_total - bet_total

    if abs(total_delta) >= 3:
        total_bet = f"{5 * round(abs(total_delta) * 15 / 5)}"

    data_for_df_3.append({
        "Team": matchup['home'],
        "QB DVOA": round(team1.generate_qb_value(), 1),
        "QB Val": round(team1.get_qb_value(), 1),
        "Rush DVOA": round(team1.generate_rushing_value(), 1),
        "Rush Val": round(team1.get_rushing_value(), 1),
        "Rec DVOA": round(team1.generate_rec_value(), 1),
        "Rec Val": round(team1.get_rec_value(), 1),
        "OL Pass Val": round(team1.get_ol_pass_value(), 1),
        "OL Rush Val": round(team1.get_ol_rush_value(), 1),
        "Off Pass Val": round(team1.get_off_pass_value(), 1),
        "Off Rush Val": round(team1.get_off_rush_value(), 1),
        "Def Pass Val": round(team1.get_def_pass_value(), 1),
        "Def Rush Val": round(team1.get_def_rush_value(), 1)
    })
    data_for_df_3.append({
        "Team": matchup['away'],
        "QB DVOA": round(team2.generate_qb_value(), 1),
        "QB Val": round(team2.get_qb_value(), 1),
        "Rush DVOA": round(team2.generate_rushing_value(), 1),
        "Rush Val": round(team2.get_rushing_value(), 1),
        "Rec DVOA": round(team2.generate_rec_value(), 1),
        "Rec Val": round(team2.get_rec_value(), 1),
        "OL Pass Val": round(team2.get_ol_pass_value(), 1),
        "OL Rush Val": round(team2.get_ol_rush_value(), 1),
        "Off Pass Val": round(team2.get_off_pass_value(), 1),
        "Off Rush Val": round(team2.get_off_rush_value(), 1),
        "Def Pass Val": round(team2.get_def_pass_value(), 1),
        "Def Rush Val": round(team2.get_def_rush_value(), 1)
    })

    data_for_df_2.append({
        "Home": matchup['home'],
        "Away": matchup['away'],
        "H Pass Adv": round(hp_delta, 1) * 10,
        "H Rush Adv": round(hr_delta, 1) * 10,
        "A Pass Adv": round(ap_delta, 1) * 10,
        "A Rush Adv": round(ar_delta, 1) * 10,
    })

    data_for_df.append({
        "Home": matchup['home'],
        "Away": matchup['away'],
        "H_O": round(h_off, 1),
        "A_O": round(a_off, 1),
        "HP": round(f_h_pts),
        "AP": round(f_a_pts),
        "Spread": round(spread),
        "H Win %": round(home_win_pct, 1),
        "A Win %": round(away_win_pct, 1),
        "H ML": h_ml,
        "A ML": a_ml,
        "~H Win %": round(implied_h_win_pct, 1),
        "~A Win %": round(implied_a_win_pct, 1),
        "~HD": round(h_win_pct_delta, 1),
        "~AD": round(a_win_pct_delta, 1),
        "H Spread": h_spread,
        "A Spread": a_spread,
        "~HSD": round(h_spread_delta, 1),
        "~ASD": round(a_spread_delta, 1),
        "PrjTotal": round(f_h_pts + f_a_pts, 1),
        "Total": matchup['betting_lines']['total'],
        "~TD": round(proj_total - bet_total, 1),
        "O/U": over_under_bet,
        "ML Bet": ml_bet,
        "Spr Bet": spread_bet,
        "Tot Bet": total_bet
    })

    data_for_df_4.append({
        "Home": matchup['home'],
        "HP": round(f_h_pts),
        "AP": round(f_a_pts),
        "Away": matchup['away'],
        "Total": round(proj_total, 1)
    })

# Step 3: Create a DataFrame
df = pd.DataFrame(data_for_df)
df2 = pd.DataFrame(data_for_df_2)
df3 = pd.DataFrame(data_for_df_3)
df4 = pd.DataFrame(data_for_df_4)

# Step 4: Print the DataFrame

print(df2.to_string(index=False))
print()
print(df3.to_string(index=False))
print()
print(df.to_string(index=False))
print()
print(df4.to_string(index=False))
print()
