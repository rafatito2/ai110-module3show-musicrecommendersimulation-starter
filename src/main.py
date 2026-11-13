"""
Command line runner for the Music Recommender Simulation.

Run it from the project root with:

    python -m src.main                 # all profiles
    python -m src.main --experiment    # weight-shift experiment
    python -m src.main --mode mood-first
    python -m src.main --diverse       # penalize repeated artists and genres
"""

import argparse

from tabulate import tabulate

from src.recommender import STRATEGIES, load_songs, recommend_songs

# Three everyday listeners plus two profiles built to trick the scoring.
PROFILES = {
    "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.85},
    "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35, "likes_acoustic": True},
    "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.95},
    "Adversarial: Sad but Hyper": {"genre": "blues", "mood": "sad", "energy": 0.95},
    "Adversarial: Ghost Genre": {"genre": "k-pop", "mood": "happy", "energy": 0.5},
    # Profiles that use the advanced song attributes.
    "Focus Session": {
        "genre": "lofi", "mood": "focused", "energy": 0.4,
        "target_instrumentalness": 0.9, "mood_tags": ["mellow", "steady"],
        "favorite_decade": 2020, "prefers_popular": False,
    },
    "Clean Workout": {
        "genre": "pop", "mood": "intense", "energy": 0.9,
        "allow_explicit": False, "prefers_popular": True,
    },
}

# Experiment from Phase 4: double the importance of energy, halve genre.
EXPERIMENT_WEIGHTS = {"genre": 1.0, "energy": 3.0}


def print_recommendations(name: str, user_prefs: dict, recommendations: list) -> None:
    """Prints one profile's ranked recommendations as a table with score and reasons."""
    print(f"\n=== {name} ===")
    print(f"Profile: {user_prefs}")
    rows = [
        [rank, song["title"], song["artist"], song["genre"], f"{score:.2f}",
         "\n".join(explanation.split("; "))]
        for rank, (song, score, explanation) in enumerate(recommendations, start=1)
    ]
    headers = ["#", "Title", "Artist", "Genre", "Score", "Reasons"]
    print(tabulate(rows, headers=headers, tablefmt="grid"))


def run_experiment(songs: list, k: int) -> None:
    """Shows the same profile before and after the weight shift."""
    name = "High-Energy Pop"
    prefs = PROFILES[name]
    print_recommendations(f"{name} (baseline weights)", prefs, recommend_songs(prefs, songs, k))
    print_recommendations(
        f"{name} (experiment: genre 1.0, energy 3.0)",
        prefs,
        recommend_songs(prefs, songs, k, weights=EXPERIMENT_WEIGHTS),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument("-k", type=int, default=5, help="how many songs to recommend")
    parser.add_argument("--experiment", action="store_true", help="run the weight-shift experiment")
    parser.add_argument(
        "--mode", choices=list(STRATEGIES), default="balanced",
        help="ranking strategy to use",
    )
    parser.add_argument(
        "--diverse", action="store_true",
        help="apply the diversity penalty for repeated artists and genres",
    )
    args = parser.parse_args()

    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    if args.experiment:
        run_experiment(songs, args.k)
        return

    strategy = STRATEGIES[args.mode]
    print(f"Ranking mode: {strategy.name} ({strategy.description})")
    print(f"Diversity penalty: {'on' if args.diverse else 'off'}")

    for name, prefs in PROFILES.items():
        results = recommend_songs(prefs, songs, args.k, strategy=strategy, diversity=args.diverse)
        print_recommendations(name, prefs, results)


if __name__ == "__main__":
    main()
