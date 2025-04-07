from client import game_lobby


def main():
    # Example player name, replace with actual input
    player_name = "Player1"

    # Initialize the game lobby
    lobby = game_lobby.GameLobby(player_name)

    # Run the lobby
    lobby.run()


if __name__ == "__main__":
    main()
