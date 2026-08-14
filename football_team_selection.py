"""
Football Team Selection under Uncertainty
football_team_selection.py

Reproducible implementation of the neutrosophic-soft orbit framework
for constrained football starting-XI selection.

The module implements:
    - role-specific neutrosophic scores;
    - normalized player scores;
    - tactical compatibility from a directed interaction matrix;
    - the deterministic orbit map and forward orbits;
    - the Orbit Tactical Interaction index (OTI);
    - multi-position eligibility;
    - exhaustive 4-3-3 optimization;
    - orbit-retention and orbit-openness diagnostics;
    - Monte Carlo sensitivity analysis.

----------------------------------------------------------------------------------
author: Giorgio Nordo - Dipartimento MIFT. Università di Messina, Italy
www.nordo.it   |  giorgio.nordo@unime.it
"""

from __future__ import annotations

#------------------ import of required modules
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from random import Random
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple
import argparse
import csv
import math


Role = str
PlayerCode = str
Triple = Tuple[float, float, float]

ROLES: Tuple[Role, ...] = ("G", "D", "M", "F")
ROLE_COUNTS: Dict[Role, int] = {"G": 1, "D": 4, "M": 3, "F": 3}
N_STARTERS = sum(ROLE_COUNTS.values())
N_PAIRS = N_STARTERS * (N_STARTERS - 1) // 2

#------------------ default model parameters
DEFAULT_ALPHA_I = 1.0
DEFAULT_ALPHA_F = 1.0
DEFAULT_ALPHA = 0.50
DEFAULT_BETA = 0.35
DEFAULT_GAMMA = 0.15

#------------------ default folders
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = BASE_DIR / "data"
DEFAULT_OUTPUT_DIR = BASE_DIR / "output"


#------------------ class Player
@dataclass(frozen=True)
class Player:
    code: PlayerCode
    name: str
    official_role: Role
    eligible_roles: Tuple[Role, ...]

    # method is_eligible
    def is_eligible(self, role: Role) -> bool:
        return role in self.eligible_roles


#------------------ class ModelParameters
@dataclass(frozen=True)
class ModelParameters:
    alpha_I: float
    alpha_F: float
    alpha: float
    beta: float
    gamma: float

    # method validate
    def validate(self) -> None:
        if self.alpha_I < 0 or self.alpha_F < 0:
            raise ValueError("alpha_I and alpha_F must be non-negative")
        if min(self.alpha, self.beta, self.gamma) < 0:
            raise ValueError("alpha, beta and gamma must be non-negative")
        if not math.isclose(self.alpha + self.beta + self.gamma, 1.0, abs_tol=1e-12):
            raise ValueError("alpha + beta + gamma must be equal to 1")


#------------------ class TeamResult
@dataclass(frozen=True)
class TeamResult:
    assignment: Tuple[Tuple[PlayerCode, Role], ...]
    selected: Tuple[PlayerCode, ...]
    individual_component: float
    compatibility_component: float
    orbit_component: float
    tsf: float
    retained_orbit_transitions: int
    orbit_open: bool

    # method role_of
    def role_of(self, player_code: PlayerCode) -> Role | None:
        for code, role in self.assignment:
            if code == player_code:
                return role
        return None


#------------------ function read_players
def read_players(path: str | Path) -> Dict[PlayerCode, Player]:
    players: Dict[PlayerCode, Player] = {}

    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"code", "name", "official_role", "eligible_roles"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: required columns are {sorted(required)}")

        for row in reader:
            code = row["code"].strip()
            official_role = row["official_role"].strip()
            eligible_roles = tuple(
                role.strip()
                for role in row["eligible_roles"].split("|")
                if role.strip()
            )

            if not code:
                raise ValueError(f"{path}: empty player code")
            if code in players:
                raise ValueError(f"{path}: duplicated player code {code}")
            if official_role not in ROLES:
                raise ValueError(f"{path}: invalid official role {official_role} for {code}")
            if not eligible_roles:
                raise ValueError(f"{path}: no eligible role declared for {code}")
            if any(role not in ROLES for role in eligible_roles):
                raise ValueError(f"{path}: invalid eligible role for {code}")
            if official_role not in eligible_roles:
                raise ValueError(
                    f"{path}: official role {official_role} must be included "
                    f"among eligible roles for {code}"
                )

            players[code] = Player(
                code=code,
                name=row["name"].strip(),
                official_role=official_role,
                eligible_roles=eligible_roles,
            )

    if not players:
        raise ValueError(f"{path}: no player was loaded")

    return players


