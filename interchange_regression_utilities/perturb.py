import inspect
from collections import defaultdict
from typing import Dict, List, Tuple

from openff.toolkit.typing.engines.smirnoff import (
    ForceField,
    ParameterAttribute,
    ParameterHandler,
)
from openff.toolkit.utils import all_subclasses
from openff.units import unit
from openff.units.openmm import from_openmm

from interchange_regression_utilities.models import Perturbation
from interchange_regression_utilities.utilities import use_openff_units

IGNORED_HANDLERS = [
    # Abstract classes.
    "ParameterHandler",
    "_NonbondedHandler",
]
IGNORED_ATTRIBUTES = [
    # No effect on OpenMM system.
    "version",
    "smirks",
    "id",
    "name",
    "parent_id",
]


def get_parameter_attributes(parent_class) -> Dict[str, List[str]]:

    attributes = dict(
        (name, descriptor)
        for c in reversed(inspect.getmro(parent_class))
        for name, descriptor in c.__dict__.items()
        if isinstance(descriptor, ParameterAttribute)
    )
    attributes_by_type = defaultdict(list)

    for name, attribute in attributes.items():

        if name in IGNORED_ATTRIBUTES:
            continue

        attributes_by_type[attribute.__class__.__name__].append(name)

    return attributes_by_type


def get_all_attributes():

    built_in_handler_classes = all_subclasses(ParameterHandler)

    attributes_by_type = defaultdict(list)

    for handler_class in built_in_handler_classes:

        handler_name = handler_class.__name__

        if handler_name in IGNORED_HANDLERS:
            continue

        for attribute_type, attributes in get_parameter_attributes(
            handler_class
        ).items():

            attributes_by_type[attribute_type].extend(
                (handler_name, name) for name in attributes
            )

        parameter_class = handler_class._INFOTYPE

        if parameter_class is None:
            continue

        for attribute_type, attributes in get_parameter_attributes(
            parameter_class
        ).items():

            attributes_by_type[attribute_type].extend(
                (handler_name, handler_class._TAGNAME, name) for name in attributes
            )

    return {**attributes_by_type}


def enumerate_perturbations(
    force_field: ForceField,
) -> Tuple[List[Perturbation], List[str]]:

    handlers_by_type = {
        handler.__class__.__name__: handler
        for handler in force_field._parameter_handlers.values()
    }
    attributes_by_type = get_all_attributes()

    perturbations = []
    warning_messages = []

    for attribute_type, attributes in attributes_by_type.items():

        for attribute_path_split in attributes:

            handler_type, *parameter_types, attribute_name = attribute_path_split
            attribute_path = "/".join([handler_type, *parameter_types, attribute_name])

            if attribute_type not in {
                "ParameterAttribute",
                "IndexedParameterAttribute",
            }:

                warning_messages.append(
                    f"skipping {attribute_path} - unsupported attribute type of "
                    f"{attribute_type}"
                )
                continue

            handler = handlers_by_type.get(handler_type, None)

            if handler is None:

                warning_messages.append(
                    f"skipping {attribute_path} - {handler_type} not in force field"
                )

                continue

            attribute_parent = (
                handler if len(attribute_path_split) == 2 else handler.parameters[0]
            )

            if attribute_type == "IndexedParameterAttribute":

                if getattr(attribute_parent, attribute_name) is None:

                    warning_messages.append(
                        f"skipping {attribute_path} - array value is `None`"
                    )
                    continue

                attribute_name = f"{attribute_name}1"
                attribute_path = "/".join(
                    [handler_type, *parameter_types, attribute_name]
                )

            old_value = getattr(attribute_parent, attribute_name)

            if isinstance(old_value, str) or old_value is None:

                warning_messages.append(
                    f"skipping {attribute_path} - can only perturb numeric values"
                )
                continue

            if not use_openff_units():

                from openmm import unit as openmm_unit

                if isinstance(old_value, openmm_unit.Quantity):
                    old_value = from_openmm(old_value)

            value_multiplier = (
                old_value.units if isinstance(old_value, unit.Quantity) else 1.0
            )

            new_value = old_value + 1.0 * value_multiplier

            if isinstance(old_value, unit.Quantity):
                expected_unit = f"{old_value.units:D}"
                new_value = new_value.m_as(old_value.units)
            else:
                expected_unit = None

            perturbations.append(
                Perturbation(
                    path=attribute_path,
                    new_value=new_value,
                    new_units=expected_unit,
                )
            )

    return perturbations, warning_messages
