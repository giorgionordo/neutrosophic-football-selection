# Release notes

## v1.0.0 — 2026-08-14

First reproducible release of **Neutrosophic-Soft Orbit Football Team Selection**, the Python implementation accompanying the manuscript:

> *A Novel Neutrosophic Over Soft Orbit Topological Framework for Football Team Selection under Uncertainty*

### Included in this release

- complete Python implementation of the neutrosophic-soft football-selection framework;
- 20-player Manchester City 2024-2025 Premier League case study;
- 12-criterion neutrosophic evaluation matrix;
- role-dependent criterion weights;
- directed tactical interaction matrix with unit diagonal convention;
- symmetric Tactical Compatibility Index (TCI);
- deterministic orbit-successor map and forward-orbit diagnostics;
- constrained exhaustive 4-3-3 optimization with explicit role eligibility;
- Team Selection Function combining individual, compatibility, and orbit components;
- 1000-repetition Monte Carlo sensitivity analysis;
- per-replication `delta_tsf`, regret, Jaccard similarity, selected players, and orbit-open status;
- player-level selection frequencies;
- frozen numerical inputs and generated outputs for reproducibility;
- data-provenance and data-acquisition documentation;
- optional Kaggle-based upstream data acquisition workflow;
- automated unit tests and GitHub Actions CI on Python 3.10 and 3.12;
- MIT License and `CITATION.cff` metadata.

### Baseline reproduced result

The release enumerates **13,020** feasible 4-3-3 assignments and returns the following optimal starting XI:

- G: P1 — Ederson
- D: P3 — Rúben Dias
- D: P5 — Manuel Akanji
- D: P7 — Joško Gvardiol
- D: P8 — Rico Lewis
- M: P10 — Kevin De Bruyne
- M: P11 — Bernardo Silva
- M: P13 — Matheus Nunes
- F: P14 — Phil Foden
- F: P15 — Jérémy Doku
- F: P16 — Jack Grealish

Baseline objective value:

`TSF = 0.4556941843506398`

The selected set is orbit-open and retains all 11 first orbit transitions.

### Sensitivity experiment

The default experiment uses:

- 1000 Monte Carlo repetitions;
- ±10% multiplicative perturbation of role-specific criterion weights;
- renormalization after perturbation;
- random seed 2026.

The same starting XI is selected in all 1000 repetitions in the frozen case study. Detailed results are stored in `output/sensitivity.csv` and `output/selection_frequencies.csv`.

### Reproduction

From the repository root:

```bash
python run_case_study.py
```

No third-party package is required for reproduction from the frozen inputs. Optional upstream data acquisition uses the dependencies listed in `requirements-data.txt`.
