import pickle
from pathlib import Path
from typing import Optional

import openmm
from openff.interchange.components.interchange import Interchange
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from openff.units.openmm import to_openmm

from interchange_regression_utilities.models import Perturbation, TopologyDefinition
from interchange_regression_utilities.utilities import (
    capture_toolkit_warnings,
    use_openff_units,
)


def perturb_force_field(
    force_field: ForceField, perturbation: Perturbation
) -> ForceField:

    force_field = pickle.loads(pickle.dumps(force_field))

    handlers_by_type = {
        handler.__class__.__name__: handler
        for handler in force_field._parameter_handlers.values()
    }

    attribute_path = perturbation.path.split("/")
    handler_type, *_, attribute_name = attribute_path

    handler = handlers_by_type[handler_type]

    attribute_parent = handler if len(attribute_path) == 2 else handler.parameters[0]

    new_value = perturbation.new_value

    if perturbation.new_units is not None:
        new_value = unit.Quantity(new_value, perturbation.new_units)

    if not use_openff_units():

        if isinstance(new_value, unit.Quantity):
            new_value = to_openmm(new_value)

    setattr(attribute_parent, attribute_name, new_value)

    return force_field


def create_openmm_system(
    topology_definition: TopologyDefinition,
    force_field: ForceField,
    using_interchange: bool,
    output_path: Optional[Path] = None,
    perturbation: Optional[Perturbation] = None,
) -> openmm.System:
    """Create an OpenMM system by applying a SMIRNOFF force field to a given topology
    definition optionally, using OpenFF Interchange rather than via the OpenFF Toolkit
    legacy exporter.
    """

    with capture_toolkit_warnings():

        if perturbation is not None:
            force_field = perturb_force_field(force_field, perturbation)

        topology = topology_definition.to_topology()

        if using_interchange:
            openff_interchange = Interchange.from_smirnoff(force_field, topology)
            openmm_system = openff_interchange.to_openmm(combine_nonbonded_forces=True)
        else:
            openmm_system = force_field.create_openmm_system(topology)

    if output_path is not None:

        with output_path.open("w") as file:
            file.write(openmm.XmlSerializer.serialize(openmm_system))

    return openmm_system
