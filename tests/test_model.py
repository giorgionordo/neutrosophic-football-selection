"""Automated tests for the neutrosophic football-selection framework."""

from __future__ import annotations

from pathlib import Path
import unittest

from football_team_selection import (
    ModelParameters,
    compute_all_scores,
    compute_oti,
    compute_sigma,
    compute_tci_matrix,
    optimize_433,
    orbit_open,
    read_interaction_matrix,
    read_neutrosophic_matrix,
    read_players,
    read_weights,
    selection_frequencies,
)


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


class ModelReproducibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.players = read_players(DATA_DIR / "players.csv")
        cls.player_codes = tuple(cls.players.keys())
        cls.weights = read_weights(DATA_DIR / "weights.csv")
        cls.neutrosophic_matrix = read_neutrosophic_matrix(
            DATA_DIR / "neutrosophic_matrix.csv",
            cls.player_codes,
        )
        cls.interaction = read_interaction_matrix(
            DATA_DIR / "interaction_matrix.csv",
            cls.player_codes,
        )
        cls.parameters = ModelParameters(
            alpha_I=1.0,
            alpha_F=1.0,
            alpha=0.50,
            beta=0.35,
            gamma=0.15,
        )
        _, cls.normalized_scores = compute_all_scores(
            cls.players,
            cls.neutrosophic_matrix,
            cls.weights,
            cls.parameters,
        )
        cls.tci = compute_tci_matrix(cls.interaction, cls.player_codes)
        cls.sigma = compute_sigma(cls.tci, cls.player_codes)
        cls.oti = compute_oti(cls.tci, cls.sigma)

    def test_role_weights_are_normalized(self) -> None:
        for role, values in self.weights.items():
            with self.subTest(role=role):
                self.assertAlmostEqual(sum(values), 1.0, places=12)

    def test_interaction_matrix_has_unit_diagonal(self) -> None:
        for player in self.player_codes:
            with self.subTest(player=player):
                self.assertEqual(self.interaction[player][player], 1.0)

    def test_tci_is_symmetric_with_unit_diagonal(self) -> None:
        for player_i in self.player_codes:
            self.assertEqual(self.tci[player_i][player_i], 1.0)
            for player_j in self.player_codes:
                with self.subTest(player_i=player_i, player_j=player_j):
                    self.assertAlmostEqual(
                        self.tci[player_i][player_j],
                        self.tci[player_j][player_i],
                        places=15,
                    )

    def test_sigma_never_selects_self(self) -> None:
        for player, successor in self.sigma.items():
            with self.subTest(player=player):
                self.assertNotEqual(player, successor)

    def test_sigma_uses_lower_player_index_to_break_ties(self) -> None:
        tci = {
            "P1": {"P1": 1.0, "P2": 0.5, "P3": 0.5},
            "P2": {"P1": 0.4, "P2": 1.0, "P3": 0.4},
            "P3": {"P1": 0.4, "P2": 0.4, "P3": 1.0},
        }
        sigma = compute_sigma(tci, ("P1", "P2", "P3"))
        self.assertEqual(sigma["P1"], "P2")
        self.assertEqual(sigma["P2"], "P1")
        self.assertEqual(sigma["P3"], "P1")

    def test_orbit_open_condition(self) -> None:
        sigma = {"P1": "P2", "P2": "P1", "P3": "P2"}
        self.assertTrue(orbit_open(("P1", "P2"), sigma))
        self.assertFalse(orbit_open(("P1", "P3"), sigma))

    def test_baseline_optimum_is_reproduced(self) -> None:
        optimum, feasible_count = optimize_433(
            self.players,
            self.normalized_scores,
            self.tci,
            self.sigma,
            self.oti,
            self.parameters,
        )

        expected_assignment = (
            ("P1", "G"),
            ("P3", "D"),
            ("P5", "D"),
            ("P7", "D"),
            ("P8", "D"),
            ("P10", "M"),
            ("P11", "M"),
            ("P13", "M"),
            ("P14", "F"),
            ("P15", "F"),
            ("P16", "F"),
        )

        self.assertEqual(feasible_count, 13020)
        self.assertEqual(optimum.assignment, expected_assignment)
        self.assertAlmostEqual(optimum.tsf, 0.4556941843506398, places=12)
        self.assertTrue(optimum.orbit_open)
        self.assertEqual(optimum.retained_orbit_transitions, 11)

    def test_selection_frequency_computation(self) -> None:
        rows = [
            {"selected_players": "P1|P2"},
            {"selected_players": "P1|P3"},
        ]
        frequencies = {
            row["player"]: row
            for row in selection_frequencies(rows, self.players)
        }

        self.assertEqual(frequencies["P1"]["selection_count"], 2)
        self.assertEqual(frequencies["P1"]["selection_frequency"], 1.0)
        self.assertEqual(frequencies["P2"]["selection_count"], 1)
        self.assertEqual(frequencies["P2"]["selection_frequency"], 0.5)
        self.assertEqual(frequencies["P4"]["selection_count"], 0)


if __name__ == "__main__":
    unittest.main()
