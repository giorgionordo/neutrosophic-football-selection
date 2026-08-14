# Neutrosophic-Soft Orbit Football Team Selection

Reproducible Python implementation for the numerical case study of

**A Neutrosophic Over Soft Orbit Topological Framework for Football Team
Selection under Uncertainty**

The code follows the mathematical definitions in the manuscript and is written
so that every derived numerical table can be regenerated from the source data.

## Quick start

Python 3.10 or later is recommended. No third-party packages are required.

From PyCharm, run:

```text
run_case_study.py
```

or from a terminal:

```bash
python run_case_study.py
```

The program rebuilds the neutrosophic matrix, rebuilds the pairwise tactical
matrix, optimizes all feasible 4-3-3 assignments and runs the 1000-repetition
sensitivity analysis.

## Main files

- `run_case_study.py` -- one-click reproduction.
- `build_neutrosophic_matrix.py` -- raw data -> (T,I,F).
- `build_interaction_matrix.py` -- passing-role affinity matrix.
- `football_team_selection.py` -- orbit construction and optimization.
- `data/raw_player_metrics.csv` -- final Manchester City PL 2024-25 inputs.
- `data/neutrosophic_matrix.csv` -- generated 20x12 neutrosophic matrix.
- `data/interaction_matrix.csv` -- generated 20x20 directed affinity matrix.
- `output/player_scores.csv` -- NOS, normalized NOS, sigma and OTI.
- `output/orbits.csv` -- orbit diagnostics.
- `output/optimal_starting_xi.csv` -- maximizing 4-3-3.
- `output/sensitivity.csv` -- 1000 Monte Carlo perturbations.
- `DATA_PROVENANCE.md` -- exact data definitions and source.
- `CASE_STUDY_RESULTS.md` -- numerical summary.

## Reproducibility

The repository never reconstructs missing measurements by guesswork. Tracking
variables unavailable on a common public basis are represented through the
indeterminacy component rather than filled with artificial values.

See `DATA_PROVENANCE.md` for the complete methodological specification.
