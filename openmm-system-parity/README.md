# OpenMM Parity Comparisons

*Scripts for comparisons between OpenMM systems created using different*

1. Create a conda environment containing both the OpenFF Toolkit and OpenFF Interchange

```shell
cd ..
mamba env create --name interchange-regression-testing-latest --file environment-latest.yaml
mamba activate interchange-regression-testing-latest
python setup.py develop
cd -
```

2. Export the current toolkit and interchange versions

```shell
export TOOLKIT_VERSION=$(python -c "import openff.toolkit; print(openff.toolkit.__version__)")
export INTERCHANGE_VERSION=$(python -c "import openff.interchange; print(openff.interchange.__version__)")
```

3. Create the default comparison settings and any expected changes

```shell
python create-comparison-settings.py
python create-expected-changes.py
```

4. For each set of comparisons `xxx` you wish to run, e.g. `small-molecule`:

```shell
# Create the files specifying which topologies to create systems for
python create-xxx-inputs.py

# Create OpenMM system files for each molecule / topology of interest using both the 
# toolkit and OpenFF Interchange
create_openmm_systems --input  "xxx/input-topologies.json" \
                      --output "xxx" \
                      --using-interchange \
                      --n-procs 10   
create_openmm_systems --input  "xxx/input-topologies.json" \
                      --output "xxx" \
                      --using-toolkit \
                      --n-procs 10
                      
# Compare the OpenMM systems created using the legacy toolkit and new OpenFF Interchange
# code
compare_openmm_systems --input-dir-a "xxx/omm-systems-toolkit-$TOOLKIT_VERSION" \
                       --input-dir-b "xxx/omm-systems-interchange-$INTERCHANGE_VERSION" \
                       --output      "xxx-toolkit-$TOOLKIT_VERSION-vs-interchange-$INTERCHANGE_VERSION.json" \
                       --settings    "comparison-settings/default-comparison-settings.json" \
                       --expected-changes "expected-changes/toolkit-0-11-x-to-interchange-0-2-x.json" \
                       --n-procs     10
```
