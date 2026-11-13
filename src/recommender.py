import csv
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple

# Default point values from the Algorithm Recipe in the README.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "genre": 2.0,
    "mood": 1.0,
    "energy": 1.5,
    "acoustic": 0.5,
    # Advanced attributes: only used when the profile asks for them.
    "decade": 0.5,
    "mood_tag": 0.5,
    "popularity": 0.5,
    "instrumental": 0.5,
    "explicit_penalty": 2.0,
}

INT_FIELDS = {"id", "popularity", "release_decade"}
FLOAT_FIELDS = {"energy", "tempo_bpm", "valence", "danceability", "acousticness", "instrumentalness"}


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: int = 50
    release_decade: int = 0
    mood_tags: List[str] = field(default_factory=list)
    instrumentalness: float = 0.0
    explicit: bool = False


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    favorite_decade: Optional[int] = None
    mood_tags: Optional[List[str]] = None
    prefers_popular: Optional[bool] = None
    target_instrumentalness: Optional[float] = None
    allow_explicit: Optional[bool] = None


def profile_to_prefs(user: UserProfile) -> Dict:
    """Converts a UserProfile object into the prefs dictionary used by score_song."""
    prefs = {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "energy": user.target_energy,
        "likes_acoustic": user.likes_acoustic,
        "favorite_decade": user.favorite_decade,
        "mood_tags": user.mood_tags,
        "prefers_popular": user.prefers_popular,
        "target_instrumentalness": user.target_instrumentalness,
        "allow_explicit": user.allow_explicit,
    }
    return {key: value for key, value in prefs.items() if value is not None}


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Returns the k Song objects with the highest score for this user."""
        prefs = profile_to_prefs(user)
        ranked = sorted(
            self.songs,
            key=lambda song: score_song(prefs, asdict(song))[0],
            reverse=True,
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Returns the score and the reasons behind it as one readable sentence."""
        score, reasons = score_song(profile_to_prefs(user), asdict(song))
        return f"Score {score:.2f}: " + ", ".join(reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """Reads the song catalog from a CSV file and converts numeric columns to numbers."""
    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            for field in INT_FIELDS & row.keys():
                row[field] = int(row[field])
            for field in FLOAT_FIELDS & row.keys():
                row[field] = float(row[field])
            if "mood_tags" in row:
                row["mood_tags"] = [tag for tag in row["mood_tags"].split("|") if tag]
            if "explicit" in row:
                row["explicit"] = row["explicit"] == "1"
            songs.append(row)
    return songs


def score_song(
    user_prefs: Dict, song: Dict, weights: Optional[Dict[str, float]] = None
) -> Tuple[float, List[str]]:
    """Scores one song against the user's preferences and returns (score, reasons)."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    score = 0.0
    reasons: List[str] = []

    if user_prefs.get("genre") and song["genre"].lower() == user_prefs["genre"].lower():
        score += w["genre"]
        reasons.append(f"genre match: {song['genre']} (+{w['genre']:.2f})")

    if user_prefs.get("mood") and song["mood"].lower() == user_prefs["mood"].lower():
        score += w["mood"]
        reasons.append(f"mood match: {song['mood']} (+{w['mood']:.2f})")

    if user_prefs.get("energy") is not None:
        # Closeness, not size: 1.0 when the song sits exactly on the target.
        closeness = 1.0 - abs(song["energy"] - user_prefs["energy"])
        points = w["energy"] * closeness
        score += points
        reasons.append(
            f"energy {song['energy']:.2f} vs target {user_prefs['energy']:.2f} (+{points:.2f})"
        )

    if user_prefs.get("likes_acoustic") is not None:
        fit = song["acousticness"] if user_prefs["likes_acoustic"] else 1.0 - song["acousticness"]
        points = w["acoustic"] * fit
        score += points
        label = "acoustic" if user_prefs["likes_acoustic"] else "non-acoustic"
        reasons.append(f"{label} fit (+{points:.2f})")

    score += _score_advanced(user_prefs, song, w, reasons)
    return round(score, 2), reasons


def _score_advanced(user_prefs: Dict, song: Dict, w: Dict[str, float], reasons: List[str]) -> float:
    """Adds points for decade, mood tags, popularity, instrumentalness and explicit content."""
    points = 0.0

    decade = user_prefs.get("favorite_decade")
    if decade and song.get("release_decade"):
        gap = abs(song["release_decade"] - decade)
        if gap <= 10:
            earned = w["decade"] if gap == 0 else w["decade"] / 2
            points += earned
            label = "decade match" if gap == 0 else "neighboring decade"
            reasons.append(f"{label}: {song['release_decade']}s (+{earned:.2f})")

    wanted_tags = user_prefs.get("mood_tags")
    if wanted_tags:
        shared = sorted(set(wanted_tags) & set(song.get("mood_tags", [])))
        if shared:
            earned = w["mood_tag"] * len(shared)
            points += earned
            reasons.append(f"mood tags: {', '.join(shared)} (+{earned:.2f})")

    if user_prefs.get("prefers_popular") is not None and "popularity" in song:
        share = song["popularity"] / 100
        earned = w["popularity"] * (share if user_prefs["prefers_popular"] else 1.0 - share)
        points += earned
        label = "popular pick" if user_prefs["prefers_popular"] else "hidden gem"
        reasons.append(f"{label}, popularity {song['popularity']} (+{earned:.2f})")

    target = user_prefs.get("target_instrumentalness")
    if target is not None and "instrumentalness" in song:
        earned = w["instrumental"] * (1.0 - abs(song["instrumentalness"] - target))
        points += earned
        reasons.append(f"instrumentalness {song['instrumentalness']:.2f} (+{earned:.2f})")

    if user_prefs.get("allow_explicit") is False and song.get("explicit"):
        points -= w["explicit_penalty"]
        reasons.append(f"explicit content (-{w['explicit_penalty']:.2f})")

    return points


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    weights: Optional[Dict[str, float]] = None,
) -> List[Tuple[Dict, float, str]]:
    """Scores every song, sorts from highest to lowest and returns the top k with explanations."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, weights)
        scored.append((song, score, "; ".join(reasons)))
    # sorted() returns a new list and leaves the catalog order untouched.
    return sorted(scored, key=lambda item: item[1], reverse=True)[:k]