#------------------ function read_weights
def read_weights(path: str | Path) -> Dict[Role, Tuple[float, ...]]:
    weights: Dict[Role, List[float]] = {role: [] for role in ROLES}

    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"criterion", *ROLES}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: required columns are {sorted(required)}")

        rows = list(reader)

    if len(rows) != 12:
        raise ValueError(f"{path}: exactly 12 criterion rows are required")

    for row in rows:
        for role in ROLES:
            value = float(row[role])
            if value < 0:
                raise ValueError(f"{path}: negative weight for role {role}")
            weights[role].append(value)

    result: Dict[Role, Tuple[float, ...]] = {}
    for role, values in weights.items():
        total = sum(values)
        if not math.isclose(total, 1.0, abs_tol=1e-9):
            raise ValueError(
                f"{path}: weights for role {role} sum to {total:.12f}, not 1"
            )
        result[role] = tuple(values)

    return result


#------------------ function read_neutrosophic_matrix
def read_neutrosophic_matrix(
    path: str | Path,
    player_codes: Iterable[PlayerCode],
) -> Dict[PlayerCode, Tuple[Triple, ...]]:
    expected_players = set(player_codes)
    matrix: Dict[PlayerCode, Dict[int, Triple]] = {}

    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"player", "criterion", "T", "I", "F"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path}: required columns are {sorted(required)}")

        for row in reader:
            player = row["player"].strip()
            if player not in expected_players:
                raise ValueError(f"{path}: unknown player {player}")

            criterion_text = row["criterion"].strip().upper()
            if not criterion_text.startswith("C"):
                raise ValueError(f"{path}: invalid criterion {criterion_text}")
            criterion = int(criterion_text[1:])
            if not 1 <= criterion <= 12:
                raise ValueError(f"{path}: invalid criterion {criterion_text}")

            triple = (float(row["T"]), float(row["I"]), float(row["F"]))
            if any(x < 0 or x > 1 for x in triple):
                raise ValueError(
                    f"{path}: neutrosophic components must lie in [0,1] "
                    f"for {player}, {criterion_text}"
                )

            matrix.setdefault(player, {})
            if criterion in matrix[player]:
                raise ValueError(
                    f"{path}: duplicated value for {player}, {criterion_text}"
                )
            matrix[player][criterion] = triple

    missing_players = expected_players.difference(matrix)
    if missing_players:
        raise ValueError(
            f"{path}: missing neutrosophic data for "
            f"{', '.join(sorted(missing_players))}"
        )

    result: Dict[PlayerCode, Tuple[Triple, ...]] = {}
    for player in sorted(expected_players):
        criteria = matrix[player]
        missing = [j for j in range(1, 13) if j not in criteria]
        if missing:
            missing_labels = ", ".join(f"C{j}" for j in missing)
            raise ValueError(
                f"{path}: missing criteria for {player}: {missing_labels}"
            )
        result[player] = tuple(criteria[j] for j in range(1, 13))

    return result


#------------------ function read_interaction_matrix
def read_interaction_matrix(
    path: str | Path,
    player_codes: Sequence[PlayerCode],
) -> Dict[PlayerCode, Dict[PlayerCode, float]]:
    player_codes = tuple(player_codes)
    expected = set(player_codes)
    matrix: Dict[PlayerCode, Dict[PlayerCode, float]] = {}

    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: empty interaction matrix")

        required = {"player", *player_codes}
        if not required.issubset(reader.fieldnames):
            missing = sorted(required.difference(reader.fieldnames))
            raise ValueError(f"{path}: missing columns {missing}")

        for row in reader:
            source = row["player"].strip()
            if source not in expected:
                raise ValueError(f"{path}: unknown source player {source}")
            if source in matrix:
                raise ValueError(f"{path}: duplicated row for {source}")

            matrix[source] = {}
            for target in player_codes:
                value_text = row[target].strip()
                if value_text == "":
                    raise ValueError(
                        f"{path}: missing interaction {source} -> {target}"
                    )
                value = float(value_text)
                if value < 0 or value > 1:
                    raise ValueError(
                        f"{path}: interaction values must lie in [0,1]"
                    )
                matrix[source][target] = value

    missing_rows = expected.difference(matrix)
    if missing_rows:
        raise ValueError(
            f"{path}: missing rows for {', '.join(sorted(missing_rows))}"
        )

    return matrix


