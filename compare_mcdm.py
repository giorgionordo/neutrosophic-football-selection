"""
compare_mcdm.py

Reproducible player-level comparison between the individual neutrosophic-soft
score used by the football-team-selection framework and four MCDM benchmarks:

    * AHP-style quantitative ratings;
    * classical TOPSIS;
    * classical VIKOR;
    * single-valued neutrosophic TOPSIS.

The comparison is deliberately performed WITHIN each player's official role,
because data/weights.csv contains role-specific criterion weights. Phil Foden
(P14), for example, is ranked as a midfielder here because M is his official
role, even though he is also eligible as a forward in the team optimizer.

The reference ranking is the raw role-specific NOS already defined by the main
model:
    NOS_i^k = sum_j w_j^k (T_ij - alpha_I I_ij - alpha_F F_ij).

Spearman's rho measures agreement between each benchmark ranking and the
reference NOS ranking. It does not compare the benchmark methods with the
team-level TSF optimizer.

No third-party packages are required.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

from football_team_selection import (
    DEFAULT_ALPHA_F,
    DEFAULT_ALPHA_I,
    ROLES,
    Player,
    Triple,
    raw_nos,
    read_neutrosophic_matrix,
    read_players,
    read_weights,
)


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "data"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"

MethodScores = Dict[str, float]


def average_ranks(
    values: Mapping[str, float],
    *,
    higher_is_better: bool = True,
    tie_tol: float = 1e-12,
) -> Dict[str, float]:
    """Return 1-based average ranks, assigning rank 1 to the best value."""
    if tie_tol < 0:
        raise ValueError("tie_tol must be non-negative")
    if not values:
        raise ValueError("Cannot rank an empty mapping")

    ordered = sorted(
        values.items(),
        key=lambda item: ((-item[1]) if higher_is_better else item[1], item[0]),
    )

    ranks: Dict[str, float] = {}
    start = 0
    n = len(ordered)

    while start < n:
        end = start + 1
        anchor = ordered[start][1]
        while end < n and math.isclose(
            ordered[end][1],
            anchor,
            rel_tol=0.0,
            abs_tol=tie_tol,
        ):
            end += 1

        average = ((start + 1) + end) / 2.0
        for index in range(start, end):
            ranks[ordered[index][0]] = average
        start = end

    return ranks


def pearson_correlation(x: Sequence[float], y: Sequence[float]) -> float:
    """Pearson correlation, used here on rank vectors to obtain Spearman rho."""
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")
    if len(x) < 2:
        raise ValueError("At least two observations are required")

    mean_x = sum(x) / len(x)
    mean_y = sum(y) / len(y)

    dx = [value - mean_x for value in x]
    dy = [value - mean_y for value in y]
    denominator = math.sqrt(
        sum(value * value for value in dx)
        * sum(value * value for value in dy)
    )
    if denominator <= 0:
        raise ValueError("Spearman correlation is undefined for a constant ranking")

    return sum(a * b for a, b in zip(dx, dy)) / denominator


def spearman_from_ranks(
    reference_ranks: Mapping[str, float],
    method_ranks: Mapping[str, float],
) -> float:
    """Spearman rho as Pearson correlation of average ranks."""
    codes = sorted(reference_ranks)
    if set(codes) != set(method_ranks):
        raise ValueError("Rank mappings must refer to the same players")

    return pearson_correlation(
        [reference_ranks[code] for code in codes],
        [method_ranks[code] for code in codes],
    )


def ahp_ratings_scores(
    player_codes: Sequence[str],
    matrix: Mapping[str, Sequence[Triple]],
    weights: Sequence[float],
) -> MethodScores:
    """Quantitative AHP-ratings benchmark using T as local criterion priorities.

    The criterion weights are the role-specific weights already supplied by the
    case study. This is intentionally a ratings-mode benchmark; it does not
    invent pairwise player-judgment matrices that are absent from the data.
    """
    return {
        code: sum(
            weight * triple[0]
            for weight, triple in zip(weights, matrix[code])
        )
        for code in player_codes
    }


def topsis_scores(
    player_codes: Sequence[str],
    matrix: Mapping[str, Sequence[Triple]],
    weights: Sequence[float],
) -> MethodScores:
    """Classical TOPSIS on T components, with vector normalization.

    All criteria are benefit criteria because T is already constructed so that
    larger values mean better criterion satisfaction.
    """
    n_criteria = len(weights)
    if n_criteria == 0:
        raise ValueError("At least one criterion is required")

    denominators = []
    for j in range(n_criteria):
        denominator = math.sqrt(sum(matrix[code][j][0] ** 2 for code in player_codes))
        denominators.append(denominator)

    weighted: Dict[str, List[float]] = {}
    for code in player_codes:
        row = []
        for j, weight in enumerate(weights):
            denominator = denominators[j]
            normalized = matrix[code][j][0] / denominator if denominator > 0 else 0.0
            row.append(weight * normalized)
        weighted[code] = row

    positive = [
        max(weighted[code][j] for code in player_codes)
        for j in range(n_criteria)
    ]
    negative = [
        min(weighted[code][j] for code in player_codes)
        for j in range(n_criteria)
    ]

    scores: MethodScores = {}
    for code in player_codes:
        d_plus = math.sqrt(
            sum((weighted[code][j] - positive[j]) ** 2 for j in range(n_criteria))
        )
        d_minus = math.sqrt(
            sum((weighted[code][j] - negative[j]) ** 2 for j in range(n_criteria))
        )
        total = d_plus + d_minus
        scores[code] = d_minus / total if total > 0 else 0.5

    return scores


def vikor_scores(
    player_codes: Sequence[str],
    matrix: Mapping[str, Sequence[Triple]],
    weights: Sequence[float],
    *,
    v: float = 0.5,
) -> MethodScores:
    """Classical VIKOR compromise index Q on the T components.

    Lower Q is better. Constant criteria contribute zero.
    """
    if not 0.0 <= v <= 1.0:
        raise ValueError("VIKOR v must lie in [0,1]")

    n_criteria = len(weights)
    best = [
        max(matrix[code][j][0] for code in player_codes)
        for j in range(n_criteria)
    ]
    worst = [
        min(matrix[code][j][0] for code in player_codes)
        for j in range(n_criteria)
    ]

    s_values: Dict[str, float] = {}
    r_values: Dict[str, float] = {}

    for code in player_codes:
        terms: List[float] = []
        for j, weight in enumerate(weights):
            spread = best[j] - worst[j]
            if spread <= 0:
                term = 0.0
            else:
                term = weight * (best[j] - matrix[code][j][0]) / spread
            terms.append(term)

        s_values[code] = sum(terms)
        r_values[code] = max(terms) if terms else 0.0

    s_best = min(s_values.values())
    s_worst = max(s_values.values())
    r_best = min(r_values.values())
    r_worst = max(r_values.values())

    scores: MethodScores = {}
    for code in player_codes:
        s_part = (
            (s_values[code] - s_best) / (s_worst - s_best)
            if s_worst > s_best
            else 0.0
        )
        r_part = (
            (r_values[code] - r_best) / (r_worst - r_best)
            if r_worst > r_best
            else 0.0
        )
        scores[code] = v * s_part + (1.0 - v) * r_part

    return scores


def neutrosophic_topsis_scores(
    player_codes: Sequence[str],
    matrix: Mapping[str, Sequence[Triple]],
    weights: Sequence[float],
) -> MethodScores:
    """Single-valued neutrosophic TOPSIS with weighted Euclidean distance.

    For each criterion j, the positive ideal is
        (max T_ij, min I_ij, min F_ij)
    and the negative ideal is
        (min T_ij, max I_ij, max F_ij).

    The distance uses the role-specific criterion weights:
        d(A,B) = sqrt((1/3) * sum_j w_j *
                      [(T_A-T_B)^2 + (I_A-I_B)^2 + (F_A-F_B)^2]).
    The closeness coefficient d_minus / (d_plus + d_minus) is ranked high-to-low.
    """
    n_criteria = len(weights)
    positive: List[Triple] = []
    negative: List[Triple] = []

    for j in range(n_criteria):
        t_values = [matrix[code][j][0] for code in player_codes]
        i_values = [matrix[code][j][1] for code in player_codes]
        f_values = [matrix[code][j][2] for code in player_codes]

        positive.append((max(t_values), min(i_values), min(f_values)))
        negative.append((min(t_values), max(i_values), max(f_values)))

    def distance(code: str, ideal: Sequence[Triple]) -> float:
        total = 0.0
        for weight, actual, target in zip(weights, matrix[code], ideal):
            total += weight * sum(
                (a - b) ** 2
                for a, b in zip(actual, target)
            )
        return math.sqrt(total / 3.0)

    scores: MethodScores = {}
    for code in player_codes:
        d_plus = distance(code, positive)
        d_minus = distance(code, negative)
        total = d_plus + d_minus
        scores[code] = d_minus / total if total > 0 else 0.5

    return scores


def role_player_codes(
    players: Mapping[str, Player],
    role: str,
) -> List[str]:
    """Official-role candidates, sorted deterministically by player index."""
    def player_key(code: str) -> Tuple[int, str]:
        if code.startswith("P") and code[1:].isdigit():
            return int(code[1:]), code
        return 10**9, code

    return sorted(
        (
            player.code
            for player in players.values()
            if player.official_role == role
        ),
        key=player_key,
    )


def write_player_rankings(
    path: Path,
    rows: Iterable[Mapping[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "role",
        "player",
        "name",
        "reference_nos",
        "reference_rank",
        "ahp_ratings_score",
        "ahp_rank",
        "topsis_score",
        "topsis_rank",
        "vikor_q",
        "vikor_rank",
        "neutrosophic_topsis_score",
        "neutrosophic_topsis_rank",
    ]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_spearman(
    path: Path,
    rows: Iterable[Mapping[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["role", "n_players", "method", "spearman_vs_reference"]

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_comparison(
    *,
    data_dir: Path,
    output_dir: Path,
    alpha_i: float,
    alpha_f: float,
    vikor_v: float,
) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    players = read_players(data_dir / "players.csv")
    weights = read_weights(data_dir / "weights.csv")
    matrix = read_neutrosophic_matrix(
        data_dir / "neutrosophic_matrix.csv",
        players.keys(),
    )

    ranking_rows: List[Dict[str, object]] = []
    spearman_rows: List[Dict[str, object]] = []

    for role in ROLES:
        codes = role_player_codes(players, role)
        if len(codes) < 2:
            continue

        role_weights = weights[role]

        reference = {
            code: raw_nos(matrix[code], role_weights, alpha_i, alpha_f)
            for code in codes
        }
        ahp = ahp_ratings_scores(codes, matrix, role_weights)
        topsis = topsis_scores(codes, matrix, role_weights)
        vikor = vikor_scores(codes, matrix, role_weights, v=vikor_v)
        neutro_topsis = neutrosophic_topsis_scores(codes, matrix, role_weights)

        reference_rank = average_ranks(reference, higher_is_better=True)
        ahp_rank = average_ranks(ahp, higher_is_better=True)
        topsis_rank = average_ranks(topsis, higher_is_better=True)
        vikor_rank = average_ranks(vikor, higher_is_better=False)
        neutro_topsis_rank = average_ranks(neutro_topsis, higher_is_better=True)

        for code in codes:
            ranking_rows.append(
                {
                    "role": role,
                    "player": code,
                    "name": players[code].name,
                    "reference_nos": f"{reference[code]:.9f}",
                    "reference_rank": f"{reference_rank[code]:.6f}",
                    "ahp_ratings_score": f"{ahp[code]:.9f}",
                    "ahp_rank": f"{ahp_rank[code]:.6f}",
                    "topsis_score": f"{topsis[code]:.9f}",
                    "topsis_rank": f"{topsis_rank[code]:.6f}",
                    "vikor_q": f"{vikor[code]:.9f}",
                    "vikor_rank": f"{vikor_rank[code]:.6f}",
                    "neutrosophic_topsis_score": f"{neutro_topsis[code]:.9f}",
                    "neutrosophic_topsis_rank": f"{neutro_topsis_rank[code]:.6f}",
                }
            )

        method_ranks = [
            ("AHP-ratings", ahp_rank),
            ("TOPSIS", topsis_rank),
            ("VIKOR", vikor_rank),
            ("Neutrosophic TOPSIS", neutro_topsis_rank),
        ]
        for method, ranks in method_ranks:
            rho = spearman_from_ranks(reference_rank, ranks)
            spearman_rows.append(
                {
                    "role": role,
                    "n_players": len(codes),
                    "method": method,
                    "spearman_vs_reference": f"{rho:.9f}",
                }
            )

    write_player_rankings(output_dir / "mcdm_player_rankings.csv", ranking_rows)
    write_spearman(output_dir / "mcdm_spearman.csv", spearman_rows)

    return ranking_rows, spearman_rows


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare role-specific player rankings from the individual "
            "neutrosophic-soft score with AHP-ratings, TOPSIS, VIKOR, "
            "and single-valued neutrosophic TOPSIS."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Input data directory (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--alpha-i",
        type=float,
        default=DEFAULT_ALPHA_I,
        help=f"Indeterminacy penalty in reference NOS (default: {DEFAULT_ALPHA_I})",
    )
    parser.add_argument(
        "--alpha-f",
        type=float,
        default=DEFAULT_ALPHA_F,
        help=f"Falsity penalty in reference NOS (default: {DEFAULT_ALPHA_F})",
    )
    parser.add_argument(
        "--vikor-v",
        type=float,
        default=0.5,
        help="VIKOR strategy weight v in [0,1] (default: 0.5)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.alpha_i < 0 or args.alpha_f < 0:
        raise SystemExit("--alpha-i and --alpha-f must be non-negative")
    if not 0.0 <= args.vikor_v <= 1.0:
        raise SystemExit("--vikor-v must lie in [0,1]")

    _, spearman_rows = run_comparison(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        alpha_i=args.alpha_i,
        alpha_f=args.alpha_f,
        vikor_v=args.vikor_v,
    )

    print("Role-specific Spearman correlations vs. reference NOS")
    print("(G is reported for reproducibility but n=2 is too small for interpretation.)")
    print()
    for row in spearman_rows:
        print(
            f"{row['role']:>1}  "
            f"{row['method']:<22} "
            f"n={row['n_players']:>2}  "
            f"rho={float(row['spearman_vs_reference']): .6f}"
        )

    print()
    print(f"Wrote {args.output_dir / 'mcdm_player_rankings.csv'}")
    print(f"Wrote {args.output_dir / 'mcdm_spearman.csv'}")


if __name__ == "__main__":
    main()
