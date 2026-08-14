"""
Football Team Selection under Uncertainty
run_case_study.py

One-click reproduction of the numerical case study.

The program:
    1. builds the neutrosophic matrix from raw_player_metrics.csv;
    2. builds the tactical passing-affinity matrix;
    3. optimizes the 4-3-3 starting XI;
    4. performs the Monte Carlo sensitivity analysis;
    5. writes per-simulation robustness diagnostics to output/sensitivity.csv;
    6. writes player selection frequencies to output/selection_frequencies.csv.

The sensitivity output includes the selected players, Jaccard similarity with
the baseline XI, the perturbed optimum TSF, Delta_b = TSF_b - TSF_0, the TSF
of the baseline XI under the same perturbation, the corresponding regret, and
orbit-openness. Selection frequencies f_i are computed over all Monte Carlo
replications.

----------------------------------------------------------------------------------
author: Giorgio Nordo - Dipartimento MIFT. Università di Messina, Italy
www.nordo.it   |  giorgio.nordo@unime.it
"""

from __future__ import annotations

#------------------ import of required modules
from pathlib import Path

from build_neutrosophic_matrix import build_neutrosophic_matrix
from build_interaction_matrix import build_interaction_matrix
from football_team_selection import ModelParameters, run_case_study


#------------------ default parameters
ALPHA_I = 1.0
ALPHA_F = 1.0
ALPHA = 0.50
BETA = 0.35
GAMMA = 0.15

SENSITIVITY_B = 1000
SENSITIVITY_DELTA = 0.10
SENSITIVITY_SEED = 2026


#------------------ main program
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    DATA_DIR = BASE_DIR / "data"
    OUTPUT_DIR = BASE_DIR / "output"

    print("Step 1/3 - Building the neutrosophic matrix")
    build_neutrosophic_matrix(
        DATA_DIR / "raw_player_metrics.csv",
        DATA_DIR / "neutrosophic_matrix.csv",
    )

    print("Step 2/3 - Building the interaction matrix")
    build_interaction_matrix(
        DATA_DIR / "raw_player_metrics.csv",
        DATA_DIR / "interaction_matrix.csv",
    )

    print("Step 3/3 - Optimizing the starting XI and running sensitivity analysis")
    parameters = ModelParameters(
        alpha_I=ALPHA_I,
        alpha_F=ALPHA_F,
        alpha=ALPHA,
        beta=BETA,
        gamma=GAMMA,
    )

    run_case_study(
        data_dir=DATA_DIR,
        output_dir=OUTPUT_DIR,
        parameters=parameters,
        sensitivity_B=SENSITIVITY_B,
        sensitivity_delta=SENSITIVITY_DELTA,
        sensitivity_seed=SENSITIVITY_SEED,
    )
