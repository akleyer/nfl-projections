import random
import json
import csv
from typing import List, Dict, Tuple

class Player:
    def __init__(self, name: str, wins: int = 0, losses: int = 0, opponents: List[str] = None):
        self.name = name
        self.wins = wins
        self.losses = losses
        self.opponents = opponents or []

    def __repr__(self):
        return f"{self.name} ({self.wins}-{self.losses})"

def load_players_from_csv(filename: str) -> List[Player]:
    players = []
    with open(filename, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row
        for row in reader:
            players.append(Player(row[2]))  # Player name is in the third column
    return players

def load_or_create_data(json_filename: str) -> Dict[str, List[Player]]:
    try:
        with open(json_filename, 'r') as f:
            data = json.load(f)
        return {position: [Player(**p) for p in players] for position, players in data.items()}
    except FileNotFoundError:
        positions = ['qb', 'rb', 'te', 'wr']
        data = {}
        for position in positions:
            try:
                data[position] = load_players_from_csv(f"projections/2024/season/{position}.csv")
            except FileNotFoundError:
                print(f"Warning: {position}.csv not found. Skipping this position.")
        return data

def save_data(data: Dict[str, List[Player]], filename: str):
    serialized_data = {
        position: [{"name": p.name, "wins": p.wins, "losses": p.losses, "opponents": p.opponents} 
                   for p in players]
        for position, players in data.items()
    }
    with open(filename, 'w') as f:
        json.dump(serialized_data, f, indent=2)

def get_winner_input(player1: Player, player2: Player) -> Player:
    while True:
        choice = input(f"Who won? Enter (1) for {player1.name} or (2) for {player2.name}: ").strip()
        if choice == '1':
            return player1
        elif choice == '2':
            return player2
        else:
            print("Invalid input. Please enter either 1 or 2.")

def match_players(players: List[Player]) -> List[Tuple[Player, Player]]:
    sorted_players = sorted(players, key=lambda x: (-x.wins, x.losses))
    matchups = []
    used_players = set()

    for i in range(0, len(sorted_players), 2):
        if i + 1 < len(sorted_players):
            player1, player2 = sorted_players[i], sorted_players[i + 1]
            if player2.name not in player1.opponents and player1.name not in player2.opponents:
                matchups.append((player1, player2))
                used_players.add(player1)
                used_players.add(player2)

    remaining_players = [p for p in sorted_players if p not in used_players]
    while len(remaining_players) >= 2:
        player1 = remaining_players.pop(0)
        for i, player2 in enumerate(remaining_players):
            if player2.name not in player1.opponents and player1.name not in player2.opponents:
                matchups.append((player1, player2))
                remaining_players.pop(i)
                break

    return matchups

def play_round(players: List[Player], data: Dict[str, List[Player]], filename: str):
    matchups = match_players(players)
    
    if not matchups:
        print("No more valid matchups available. Rankings are complete.")
        return False

    for player1, player2 in matchups:
        print(f"\nMatch: {player1} vs {player2}")
        winner = get_winner_input(player1, player2)
        loser = player2 if winner == player1 else player1

        winner.wins += 1
        loser.losses += 1
        winner.opponents.append(loser.name)
        loser.opponents.append(winner.name)

        save_data(data, filename)
        print(f"{winner.name} wins!")

    return True

def main():
    filename = "nfl_rankings.json"
    data = load_or_create_data(filename)

    while True:
        position = input("Enter the position to rank (qb/rb/te/wr) or 'q' to quit: ").strip().lower()
        if position == 'q':
            break

        if position not in data:
            print(f"No data found for {position}. Please make sure {position}.csv exists.")
            continue

        players = data[position]
        print(f"\nCurrent rankings for {position.upper()}:")
        for player in sorted(players, key=lambda x: (-x.wins, x.losses)):
            print(player)

        if play_round(players, data, filename):
            print(f"\nUpdated rankings for {position.upper()}:")
            for player in sorted(players, key=lambda x: (-x.wins, x.losses)):
                print(player)
        else:
            print(f"Rankings for {position.upper()} are complete.")

if __name__ == "__main__":
    main()