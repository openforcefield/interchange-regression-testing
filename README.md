# interchange-regression-testing
Regression testing Interchange's OpenMM export against the OpenFF Toolkit

To test against the Industry Benchmarking Season 1 v1.0 dataset, run something like
$ conda env create --file dev_env.yaml --quiet
$ conda activate interchange-regression-testing
$ wget https://raw.githubusercontent.com/openforcefield/qca-dataset-submission/master/submissions/2021-03-30-OpenFF-Industry-Benchmark-Season-1-v1.0/dataset.smi
$ python compare-against-toolkit.py
```

This will take a few to several hours and produce a large file `data.csv` with per-component potential energy
differences between the `openmm.System` objects produced by `ForceField.create_openmm_system` and
`Interchange.to_openmm`. These can be read up in Python with

```python3
import pandas as pd
df = pd.read_csv('data.csv', index_col='SMILES')
```

for analysis with any Pandas-compatible tool.

To compare against physical properties, use something like a [Sage training
set](https://github.com/openforcefield/openff-sage/blob/main/data-set-curation/physical-property/optimizations/data-sets/sage-train-v1.json) and run
```
$ python compare-condensed-systems.py
Run other tests with something like
```
$ pytest -v
```
