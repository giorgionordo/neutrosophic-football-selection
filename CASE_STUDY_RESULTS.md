# Reproducible case-study results

Parameters:

- alpha_I = 1.00
- alpha_F = 1.00
- alpha = 0.50
- beta = 0.35
- gamma = 0.15

Number of feasible 4-3-3 assignments: **13020**.

Optimal Team Selection Function:

- individual component = **0.626305247**
- compatibility component = **0.228708902**
- orbit component = **0.416622967**
- TSF = **0.455694184**
- retained orbit transitions = **11/11**
- selected set orbit-open = **True**

## Selected starting XI

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

## Sensitivity analysis

Monte Carlo perturbations: **1000**

Perturbation envelope: **+-10%**

Random seed: **2026**

For each replication `b`, the code records the perturbed optimum `TSF_b`, the
baseline-reference value `TSF_0`,

```text
Delta_b = TSF_b - TSF_0,
```

the TSF attained by the baseline XI under the same perturbed weights, and the
corresponding regret.

Across all 1000 perturbations:

- mean Jaccard similarity with the baseline XI = **1.000000**
- minimum Jaccard similarity = **1.000000**
- maximum regret = **0.000000000**
- orbit-open frequency = **1.000000**
- mean optimized TSF = **0.455691794**
- standard deviation of optimized TSF = **0.000864886**
- mean Delta_b = **-0.000002390**
- minimum Delta_b = **-0.002746697**
- maximum Delta_b = **0.002713591**

The same starting XI was retained in all 1000 simulations under the specified
criterion-weight perturbation experiment. Consequently, the eleven baseline
players have selection frequency `f_i = 1.0`, while all remaining candidates
have `f_i = 0.0`.

Detailed per-replication diagnostics are stored in
`output/sensitivity.csv`. Player-level selection counts and frequencies are
stored in `output/selection_frequencies.csv`.
