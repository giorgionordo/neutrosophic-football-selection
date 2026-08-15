# Neutrosophic-Soft Orbit Football Team Selection

Research code accompanying the paper

> **A Novel Neutrosophic Over Soft Orbit Topological Framework for Football Team Selection under Uncertainty**

This repository contains a reproducible Python implementation of the numerical football case study developed in the manuscript. The framework combines **neutrosophic-soft multi-criteria evaluation**, **orbit topology induced by a fixed player-interaction map**, **tactical compatibility**, **position-dependent weighting**, **constrained 4-3-3 team optimization**, and a **role-specific MCDM/Spearman benchmark** for the player-level comparison reported in the paper.

The numerical objects used in the case study are generated from frozen source data committed to the repository, so the reported experiment can be reproduced without manually copying values from tables in the paper.

---

## Authors

| Author | Affiliation |
|---|---|
| **Murtadha M. Abdulkadhim** | Department of First Grade Teacher Education, College of Basic Education, Al-Muthanna University, Samawah 66001, Iraq |
| **Qays Hatem Imran** | Department of Mathematics, College of Education for Pure Science, Al-Muthanna University, Samawah 66001, Iraq |
| **Yaseen S. R.** | Department of Mathematics, College of Education for Pure Science, Tikrit University, Tikrit 34001, Iraq |
| **Giorgio Nordo** | MIFT Department, University of Messina, Viale Ferdinando Stagno d'Alcontres 31, 98166 Messina, Italy |

**Corresponding author:** Qays Hatem Imran — `qays.imran@mu.edu.iq`

---

## Overview

Selecting a football team is not simply a matter of ranking players by individual performance. A realistic selection procedure must also account for uncertainty in the available data, positional constraints, tactical relationships between players, and the fact that the value of a player can depend on the role in which that player is used.

The proposed framework uses two mathematically distinct but computationally connected layers:

1. **Neutrosophic-soft evaluation layer** — each player is evaluated under multiple criteria through triples $(T,I,F)$ representing truth/satisfactory performance, indeterminacy, and falsity/unsatisfactory performance.
2. **Crisp orbit-topological interaction layer** — a fixed self-map on the player set is derived from pairwise tactical compatibility, generating forward orbits and an associated orbit topology.

These layers are combined in a team-level objective optimized under role and formation constraints.

The case study considers **20 Manchester City players from the 2024-2025 Premier League season** and searches for a feasible **4-3-3 starting eleven**.

The repository also contains a separate player-level benchmark used for the manuscript's MCDM comparison. It evaluates agreement between the role-specific individual neutrosophic-soft ranking and TOPSIS, VIKOR, and single-valued neutrosophic TOPSIS through Spearman's rank correlation.

---

## Main mathematical ingredients

### 1. Football evaluation universe

Let

```math
U=\{P_1,\ldots,P_n\}
```

be the set of candidate players. Each player is evaluated with respect to twelve criteria:

| Code | Criterion |
|---|---|
| `C1` | Passing Accuracy |
| `C2` | Ball Control |
| `C3` | Dribbling Ability |
| `C4` | Shooting Accuracy |
| `C5` | Defensive Ability |
| `C6` | Tactical Awareness |
| `C7` | Positioning |
| `C8` | Speed |
| `C9` | Stamina |
| `C10` | Teamwork |
| `C11` | Decision Making |
| `C12` | Physical Fitness |

The importance of the criteria is **role-dependent**: goalkeepers, defenders, midfielders, and forwards use different normalized weight vectors.

### 2. Neutrosophic evaluation matrix

The player-evaluation matrix is

```math
M=\big[(T_{ij},I_{ij},F_{ij})\big]_{n\times 12}.
```

For player $P_i$ and criterion $C_j$, the three components preserve separate information about satisfactory performance, uncertainty, and unsatisfactory performance.

The role-specific Neutrosophic Overall Score is

```math
\mathrm{NOS}^{k}(P_i)
=
\sum_{j=1}^{12} w_j^k
\left(T_{ij}-\alpha_I I_{ij}-\alpha_F F_{ij}\right),
```

where $k\in\{G,D,M,F\}$. In the numerical case study, $\alpha_I=\alpha_F=1$.

The implementation also uses the normalized score

