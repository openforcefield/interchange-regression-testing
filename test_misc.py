import numpy as np
import pytest
from openff.interchange.components.interchange import Interchange
from openff.toolkit.tests.utils import get_14_scaling_factors
from openff.toolkit.topology import Molecule, Topology
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.toolkit.utils import (
    AmberToolsToolkitWrapper,
    OpenEyeToolkitWrapper,
    RDKitToolkitWrapper,
    ToolkitRegistry,
    get_data_file_path,
)
from openmm import XmlSerializer, app


def round_charge(xml):
    """Round charge fields in a serialized OpenMM system to 2 decimal places"""
    # Example Particle line:                <Particle eps=".4577296" q="-.09709000587463379" sig=".1908"/>
    xmlsp = xml.split(' q="')
    for index, chunk in enumerate(xmlsp):
        # Skip file before first q=
        if index == 0:
            continue
        chunksp = chunk.split('" sig')
        chunksp[0] = f"{float(chunksp[0]):.2f}"
        chunk = '" sig'.join(chunksp)
        xmlsp[index] = chunk
    return ' q="'.join(xmlsp)


def test_modified_14_factors():
    topology = Molecule.from_smiles("CCCC").to_topology()
    default_14 = ForceField("test_forcefields/test_forcefield.offxml")
    e_mod_14 = ForceField("test_forcefields/test_forcefield.offxml")
    vdw_mod_14 = ForceField("test_forcefields/test_forcefield.offxml")

    e_mod_14["Electrostatics"].scale14 = 0.66
    assert e_mod_14["Electrostatics"].scale14 == 0.66

    vdw_mod_14["vdW"].scale14 = 0.777
    assert vdw_mod_14["vdW"].scale14 == 0.777

    default_omm_sys = Interchange.from_smirnoff(
        force_field=default_14,
        topology=topology,
    ).to_openmm(combine_nonbonded_forces=True)
    e_mod_omm_sys = Interchange.from_smirnoff(
        force_field=e_mod_14,
        topology=topology,
    ).to_openmm(combine_nonbonded_forces=True)
    vdw_mod_omm_sys = Interchange.from_smirnoff(
        force_field=vdw_mod_14,
        topology=topology,
    ).to_openmm(combine_nonbonded_forces=True)

    for omm_sys, expected_vdw_14, expected_coul_14 in [
        [default_omm_sys, 0.5, 0.833333],
        [e_mod_omm_sys, 0.5, 0.66],
        [vdw_mod_omm_sys, 0.777, 0.833333],
    ]:
        found_coul_14, found_vdw_14 = get_14_scaling_factors(omm_sys)

        np.testing.assert_almost_equal(
            actual=found_vdw_14,
            desired=expected_vdw_14,
            decimal=10,
            err_msg="vdW 1-4 scaling factors do not match",
        )

        np.testing.assert_almost_equal(
            actual=found_coul_14,
            desired=expected_coul_14,
            decimal=10,
            err_msg="Electrostatics 1-4 scaling factors do not match",
        )


@pytest.mark.parametrize(
    "toolkit_registry",
    [
        ToolkitRegistry(toolkit_precedence=[OpenEyeToolkitWrapper]),
        ToolkitRegistry(
            toolkit_precedence=[RDKitToolkitWrapper, AmberToolsToolkitWrapper]
        ),
    ],
)
def test_parameterize_ethanol_different_reference_ordering(toolkit_registry):
    force_field = ForceField("openff-1.0.0.offxml")

    pdbfile = app.PDBFile(get_data_file_path("systems/test_systems/1_ethanol.pdb"))

    # Load the unique molecules with one atom ordering
    molecules1 = [Molecule.from_file(get_data_file_path("molecules/ethanol.sdf"))]
    topology1 = Topology.from_openmm(
        pdbfile.topology,
        unique_molecules=molecules1,
    )
    omm_system1 = Interchange.from_smirnoff(
        force_field=force_field, topology=topology1, toolkit_registry=toolkit_registry
    ).to_openmm(combine_nonbonded_forces=True)

    # Load the unique molecules with a different atom ordering
    molecules2 = [
        Molecule.from_file(get_data_file_path("molecules/ethanol_reordered.sdf"))
    ]
    topology2 = Topology.from_openmm(
        pdbfile.topology,
        unique_molecules=molecules2,
    )
    omm_system2 = Interchange.from_smirnoff(
        force_field=force_field, topology=topology2, toolkit_registry=toolkit_registry
    ).to_openmm(combine_nonbonded_forces=True)

    serialized_1 = XmlSerializer.serialize(omm_system1)
    serialized_2 = XmlSerializer.serialize(omm_system2)

    serialized_1 = round_charge(serialized_1)
    serialized_2 = round_charge(serialized_2)

    assert serialized_1 == serialized_2
