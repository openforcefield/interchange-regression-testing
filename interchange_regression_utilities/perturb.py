import inspect
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

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

PerturbationFunc = Callable[[str, Any], Tuple[Any, bool]]


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


def default_perturbation(path: str, old_value: Any) -> Tuple[Any, bool]:

    if path == "ConstraintHandler/Constraints/distance" and old_value is None:
        new_value = 0.1234 * unit.angstrom
    elif isinstance(old_value, str) or old_value is None:
        return None, False
    else:
        value_multiplier = (
            old_value.units if isinstance(old_value, unit.Quantity) else 1.0
        )
        new_value = old_value + 1.0 * value_multiplier

    return new_value, True


def enumerate_perturbations(
    force_field: ForceField, perturbation_func: Optional[PerturbationFunc] = None
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

            default_to_none = False

            if attribute_type == "IndexedParameterAttribute":

                default_to_none = getattr(attribute_parent, attribute_name) is None

                attribute_name = f"{attribute_name}1"
                attribute_path = "/".join(
                    [handler_type, *parameter_types, attribute_name]
                )

            if default_to_none:
                # Indexed attributes whose values are currently not set
                old_value = None
            else:
                old_value = getattr(attribute_parent, attribute_name)

            if not use_openff_units():

                from openmm import unit as openmm_unit

                if isinstance(old_value, openmm_unit.Quantity):
                    old_value = from_openmm(old_value)

            if perturbation_func is None:
                new_value, successful = default_perturbation(attribute_path, old_value)

                if not successful:

                    warning_messages.append(
                        f"skipping {attribute_path} - can only perturb numeric values "
                        f"using the default perturbation function"
                    )
                    continue

            else:
                new_value, successful = perturbation_func(attribute_path, old_value)

                if not successful:

                    warning_messages.append(
                        f"skipping {attribute_path} - could not perturb with custom "
                        f"function"
                    )
                    continue

            if isinstance(new_value, unit.Quantity):
                expected_unit = f"{new_value.units:D}"
                new_value = new_value.m_as(new_value.units)
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
