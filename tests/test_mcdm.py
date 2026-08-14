from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compare_mcdm import run_comparison


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


class MCDMComparisonReproducibilityTests(unittest.TestCase):
    def test_role_specific_spearman_values_are_reproduced(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, rows = run_comparison(
                data_dir=DATA_DIR,
                output_dir=Path(tmpdir),
                alpha_i=1.0,
                alpha_f=1.0,
                vikor_v=0.5,
            )

        observed = {
            (row["role"], row["method"]): float(row["spearman_vs_reference"])
            for row in rows
        }

        expected = {
            ("G", "Weighted-sum T (AHP-style proxy)"): 1.0,
            ("G", "TOPSIS"): 1.0,
            ("G", "VIKOR"): 1.0,
            ("G", "Neutrosophic TOPSIS"): 1.0,
            ("D", "Weighted-sum T (AHP-style proxy)"): 1.0,
            ("D", "TOPSIS"): 0.542857143,
            ("D", "VIKOR"): 0.371428571,
            ("D", "Neutrosophic TOPSIS"): 1.0,
            ("M", "Weighted-sum T (AHP-style proxy)"): 0.476190476,
            ("M", "TOPSIS"): 0.714285714,
            ("M", "VIKOR"): 0.595238095,
            ("M", "Neutrosophic TOPSIS"): 1.0,
            ("F", "Weighted-sum T (AHP-style proxy)"): -0.4,
            ("F", "TOPSIS"): 0.2,
            ("F", "VIKOR"): -0.8,
            ("F", "Neutrosophic TOPSIS"): 1.0,
        }

        self.assertEqual(set(observed), set(expected))
        for key, expected_value in expected.items():
            self.assertAlmostEqual(observed[key], expected_value, places=8)

    def test_ahp_style_row_is_explicitly_marked_as_proxy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            _, rows = run_comparison(
                data_dir=DATA_DIR,
                output_dir=Path(tmpdir),
                alpha_i=1.0,
                alpha_f=1.0,
                vikor_v=0.5,
            )

        proxy_rows = [
            row for row in rows
            if row["method"] == "Weighted-sum T (AHP-style proxy)"
        ]
        self.assertTrue(proxy_rows)
        for row in proxy_rows:
            self.assertIn("not a full AHP", row["status"])


if __name__ == "__main__":
    unittest.main()
