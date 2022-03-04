# interchange-regression-testing
Regression testing Interchange's OpenMM export against the OpenFF Toolkit

Two conda environments are shipped via YAML files:
  * `reference_env.yaml` captures behavior and functionality as of OpenFF Toolkit v0.10.2.
  * `candidate_env.yaml` captures changes based on the version specified in file.

Create either via i.e.

```
$ mamba env create --file reference_env.yaml
$ mamba env create --file candidate_env.yaml
```

To evaluate single-molecule energies using [Industry Benchmarking Season 1 v1.0](https://github.com/openforcefield/qca-dataset-submission/tree/master/submissions/2021-03-30-OpenFF-Industry-Benchmark-Season-1-v1.0#readme) dataset, activate the appropriate conda environment and run
```
$ python evaluate-single-molecules.py
```

This will take a few to several hours and produce a large file somewhere in `results/TOOLKIT_VERSION/single-molecule-energies.csv` with per-component potential energy
evaluations using the `openmm.System` objects produced by `ForceField.create_openmm_system`. This
CSV file can then be processed with Pandas or a similar library:

```python3
import pandas as pd
df = pd.read_csv(
    "results/TOOLKIT_VERSION/single-molecule-energies.csv",
    index_col="SMILES",
)
```

To compare against physical properties, use something like a [Sage training
set](https://github.com/openforcefield/openff-sage/blob/main/data-set-curation/physical-property/optimizations/data-sets/sage-train-v1.json) and run
```
$ cd condensed-phase
$ sh run_condensed.sh
```

Run other tests with something like
```
$ pytest -v
```
