export TOOLKIT_VERSION=$(python -c "import openff.toolkit; print(openff.toolkit.__version__)")
export INTERCHANGE_VERSION=$(python -c "import openff.interchange; print(openff.interchange.__version__)")

export CATEGORY=virtual-sites

python create-$CATEGORY-molecule-inputs.py

create_openmm_systems \
    --input "$CATEGORY-molecule/input-topologies.json" \
    --output "$CATEGORY-molecule/" \
    --using-toolkit \
    --force-field "openff-2.0.0.offxml" \
    --force-field "force-fields/$CATEGORY.offxml" \
    --n-procs 10

create_openmm_systems \
    --input "$CATEGORY-molecule/input-topologies.json" \
    --output "$CATEGORY-molecule/" \
    --using-interchange \
    --force-field "openff-2.0.0.offxml" \
    --force-field "force-fields/$CATEGORY.offxml" \
    --n-procs 10

compare_openmm_systems \
    --input-dir-a "$CATEGORY-molecule/omm-systems-toolkit-$TOOLKIT_VERSION" \
    --input-dir-b "$CATEGORY-molecule/omm-systems-interchange-$INTERCHANGE_VERSION" \
    --output "$CATEGORY-molecule-toolkit-$TOOLKIT_VERSION-vs-interchange-$INTERCHANGE_VERSION.json" \
    --settings "comparison-settings/default-comparison-settings.json" \
    --expected-changes "expected-changes/toolkit-0-11-x-to-interchange-0-2-x.json" \
    --n-procs 10