#------------------ function raw_nos
def raw_nos(
    triples: Sequence[Triple],
    weights: Sequence[float],
    alpha_I: float,
    alpha_F: float,
) -> float:
    if len(triples) != 12 or len(weights) != 12:
        raise ValueError("Exactly 12 triples and 12 weights are required")

    return sum(
        weight * (T - alpha_I * I - alpha_F * F)
        for weight, (T, I, F) in zip(weights, triples)
    )


#------------------ function normalized_nos
def normalized_nos(
    value: float,
    alpha_I: float,
    alpha_F: float,
) -> float:
    denominator = 1.0 + alpha_I + alpha_F
    return (value + alpha_I + alpha_F) / denominator


#------------------ function compute_all_scores
def compute_all_scores(
    players: Mapping[PlayerCode, Player],
    neutrosophic_matrix: Mapping[PlayerCode, Sequence[Triple]],
    weights: Mapping[Role, Sequence[float]],
    parameters: ModelParameters,
) -> Tuple[
    Dict[Tuple[PlayerCode, Role], float],
    Dict[Tuple[PlayerCode, Role], float],
]:
    raw: Dict[Tuple[PlayerCode, Role], float] = {}
    normalized: Dict[Tuple[PlayerCode, Role], float] = {}

    for player in players.values():
        triples = neutrosophic_matrix[player.code]
        for role in player.eligible_roles:
            value = raw_nos(
                triples,
                weights[role],
                parameters.alpha_I,
                parameters.alpha_F,
            )
            raw[(player.code, role)] = value
            normalized[(player.code, role)] = normalized_nos(
                value,
                parameters.alpha_I,
                parameters.alpha_F,
            )

    return raw, normalized


#------------------ function tactical_compatibility
def tactical_compatibility(
    interaction: Mapping[PlayerCode, Mapping[PlayerCode, float]],
    player_i: PlayerCode,
    player_j: PlayerCode,
) -> float:
    if player_i == player_j:
        return 1.0
    return 0.5 * (
        interaction[player_i][player_j]
        + interaction[player_j][player_i]
    )


#------------------ function compute_tci_matrix
def compute_tci_matrix(
    interaction: Mapping[PlayerCode, Mapping[PlayerCode, float]],
    player_codes: Sequence[PlayerCode],
) -> Dict[PlayerCode, Dict[PlayerCode, float]]:
    tci: Dict[PlayerCode, Dict[PlayerCode, float]] = {}

    for player_i in player_codes:
        tci[player_i] = {}
        for player_j in player_codes:
            tci[player_i][player_j] = tactical_compatibility(
                interaction,
                player_i,
                player_j,
            )

    return tci


#------------------ function compute_sigma
def compute_sigma(
    tci: Mapping[PlayerCode, Mapping[PlayerCode, float]],
    player_codes: Sequence[PlayerCode],
) -> Dict[PlayerCode, PlayerCode]:
    sigma: Dict[PlayerCode, PlayerCode] = {}

    # deterministic tie-breaking: lower numeric P-index
    def player_key(code: PlayerCode) -> Tuple[int, str]:
        if code.startswith("P") and code[1:].isdigit():
            return int(code[1:]), code
        return 10**9, code

    for player_i in player_codes:
        candidates = [player_j for player_j in player_codes if player_j != player_i]
        if not candidates:
            raise ValueError("At least two players are required")

        best_value = max(tci[player_i][player_j] for player_j in candidates)
        maximizers = [
            player_j
            for player_j in candidates
            if math.isclose(tci[player_i][player_j], best_value, abs_tol=1e-12)
        ]
        sigma[player_i] = min(maximizers, key=player_key)

    return sigma


