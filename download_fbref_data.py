"""
Football Team Selection under Uncertainty
download_fbref_data.py

Downloads the public 2024-2025 FBref player-statistics dataset from Kaggle
and converts the Manchester City rows into data/raw_player_metrics.csv.

The source dataset is:
    Hubert Sidorowicz,
    "Football Players Stats (2024-2025)",
    Kaggle, derived from FBref.

The program deliberately keeps physical tracking variables (top speed and
distance covered per 90) separate from the FBref import, because those
variables are not part of the FBref dataset. If data/physical_metrics.csv is
present, its values are merged into the final raw-player file.

----------------------------------------------------------------------------------
author: Giorgio Nordo - Dipartimento MIFT. Università di Messina, Italy
www.nordo.it   |  giorgio.nordo@unime.it
"""

from __future__ import annotations

#------------------ import of required modules
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence
import csv
import math
import re
import unicodedata

try:
    import kagglehub
except ImportError as exc:
    raise SystemExit(
        "The package 'kagglehub' is required.\n"
        "Install it in the PyCharm environment with:\n"
        "    pip install kagglehub"
    ) from exc


#------------------ constants
KAGGLE_HANDLE = "hubertsidorowicz/football-players-stats-2024-2025"
KAGGLE_FILE = "players_data-2024_2025.csv"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXTERNAL_DIR = BASE_DIR / "external_data" / "fbref_2024_2025"

OUTPUT_FILE = DATA_DIR / "raw_player_metrics.csv"
PHYSICAL_FILE = DATA_DIR / "physical_metrics.csv"
SOURCE_COPY = DATA_DIR / "manchester_city_fbref_source.csv"


#------------------ player names used in the manuscript
PLAYER_NAMES: Dict[str, tuple[str, ...]] = {
    "P1": ("Ederson Moraes", "Ederson"),
    "P2": ("Stefan Ortega", "Stefan Ortega Moreno"),
    "P3": ("Ruben Dias", "Rúben Dias"),
    "P4": ("John Stones",),
    "P5": ("Manuel Akanji",),
    "P6": ("Nathan Ake", "Nathan Aké"),
    "P7": ("Josko Gvardiol", "Joško Gvardiol"),
    "P8": ("Rico Lewis",),
    "P9": ("Rodri", "Rodrigo Hernandez", "Rodrigo Hernández"),
    "P10": ("Kevin De Bruyne",),
    "P11": ("Bernardo Silva",),
    "P12": ("Mateo Kovacic", "Mateo Kovačić"),
    "P13": ("Matheus Nunes",),
    "P14": ("Phil Foden",),
    "P15": ("Jeremy Doku", "Jérémy Doku"),
    "P16": ("Jack Grealish",),
    "P17": ("Erling Haaland",),
    "P18": ("Oscar Bobb",),
    "P19": ("James McAtee",),
    "P20": ("Ilkay Gundogan", "İlkay Gündoğan", "Ilkay Gündoğan"),
}

OFFICIAL_ROLES: Dict[str, str] = {
    "P1": "G", "P2": "G",
    "P3": "D", "P4": "D", "P5": "D", "P6": "D", "P7": "D", "P8": "D",
    "P9": "M", "P10": "M", "P11": "M", "P12": "M", "P13": "M", "P14": "M",
    "P15": "F", "P16": "F", "P17": "F", "P18": "F",
    "P19": "M", "P20": "M",
}

OUTPUT_COLUMNS = (
    "player",
    "official_role",
    "nineties",
    "pass_completion_pct",
    "takeon_success_pct",
    "miscontrols_per90",
    "dispossessed_per90",
    "successful_takeons_per90",
    "progressive_carries_per90",
    "shots_on_target_pct",
    "tackles_interceptions_per90",
    "blocks_per90",
    "clearances_per90",
    "gk_save_pct",
    "recoveries_per90",
    "progressive_passes_per90",
    "gk_opa_per90",
    "progressive_receptions_per90",
    "touches_att_pen_per90",
    "gk_psxg_plus_minus_per90",
    "top_speed_kmh",
    "distance_per90_km",
    "completed_passes_per90",
    "key_passes_per90",
    "errors_per90",
)


