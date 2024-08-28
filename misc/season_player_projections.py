import csv
from typing import Dict, List

class ScoringSettings:
    def __init__(self):
        self.settings: Dict[str, float] = {}

    def add_setting(self, stat: str, points: float):
        self.settings[stat] = points

    def get_points(self, stat: str) -> float:
        return self.settings.get(stat, 0.0)

class Player:
    def __init__(self, name: str, position: str):
        self.name = name
        self.position = position
        self.stats: Dict[str, float] = {}

    def add_stat(self, stat: str, value: float):
        self.stats[stat] = value

    def calculate_score(self, scoring: ScoringSettings) -> float:
        return sum(value * scoring.get_points(stat) for stat, value in self.stats.items())

def load_players_from_csv(filename: str) -> List[Player]:
    players = []
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            player = Player(row['Player'], row['Pos'])
            for stat, value in row.items():
                if stat not in ['Player', 'Pos', 'Team']:
                    try:
                        player.add_stat(stat, float(value))
                    except ValueError:
                        pass  # Skip non-numeric values
            players.append(player)
    return players

def get_scoring_settings() -> ScoringSettings:
    scoring = ScoringSettings()
    print("Enter your scoring settings. Type 'done' when finished.")
    while True:
        stat = input("Enter stat name (e.g., 'PassYds', 'RushTD'): ").strip()
        if stat.lower() == 'done':
            break
        try:
            points = float(input(f"Enter points for {stat}: "))
            scoring.add_setting(stat, points)
        except ValueError:
            print("Invalid input. Please enter a number for points.")
    return scoring

def main():
    # Load players from CSV
    filename = input("Enter the name of your CSV file with player stats: ")
    players = load_players_from_csv(filename)

    # Get scoring settings
    scoring = get_scoring_settings()

    # Calculate and display scores
    print("\nCalculated Scores:")
    for player in players:
        score = player.calculate_score(scoring)
        print(f"{player.name} ({player.position}): {score:.2f} points")

if __name__ == "__main__":
    main()