#------------------ function forward_orbit
def forward_orbit(
    start: PlayerCode,
    sigma: Mapping[PlayerCode, PlayerCode],
) -> Tuple[PlayerCode, ...]:
    orbit: List[PlayerCode] = []
    seen: set[PlayerCode] = set()
    current = start

    while current not in seen:
        seen.add(current)
        orbit.append(current)
        current = sigma[current]

    return tuple(orbit)


#------------------ function all_forward_orbits
def all_forward_orbits(
    player_codes: Sequence[PlayerCode],
    sigma: Mapping[PlayerCode, PlayerCode],
) -> Dict[PlayerCode, Tuple[PlayerCode, ...]]:
    return {
        player: forward_orbit(player, sigma)
        for player in player_codes
    }


#------------------ function compute_oti
def compute_oti(
    tci: Mapping[PlayerCode, Mapping[PlayerCode, float]],
    sigma: Mapping[PlayerCode, PlayerCode],
) -> Dict[PlayerCode, float]:
    return {
        player: tci[player][sigma[player]]
        for player in sigma
    }


#------------------ function orbit_open
def orbit_open(
    selected: Iterable[PlayerCode],
    sigma: Mapping[PlayerCode, PlayerCode],
) -> bool:
    selected_set = set(selected)
    return all(
        sigma[player] in selected_set
        for player in selected_set
    )


#------------------ function eligible_combinations
def eligible_combinations(
    players: Mapping[PlayerCode, Player],
    role: Role,
    size: int,
    excluded: Iterable[PlayerCode] = (),
) -> Iterable[Tuple[PlayerCode, ...]]:
    excluded_set = set(excluded)
    pool = sorted(
        player.code
        for player in players.values()
        if player.code not in excluded_set and player.is_eligible(role)
    )
    return combinations(pool, size)


#------------------ function generate_433_assignments
def generate_433_assignments(
    players: Mapping[PlayerCode, Player],
) -> Iterable[Tuple[Tuple[PlayerCode, Role], ...]]:
    for goalkeepers in eligible_combinations(players, "G", ROLE_COUNTS["G"]):
        used_g = set(goalkeepers)

        for defenders in eligible_combinations(
            players, "D", ROLE_COUNTS["D"], used_g
        ):
            used_d = used_g.union(defenders)

            for midfielders in eligible_combinations(
                players, "M", ROLE_COUNTS["M"], used_d
            ):
                used_m = used_d.union(midfielders)

                for forwards in eligible_combinations(
                    players, "F", ROLE_COUNTS["F"], used_m
                ):
                    assignment: List[Tuple[PlayerCode, Role]] = []
                    assignment.extend((code, "G") for code in goalkeepers)
                    assignment.extend((code, "D") for code in defenders)
                    assignment.extend((code, "M") for code in midfielders)
                    assignment.extend((code, "F") for code in forwards)
                    yield tuple(assignment)


#------------------ function evaluate_assignment
def evaluate_assignment(
    assignment: Sequence[Tuple[PlayerCode, Role]],
    normalized_scores: Mapping[Tuple[PlayerCode, Role], float],
    tci: Mapping[PlayerCode, Mapping[PlayerCode, float]],
    sigma: Mapping[PlayerCode, PlayerCode],
    oti: Mapping[PlayerCode, float],
    parameters: ModelParameters,
) -> TeamResult:
    parameters.validate()

    selected = tuple(code for code, _ in assignment)
    selected_set = set(selected)

    if len(selected) != N_STARTERS or len(selected_set) != N_STARTERS:
        raise ValueError("A feasible assignment must contain 11 distinct players")

    individual_component = sum(
        normalized_scores[(code, role)]
        for code, role in assignment
    ) / N_STARTERS

    compatibility_sum = sum(
        tci[player_i][player_j]
        for player_i, player_j in combinations(selected, 2)
    )
    compatibility_component = compatibility_sum / N_PAIRS

    retained = [
        player
        for player in selected
        if sigma[player] in selected_set
    ]
    orbit_component = sum(oti[player] for player in retained) / N_STARTERS

    tsf = (
        parameters.alpha * individual_component
        + parameters.beta * compatibility_component
        + parameters.gamma * orbit_component
    )

    return TeamResult(
        assignment=tuple(assignment),
        selected=tuple(sorted(selected)),
        individual_component=individual_component,
        compatibility_component=compatibility_component,
        orbit_component=orbit_component,
        tsf=tsf,
        retained_orbit_transitions=len(retained),
        orbit_open=(len(retained) == N_STARTERS),
    )