```math
\widehat{\mathrm{NOS}}^{k}(P_i)
=
\frac{\mathrm{NOS}^{k}(P_i)+\alpha_I+\alpha_F}
{1+\alpha_I+\alpha_F}.
```

### 3. Tactical compatibility

A normalized directed interaction matrix

```math
A=(a_{ij}), \qquad 0\le a_{ij}\le 1,
```

is used to derive the symmetric Tactical Compatibility Index

```math
\mathrm{TCI}(P_i,P_j)
=
\frac{a_{ij}+a_{ji}}{2},
\qquad i\neq j.
```

The diagonal follows the self-similarity convention

```math
a_{ii}=1,
```

but self-interaction is excluded when the orbit successor is chosen.

### 4. Fixed orbit map and orbit topology

For every player,

```math
\phi(P_i)
=
P_{\mathrm{arg\,max}_{k\ne i}\mathrm{TCI}(P_i,P_k)},
```

with deterministic tie breaking when necessary.

The forward orbit is

```math
\mathrm{Orb}_{\phi}(P_i)
=
\{P_i,\phi(P_i),\phi^2(P_i),\ldots\}.
```

The associated orbit topology is

```math
\tau_{\phi}
=
\{O\subseteq U:\phi(O)\subseteq O\}.
```

A key modelling point is that **the map $\phi$ is fixed globally**. This prevents the orbit-open condition from becoming vacuous through a set-dependent choice of the map.

### 5. Orbit Tactical Interaction index

For each player,

```math
\mathrm{OTI}(P_i)
=
\mathrm{TCI}(P_i,\phi(P_i)),
```

which measures the strength of the first transition in the player's orbit.

### 6. Constrained team selection

The implementation enforces:

- 1 goalkeeper;
- 4 defenders;
- 3 midfielders;
- 3 forwards;
- 11 distinct players;
- assignment only to explicitly eligible roles.

The Team Selection Function combines:

1. role-specific normalized player quality;
2. pairwise tactical compatibility;
3. retained orbit interactions.

With the default parameters,

```math
\alpha=0.50,\qquad \beta=0.35,\qquad \gamma=0.15.
```

The code exhaustively evaluates every feasible 4-3-3 assignment and returns the maximum TSF.

---

## Computational workflow

```text
Frozen raw player metrics
        |
        v
Neutrosophic evaluation matrix (T, I, F)
        |
        v
Directed passing-role interaction matrix
        |
        v
TCI matrix + fixed orbit map phi
        |
        v
Forward orbits + OTI diagnostics
        |
        v
Role-specific NOS / normalized NOS
        |
        +-----------------------------> Player-level MCDM benchmark
        |                                  |
        |                                  +--> TOPSIS
        |                                  +--> VIKOR
        |                                  +--> Neutrosophic TOPSIS
        |                                  +--> Spearman rank agreement
        |
        v
Feasible 4-3-3 assignments
        |
        v
Team Selection Function
        |
        v
Optimal feasible starting XI
        |
        v
Monte Carlo sensitivity analysis
        |
        +--> per-replication diagnostics
        +--> player selection frequencies
```

The MCDM comparison is deliberately a **player-level** benchmark. It does not replace or re-express the team-level TSF optimizer.

---

## Data provenance

The statistical source underlying the frozen case-study data is **FBref**. For automated acquisition, `download_fbref_data.py` uses the public Kaggle dataset **Hubert Sidorowicz, Football Players Stats (2024-2025)**, which is derived from FBref.

The documented acquisition chain is:

```text
FBref season statistics
    -> FBref-derived Kaggle dataset
    -> download_fbref_data.py
    -> data/manchester_city_fbref_source.csv
    -> data/raw_player_metrics.csv
```

The frozen `data/raw_player_metrics.csv` is sufficient to reproduce the numerical experiment. Re-downloading the external source is optional.

Top-speed and distance-covered variables are left missing when no homogeneous season-level source is available for all twenty players. The code does **not** invent these values; missing evidence is represented through the indeterminacy component.

See `DATA_PROVENANCE.md` and `DATA_SOURCES.md` for the complete definitions and acquisition details.

---

## Reproduced case-study result

With official roles only, the roster counts would give

```math
2\binom{6}{4}\binom{8}{3}\binom{4}{3}=6720
```

