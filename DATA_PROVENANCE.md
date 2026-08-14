# Data provenance

## Scope

The numerical example uses **Manchester City, Premier League 2024-2025 only**.
The 20 players are the candidates listed in the manuscript.

The raw football statistics in `data/raw_player_metrics.csv` were transcribed
from the final 2024-2025 Manchester City Premier League tables on FBref.

Source page:

https://fbref.com/en/squads/b8fd03ef/2024-2025/Manchester-City-Stats

The page reports the final league record (38 matches) and provides the
standard, shooting, passing, defensive-actions, possession, miscellaneous,
goalkeeping and advanced-goalkeeping tables used here.

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
(T,I,F)=(0.5,1,0.5). C12 (Physical Fitness) still contains the availability
component derived from playing time, with the missing distance component
reflected in its completeness factor.

## Neutrosophic transformation

For every available indicator, the case-study program applies min-max
normalization. Cost variables such as miscontrols, dispossessions and errors
are reversed.

For normalized evidence q_1,...,q_r,

    T = mean(q_1,...,q_r)
    F = 1 - T
    I = 1 - min(1, 90s/20) * completeness

Thus T+F=1 while I is independent. In particular, T+I+F=1 is not imposed.

## Pairwise tactical matrix

The public aggregate FBref tables do not contain observed player-to-player
pass counts. The case study therefore does not claim that `interaction_matrix.csv`
is a direct passing network.

Instead, `build_interaction_matrix.py` constructs a transparent
**passing-role interaction potential**. Let p_i be normalized progressive
passes per 90, r_i normalized progressive receptions per 90, and

    rho_i = min(1, 90s_i/20).

For i != j,

    b_ij = sqrt(rho_i rho_j) p_i r_j.

The off-diagonal values are divided by their maximum to produce a_ij in
[0,1]. The diagonal is set to zero and is excluded from the orbit successor.

This definition makes the pairwise matrix fully reproducible from the
published aggregate data while explicitly distinguishing tactical affinity
from directly observed player-to-player passes.
