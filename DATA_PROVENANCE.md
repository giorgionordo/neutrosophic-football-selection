# Data provenance

## Scope

The numerical example uses **Manchester City, Premier League 2024-2025 only**.
The 20 players are the candidates listed in the manuscript.

## Provenance chain

The statistical source underlying the case study is **FBref**. For automated
and reproducible acquisition, `download_fbref_data.py` uses the public Kaggle
dataset

**Hubert Sidorowicz, Football Players Stats (2024-2025)**,

which is derived from FBref and contains the season-level player tables needed
by the case study. The script filters the Manchester City Premier League rows,
preserves a source snapshot, and converts the required fields into the frozen
input file used by the numerical workflow.

The resulting provenance chain is therefore:

```text
FBref season statistics
    -> FBref-derived Kaggle dataset
    -> download_fbref_data.py
    -> data/manchester_city_fbref_source.csv
    -> data/raw_player_metrics.csv
```

The frozen `data/raw_player_metrics.csv` committed to this repository is the
input used to reproduce the published numerical experiment. A user who only
wants to reproduce the case study does not need to download the external
dataset again.

The corresponding FBref Manchester City 2024-2025 page is:

https://fbref.com/en/squads/b8fd03ef/2024-2025/Manchester-City-Stats

The underlying FBref material includes standard, shooting, passing,
defensive-actions, possession, miscellaneous, goalkeeping and
advanced-goalkeeping statistics.

See `DATA_SOURCES.md` for the acquisition commands and the distinction between
reproducing the frozen case study and rebuilding the raw input from the
external source.

## Variables

The raw file contains the following derived values.

- `nineties`: FBref 90s.
- `pass_completion_pct`: passing Cmp%.
- `takeon_success_pct`: possession take-on success percentage.
- `miscontrols_per90`: Mis / 90s.
- `dispossessed_per90`: Dis / 90s.
- `successful_takeons_per90`: successful take-ons / 90s.
- `progressive_carries_per90`: PrgC / 90s.
- `shots_on_target_pct`: shooting SoT%.
- `tackles_interceptions_per90`: (Tkl+Int) / 90s.
- `blocks_per90`: Blocks / 90s.
- `clearances_per90`: Clr / 90s.
- `recoveries_per90`: Recov / 90s.
- `progressive_passes_per90`: PrgP / 90s.
- `progressive_receptions_per90`: PrgR / 90s.
- `touches_att_pen_per90`: Att Pen touches / 90s.
- `completed_passes_per90`: passing Cmp / 90s.
- `key_passes_per90`: KP / 90s.
- `errors_per90`: Err / 90s.
- Goalkeeper-specific variables: Save%, #OPA/90 and PSxG+/-/90.

## Speed and stamina

A single homogeneous public season-level tracking table containing both
top speed and distance covered per 90 for all 20 candidates was not used.
Consequently, `top_speed_kmh` and `distance_per90_km` are deliberately left
empty in `raw_player_metrics.csv`.

The neutrosophic transformation does **not** impute or invent these values.
Missing evidence is represented explicitly through indeterminacy. For C8
(Speed) and C9 (Stamina), no observed tracking evidence therefore gives
`(T,I,F)=(0.5,1,0.5)`. C12 (Physical Fitness) still contains the availability
component derived from playing time, with the missing distance component
reflected in its completeness factor.

## Neutrosophic transformation

For every available indicator, the case-study program applies min-max
normalization. Cost variables such as miscontrols, dispossessions and errors
are reversed.

For normalized evidence `q_1,...,q_r`,

```text
T = mean(q_1,...,q_r)
F = 1 - T
I = 1 - min(1, 90s/20) * completeness
```

Thus `T+F=1` while `I` is independent. In particular, `T+I+F=1` is not
imposed.

## Pairwise tactical matrix

The public aggregate source data do not contain observed player-to-player pass
counts. The case study therefore does not claim that `interaction_matrix.csv`
is a direct passing network.

Instead, `build_interaction_matrix.py` constructs a transparent
**passing-role interaction potential**. Let `p_i` be normalized progressive
passes per 90, `r_i` normalized progressive receptions per 90, and

```text
rho_i = min(1, 90s_i/20).
```

For `i != j`,

```text
b_ij = sqrt(rho_i rho_j) p_i r_j.
```

The off-diagonal values are divided by their maximum to produce `a_ij` in
`[0,1]`. In accordance with the manuscript convention, the stored matrix uses
`a_ii = 1` on the diagonal as a self-similarity value. These diagonal entries
are excluded from the orbit-successor search, so they do not affect the map
`sigma`. The tactical compatibility function is therefore consistent with the
same convention `TCI(P_i,P_i)=1`.

This definition makes the pairwise matrix fully reproducible from the frozen
aggregate data while explicitly distinguishing tactical affinity from directly
observed player-to-player passes.
