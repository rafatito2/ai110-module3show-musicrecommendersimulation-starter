"""
Command line runner for the Music Recommender Simulation.

Run it from the project root with:  python -m src.main
"""

from src.recommender import load_songs, recommend_songs


def print_recommendations(name: str, user_prefs: dict, recommendations: list) -> None:
    """Prints one profile's ranked recommendations with score and reasons."""
    print(f"\n=== {name} ===")
    print(f"Profile: {user_prefs}\n")
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} by {song['artist']} - Score: {score:.2f}")
        for reason in explanation.split("; "):
            print(f"     - {reason}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    recommendations = recommend_songs(user_prefs, songs, k=5)
    print_recommendations("Default Pop/Happy", user_prefs, recommendations)


if __name__ == "__main__":
    main()
