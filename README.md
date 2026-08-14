# Neutrosophic-Soft Orbit Football Team Selection

Research code accompanying the manuscript

> **A Novel Neutrosophic Over Soft Orbit Topological Framework for Football Team Selection under Uncertainty**

This repository contains a reproducible Python implementation of the numerical football case study developed in the manuscript. The framework combines **neutrosophic-soft multi-criteria evaluation**, **orbit topology induced by a fixed player-interaction map**, **tactical compatibility**, **position-dependent weighting**, and **constrained 4-3-3 team optimization**.

The code is organized so that the numerical objects used in the case study can be rebuilt from the source data rather than copied manually from tables in the paper.

---

## Authors

| Author | Affiliation |
|---|---|
| **Murtadha M. Abdulkadhim** | Department of First Grade Teacher Education, College of Basic Education, Al-Muthanna University, Samawah 66001, Iraq |
| **Qays Hatem Imran*** | Department of Mathematics, College of Education for Pure Science, Al-Muthanna University, Samawah 66001, Iraq |
| **Yaseen S. R.** | Department of Mathematics, College of Education for Pure Science, Tikrit University, Tikrit 34001, Iraq |
| **Giorgio Nordo** | MIFT Department, University of Messina, Viale Ferdinando Stagno d'Alcontres 31, 98166 Messina, Italy |

**Corresponding author:** Qays Hatem Imran — `qays.imran@mu.edu.iq`

---

## Overview

Selecting a football team is not simply a matter of ranking players by individual performance. A realistic selection procedure must also account for uncertainty in the available data, positional constraints, tactical relationships between players, and the fact that the value of a player can depend on the role in which that player is used.

The proposed framework addresses these aspects through two mathematically distinct but computationally connected layers:

1. **Neutrosophic-soft evaluation layer** — each player is evaluated under multiple criteria through triples
   $(T,I,F)$, representing truth/satisfactory performance, indeterminacy, and falsity/unsatisfactory performance.
2. **Crisp orbit-topological interaction layer** — a fixed self-map on the player set is derived from pairwise tactical interaction data, generating forward orbits and an associated orbit topology.

These layers are then combined in a team-level optimization model rather than using individual ranking alone.

The case study considers **20 Manchester City first-team players from the 2024-2025 season** and searches for a feasible **4-3-3 starting eleven**.

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
\operatorname{NOS}^{k}(P_i)
=
\sum_{j=1}^{12} w_j^k
\left(T_{ij}-\alpha_I I_{ij}-\alpha_F F_{ij}\right),
```

where $k\in\{G,D,M,F\}$ denotes goalkeeper, defender, midfielder, or forward. In the numerical case study, $\alpha_I=\alpha_F=1$.

### 3. Tactical compatibility

A normalized directed interaction matrix

```math
A=(a_{ij}), \qquad 0\le a_{ij}\le 1,
```

is used to derive the symmetric Tactical Compatibility Index

```math
\operatorname{TCI}(P_i,P_j)
=
\frac{a_{ij}+a_{ji}}{2},
\qquad i\neq j.
```

The diagonal is treated only as a similarity convention and is **excluded** when the orbit successor is chosen.

### 4. Fixed orbit map and orbit topology

For every player,

```math
\phi(P_i)
=
P_{\arg\max_{k\ne i}\operatorname{TCI}(P_i,P_k)},
```

with deterministic tie breaking when necessary.

The forward orbit is

```math
\operatorname{Orb}_{\phi}(P_i)
=
\{P_i,\phi(P_i),\phi^2(P_i),\ldots\}.
```

The associated orbit topology is

```math
\tau_{\phi}
=
\{O\subseteq U:\phi(O)\subseteq O\}.
```

A key modelling point is that **the map $\phi$ is fixed globally**. This prevents the orbit-open condition from becoming mathematically vacuous through a set-dependent choice of the map.

### 5. Orbit Interaction Index

For each player,

```math
\operatorname{OTI}(P_i)
=
\operatorname{TCI}(P_i,\phi(P_i)),
```

which measures the strength of the first transition in the player's orbit.

### 6. Constrained team selection

The implementation enforces role eligibility and the positional requirements of a 4-3-3 formation:

- 1 goalkeeper;
- 4 defenders;
- 3 midfielders;
- 3 forwards;
- no player can occupy more than one selected role;
- a player can only be assigned to a role declared as eligible.

The Team Selection Function combines three normalized components:

1. role-specific individual quality (`NOS`);
2. pairwise tactical compatibility (`TCI`);
3. retention of strong orbit transitions (`OTI`).

The final starting eleven is selected by maximizing this team-level objective over all feasible assignments.

---

## Computational workflow

The repository implements the following reproducible pipeline:

```text
Raw player metrics
        |
        v
Neutrosophic evaluation matrix (T, I, F)
        |
        v
Normalized interaction matrix
        |
        v
TCI matrix + fixed orbit map phi
        |
        v
Forward orbits + orbit diagnostics
        |
        v
