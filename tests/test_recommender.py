from src.recommender import Song, UserProfile, Recommender

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---- Tests for the functional API used by src/main.py ----

from src.recommender import load_songs, recommend_songs, score_song

POP_FAN = {"genre": "pop", "mood": "happy", "energy": 0.8}


def make_song(**overrides) -> dict:
    song = {
        "id": 1, "title": "T", "artist": "A", "genre": "pop", "mood": "happy",
        "energy": 0.8, "tempo_bpm": 120.0, "valence": 0.8,
        "danceability": 0.8, "acousticness": 0.2,
    }
    song.update(overrides)
    return song


def test_load_songs_reads_catalog_and_converts_numbers():
    songs = load_songs("data/songs.csv")
    assert len(songs) >= 15
    assert isinstance(songs[0]["energy"], float)
    assert isinstance(songs[0]["id"], int)


def test_perfect_match_gets_full_points_and_reasons():
    score, reasons = score_song(POP_FAN, make_song())
    assert score == 4.5  # 2.0 genre + 1.0 mood + 1.5 energy
    assert len(reasons) == 3
    assert any("genre match" in r for r in reasons)


def test_energy_rewards_closeness_not_size():
    close, _ = score_song({"energy": 0.4}, make_song(energy=0.45))
    loud, _ = score_song({"energy": 0.4}, make_song(energy=0.95))
    assert close > loud


def test_genre_outweighs_mood():
    genre_only, _ = score_song(POP_FAN, make_song(mood="sad"))
    mood_only, _ = score_song(POP_FAN, make_song(genre="rock"))
    assert genre_only > mood_only


def test_recommend_songs_is_sorted_and_limited_to_k():
    songs = load_songs("data/songs.csv")
    results = recommend_songs(POP_FAN, songs, k=3)
    scores = [score for _, score, _ in results]
    assert len(results) == 3
    assert scores == sorted(scores, reverse=True)
    assert results[0][0]["title"] == "Sunrise City"


def test_custom_weights_change_the_score():
    base, _ = score_song(POP_FAN, make_song())
    shifted, _ = score_song(POP_FAN, make_song(), weights={"genre": 1.0, "energy": 3.0})
    assert shifted == 5.0 and base == 4.5


# ---- Advanced attributes ----

def test_base_profile_ignores_advanced_attributes():
    plain, _ = score_song(POP_FAN, make_song())
    rich, _ = score_song(POP_FAN, make_song(popularity=99, explicit=True, release_decade=1980))
    assert plain == rich


def test_explicit_song_is_penalized_when_not_allowed():
    prefs = {**POP_FAN, "allow_explicit": False}
    clean, _ = score_song(prefs, make_song(explicit=False))
    explicit, reasons = score_song(prefs, make_song(explicit=True))
    assert clean - explicit == 2.0
    assert any("explicit" in r for r in reasons)


def test_shared_mood_tags_and_decade_add_points():
    prefs = {**POP_FAN, "mood_tags": ["warm", "nostalgic"], "favorite_decade": 1990}
    score, _ = score_song(prefs, make_song(mood_tags=["warm", "nostalgic"], release_decade=1990))
    assert score == 4.5 + 1.0 + 0.5
