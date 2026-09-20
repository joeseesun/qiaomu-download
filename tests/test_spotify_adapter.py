#!/usr/bin/env python3
"""Unit tests for the Spotify public-metadata adapter."""

import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "spotify_adapter.py"
SPEC = importlib.util.spec_from_file_location("spotify_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
spotify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(spotify)


class SpotifyAdapterTests(unittest.TestCase):
    def test_normalizes_track_and_drops_tracking_query(self) -> None:
        url, track_id = spotify.normalize_track_url(
            "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT?si=tracking"
        )
        self.assertEqual(url, "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT")
        self.assertEqual(track_id, "4cOdK2wGLETKBW3PvgPWqT")

    def test_rejects_collections_and_non_spotify_hosts(self) -> None:
        for url in (
            "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            "https://example.com/track/4cOdK2wGLETKBW3PvgPWqT",
        ):
            with self.assertRaises(spotify.AdapterError):
                spotify.normalize_track_url(url)

    def test_exact_verified_candidate_scores_high(self) -> None:
        track = {"title": "Example Song", "artist": "Example Artist", "duration": 200}
        item = {"title": "Example Artist - Example Song", "channel": "Example Artist",
                "duration": 200, "channel_is_verified": True}
        score, detail = spotify.score(track, item)
        self.assertGreater(score, 85)
        self.assertEqual(detail["variant_penalty"], 0)

    def test_variant_and_duration_mismatch_are_penalized(self) -> None:
        track = {"title": "Example Song", "artist": "Example Artist", "duration": 200}
        exact = {"title": "Example Artist - Example Song", "channel": "Example Artist", "duration": 200}
        wrong = {"title": "Example Artist - Example Song live remix", "channel": "Example Artist", "duration": 420}
        exact_score, _ = spotify.score(track, exact)
        wrong_score, wrong_detail = spotify.score(track, wrong)
        self.assertGreater(exact_score, wrong_score)
        self.assertGreater(wrong_detail["variant_penalty"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
