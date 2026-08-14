"""
Football Team Selection under Uncertainty
build_neutrosophic_matrix.py

Builds the complete neutrosophic evaluation matrix used by
football_team_selection.py from transparent raw football statistics.

For each criterion, raw indicators are min-max normalized. Benefit indicators
are oriented so that larger values are better, cost indicators are reversed.

For normalized evidence values q_1,...,q_r:
    T = mean(q_1,...,q_r)
    F = 1 - T
    I = 1 - min(1, 90s / REFERENCE_NINETIES) * completeness

Thus T+F=1, while I is independent and represents sample-size/data uncertainty.

----------------------------------------------------------------------------------
author: Giorgio Nordo - Dipartimento MIFT. Università di Messina, Italy
www.nordo.it   |  giorgio.nordo@unime.it
"""

from __future__ import annotations

#------------------ import of required modules
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Mapping, Tuple
import csv
import math


PlayerCode = str

REFERENCE_NINETIES = 20.0
NORMALIZATION_MIN_NINETIES = 5.0


#------------------ class MetricRule
@dataclass(frozen=True)
class MetricRule:
    name: str
    orientation: str = "benefit"

    # method validate
    def validate(self) -> None:
        if self.orientation not in ("benefit", "cost"):
            raise ValueError(
                f"Invalid orientation {self.orientation!r} for metric {self.name}"
            )


#------------------ class CriterionRule
@dataclass(frozen=True)
class CriterionRule:
    code: str
    name: str
    general_metrics: Tuple[MetricRule, ...]
    goalkeeper_metrics: Tuple[MetricRule, ...] | None = None

    # method metrics_for_role
    def metrics_for_role(self, role: str) -> Tuple[MetricRule, ...]:
        if role == "G" and self.goalkeeper_metrics is not None:
            return self.goalkeeper_metrics
        return self.general_metrics


#------------------ criterion definitions
CRITERIA: Tuple[CriterionRule, ...] = (
    CriterionRule("C1", "Passing Accuracy",
                  (MetricRule("pass_completion_pct"),)),
    CriterionRule("C2", "Ball Control",
                  (MetricRule("takeon_success_pct"),
                   MetricRule("miscontrols_per90", "cost"),
                   MetricRule("dispossessed_per90", "cost")),
                  goalkeeper_metrics=(
                      MetricRule("pass_completion_pct"),
                      MetricRule("miscontrols_per90", "cost"))),
    CriterionRule("C3", "Dribbling Ability",
                  (MetricRule("successful_takeons_per90"),
                   MetricRule("progressive_carries_per90"))),
    CriterionRule("C4", "Shooting Accuracy",
                  (MetricRule("shots_on_target_pct"),)),
    CriterionRule("C5", "Defensive Ability",
                  (MetricRule("tackles_interceptions_per90"),
                   MetricRule("blocks_per90"),
                   MetricRule("clearances_per90")),
                  goalkeeper_metrics=(MetricRule("gk_save_pct"),)),
    CriterionRule("C6", "Tactical Awareness",
                  (MetricRule("recoveries_per90"),
                   MetricRule("progressive_passes_per90")),
                  goalkeeper_metrics=(
                      MetricRule("gk_opa_per90"),
                      MetricRule("gk_save_pct"))),
    CriterionRule("C7", "Positioning",
                  (MetricRule("progressive_receptions_per90"),
                   MetricRule("touches_att_pen_per90")),
                  goalkeeper_metrics=(
                      MetricRule("gk_psxg_plus_minus_per90"),)),
    CriterionRule("C8", "Speed",
                  (MetricRule("top_speed_kmh"),)),
    CriterionRule("C9", "Stamina",
                  (MetricRule("distance_per90_km"),)),
    CriterionRule("C10", "Teamwork",
                  (MetricRule("completed_passes_per90"),
                   MetricRule("key_passes_per90")),
                  goalkeeper_metrics=(
                      MetricRule("completed_passes_per90"),)),
    CriterionRule("C11", "Decision Making",
                  (MetricRule("pass_completion_pct"),
                   MetricRule("miscontrols_per90", "cost"),
                   MetricRule("dispossessed_per90", "cost"),
                   MetricRule("errors_per90", "cost")),
                  goalkeeper_metrics=(
                      MetricRule("pass_completion_pct"),
                      MetricRule("errors_per90", "cost"))),
    CriterionRule("C12", "Physical Fitness",
                  (MetricRule("availability_ratio"),
                   MetricRule("distance_per90_km")),
                  goalkeeper_metrics=(
                      MetricRule("availability_ratio"),)),
)


#------------------ function required_metric_names
def required_metric_names() -> Tuple[str, ...]:
    names = {"nineties", "official_role"}

    for criterion in CRITERIA:
        for rule in criterion.general_metrics:
            names.add(rule.name)
        if criterion.goalkeeper_metrics is not None:
            for rule in criterion.goalkeeper_metrics:
                names.add(rule.name)

    names.discard("availability_ratio")
    return tuple(sorted(names))


