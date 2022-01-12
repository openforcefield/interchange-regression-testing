# interchange-regression-testing
Regression testing Interchange's OpenMM export against the OpenFF Toolkit

To test against the NCI dataset, run something like
```shell
$ conda env create --file dev_env.yaml --quiet
$ conda activate interchange-regression-testing
$ curl https://cactus.nci.nih.gov/download/nci/NCI-Open_2012-05-01.sdf.gz --output NCI-molecules.sdf.gz
$ gunzip NCI-molecules.sdf.gz
$ python compare_against_toolkit.py
```

This will take several hours and produce a large file `data.csv` with per-component potential energy
differences between the `openmm.System` objects produced by `ForceField.create_openmm_system` and
`Interchange.to_openmm`. These can be read up in Python with

```python3
import pandas as pd
df = pd.read_csv('data.csv', index_col='SMILES')
```

for analysis with any Pandas-compatible tool.

Run other unit tests with something like
```
$ pytest -v
```
