import random

class NFLDrivePredictor:
    def __init__(self):
        self.stats = {
            'qb_rating': 0,
            'qb_epa_per_play': 0,
            'rb_yards_per_carry': 0,
            'wr_yards_per_reception': 0,
            'ol_pass_block_win_rate': 0,
            'ol_run_block_win_rate': 0,
            'off_third_down_rate': 0,
            'off_red_zone_efficiency': 0,
            'def_dvoa': 0,
            'def_pressure_rate': 0,
            'def_coverage_rating': 0,
            'pace_of_play': 0,  # Seconds per play
            'kicker_accuracy': 0  # New stat for kicker accuracy
        }
        
        self.weights = {
            'qb_rating': 0.15,
            'qb_epa_per_play': 0.15,
            'rb_yards_per_carry': 0.1,
            'wr_yards_per_reception': 0.1,
            'ol_pass_block_win_rate': 0.05,
            'ol_run_block_win_rate': 0.05,
            'off_third_down_rate': 0.1,
            'off_red_zone_efficiency': 0.1,
            'def_dvoa': -0.1,
            'def_pressure_rate': -0.05,
            'def_coverage_rating': -0.05
        }

    def normalize_stat(self, stat, value, max_value):
        self.stats[stat] = max(0, min(value / max_value, 1))

    def set_offensive_stats(self, qb_rating, qb_epa_per_play, rb_ypc, wr_ypr, 
                            ol_pbwr, ol_rbwr, third_down_rate, rz_efficiency, pace_of_play, kicker_accuracy):
        self.normalize_stat('qb_rating', qb_rating, 158.3)  # Perfect passer rating
        self.normalize_stat('qb_epa_per_play', qb_epa_per_play, 0.5)  # Approximate max EPA/play
        self.normalize_stat('rb_yards_per_carry', rb_ypc, 6.0)
        self.normalize_stat('wr_yards_per_reception', wr_ypr, 20.0)
        self.normalize_stat('ol_pass_block_win_rate', ol_pbwr, 100)
        self.normalize_stat('ol_run_block_win_rate', ol_rbwr, 100)
        self.normalize_stat('off_third_down_rate', third_down_rate, 100)
        self.normalize_stat('off_red_zone_efficiency', rz_efficiency, 100)
        self.stats['pace_of_play'] = pace_of_play  # Seconds per play, not normalized
        self.normalize_stat('kicker_accuracy', kicker_accuracy, 100)  # Kicker accuracy percentage

    def set_defensive_stats(self, def_dvoa, def_pressure_rate, def_coverage_rating):
        self.normalize_stat('def_dvoa', def_dvoa, 30)  # Approximate max DVOA
        self.normalize_stat('def_pressure_rate', def_pressure_rate, 50)  # Approximate max pressure rate
        self.normalize_stat('def_coverage_rating', def_coverage_rating, 100)

    def simulate_field_goal(self, distance):
        # Base probability of making the field goal
        base_prob = max(0, min(1, 1.1 - (distance / 60)))  # Linear decrease in probability as distance increases
        
        # Adjust probability based on kicker's accuracy
        adjusted_prob = base_prob * (0.5 + 0.5 * self.stats['kicker_accuracy'])
        
        # Simulate the kick
        return random.random() < adjusted_prob

    def format_field_position(self, yard):
        if yard <= 50:
            return f"Own {yard}"
        else:
            return f"Opponent {100 - yard}"

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}:{remaining_seconds:02d}"

    def predict_drive_outcome(self, starting_yard):
        drive_score = sum(self.stats[stat] * self.weights[stat] for stat in self.stats if stat not in ['pace_of_play', 'kicker_accuracy'])
        
        # Normalize drive score to be between 0 and 1
        drive_score = max(0, min(drive_score, 1))
        
        # Determine drive outcome probabilities
        td_prob = drive_score * 0.6  # Max 60% chance of TD
        fg_prob = (1 - td_prob) * 0.4  # Max 40% chance of FG if not TD
        punt_prob = 1 - td_prob - fg_prob
        
        # Simulate drive outcome
        outcome = random.choices(['Touchdown', 'Field Goal Attempt', 'Punt', 'Turnover'], 
                                 weights=[td_prob, fg_prob, punt_prob * 0.8, punt_prob * 0.2])[0]
        
        # Calculate yards gained and ending yard
        if outcome == 'Touchdown':
            yards_gained = 100 - starting_yard
            ending_yard = 100
        elif outcome == 'Field Goal Attempt':
            ending_yard = min(random.randint(65, 85), 100)  # Field goal range
            yards_gained = ending_yard - starting_yard
            fg_distance = 100 - ending_yard + 17  # Add 17 yards for the end zone and holder
            fg_made = self.simulate_field_goal(fg_distance)
            outcome = 'Field Goal' if fg_made else 'Missed Field Goal'
        else:
            avg_drive_length = 30  # Average NFL drive length
            yards_gained = max(0, min(round(avg_drive_length * (1 + drive_score) * random.uniform(0.5, 1.5)), 100 - starting_yard))
            ending_yard = starting_yard + yards_gained

        # Calculate projected points
        if outcome == 'Touchdown':
            points = 6 + (0.94 * 1)  # TD + extra point (94% success rate)
        elif outcome == 'Field Goal':
            points = 3
        else:
            points = 0
        
        # Calculate number of plays and time used
        avg_plays_per_drive = 6.5  # NFL average
        play_variation = random.uniform(0.8, 1.2)  # Add some randomness
        num_plays = max(1, round(avg_plays_per_drive * play_variation * (1 + drive_score)))
        
        time_used = num_plays * self.stats['pace_of_play']
        
        # Determine next possession start for punts, turnovers, and missed field goals
        if outcome in ['Punt', 'Turnover', 'Missed Field Goal']:
            if outcome == 'Punt':
                next_possession_start = max(20, min(100 - ending_yard + random.randint(35, 45), 80))
            elif outcome == 'Turnover':
                next_possession_start = min(ending_yard + random.randint(0, 10), 80)
            else:  # Missed Field Goal
                next_possession_start = min(100 - fg_distance + 10, 80)  # Ball placed at spot of kick or 20-yard line, whichever is farther
        else:
            next_possession_start = None

        return outcome, points, num_plays, time_used, starting_yard, yards_gained, ending_yard, next_possession_start, fg_distance if 'Field Goal' in outcome else None

    def simulate_drive(self, starting_yard):
        outcome, points, num_plays, time_used, start_yard, yards_gained, end_yard, next_start, fg_distance = self.predict_drive_outcome(starting_yard)
        drive_quality = sum(self.stats[stat] * self.weights[stat] for stat in self.stats if stat not in ['pace_of_play', 'kicker_accuracy'])
        drive_quality = max(0, min(drive_quality, 1))  # Normalize to 0-1
        
        print(f"Drive Quality: {drive_quality:.2f}")
        print(f"Starting Field Position: {self.format_field_position(start_yard)}")
        print(f"Yards Gained: {yards_gained}")
        print(f"Ending Field Position: {self.format_field_position(end_yard) if end_yard != 100 else 'Opponent Goal Line'}")
        print(f"Drive Outcome: {outcome}")
        if fg_distance:
            print(f"Field Goal Attempt Distance: {fg_distance} yards")
        print(f"Points Scored: {points:.2f}")
        print(f"Number of Plays: {num_plays}")
        print(f"Time Used: {self.format_time(time_used)}")
        
        if next_start:
            print(f"Next Possession Starts At: {self.format_field_position(100 - next_start)}")

# Example usage
predictor = NFLDrivePredictor()

# Set offensive stats
predictor.set_offensive_stats(
    qb_rating=105.0,
    qb_epa_per_play=0.25,
    rb_ypc=4.5,
    wr_ypr=12.0,
    ol_pbwr=65,
    ol_rbwr=60,
    third_down_rate=45,
    rz_efficiency=60,
    pace_of_play=28,  # Average seconds per play
    kicker_accuracy=85  # 85% field goal accuracy
)

# Set defensive stats
predictor.set_defensive_stats(
    def_dvoa=-10,
    def_pressure_rate=30,
    def_coverage_rating=75
)

# Simulate a drive starting from the team's own 25-yard line
predictor.simulate_drive(25)

