import random
from rile import NFLDrivePredictor  # Assuming the previous class is in this file

class NFLGameSimulator:
    def __init__(self, team1_name, team2_name):
        self.team1 = {'name': team1_name, 'score': 0, 'predictor': NFLDrivePredictor()}
        self.team2 = {'name': team2_name, 'score': 0, 'predictor': NFLDrivePredictor()}
        self.quarter = 1
        self.time_left = 15 * 60  # 15 minutes in seconds
        self.possession = None
        self.field_position = 25  # Starting at 25-yard line after kickoff

    def set_team_stats(self, team, offensive_stats, defensive_stats):
        team['predictor'].set_offensive_stats(**offensive_stats)
        team['predictor'].set_defensive_stats(**defensive_stats)

    def simulate_extra_point(self, kicker_accuracy):
        return random.random() < (kicker_accuracy / 100)

    def simulate_drive(self, offense, defense):
        drive_result = offense['predictor'].predict_drive_outcome(self.field_position)
        outcome, points, num_plays, time_used, _, yards_gained, end_yard, next_start, fg_distance = drive_result

        # Ensure time_used doesn't exceed remaining time
        time_used = min(time_used, self.time_left)
        self.time_left -= time_used

        # Handle scoring
        if outcome == 'Touchdown':
            points = 6
            if self.simulate_extra_point(offense['predictor'].stats['kicker_accuracy']):
                points += 1
                print("Extra point is good!")
            else:
                print("Extra point is no good!")
        elif outcome == 'Field Goal':
            points = 3
        else:
            points = 0

        # Update score and field position
        offense['score'] += points
        self.field_position = 100 - next_start if next_start else 25  # Touchback if no next_start

        return outcome, points, yards_gained, end_yard, fg_distance, time_used

    def end_quarter(self):
        self.quarter += 1
        if self.quarter <= 4:
            self.time_left = 15 * 60
            print(f"\nEnd of Quarter {self.quarter - 1}")
            print(f"Start of Quarter {self.quarter}")
        else:
            self.time_left = 0  # End of game

    def switch_possession(self):
        self.possession = self.team2 if self.possession == self.team1 else self.team1

    def format_time(self, seconds):
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:02d}"

    def simulate_game(self):
        self.possession = random.choice([self.team1, self.team2])
        print(f"{self.team1['name']} vs {self.team2['name']}")
        print(f"{self.possession['name']} receives the opening kickoff.")

        while self.quarter <= 4 and self.time_left > 0:
            offense = self.possession
            defense = self.team2 if offense == self.team1 else self.team1

            print(f"\nQuarter: {self.quarter}, Time Left: {self.format_time(self.time_left)}")
            print(f"{offense['name']} ball at {offense['predictor'].format_field_position(self.field_position)}")

            outcome, points, yards, end_yard, fg_distance, time_used = self.simulate_drive(offense, defense)

            print(f"Drive result: {outcome}")
            if fg_distance:
                print(f"Field Goal Attempt Distance: {fg_distance} yards")
            print(f"Yards gained: {yards}")
            print(f"Drive ended at: {offense['predictor'].format_field_position(end_yard)}")
            print(f"Time used: {self.format_time(time_used)}")
            if points > 0:
                print(f"{offense['name']} scores {points} points!")

            print(f"Score: {self.team1['name']} {self.team1['score']} - {self.team2['name']} {self.team2['score']}")

            if self.time_left == 0:
                if self.quarter < 4:
                    self.end_quarter()
                else:
                    print("\nGame Over!")
                    break

            if self.quarter == 2 and self.time_left == 15 * 60:
                print("\nHalftime!")
                self.switch_possession()  # Other team gets the ball to start the second half
            elif outcome in ['Punt', 'Turnover', 'Missed Field Goal', 'Touchdown', 'Field Goal']:
                self.switch_possession()

        print(f"\nFinal Score: {self.team1['name']} {self.team1['score']} - {self.team2['name']} {self.team2['score']}")

# Example usage
game = NFLGameSimulator("Eagles", "Chiefs")

# Set stats for Eagles
game.set_team_stats(game.team1, 
    offensive_stats={
        'qb_rating': 105.0, 'qb_epa_per_play': 0.25, 'rb_ypc': 4.5, 'wr_ypr': 12.0,
        'ol_pbwr': 65, 'ol_rbwr': 60, 'third_down_rate': 45, 'rz_efficiency': 60,
        'pace_of_play': 28, 'kicker_accuracy': 94
    },
    defensive_stats={
        'def_dvoa': -10, 'def_pressure_rate': 30, 'def_coverage_rating': 75
    }
)

# Set stats for Chiefs
game.set_team_stats(game.team2, 
    offensive_stats={
        'qb_rating': 110.0, 'qb_epa_per_play': 0.28, 'rb_ypc': 4.2, 'wr_ypr': 13.0,
        'ol_pbwr': 70, 'ol_rbwr': 55, 'third_down_rate': 48, 'rz_efficiency': 65,
        'pace_of_play': 26, 'kicker_accuracy': 95
    },
    defensive_stats={
        'def_dvoa': -5, 'def_pressure_rate': 28, 'def_coverage_rating': 80
    }
)

game.simulate_game()