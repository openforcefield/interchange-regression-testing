# Value Propagation

## Instructions

*Check that changes to a force field propagate through to changes in an OpenMM system*

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

3. Enumerate the fields of a SMIRNOFF force field that can be easily perturbed

```shell
python enumerate-perturbations.py --force-field "openff-2.0.0.offxml" \
                                  --output      "perturbations/default-perturbations.json"
```

4. Define the topologies that the perturbed force field will be applied to

```shell
python create-perturbed-molecule-inputs.py
```

5. Create the perturbed OpenMM systems

```shell
create_openmm_systems --input         "perturbed-systems/input-topologies.json" \
                      --output        "perturbed-systems" \
                      --perturbations "perturbations/default-perturbations.json" \
                      --using-toolkit \
                      --n-procs 1
                      
create_openmm_systems --input         "perturbed-systems/input-topologies.json" \
                      --output        "perturbed-systems" \
                      --perturbations "perturbations/default-perturbations.json" \
                      --using-interchange \
                      --n-procs 1
```

5a. (optionally) create un-perturbed OpenMM systems:

```shell
create_openmm_systems --input         "perturbed-systems/input-topologies.json" \
                      --output        "perturbed-systems" \
                      --using-toolkit \
                      --n-procs 1
create_openmm_systems --input         "perturbed-systems/input-topologies.json" \
                      --output        "perturbed-systems" \
                      --using-interchange \
                      --n-procs 1
```

6. Compare whether the legacy OpenFF toolkit and new OpenFF Interchange exporters agree on how values
   should be propagated

```shell
compare_openmm_systems --input-dir-a "perturbed-systems/omm-systems-toolkit-$TOOLKIT_VERSION" \
                       --input-dir-b "perturbed-systems/omm-systems-interchange-$INTERCHANGE_VERSION" \
                       --output      "perturbed-systems-$TOOLKIT_VERSION-vs-interchange-$INTERCHANGE_VERSION.json" \
                       --settings         "../openmm-system-parity/comparison-settings/default-comparison-settings.json" \
                       --n-procs     2
```

## Notes

For each of the below attributes, the OpenFF Toolkit version 0.10.x only supports one value and therefore no value 
propagation can be tested:

* `vdWHandler.potential`
* `vdWHandler.combining_rules`
* `vdWHandler.scale12`
* `vdWHandler.scale13`
* `vdWHandler.scale15`
* `vdWHandler.method`
* `ElectrostaticsHandler.scale12`
* `ElectrostaticsHandler.scale13`
* `ElectrostaticsHandler.scale15`
* `ElectrostaticsHandler.cutoff`
* `ElectrostaticsHandler.switch_width`
* `ElectrostaticsHandler.method`
* `BondHandler.potential`
* `BondHandler.fractional_bondorder_method`
* `BondHandler.fractional_bondorder_interpolation`
* `BondHandler.BondType.smirks`
* `BondHandler.BondType.id`
* `BondHandler.BondType.parent_id`
* `AngleHandler.potential`
* `AngleHandler.AngleType.smirks`
* `AngleHandler.AngleType.id`
* `AngleHandler.AngleType.parent_id`
* `ProperTorsionHandler.potential`
* `ProperTorsionHandler.fractional_bondorder_method`
* `ProperTorsionHandler.fractional_bondorder_interpolation`
* `ProperTorsionType.default_idivf`
* `ProperTorsionType.id`
* `ProperTorsionType.parent_id`
* `ImproperTorsionHandler.potential`
* `ImproperTorsionType.default_idivf`
* `ImproperTorsionType.id`
* `ImproperTorsionType.parent_id`
* `GBSAHandler.gb_model`
* `GBSAHandler.solvent_dielectric`
* `GBSAHandler.solute_dielectric`
* `GBSAHandler.sa_model`
* `GBSAHandler.surface_area_penalty`
* `GBSAHandler.solvent_radius`
* `GBSAType.smirks`
* `GBSAType.radius`
* `GBSAType.scale`
* `GBSAType.id`
* `GBSAType.parent_id`
* `ConstraintType.smirks`
* `VirtualSiteHandler.exclusion_policy`
* `VirtualSiteBondChargeType.smirks`
* `VirtualSiteMonovalentLonePairType.smirks`
* `VirtualSiteDivalentLonePairType.smirks`
* `VirtualSiteTrivalentLonePairType.smirks`
* `VirtualSiteBondChargeType.type`
* `VirtualSiteMonovalentLonePairType.type`
* `VirtualSiteDivalentLonePairType.type`
* `VirtualSiteTrivalentLonePairType.type`
* `VirtualSiteBondChargeType.name`
* `VirtualSiteMonovalentLonePairType.name`
* `VirtualSiteDivalentLonePairType.name`
* `VirtualSiteTrivalentLonePairType.name`
* `VirtualSiteBondChargeType.match`
* `VirtualSiteMonovalentLonePairType.match`
* `VirtualSiteDivalentLonePairType.match`
* `VirtualSiteTrivalentLonePairType.match`