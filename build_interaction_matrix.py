"""
Football Team Selection under Uncertainty
build_interaction_matrix.py

Builds a reproducible directed tactical passing-affinity matrix from the
season-level FBref statistics used in the case study.

For each player P_i, p_i is the min-max normalized number of progressive
passes per 90 minutes and r_i is the min-max normalized number of progressive
receptions per 90 minutes. To reduce small-sample distortion, each player is
assigned the reliability factor

    rho_i = min(1, 90s_i / REFERENCE_NINETIES).

For i != j, the directed raw affinity from P_i to P_j is

    b_ij = sqrt(rho_i * rho_j) * p_i * r_j.

The off-diagonal values are then divided by their global maximum so that the
largest directed affinity equals 1. Following the similarity convention used
in the manuscript, the diagonal is set to a_ii = 1. The orbit successor is
nevertheless always chosen among k != i, so diagonal entries never determine
the orbit map.

This matrix represents passing-role interaction potential, not observed
player-to-player pass counts. This distinction is explicitly documented in
the numerical case study.

----------------------------------------------------------------------------------
author: Giorgio Nordo - Dipartimento MIFT. Università di Messina, Italy
www.nordo.it   |  giorgio.nordo@unime.it
"""

from __future__ import annotations

#------------------ import of required modules
from pathlib import Path
from typing import Dict, Mapping, Tuple
import csv
import math


REFERENCE_NINETIES = 20.0
NORMALIZATION_MIN_NINETIES = 5.0

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


#------------------ function read_metrics
def read_metrics(path: str | Path) -> Dict[str, Dict[str, float]]:
    result: Dict[str, Dict[str, float]] = {}

    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {
            "player",
            "nineties",
            "progressive_passes_per90",
            "progressive_receptions_per90",
        }
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: required columns are {sorted(required)}")

        for row in reader:
            player = row["player"].strip()
            result[player] = {
                "nineties": float(row["nineties"]),
                "progressive_passes_per90": float(row["progressive_passes_per90"]),
                "progressive_receptions_per90": float(row["progressive_receptions_per90"]),
            }

    return result


#------------------ function minmax_bounds
def minmax_bounds(
    metrics: Mapping[str, Mapping[str, float]],
    field: str,
) -> Tuple[float, float]:
    reference = [
        values[field]
        for values in metrics.values()
        if values["nineties"] >= NORMALIZATION_MIN_NINETIES
    ]

    if len(reference) < 2:
        reference = [values[field] for values in metrics.values()]

    return min(reference), max(reference)


#------------------ function normalized
def normalized(value: float, lower: float, upper: float) -> float:
    if math.isclose(lower, upper, abs_tol=1e-12):
        return 0.5

    result = (value - lower) / (upper - lower)
    return max(0.0, min(1.0, result))


#------------------ function build_interaction_matrix
def build_interaction_matrix(
    raw_path: str | Path,
    output_path: str | Path,
) -> None:
    metrics = read_metrics(raw_path)
    players = sorted(
        metrics,
        key=lambda code: (
            int(code[1:]) if code.startswith("P") and code[1:].isdigit() else 10**9,
            code,
        ),
    )

    p_lower, p_upper = minmax_bounds(metrics, "progressive_passes_per90")
    r_lower, r_upper = minmax_bounds(metrics, "progressive_receptions_per90")

    p: Dict[str, float] = {}
    r: Dict[str, float] = {}
    rho: Dict[str, float] = {}

    for player in players:
        values = metrics[player]
        p[player] = normalized(
            values["progressive_passes_per90"],
            p_lower,
            p_upper,
        )
        r[player] = normalized(
            values["progressive_receptions_per90"],
            r_lower,
            r_upper,
        )
        rho[player] = min(
            1.0,
            values["nineties"] / REFERENCE_NINETIES,
        )

    raw: Dict[Tuple[str, str], float] = {}
    for player_i in players:
        for player_j in players:
            if player_i == player_j:
                raw[(player_i, player_j)] = 1.0
            else:
                raw[(player_i, player_j)] = (
                    math.sqrt(rho[player_i] * rho[player_j])
                    * p[player_i]
                    * r[player_j]
                )

    maximum = max(
        value
        for (player_i, player_j), value in raw.items()
        if player_i != player_j
    )
    if maximum <= 0:
        raise ValueError("The interaction matrix has no positive off-diagonal value")

    output_path = Path(output_path)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["player", *players])

        for player_i in players:
            row = [player_i]
            for player_j in players:
                value = (
                    1.0
                    if player_i == player_j
                    else raw[(player_i, player_j)] / maximum
                )
                row.append(f"{value:.9f}")
            writer.writerow(row)


#------------------ main program
if __name__ == "__main__":
    raw_path = DATA_DIR / "raw_player_metrics.csv"
    output_path = DATA_DIR / "interaction_matrix.csv"

    build_interaction_matrix(raw_path, output_path)
    print(f"Created: {output_path}")
