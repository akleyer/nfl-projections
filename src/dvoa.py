import config
import csv
import utils

class DVOA:
    def __init__(self):
        self.data = self._load_all_dvoa_data()
        self.dave = self._load_dave_data()
        return

    def get_data(self):
        return self.data

    def get_dave(self):
        return self.dave

    def _load_dave_data(self):
        team_data = {}
        file_path = "../data/raw/dvoa/dave.csv"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                team = row['TEAM']
                off_dave = row['OFF DAVE']
                def_dave = row['DEF DAVE']
                st_dave = row['ST DAVE']
                team_data.setdefault(team, []).append((off_dave, def_dave, st_dave))
        return team_data 

    def _load_all_dvoa_data(self):
        data = {}
        for year in config.YEARS:
            data[year] = {
                "Passing" : self._get_passing_dvoa(year),
                "Rushing" : self._get_rush_dvoa(year),
                "Receiving" : self._get_rec_dvoa(year),
                "OL Pass" : self._get_ol_dvoa(year, "Pass"),
                "OL Run" : self._get_ol_dvoa(year, "Rush"),
                "Defense Pass" : self._get_def_dvoa(year, "Pass"),
                "Defense Rush" : self._get_def_dvoa(year, "Rush")
            }
        return data

    def _get_def_dvoa(self, year, group):
        team_data = {}
        file_path = f"../data/raw/dvoa/{year}/team_defense_dvoa.csv"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    team = row['TEAM']
                    if group == "Pass":
                        def_dvoa = self._convert_strpct_to_float(row['PASS'])
                    elif group == "Rush":
                        def_dvoa = self._convert_strpct_to_float(row['RUSH'])
                    else:
                        print("Wrong group type for DEF")
                        quit()
                    team_data.setdefault(team, []).append((def_dvoa))
                except KeyError:
                    continue
        return team_data 

    def _get_ol_dvoa(self, year, group):
        team_data = {}
        file_path = f"../data/raw/dvoa/{year}/dvoa_adjusted_line_yards.csv"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                team = row['Team']
                if group == "Pass":
                    ol_dvoa = self._convert_strpct_to_float(row['Adjusted Sack Rate'])
                elif group == "Rush":
                    ol_dvoa = utils.safe_float(row['Adjusted Line Yards'])
                else:
                    print("Wrong group type for OL")
                    quit()
                team_data.setdefault(team, []).append((ol_dvoa))
        return team_data 

    def _get_rec_dvoa(self, year):
        player_data = {}
        file_path = f"../data/raw/dvoa/{year}/receiving_dvoa.csv"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                player_name = row['Player']
                receiving_dvoa = self._convert_strpct_to_float(row['DVOA'])
                targets = float(row['TAR'])
                player_data.setdefault(player_name, []).append((receiving_dvoa, targets))
        return player_data

    def _get_rush_dvoa(self, year):
        player_data = {}
        file_path = f"../data/raw/dvoa/{year}/rushing_dvoa.csv"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                player_name = row['Player']
                try:
                    rushing_dvoa = self._convert_strpct_to_float(row['DVOA'])
                    rush_attempts = float(row['ATT'])
                except ValueError:
                    rushing_dvoa = 0
                    rush_attempts = 1
                player_data.setdefault(player_name, []).append((rushing_dvoa, rush_attempts))
        return player_data
    
    def _get_passing_dvoa(self, year):
        player_data = {}
        file_path = f"../data/raw/dvoa/{year}/passing_dvoa.csv"
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                player_name = row['Player']
                passing_dvoa = self._convert_strpct_to_float(row['DVOA'])
                passing_attempts = float(row['ATT'])
                player_data.setdefault(player_name, []).append((passing_dvoa, passing_attempts))
        return player_data
    
    def _convert_strpct_to_float(self, str_pct):
        return float(str_pct.replace("%","").replace("\"","").replace("\'",""))/100