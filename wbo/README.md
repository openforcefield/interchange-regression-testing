Some molecules presumed to have fractional bond orders are selected from [here](https://github.com/openforcefield/qca-dataset-submission/blob/f5be666d368a8781379fe229df8ab6ecc865c61a/submissions/2020-10-06-OpenFF-Phenyl-Set/molecules.smi#L1-L10)

An OFFXML snippet is taken from
[tests](https://github.com/openforcefield/openff-toolkit/blob/9be59f23a90cb64f207eabc895ed55200826dd3a/openff/toolkit/tests/test_forcefield.py#L310)
in the OpenFF Toolkit.

To prepare referennce and candidate data and run the XML-based comparison, run
```
$ conda activate reference-env
$ python serialize-wbo-molecules.py
$ conda activate candidate-env
$ python serialize-wbo-molecules.py
$ python diff.py
```