4-3-3 combinations. The executable model also allows Phil Foden (`P14`) as `M|F`, so the actual search space contains **13,020 feasible assignments**.

The current reproducible optimum is:

| Role | Player code | Player |
|---|---|---|
| G | P1 | Ederson |
| D | P3 | Rúben Dias |
| D | P5 | Manuel Akanji |
| D | P7 | Joško Gvardiol |
| D | P8 | Rico Lewis |
| M | P10 | Kevin De Bruyne |
| M | P11 | Bernardo Silva |
| M | P13 | Matheus Nunes |
| F | P14 | Phil Foden |
| F | P15 | Jérémy Doku |
| F | P16 | Jack Grealish |

The corresponding objective values are:

```text
individual component     0.626305247
compatibility component  0.228708902
orbit component          0.416622967
TSF                      0.455694184
orbit transitions        11/11
orbit-open               True
```

The authoritative generated files are `output/optimal_starting_xi.csv` and `CASE_STUDY_RESULTS.md`.

---

## Quick start

**Python 3.10 or later** is recommended.

### Reproduce the frozen case study

The core experiment uses only the Python standard library:

```bash
python run_case_study.py
```

No third-party dependency is required for this step. `requirements.txt` documents this core environment.

The command:

- rebuilds the neutrosophic evaluation matrix;
- rebuilds the directed interaction matrix;
- constructs TCI, the fixed orbit map and orbit diagnostics;
- computes player-level scores;
- exhaustively optimizes the feasible 4-3-3 assignments;
- runs 1000 Monte Carlo weight perturbations;
- writes per-replication sensitivity diagnostics;
- writes player selection frequencies.

### Reproduce the MCDM/Spearman comparison

The role-specific player-ranking comparison reported in the manuscript is reproduced with:

```bash
python compare_mcdm.py
```

The comparison is performed independently within each player's **official role**, because `data/weights.csv` contains role-specific criterion weights. The reference ranking is the raw role-specific neutrosophic-soft NOS ranking. Phil Foden (`P14`) is therefore treated as a midfielder in this benchmark, even though the team optimizer also permits him to be assigned as a forward.

The script evaluates:

- a weighted-sum $T$ diagnostic retained only as an **AHP-style proxy**;
- classical TOPSIS on the $T$ components;
- classical VIKOR on the $T$ components, with default $v=0.5$;
- single-valued neutrosophic TOPSIS using the complete $(T,I,F)$ triples.

The weighted-sum result is **not** presented as a full AHP benchmark, because the frozen case-study data contain neither pairwise AHP judgements nor an externally calibrated absolute-rating scale.

Spearman's coefficient is calculated as the Pearson correlation of average rank vectors, so ties are handled explicitly. The goalkeeper group is retained in the machine-readable calculation for reproducibility, but its value is not interpreted in the manuscript because only two goalkeeper candidates are available.

The script generates:

```text
output/mcdm_player_rankings.csv
output/mcdm_spearman.csv
```

For the role classes reported in the manuscript, the reproduced Spearman coefficients versus NOS are:

| Method | Defender D | Midfielder M | Forward F |
|---|---:|---:|---:|
| TOPSIS | 0.543 | 0.714 | 0.200 |
| VIKOR | 0.371 | 0.595 | -0.800 |
| Neutrosophic TOPSIS | 1.000 | 1.000 | 1.000 |

The value `1.000` for Neutrosophic TOPSIS means that, for this frozen dataset, it induces the same within-role ordering as the individual NOS score. It does **not** imply equivalence with the complete proposed framework, which additionally uses tactical compatibility, orbit structure, role eligibility, and constrained team optimization.

### Run the automated tests

The complete reproducibility test suite is executed with:

```bash
python -m unittest discover -s tests -v
```

The tests verify the main model invariants and reproduced optimum as well as the role-specific MCDM/Spearman values.

### Rebuild the raw input from the external source

Data acquisition requires `kagglehub`:

```bash
pip install -r requirements-data.txt
python download_fbref_data.py
```

Downloaded external files are placed under `external_data/`, which is intentionally excluded from Git version control.

---

## Sensitivity analysis

The default experiment uses:

```text
B = 1000
delta = 0.10
seed = 2026
```

For each replication, the role-dependent criterion weights are independently perturbed within the specified envelope and then renormalized.