#------------------ function optimize_433
def optimize_433(
    players: Mapping[PlayerCode, Player],
    normalized_scores: Mapping[Tuple[PlayerCode, Role], float],
    tci: Mapping[PlayerCode, Mapping[PlayerCode, float]],
    sigma: Mapping[PlayerCode, PlayerCode],
    oti: Mapping[PlayerCode, float],
    parameters: ModelParameters,
) -> Tuple[TeamResult, int]:
    best: TeamResult | None = None
    feasible_count = 0

    for assignment in generate_433_assignments(players):
        feasible_count += 1
        result = evaluate_assignment(
            assignment,
            normalized_scores,
            tci,
            sigma,
            oti,
            parameters,
        )
        if best is None or result.tsf > best.tsf:
            best = result

    if best is None:
        raise ValueError("The 4-3-3 feasible set is empty")

    return best, feasible_count


#------------------ function perturb_weights
def perturb_weights(
    weights: Mapping[Role, Sequence[float]],
    delta: float,
    rng: Random,
) -> Dict[Role, Tuple[float, ...]]:
    if delta < 0 or delta >= 1:
        raise ValueError("delta must satisfy 0 <= delta < 1")

    perturbed: Dict[Role, Tuple[float, ...]] = {}

    for role in ROLES:
        values = [
            weight * (1.0 + rng.uniform(-delta, delta))
            for weight in weights[role]
        ]
        total = sum(values)
        perturbed[role] = tuple(value / total for value in values)

    return perturbed


#------------------ function jaccard
def jaccard(
    first: Iterable[PlayerCode],
    second: Iterable[PlayerCode],
) -> float:
    A = set(first)
    B = set(second)
    union = A.union(B)
    if not union:
        return 1.0
    return len(A.intersection(B)) / len(union)


#------------------ function sensitivity_analysis
def sensitivity_analysis(
    players: Mapping[PlayerCode, Player],
    neutrosophic_matrix: Mapping[PlayerCode, Sequence[Triple]],
    weights: Mapping[Role, Sequence[float]],
    tci: Mapping[PlayerCode, Mapping[PlayerCode, float]],
    sigma: Mapping[PlayerCode, PlayerCode],
    oti: Mapping[PlayerCode, float],
    parameters: ModelParameters,
    baseline: TeamResult,
    B: int = 1000,
    delta: float = 0.10,
    seed: int = 2026,
) -> List[Dict[str, float | int | str]]:
    rng = Random(seed)
    rows: List[Dict[str, float | int | str]] = []

    # The compatibility and orbit components do not depend on criterion
    # weights. Precompute them once for every feasible assignment so that
    # large Monte Carlo experiments remain practical.
    cached = []
    for assignment in generate_433_assignments(players):
        selected = tuple(code for code, _ in assignment)
        selected_set = set(selected)

        compatibility_component = (
            sum(
                tci[player_i][player_j]
                for player_i, player_j in combinations(selected, 2)
            )
            / N_PAIRS
        )

        retained = tuple(
            player
            for player in selected
            if sigma[player] in selected_set
        )
        orbit_component = (
            sum(oti[player] for player in retained)
            / N_STARTERS
        )

        static_component = (
            parameters.beta * compatibility_component
            + parameters.gamma * orbit_component
        )

        cached.append(
            (
                tuple(assignment),
                tuple(sorted(selected)),
                compatibility_component,
                orbit_component,
                len(retained),
                len(retained) == N_STARTERS,
                static_component,
            )
        )

    baseline_keys = tuple(baseline.assignment)
    baseline_reference_tsf = baseline.tsf

    for simulation in range(1, B + 1):
        perturbed_weights = perturb_weights(weights, delta, rng)
        _, normalized_scores = compute_all_scores(
            players,
            neutrosophic_matrix,
            perturbed_weights,
            parameters,
        )

        best_record = None
        best_tsf = -math.inf

        for record in cached:
            assignment = record[0]
            individual_component = (
                sum(
                    normalized_scores[(code, role)]
                    for code, role in assignment
                )
                / N_STARTERS
            )
            tsf = (
                parameters.alpha * individual_component
                + record[6]
            )

            if tsf > best_tsf:
                best_tsf = tsf
                best_record = record

        if best_record is None:
            raise ValueError("The 4-3-3 feasible set is empty")

        baseline_individual = (
            sum(
                normalized_scores[(code, role)]
                for code, role in baseline_keys
            )
            / N_STARTERS
        )
        baseline_tsf_perturbed = (
            parameters.alpha * baseline_individual
            + parameters.beta * baseline.compatibility_component
            + parameters.gamma * baseline.orbit_component
        )

        rows.append(
            {
                "simulation": simulation,
                "selected_players": "|".join(best_record[1]),
                "jaccard": jaccard(best_record[1], baseline.selected),
                "tsf_optimum": best_tsf,
                "tsf_baseline_reference": baseline_reference_tsf,
                "delta_tsf": best_tsf - baseline_reference_tsf,
                "tsf_baseline_perturbed": baseline_tsf_perturbed,
                "regret": best_tsf - baseline_tsf_perturbed,
                "orbit_open": int(best_record[5]),
            }
        )

    return rows


