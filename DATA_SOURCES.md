# Data acquisition for the numerical case study

## Reproducing the case study from the repository

The repository already contains the frozen numerical inputs required to reproduce the case study reported by the Python implementation. No third-party package is required for this step.

Run:

```bash
python run_case_study.py
```

This rebuilds the neutrosophic matrix and tactical interaction matrix from the frozen raw metrics in `data/raw_player_metrics.csv`, then performs the constrained 4-3-3 optimization and the sensitivity analysis.

## Reconstructing the raw football data

The statistical source underlying the numerical case study is FBref. For automated acquisition, the repository uses the public Kaggle dataset:

**Hubert Sidorowicz, Football Players Stats (2024-2025)**

This dataset is derived from FBref and contains the comprehensive file `players_data-2024_2025.csv`, including standard, shooting, passing, possession, defensive, miscellaneous and goalkeeping variables.

To download that source dataset and reconstruct the Manchester City raw input file, install the optional data-acquisition dependency and run:

```bash
pip install -r requirements-data.txt
python download_fbref_data.py
```

The script creates:

```text
data/manchester_city_fbref_source.csv
data/raw_player_metrics.csv
```

The first file preserves the Manchester City rows extracted from the FBref-derived Kaggle dataset. The second contains only the variables used by the neutrosophic transformation and the tactical-interaction construction.

The externally downloaded Kaggle files are stored under `external_data/` and are intentionally excluded from version control.

## Physical tracking variables

FBref does not provide a complete common season-level table containing both top speed and distance covered per 90 for all twenty candidates. These variables are therefore kept separate in the optional file:

```text
data/physical_metrics.csv
```

The repository also contains `data/physical_metrics_verified_partial.csv`, which records only a small number of values that were separately verified from public sources. These partial measurements are not merged automatically because they do not constitute a homogeneous common-time dataset for all twenty candidates.

When a physical measurement is unavailable, the neutrosophic transformation does not impute or invent a value. The missing evidence is represented explicitly through the indeterminacy component.

## Reproducibility chain

The complete workflow is:

```text
FBref statistical source
    -> FBref-derived Kaggle dataset
    -> download_fbref_data.py
    -> data/raw_player_metrics.csv
    -> build_neutrosophic_matrix.py
    -> data/neutrosophic_matrix.csv

and

data/raw_player_metrics.csv
    -> build_interaction_matrix.py
    -> data/interaction_matrix.csv

then

data/neutrosophic_matrix.csv + data/interaction_matrix.csv
    -> football_team_selection.py
    -> output/
```

For ordinary reproduction of the published numerical experiment, the frozen files already included in the repository are sufficient; rerunning the external data-acquisition step is optional.