The code records:

```text
selected_players
jaccard
tsf_optimum
tsf_baseline_reference
delta_tsf
tsf_baseline_perturbed
regret
orbit_open
```

where

```math
\Delta_b=TSF_b-TSF_0.
```

For the current case study, the same starting XI is retained in all 1000 simulations. The mean Jaccard similarity is 1, the maximum regret is 0 to reported precision, and all eleven baseline players have selection frequency 1.

Detailed results are stored in `output/sensitivity.csv`; player-level frequencies are stored in `output/selection_frequencies.csv`.

---

## MCDM and Spearman benchmark

`compare_mcdm.py` is intentionally separated from the team optimizer. Its purpose is to make the manuscript's player-level MCDM comparison reproducible without claiming that TOPSIS, VIKOR, or Neutrosophic TOPSIS solve the same constrained team-assignment problem as the proposed TSF model.

The comparison uses the same frozen neutrosophic matrix and the same role-specific criterion weights as the main case study. Ranking agreement is calculated within role, rather than across the full 20-player roster, because the criterion-weight vectors differ by position.

The generated `output/mcdm_player_rankings.csv` contains the underlying scores and ranks for every candidate and method. `output/mcdm_spearman.csv` contains the corresponding role-specific Spearman coefficients. These two files are regenerated whenever `python compare_mcdm.py` is run.

---

## Repository structure

```text
.
├── README.md
├── CITATION.cff
├── LICENSE
├── requirements.txt
├── requirements-data.txt
├── run_case_study.py
├── build_neutrosophic_matrix.py
├── build_interaction_matrix.py
├── download_fbref_data.py
├── football_team_selection.py
├── compare_mcdm.py
├── DATA_PROVENANCE.md
├── DATA_SOURCES.md
├── CASE_STUDY_RESULTS.md
├── RELEASE_NOTES.md
├── data/
│   ├── players.csv
│   ├── weights.csv
│   ├── criteria_definition.csv
│   ├── raw_player_metrics.csv
│   ├── physical_metrics.csv
│   ├── physical_metrics_verified_partial.csv
│   ├── neutrosophic_matrix.csv
│   ├── neutrosophic_matrix_template.csv
│   ├── interaction_matrix.csv
│   ├── interaction_matrix_template.csv
│   └── raw_player_metrics_template.csv
├── tests/
│   ├── test_model.py
│   └── test_mcdm.py
└── output/
    ├── player_scores.csv
    ├── orbits.csv
    ├── optimal_starting_xi.csv
    ├── sensitivity.csv
    ├── selection_frequencies.csv
    ├── mcdm_player_rankings.csv      # generated by compare_mcdm.py
    └── mcdm_spearman.csv             # generated by compare_mcdm.py
```

### Main files

- `run_case_study.py` — one-command reproduction of the complete numerical case study.
- `build_neutrosophic_matrix.py` — converts frozen raw player data into the $(T,I,F)$ evaluation matrix.
- `build_interaction_matrix.py` — constructs the directed passing-role interaction potential.
- `football_team_selection.py` — implements scores, tactical compatibility, orbit structure, feasibility, optimization and sensitivity analysis.
- `compare_mcdm.py` — reproduces the role-specific player-level MCDM benchmark and Spearman rank-agreement analysis used in the manuscript.
- `download_fbref_data.py` — optional reconstruction of the raw input from the FBref-derived Kaggle dataset.
- `tests/test_model.py` — automated reproducibility tests for the core football-selection model, including weights, interaction/orbit invariants, the baseline optimum and selection-frequency calculations.
- `tests/test_mcdm.py` — automated tests that reproduce the role-specific Spearman coefficients and verify that the weighted-sum diagnostic is explicitly marked as a proxy rather than a full AHP implementation.
- `data/raw_player_metrics.csv` — frozen Manchester City Premier League 2024-25 case-study input.
- `data/neutrosophic_matrix.csv` — generated $20\times12$ neutrosophic matrix.
- `data/interaction_matrix.csv` — generated $20\times20$ directed interaction matrix with unit diagonal.
- `output/player_scores.csv` — NOS, normalized NOS, successor and OTI values.
- `output/orbits.csv` — successor and forward-orbit diagnostics.
- `output/optimal_starting_xi.csv` — maximizing feasible 4-3-3 assignment.
- `output/sensitivity.csv` — per-replication Monte Carlo robustness diagnostics.
- `output/selection_frequencies.csv` — player selection counts and frequencies.
- `output/mcdm_player_rankings.csv` — generated role-specific NOS and MCDM scores/ranks for the player-level comparison.
- `output/mcdm_spearman.csv` — generated role-specific Spearman correlations versus the reference NOS ranking.
- `DATA_PROVENANCE.md` — data definitions, transformations and provenance.
- `DATA_SOURCES.md` — source-acquisition workflow.
- `CASE_STUDY_RESULTS.md` — compact numerical summary of the reproduced team-selection experiment.
- `CITATION.cff` — machine-readable software and preferred-paper citation metadata.
- `LICENSE` — MIT software license.