#------------------ function selection_frequencies
def selection_frequencies(
    rows: Sequence[Mapping[str, float | int | str]],
    players: Mapping[PlayerCode, Player],
) -> List[Dict[str, float | int | str]]:
    if not rows:
        return []

    counts: Dict[PlayerCode, int] = {
        player.code: 0
        for player in players.values()
    }

    for row in rows:
        selected_text = str(row.get("selected_players", ""))
        selected = [
            code
            for code in selected_text.split("|")
            if code
        ]
        for code in selected:
            if code not in counts:
                raise ValueError(
                    f"Unknown player {code} in sensitivity-analysis output"
                )
            counts[code] += 1

    B = len(rows)
    return [
        {
            "player": player.code,
            "name": player.name,
            "selection_count": counts[player.code],
            "selection_frequency": counts[player.code] / B,
        }
        for player in players.values()
    ]


#------------------ function write_scores
def write_scores(
    path: str | Path,
    players: Mapping[PlayerCode, Player],
    raw_scores: Mapping[Tuple[PlayerCode, Role], float],
    normalized_scores: Mapping[Tuple[PlayerCode, Role], float],
    oti: Mapping[PlayerCode, float],
    sigma: Mapping[PlayerCode, PlayerCode],
) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "player",
                "name",
                "role",
                "NOS",
                "normalized_NOS",
                "sigma",
                "OTI",
            ]
        )

        for player in players.values():
            for role in player.eligible_roles:
                writer.writerow(
                    [
                        player.code,
                        player.name,
                        role,
                        f"{raw_scores[(player.code, role)]:.9f}",
                        f"{normalized_scores[(player.code, role)]:.9f}",
                        sigma[player.code],
                        f"{oti[player.code]:.9f}",
                    ]
                )


#------------------ function write_team
def write_team(
    path: str | Path,
    result: TeamResult,
    players: Mapping[PlayerCode, Player],
) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["player", "name", "assigned_role"])
        for code, role in result.assignment:
            writer.writerow([code, players[code].name, role])

        writer.writerow([])
        writer.writerow(["individual_component", f"{result.individual_component:.9f}"])
        writer.writerow(["compatibility_component", f"{result.compatibility_component:.9f}"])
        writer.writerow(["orbit_component", f"{result.orbit_component:.9f}"])
        writer.writerow(["TSF", f"{result.tsf:.9f}"])
        writer.writerow(["retained_orbit_transitions", result.retained_orbit_transitions])
        writer.writerow(["orbit_open", result.orbit_open])


#------------------ function write_orbits
def write_orbits(
    path: str | Path,
    orbits: Mapping[PlayerCode, Sequence[PlayerCode]],
    sigma: Mapping[PlayerCode, PlayerCode],
    oti: Mapping[PlayerCode, float],
) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["player", "sigma", "OTI", "forward_orbit"])
        for player in sorted(orbits):
            writer.writerow(
                [
                    player,
                    sigma[player],
                    f"{oti[player]:.9f}",
                    " -> ".join(orbits[player]),
                ]
            )


