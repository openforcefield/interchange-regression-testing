from copy import deepcopy

import openmm
import pytest
from openff.interchange.components.interchange import Interchange
from openff.toolkit.topology.molecule import Molecule
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit


@pytest.fixture
def force_field():
    return ForceField("openff-1.0.0.offxml")


@pytest.fixture
def topology():
    molecule = Molecule.from_smiles("C")
    topology = molecule.to_topology()

    # TODO: Update if resolved
    #       https://github.com/openforcefield/openff-toolkit/issues/1084
    topology.box_vectors = [4, 4, 4] * unit.nanometer

    return topology


def test_default_cutoff(topology, force_field):

    interchange = Interchange.from_smirnoff(force_field=force_field, topology=topology)
    system_from_interchange = interchange.to_openmm(combine_nonbonded_forces=True)

    system_from_toolkit = force_field.create_openmm_system(topology)

    for force in system_from_toolkit.getForces():
        if isinstance(force, openmm.NonbondedForce):
            reference_cutoff = force.getCutoffDistance()
            break
    else:
        raise ValueError("No nonbonded force found in the system")

    for force in system_from_interchange.getForces():
        if isinstance(force, openmm.NonbondedForce):
            assert (
                force.getCutoffDistance() == reference_cutoff
            ), "detected cutoff distances do not match"
            break
    else:
        raise ValueError("No nonbonded force found in the system")


def test_nonstandard_vdw_cutoff(topology, force_field):

    modified_force_field = deepcopy(force_field)
    modified_force_field["vdW"].cutoff = 1.234 * unit.nanometer

    assert modified_force_field["vdW"].cutoff != force_field["vdW"].cutoff

    interchange = Interchange.from_smirnoff(
        force_field=modified_force_field, topology=topology
    )
    system_from_interchange = interchange.to_openmm(combine_nonbonded_forces=True)

    system_from_toolkit = modified_force_field.create_openmm_system(topology)

    for force in system_from_toolkit.getForces():
        if isinstance(force, openmm.NonbondedForce):
            reference_cutoff = force.getCutoffDistance()
            break
    else:
        raise ValueError("No nonbonded force found in the system")

    for force in system_from_interchange.getForces():
        if isinstance(force, openmm.NonbondedForce):
            assert (
                force.getCutoffDistance() == reference_cutoff
            ), "detected cutoff distances do not match"
            break
    else:
        raise ValueError("No nonbonded force found in the system")