---

## Reproducibility principles

The repository is designed to make the numerical study auditable and reproducible:

- derived matrices are generated from frozen source data rather than copied from manuscript tables;
- the orbit successor excludes self-interaction even though `a_ii=1` is retained as a similarity convention;
- tie breaking in the orbit map is deterministic;
- role eligibility is explicit;
- missing measurements are not reconstructed by guesswork;
- unavailable tracking evidence is represented through indeterminacy;
- the exhaustive search reports the actual number of feasible assignments;
- sensitivity perturbations use a fixed random seed;
- both per-replication diagnostics and player selection frequencies are exported;
- MCDM comparisons are computed within official role classes to respect role-specific criterion weights;
- the AHP-style weighted-sum diagnostic is explicitly distinguished from a full AHP implementation;
- Spearman coefficients are generated from the underlying rank vectors rather than entered manually;
- automated tests freeze the principal numerical results used by the manuscript.

---

## Complexity

Let $n$ be the number of candidate players, $m$ the number of criteria, and $N_{\mathrm{feas}}$ the number of feasible role assignments.

The principal computational costs are approximately:

- player-score construction: $O(nm)$;
- complete pairwise compatibility construction: $O(n^2)$;
- straightforward orbit generation: at most $O(n^2)$;
- exhaustive team evaluation: $O(N_{\mathrm{feas}}\,11^2)$.

The combinatorial search over feasible formations is therefore the dominant term for larger candidate pools.

The MCDM benchmark operates only on the fixed player candidate set and is computationally negligible relative to the exhaustive team search in the present case study.

---

## Interpretation and scope

This project is a **mathematically structured decision-support framework**, not a replacement for expert coaching judgement.

The current numerical experiment is deliberately limited to one professional squad, twelve predefined criteria, season-aggregated data, a fixed tactical-interaction construction and a fixed 4-3-3 formation.

The MCDM/Spearman values measure **within-role agreement between player-level rankings**. They are not measures of predictive accuracy and do not establish superiority of one decision method over another. In particular, the team-level TSF has a different final output from the ranking methods because it solves a constrained team-assignment problem.

Potential extensions include opponent-specific constraints, rolling or match-specific data, high-frequency spatiotemporal player-tracking data, expected-goals variables, fatigue indicators, substitutions, formation changes, ablation studies and richer dynamical/topological analysis of the interaction map.

---

## Keywords

`Neutrosophic Over Soft Sets` · `Orbit Topology` · `Football Team Selection` · `Multi-Criteria Decision Making` · `Sports Analytics` · `Uncertainty Modelling` · `Tactical Compatibility` · `Soft Topology`

### 2020 Mathematics Subject Classification

**Primary:** 54A40  
**Secondary:** 03E72, 37B02, 90C70, 90C27

---

## Citation

If you use this repository in academic work, please cite the accompanying manuscript. Until final publication metadata and a DOI are available, the following provisional BibTeX entry can be used and later updated:

```bibtex
@misc{abdulkadhim2026neutrosophic,
  title  = {A Novel Neutrosophic Over Soft Orbit Topological Framework for Football Team Selection under Uncertainty},
  author = {Abdulkadhim, Murtadha M. and Imran, Qays Hatem and Yaseen, S. R. and Nordo, Giorgio},
  year   = {2026},
  note   = {Manuscript and accompanying reproducible Python implementation}
}
```

The repository also contains `CITATION.cff` for machine-readable software citation metadata.