#------------------ function write_sensitivity
def write_sensitivity(
    path: str | Path,
    rows: Sequence[Mapping[str, float | int | str]],
) -> None:
    if not rows:
        return

    with Path(path).open("w", encoding="utf-8", newline="") as f:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


#------------------ function run_case_study
def run_case_study(
    data_dir: str | Path,
    output_dir: str | Path,
    parameters: ModelParameters,
    sensitivity_B: int = 0,
    sensitivity_delta: float = 0.10,
    sensitivity_seed: int = 2026,
) -> TeamResult:
    parameters.validate()

    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    players = read_players(data_dir / "players.csv")
    player_codes = tuple(players.keys())
    weights = read_weights(data_dir / "weights.csv")
    neutrosophic_matrix = read_neutrosophic_matrix(
        data_dir / "neutrosophic_matrix.csv",
        player_codes,
    )
    interaction = read_interaction_matrix(
        data_dir / "interaction_matrix.csv",
        player_codes,
    )

    raw_scores, normalized_scores = compute_all_scores(
        players,
        neutrosophic_matrix,
        weights,
        parameters,
    )
    tci = compute_tci_matrix(interaction, player_codes)
    sigma = compute_sigma(tci, player_codes)
    orbits = all_forward_orbits(player_codes, sigma)
    oti = compute_oti(tci, sigma)

    optimum, feasible_count = optimize_433(
        players,
        normalized_scores,
        tci,
        sigma,
        oti,
        parameters,
    )

    write_scores(
        output_dir / "player_scores.csv",
        players,
        raw_scores,
        normalized_scores,
        oti,
        sigma,
    )
    write_team(output_dir / "optimal_starting_xi.csv", optimum, players)
    write_orbits(output_dir / "orbits.csv", orbits, sigma, oti)

    if sensitivity_B > 0:
        rows = sensitivity_analysis(
            players,
            neutrosophic_matrix,
            weights,
            tci,
            sigma,
            oti,
            parameters,
            optimum,
            B=sensitivity_B,
            delta=sensitivity_delta,
            seed=sensitivity_seed,
        )
        write_sensitivity(output_dir / "sensitivity.csv", rows)
        frequencies = selection_frequencies(rows, players)
        write_sensitivity(
            output_dir / "selection_frequencies.csv",
            frequencies,
        )

    print(f"Feasible 4-3-3 assignments: {feasible_count}")
    print(f"Best TSF: {optimum.tsf:.9f}")
    print(
        "Components: "
        f"individual={optimum.individual_component:.9f}, "
        f"compatibility={optimum.compatibility_component:.9f}, "
        f"orbit={optimum.orbit_component:.9f}"
    )
    print(
        "Orbit retention: "
        f"{optimum.retained_orbit_transitions}/{N_STARTERS} "
        f"(orbit-open={optimum.orbit_open})"
    )
    print("Starting XI:")
    for code, role in optimum.assignment:
        print(f"  {role}: {code} - {players[code].name}")

    return optimum


#------------------ function build_argument_parser
def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Neutrosophic-soft orbit football starting-XI optimizer"
    )
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--alpha-I", type=float, default=DEFAULT_ALPHA_I)
    parser.add_argument("--alpha-F", type=float, default=DEFAULT_ALPHA_F)
    parser.add_argument("--alpha", type=float, default=DEFAULT_ALPHA)
    parser.add_argument("--beta", type=float, default=DEFAULT_BETA)
    parser.add_argument("--gamma", type=float, default=DEFAULT_GAMMA)
    parser.add_argument("--sensitivity-B", type=int, default=0)
    parser.add_argument("--sensitivity-delta", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=2026)
    return parser


#------------------ main program
if __name__ == "__main__":
    args = build_argument_parser().parse_args()

    params = ModelParameters(
        alpha_I=args.alpha_I,
        alpha_F=args.alpha_F,
        alpha=args.alpha,
        beta=args.beta,
        gamma=args.gamma,
    )

    run_case_study(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        parameters=params,
        sensitivity_B=args.sensitivity_B,
        sensitivity_delta=args.sensitivity_delta,
        sensitivity_seed=args.seed,
    )
