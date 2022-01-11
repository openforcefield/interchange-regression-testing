from copy import deepcopy

import openmm
import pytest
from openff.interchange.components.interchange import Interchange
from openff.toolkit.topology.molecule import Molecule
from openff.toolkit.typing.engines.smirnoff import (
    ElectrostaticsHandler,
    ForceField,
    LibraryChargeHandler,
    vdWHandler,
)
from openff.units import unit
from openmm import unit as openmm_unit


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


def test_nondefault_nonbonded_cutoff(topology):

    topology = Molecule.from_smiles("[#18]").to_topology()
    topology.box_vectors = [3, 3, 3] * unit.nanometer

    force_field = ForceField()

    vdw_handler = vdWHandler(version=0.3)
    vdw_handler.method = "cutoff"
    vdw_handler.cutoff = 7.89 * unit.angstrom
    vdw_handler.scale14 = 1.0

    vdw_handler.add_parameter(
        {
            "smirks": "[#18:1]",
            "epsilon": 1.0 * unit.kilojoules_per_mole,
            "sigma": 1.0 * unit.angstrom,
        }
    )
    force_field.register_parameter_handler(vdw_handler)

    electrostatics_handler = ElectrostaticsHandler(version=0.3)
    electrostatics_handler.cutoff = 7.89 * unit.angstrom
    electrostatics_handler.method = "PME"
    force_field.register_parameter_handler(electrostatics_handler)

    library_charges = LibraryChargeHandler(version=0.3)
    library_charges.add_parameter(
        {
            "smirks": "[#18:1]",
            "charge1": 0.0 * unit.elementary_charge,
        }
    )
    force_field.register_parameter_handler(library_charges)

    system = force_field.create_openmm_system(topology)

    found_cutoff = (
        system.getForce(0).getCutoffDistance().value_in_unit(openmm_unit.angstrom)
    )

    assert abs(found_cutoff - 7.89) < 1e-6
