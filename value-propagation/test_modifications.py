import openmm
import pytest
import xmltodict
from deepdiff import DeepDiff
from openff.toolkit.tests.create_molecules import create_ethanol
from openff.toolkit.tests.utils import get_14_scaling_factors
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from openmm import unit as openmm_unit


def postprocessor(path, key, value):
    try:
        return key, int(value) if "." not in value else float(value)
    except (ValueError, TypeError):
        return key, value


def deep_diff(system1: openmm.System, system2: openmm.System):
    dict1 = xmltodict.parse(
        openmm.XmlSerializer.serialize(system1), postprocessor=postprocessor
    )
    dict2 = xmltodict.parse(
        openmm.XmlSerializer.serialize(system2), postprocessor=postprocessor
    )

    diff = DeepDiff(dict1, dict2, ignore_order=True, significant_digits=6)

    return diff


class TestValuePropagation:
    @pytest.fixture()
    def force_field(self):
        return ForceField("value-propagation/minimal_forcefield.offxml")

    @pytest.fixture()
    def ethanol_topology(self):
        return create_ethanol().to_topology()


class TestvdW(TestValuePropagation):
    def test_modify_cutoff(self, force_field, ethanol_topology):
        original_system = force_field.create_openmm_system(ethanol_topology)
        force_field["vdW"].cutoff = 1.23456 * unit.nanometer
        modified_system = force_field.create_openmm_system(ethanol_topology)

        assert len(deep_diff(original_system, modified_system)) > 0

        for force in modified_system.getForces():
            if isinstance(force, openmm.NonbondedForce):
                assert force.getCutoffDistance() == 1.23456 * openmm_unit.nanometer

    def test_modify_scale_14(self, force_field, ethanol_topology):
        original_system = force_field.create_openmm_system(ethanol_topology)
        force_field["vdW"].scale14 = 0.123456
        modified_system = force_field.create_openmm_system(ethanol_topology)

        assert len(deep_diff(original_system, modified_system)) > 0

        _, found_scale_14 = get_14_scaling_factors(modified_system)

        assert all(val == pytest.approx(0.123456) for val in found_scale_14)


class TestConstraints(TestValuePropagation):
    def test_modify_constraint_distance(self, force_field, ethanol_topology):
        original_system = force_field.create_openmm_system(ethanol_topology)
        force_field["Constraints"].parameters[0].distance = 1.23456 * unit.angstrom
        modified_system = force_field.create_openmm_system(ethanol_topology)

        assert len(deep_diff(original_system, modified_system)) > 0

        for constraint_index in range(modified_system.getNumConstraints()):
            _, _, constraint_distance = modified_system.getConstraintParameters(
                constraint_index
            )
            assert constraint_distance.value_in_unit(
                openmm_unit.angstrom
            ) == pytest.approx(1.23456)
