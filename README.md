# interchange-regression-testing
Regression testing Interchange's OpenMM export against the OpenFF Toolkit

To test against the NCI dataset, run something like
```shell
$ conda env create --file dev_env.yaml --quiet
$ conda activate interchange-regression-testing
$ curl https://cactus.nci.nih.gov/download/nci/NCI-Open_2012-05-01.sdf.gz --output NCI-molecules.sdf.gz
$ gunzip NCI-molecules.sdf.gz
$ python compare_against_toolkit.py