#------------------ function read_raw_metrics
def read_raw_metrics(
    path: str | Path,
) -> Dict[PlayerCode, Dict[str, float | str | None]]:
    path = Path(path)

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: empty file")

        required = {"player", *required_metric_names()}
        missing = required.difference(reader.fieldnames)
        if missing:
            raise ValueError(
                f"{path}: missing required columns: {', '.join(sorted(missing))}"
            )

        result: Dict[PlayerCode, Dict[str, float | str | None]] = {}

        for row in reader:
            player = row["player"].strip()
            if not player:
                raise ValueError(f"{path}: empty player code")
            if player in result:
                raise ValueError(f"{path}: duplicated player {player}")

            values: Dict[str, float | str | None] = {
                "official_role": row["official_role"].strip(),
            }

            for name in required_metric_names():
                if name == "official_role":
                    continue
                value = row[name].strip()
                values[name] = None if value == "" else float(value)

            nineties = values["nineties"]
            if nineties is None or float(nineties) < 0:
                raise ValueError(f"{path}: invalid nineties for {player}")

            values["availability_ratio"] = min(1.0, float(nineties) / 38.0)
            result[player] = values

    if not result:
        raise ValueError(f"{path}: no player data")

    return result


#------------------ function normalization_bounds
def normalization_bounds(
    raw: Mapping[PlayerCode, Mapping[str, float | str | None]],
    metric_name: str,
) -> Tuple[float, float]:
    reference: List[float] = []

    for values in raw.values():
        value = values.get(metric_name)
        nineties = values.get("nineties")

        if (
            isinstance(value, (int, float))
            and isinstance(nineties, (int, float))
            and nineties >= NORMALIZATION_MIN_NINETIES
        ):
            reference.append(float(value))

    if len(reference) < 2:
        reference = [
            float(values[metric_name])
            for values in raw.values()
            if isinstance(values.get(metric_name), (int, float))
        ]

    if not reference:
        # No numerical evidence is available for this metric.
        # criterion_triple() will represent the missing evidence as
        # neutral truth/falsity with maximal indeterminacy.
        return 0.0, 1.0

    return min(reference), max(reference)


#------------------ function normalize_value
def normalize_value(
    value: float,
    lower: float,
    upper: float,
    orientation: str,
) -> float:
    if math.isclose(lower, upper, abs_tol=1e-12):
        score = 0.5
    else:
        score = (value - lower) / (upper - lower)

    score = max(0.0, min(1.0, score))

    if orientation == "cost":
        score = 1.0 - score

    return score


#------------------ function build_bounds
def build_bounds(
    raw: Mapping[PlayerCode, Mapping[str, float | str | None]],
) -> Dict[str, Tuple[float, float]]:
    metric_names = set()

    for criterion in CRITERIA:
        for rule in criterion.general_metrics:
            metric_names.add(rule.name)
        if criterion.goalkeeper_metrics is not None:
            for rule in criterion.goalkeeper_metrics:
                metric_names.add(rule.name)

    return {
        name: normalization_bounds(raw, name)
        for name in sorted(metric_names)
    }


#------------------ function criterion_triple
def criterion_triple(
    player_values: Mapping[str, float | str | None],
    criterion: CriterionRule,
    bounds: Mapping[str, Tuple[float, float]],
) -> Tuple[float, float, float]:
    role = str(player_values["official_role"])
    rules = criterion.metrics_for_role(role)

    normalized_values: List[float] = []

    for rule in rules:
        rule.validate()
        value = player_values.get(rule.name)

        if not isinstance(value, (int, float)):
            continue

        lower, upper = bounds[rule.name]
        normalized_values.append(
            normalize_value(
                float(value),
                lower,
                upper,
                rule.orientation,
            )
        )

    completeness = len(normalized_values) / len(rules)

    if normalized_values:
        T = sum(normalized_values) / len(normalized_values)
    else:
        T = 0.5

    F = 1.0 - T

    nineties = float(player_values["nineties"])
    sample_reliability = min(1.0, nineties / REFERENCE_NINETIES)
    I = 1.0 - sample_reliability * completeness

    return T, I, F


#------------------ function build_neutrosophic_matrix
def build_neutrosophic_matrix(
    raw_path: str | Path,
    output_path: str | Path,
) -> None:
    raw = read_raw_metrics(raw_path)
    bounds = build_bounds(raw)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["player", "criterion", "T", "I", "F"])

        for player in sorted(
            raw,
            key=lambda code: (
                int(code[1:]) if code.startswith("P") and code[1:].isdigit() else 10**9,
                code,
            ),
        ):
            values = raw[player]

            for criterion in CRITERIA:
                T, I, F = criterion_triple(values, criterion, bounds)
                writer.writerow(
                    [
                        player,
                        criterion.code,
                        f"{T:.9f}",
                        f"{I:.9f}",
                        f"{F:.9f}",
                    ]
                )


#------------------ main program
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"

    raw_path = DATA_DIR / "raw_player_metrics.csv"
    output_path = DATA_DIR / "neutrosophic_matrix.csv"

    if not raw_path.exists():
        print("INPUT DATA ERROR")
        print("----------------")
        print(f"Missing file: {raw_path}")
        print(
            "Copy raw_player_metrics_template.csv to raw_player_metrics.csv "
            "and fill it with the documented public data."
        )
    else:
        build_neutrosophic_matrix(raw_path, output_path)
        print(f"Created: {output_path}")
