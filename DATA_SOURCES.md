# Data acquisition for the numerical case study

## Football performance statistics

The repository uses the public Kaggle dataset:

**Hubert Sidorowicz, Football Players Stats (2024-2025)**

The dataset is derived from FBref and contains the comprehensive file
`players_data-2024_2025.csv`, with standard, shooting, passing, possession,
defensive, miscellaneous and goalkeeping variables.

Run:

```bash
pip install -r requirements.txt
python download_fbref_data.py
```

The program creates:

```text
data/manchester_city_fbref_source.csv
data/raw_player_metrics.csv
```

The first file preserves the Manchester City source rows. The second file
contains only the variables used by the neutrosophic transformation.

## Physical tracking variables

FBref does not contain a complete common season-level table for top speed and
distance covered per 90. Therefore these variables are kept in the optional
file `data/physical_metrics.csv`.

The file `data/physical_metrics_verified_partial.csv` contains only a few
values directly verified from public Premier League/BBC material. It is not
merged automatically because those values do not form a complete common-time
snapshot for all twenty players.

If a physical measurement is unavailable, the neutrosophic transformation
represents the absence explicitly through indeterminacy rather than inventing
a value.

## Reproducibility chain

```text
public Kaggle/FBref source
    -> download_fbref_data.py
    -> raw_player_metrics.csv
    -> build_neutrosophic_matrix.py
    -> neutrosophic_matrix.csv
    -> football_team_selection.py
```