Role-specific NOS + OTI
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
```

---

## Case study

The numerical example uses a 20-player Manchester City roster from the **2024-2025 season**. Public football information used in the study is based on sources such as the **Premier League**, **Manchester City FC**, and **FBref**; the repository-specific definitions and transformations are documented in `DATA_PROVENANCE.md`.

With players restricted to their listed official roles, the roster composition considered in the manuscript consists of two goalkeepers, six defenders, eight midfielders, and four forwards. This gives

```math
2\binom{6}{4}\binom{8}{3}\binom{4}{3}=6720
```

possible 4-3-3 role combinations before accounting for additional multi-position eligibility.

### Starting XI reported in the manuscript case study

| Role | Player |
|---|---|
| Goalkeeper | Ederson |
| Defender | Rúben Dias |
| Defender | Manuel Akanji |
| Defender | Nathan Aké |
| Defender | Rico Lewis |
| Midfielder | Kevin De Bruyne |
| Midfielder | Mateo Kovačić |
| Midfielder | İlkay Gündoğan |
| Forward | Jérémy Doku |
| Forward | Erling Haaland |
| Forward | Phil Foden |

Phil Foden illustrates the role-eligibility mechanism: although listed as a midfielder in the case-study roster, he can be selected as a forward only when that alternative role is explicitly enabled in the eligibility matrix.

The authoritative numerical output of the repository is generated by the code and stored in `output/optimal_starting_xi.csv`.

---

## Quick start

**Python 3.10 or later** is recommended. The current implementation uses only the Python standard library; no third-party packages are required.

From PyCharm, run:

```text
run_case_study.py
```

or from a terminal:

```bash
python run_case_study.py
```

The program:

- rebuilds the neutrosophic evaluation matrix;
- rebuilds the pairwise tactical interaction matrix;
- constructs the tactical compatibility matrix and the fixed orbit map;
- generates orbit diagnostics;
- computes player-level scores;
- enumerates and optimizes feasible 4-3-3 assignments;
- runs a **1000-repetition sensitivity analysis**.

---

## Repository structure

```text
.
├── run_case_study.py
├── build_neutrosophic_matrix.py
├── build_interaction_matrix.py
├── football_team_selection.py
├── DATA_PROVENANCE.md
├── CASE_STUDY_RESULTS.md
├── data/
│   ├── raw_player_metrics.csv
│   ├── neutrosophic_matrix.csv
│   └── interaction_matrix.csv
└── output/
    ├── player_scores.csv
    ├── orbits.csv
    ├── optimal_starting_xi.csv
    └── sensitivity.csv
```

### Main files

- `run_case_study.py` — one-command reproduction of the complete numerical experiment.
- `build_neutrosophic_matrix.py` — converts raw player data into the $(T,I,F)$ evaluation matrix.
- `build_interaction_matrix.py` — constructs the directed passing/role-affinity interaction matrix.
- `football_team_selection.py` — computes compatibility, orbit structure, scores, feasibility constraints, and team optimization.
- `data/raw_player_metrics.csv` — Manchester City Premier League 2024-25 case-study inputs.
- `data/neutrosophic_matrix.csv` — generated $20\times12$ neutrosophic matrix.
- `data/interaction_matrix.csv` — generated $20\times20$ directed interaction matrix.
- `output/player_scores.csv` — player scores and orbit-related indicators (`NOS`, normalized `NOS`, `sigma`, `OTI`).
- `output/orbits.csv` — orbit and successor diagnostics.
- `output/optimal_starting_xi.csv` — maximizing feasible 4-3-3 assignment.
- `output/sensitivity.csv` — results of the 1000 Monte Carlo perturbations.
- `DATA_PROVENANCE.md` — exact data definitions, transformations, and sources.
- `CASE_STUDY_RESULTS.md` — numerical summary of the reproduced experiment.

---

## Reproducibility principles

The repository is designed to make the numerical study auditable and reproducible.

In particular:

- derived matrices are generated from source data rather than transcribed manually;
- the orbit successor excludes self-interaction, avoiding the trivial identity map caused by diagonal values equal to one;
- tie breaking in the orbit map is deterministic;
- role eligibility is explicit rather than inferred during optimization;
- missing measurements are **not reconstructed by guesswork**;
- tracking variables unavailable on a common public basis are represented through the **indeterminacy component** rather than filled with artificial values;
- sensitivity perturbations are run repeatedly instead of relying on a single modified weight vector.

For the complete methodological specification, see `DATA_PROVENANCE.md`.

---

## Complexity

Let $n$ be the number of candidate players, $m$ the number of criteria, and $N_{\mathrm{feas}}$ the number of feasible role assignments.

The principal computational costs are approximately:

- player-score construction: $O(nm)$;
- complete pairwise compatibility construction: $O(n^2)$;
- straightforward orbit generation: at most $O(n^2)$;
- exhaustive team evaluation: $O(N_{\mathrm{feas}}\,11^2)$.

Thus, the combinatorial search over feasible formations is the dominant term for larger candidate pools.

---

## Interpretation and scope

This project is intended as a **mathematically structured decision-support framework**, not as a replacement for expert coaching judgement.

The case study demonstrates how uncertain player evaluations and tactical interaction information can be combined in a single constrained model. The current experiment is deliberately limited to one professional squad, a predefined set of criteria, season-aggregated data, and a fixed formation.

Potential extensions include:

- opponent-specific tactical constraints;
- match-specific or rolling performance data;
- GPS and real-time positional tracking;
- expected goals (`xG`) and expected assists (`xA`);
- fatigue and dynamic player-condition indicators;
- substitution and formation changes;
- ablation studies separating individual, positional, pairwise, and orbit effects;
- machine-learning or reinforcement-learning components;
- deeper study of connectedness, closure operators, recurrent classes, and fixed points in football interaction orbit topologies.

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

---

## Research focus

The repository is intended to make the link between the theoretical framework and its numerical case study explicit: **uncertain multi-criteria player evaluation is handled in the neutrosophic-soft layer, while tactical relationships are represented by a fixed crisp interaction map and its orbit topology; the final choice is made at team level under positional constraints.**