#------------------ function normalized_text
def normalized_text(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.replace("ı", "i").replace("İ", "I")
    value = re.sub(r"[^a-zA-Z0-9]+", " ", value)
    return " ".join(value.lower().split())


#------------------ function normalized_column
def normalized_column(value: str) -> str:
    return normalized_text(value).replace(" ", "")


#------------------ function read_csv_rows
def read_csv_rows(path: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    path = Path(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"{path}: empty CSV file")
        return list(reader.fieldnames), list(reader)


#------------------ function resolve_column
def resolve_column(
    fieldnames: Sequence[str],
    aliases: Sequence[str],
    required: bool = False,
) -> str | None:
    normalized = {name: normalized_column(name) for name in fieldnames}

    for alias in aliases:
        target = normalized_column(alias)
        exact = [name for name, value in normalized.items() if value == target]
        if exact:
            return exact[0]

    for alias in aliases:
        tokens = [
            normalized_column(token)
            for token in re.split(r"[_\s]+", alias)
            if token
        ]
        candidates = [
            name
            for name, value in normalized.items()
            if all(token in value for token in tokens)
        ]
        if len(candidates) == 1:
            return candidates[0]

    if required:
        raise KeyError(
            "Unable to identify a required source column.\n"
            f"Aliases tried: {aliases}\n"
            f"Available columns: {fieldnames}"
        )
    return None


#------------------ function as_float
def as_float(value: str | None) -> float | None:
    if value is None:
        return None

    value = str(value).strip().replace(",", "").replace("%", "")
    if value == "" or value.lower() in ("nan", "none", "na", "n/a"):
        return None

    try:
        return float(value)
    except ValueError:
        return None


#------------------ function per90
def per90(total: float | None, nineties: float | None) -> float | None:
    if total is None or nineties is None or nineties <= 0:
        return None
    return total / nineties


#------------------ function find_player_row
def find_player_row(
    rows: Sequence[Mapping[str, str]],
    player_column: str,
    aliases: Iterable[str],
) -> Mapping[str, str]:
    targets = {normalized_text(alias) for alias in aliases}
    matches = [
        row
        for row in rows
        if normalized_text(row.get(player_column, "")) in targets
    ]

    if not matches:
        raise KeyError(
            "Player not found in the downloaded dataset: "
            + " / ".join(aliases)
        )
    if len(matches) > 1:
        raise KeyError(
            "More than one source row matched player: "
            + " / ".join(aliases)
        )
    return matches[0]


#------------------ function optional_value
def optional_value(
    row: Mapping[str, str],
    fieldnames: Sequence[str],
    aliases: Sequence[str],
) -> float | None:
    column = resolve_column(fieldnames, aliases, required=False)
    if column is None:
        return None
    return as_float(row.get(column))


#------------------ function load_physical_metrics
def load_physical_metrics(path: str | Path) -> Dict[str, Dict[str, float | None]]:
    path = Path(path)
    if not path.exists():
        return {}

    result: Dict[str, Dict[str, float | None]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or "player" not in reader.fieldnames:
            raise ValueError(f"{path}: column 'player' is required")

        for row in reader:
            player = row["player"].strip()
            result[player] = {
                "top_speed_kmh": as_float(row.get("top_speed_kmh")),
                "distance_per90_km": as_float(row.get("distance_per90_km")),
            }
    return result


#------------------ function extract_source_rows
def extract_source_rows(
    source_path: str | Path,
) -> tuple[list[str], list[dict[str, str]]]:
    fieldnames, rows = read_csv_rows(source_path)

    player_col = resolve_column(fieldnames, ("Player",), required=True)
    squad_col = resolve_column(fieldnames, ("Squad", "Team"), required=True)
    comp_col = resolve_column(
        fieldnames,
        ("Comp", "Competition", "League"),
        required=False,
    )

    filtered = []
    for row in rows:
        if normalized_text(row.get(squad_col, "")) != "manchester city":
            continue

        if comp_col is not None:
            comp = normalized_text(row.get(comp_col, ""))
            if "premier league" not in comp:
                continue

        filtered.append(dict(row))

    if not filtered:
        raise ValueError(
            "No Manchester City Premier League rows were found in the "
            "downloaded FBref dataset."
        )

    SOURCE_COPY.parent.mkdir(parents=True, exist_ok=True)
    with SOURCE_COPY.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered)

    return fieldnames, filtered


#------------------ function build_raw_player_metrics
def build_raw_player_metrics(
    source_path: str | Path,
    output_path: str | Path = OUTPUT_FILE,
) -> None:
    fieldnames, rows = extract_source_rows(source_path)

    player_col = resolve_column(fieldnames, ("Player",), required=True)
    nineties_col = resolve_column(
        fieldnames,
        ("90s", "90s_stats_standard", "90s_standard"),
        required=True,
    )

    physical = load_physical_metrics(PHYSICAL_FILE)

    alias = {
        "pass_completion_pct": (
            "Cmp%_stats_passing", "Cmp%_passing", "PasCmp%", "Cmp%",
        ),
        "takeon_success_pct": (
            "Succ%_stats_possession", "Succ%_possession", "ToSuc%", "DriSucc%",
        ),
        "miscontrols": ("Mis_stats_possession", "Mis", "CarMis"),
        "dispossessed": ("Dis_stats_possession", "Dis", "CarDis"),
        "successful_takeons": (
            "Succ_stats_possession", "ToSuc", "DriSucc", "Succ",
        ),
        "progressive_carries": (
            "PrgC_stats_possession", "PrgC_stats_standard", "PrgC", "CarProg",
        ),
        "shots_on_target_pct": (
            "SoT%_stats_shooting", "SoT%_shooting", "SoT%",
        ),
        "tackles_interceptions": (
            "Tkl+Int_stats_defense", "Tkl+Int",
        ),
        "blocks": ("Blocks_stats_defense", "Blocks"),
        "clearances": ("Clr_stats_defense", "Clr"),
        "gk_save_pct": ("Save%_stats_keeper", "Save%_keeper", "Save%"),
        "recoveries": ("Recov_stats_misc", "Recov"),
        "progressive_passes": (
            "PrgP_stats_passing", "PrgP_stats_standard", "PrgP",
        ),
        "gk_opa_total": ("#OPA_stats_keeper_adv", "#OPA", "OPA"),
        "gk_opa_per90_direct": (
            "#OPA/90_stats_keeper_adv", "#OPA/90", "OPA/90",
        ),
        "progressive_receptions": (
            "PrgR_stats_possession", "PrgR_stats_standard", "PrgR", "RecProg",
        ),
        "touches_att_pen": (
            "Att Pen_stats_possession", "TouAttPen",
            "Touches Att Pen", "Att Pen",
        ),
        "gk_psxg_pm_total": (
            "PSxG+/-_stats_keeper_adv", "PSxG+/-",
        ),
        "gk_psxg_pm_per90_direct": (
            "PSxG+/-/90_stats_keeper_adv", "PSxG+/- /90", "PSxG+/-/90",
        ),
        "completed_passes": ("Cmp_stats_passing", "PasCmp", "Cmp"),
        "key_passes": ("KP_stats_passing", "KP"),
        "errors": ("Err_stats_defense", "Err"),
    }

    output_rows: list[dict[str, str]] = []

    for code in (f"P{i}" for i in range(1, 21)):
        row = find_player_row(rows, player_col, PLAYER_NAMES[code])
        nineties = as_float(row.get(nineties_col))

        def value(name: str) -> float | None:
            return optional_value(row, fieldnames, alias[name])

        gk_opa_direct = value("gk_opa_per90_direct")
        gk_opa = (
            gk_opa_direct
            if gk_opa_direct is not None
            else per90(value("gk_opa_total"), nineties)
        )

        gk_psxg_direct = value("gk_psxg_pm_per90_direct")
        gk_psxg = (
            gk_psxg_direct
            if gk_psxg_direct is not None
            else per90(value("gk_psxg_pm_total"), nineties)
        )

        physical_row = physical.get(code, {})

        result = {
            "player": code,
            "official_role": OFFICIAL_ROLES[code],
            "nineties": nineties,
            "pass_completion_pct": value("pass_completion_pct"),
            "takeon_success_pct": value("takeon_success_pct"),
            "miscontrols_per90": per90(value("miscontrols"), nineties),
            "dispossessed_per90": per90(value("dispossessed"), nineties),
            "successful_takeons_per90": per90(value("successful_takeons"), nineties),
            "progressive_carries_per90": per90(value("progressive_carries"), nineties),
            "shots_on_target_pct": value("shots_on_target_pct"),
            "tackles_interceptions_per90": per90(
                value("tackles_interceptions"), nineties
            ),
            "blocks_per90": per90(value("blocks"), nineties),
            "clearances_per90": per90(value("clearances"), nineties),
            "gk_save_pct": value("gk_save_pct"),
            "recoveries_per90": per90(value("recoveries"), nineties),
            "progressive_passes_per90": per90(value("progressive_passes"), nineties),
            "gk_opa_per90": gk_opa,
            "progressive_receptions_per90": per90(
                value("progressive_receptions"), nineties
            ),
            "touches_att_pen_per90": per90(value("touches_att_pen"), nineties),
            "gk_psxg_plus_minus_per90": gk_psxg,
            "top_speed_kmh": physical_row.get("top_speed_kmh"),
            "distance_per90_km": physical_row.get("distance_per90_km"),
            "completed_passes_per90": per90(value("completed_passes"), nineties),
            "key_passes_per90": per90(value("key_passes"), nineties),
            "errors_per90": per90(value("errors"), nineties),
        }

        output_rows.append(
            {
                key: (
                    ""
                    if result[key] is None
                    else (
                        result[key]
                        if isinstance(result[key], str)
                        else f"{float(result[key]):.9f}"
                    )
                )
                for key in OUTPUT_COLUMNS
            }
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Created: {output_path}")
    print(f"Created: {SOURCE_COPY}")


#------------------ function download_dataset
def download_dataset() -> Path:
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

    print("Downloading public FBref-derived dataset from Kaggle...")
    resolved = kagglehub.dataset_download(
        KAGGLE_HANDLE,
        path=KAGGLE_FILE,
        output_dir=str(EXTERNAL_DIR),
    )

    resolved_path = Path(resolved)
    candidates = []

    if resolved_path.is_file():
        candidates.append(resolved_path)
    if resolved_path.is_dir():
        candidates.extend(resolved_path.rglob(KAGGLE_FILE))
    candidates.extend(EXTERNAL_DIR.rglob(KAGGLE_FILE))

    for candidate in candidates:
        if candidate.is_file():
            print(f"Downloaded source: {candidate}")
            return candidate

    raise FileNotFoundError(
        f"Kaggle download completed but {KAGGLE_FILE} could not be located."
    )


#------------------ main program
if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    source_path = download_dataset()
    build_raw_player_metrics(source_path)

    print()
    print("FBref data import completed.")
    print(
        "Physical tracking fields are left blank unless "
        "data/physical_metrics.csv contains verified values."
    )
