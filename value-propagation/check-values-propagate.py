import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import click
from deepdiff import DeepDiff
from openff.interchange.components.toolkit import _get_14_pairs
from openff.toolkit.topology import Molecule
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from openff.units.openmm import to_openmm
from rich import get_console, pretty
from rich.console import NewLine
from rich.padding import Padding

from interchange_regression_utilities.compare import (
    compare_openmm_system_differences,
    values_from_openmm_system,
)
from interchange_regression_utilities.create import (
    create_openmm_system,
    perturb_force_field,
)
from interchange_regression_utilities.models import (
    ComparisonSettings,
    ExpectedValueChange,
    Perturbation,
    TopologyComponent,
    TopologyDefinition,
)
from interchange_regression_utilities.parsing.openmm import openmm_system_to_dict
from interchange_regression_utilities.perturb import (
    default_perturbation,
    enumerate_perturbations,
    get_all_attributes,
)
from interchange_regression_utilities.utilities import DeepDiffEncoder


def get_new_value_in_md_unit(perturbation: Perturbation) -> Any:

    from openmm import unit as openmm_unit

    value = unit.Quantity(perturbation.new_value, perturbation.new_units)
    return to_openmm(value).value_in_unit_system(openmm_unit.md_unit_system)


def get_old_values(
    system: Dict[str, Any], openmm_paths: Union[str, List[str]]
) -> List[Tuple[str, Any]]:

    openmm_paths = [openmm_paths] if isinstance(openmm_paths, str) else openmm_paths

    return [
        path_and_value
        for openmm_path in openmm_paths
        for path_and_value in values_from_openmm_system(system, openmm_path=openmm_path)
    ]


def get_simple_expected_changes(
    system: Dict[str, Any],
    perturbation: Perturbation,
) -> Optional[List[ExpectedValueChange]]:

    openff_to_openmm_path = {
        "ConstraintHandler/Constraints/distance": "Constraints/*/d",
        #
        "BondHandler/Bonds/length": [
            "Forces/HarmonicBondForce/Bonds/*/d",
            "Constraints/*/d",
        ],
        "BondHandler/Bonds/k": "Forces/HarmonicBondForce/Bonds/*/k",
        #
        "AngleHandler/Angles/angle": "Forces/HarmonicAngleForce/Angles/*/a",
        "AngleHandler/Angles/k": "Forces/HarmonicAngleForce/Angles/*/k",
        #
        "ProperTorsionHandler/ProperTorsions/periodicity1": (
            "Forces/PeriodicTorsionForce/Torsions/*/periodicity"
        ),
        "ProperTorsionHandler/ProperTorsions/phase1": (
            "Forces/PeriodicTorsionForce/Torsions/*/phase"
        ),
        "ProperTorsionHandler/ProperTorsions/k1": (
            "Forces/PeriodicTorsionForce/Torsions/*/k"
        ),
        #
        "ImproperTorsionHandler/ImproperTorsions/periodicity1": (
            "Forces/PeriodicTorsionForce/Torsions/*/periodicity"
        ),
        "ImproperTorsionHandler/ImproperTorsions/phase1": (
            "Forces/PeriodicTorsionForce/Torsions/*/phase"
        ),
    }

    if perturbation.path not in openff_to_openmm_path:
        return None

    old_values = get_old_values(system, openff_to_openmm_path[perturbation.path])
    new_value = get_new_value_in_md_unit(perturbation)

    return [
        ExpectedValueChange(
            deepdiff_path=path, old_value=old_value, new_value=new_value
        )
        for path, old_value in old_values
    ]


def get_improper_k_expected_changes(
    system: Dict[str, Any],
    perturbation: Perturbation,
) -> Optional[List[ExpectedValueChange]]:

    # The result of hard-coding in the toolkit...
    old_values = get_old_values(system, "Forces/PeriodicTorsionForce/Torsions/*/k")
    new_value = get_new_value_in_md_unit(perturbation) / 3

    return [
        ExpectedValueChange(
            deepdiff_path=path, old_value=old_value, new_value=new_value
        )
        for path, old_value in old_values
    ]


def get_torsion_idivf_expected_changes(
    system: Dict[str, Any],
    perturbation: Perturbation,
) -> Optional[List[ExpectedValueChange]]:

    openff_to_openmm_path = {
        "ProperTorsionHandler/ProperTorsions/idivf1": (
            "Forces/PeriodicTorsionForce/Torsions/*/k"
        ),
        "ImproperTorsionHandler/ImproperTorsions/idivf1": (
            "Forces/PeriodicTorsionForce/Torsions/*/k"
        ),
    }

    openmm_path = openff_to_openmm_path[perturbation.path]

    new_divisor = get_new_value_in_md_unit(perturbation)

    # The result of hard-coding in the toolkit...
    old_idivf = 1.0 if perturbation.path.startswith("ProperTorsionHandler") else 3.0

    return [
        ExpectedValueChange(
            deepdiff_path=path,
            old_value=old_value,
            new_value=old_value * old_idivf / new_divisor,
        )
        for path, old_value in get_old_values(system, openmm_path)
    ]


def get_vdw_parameter_excepted_changes(
    molecule: Molecule,
    force_field: ForceField,
    system: Dict[str, Any],
    perturbation: Perturbation,
) -> List[ExpectedValueChange]:

    # Handle the 'easy' change in particle value
    openff_attribute_name = perturbation.path.split("/")[-1]
    openmm_attribute_name = {"epsilon": "eps", "sigma": "sig", "rmin_half": "sig"}[
        openff_attribute_name
    ]

    new_value = get_new_value_in_md_unit(perturbation)

    if openff_attribute_name == "rmin_half":
        new_value = new_value * 2.0 / (2.0 ** (1.0 / 6.0))

    expected_changes = [
        ExpectedValueChange(
            deepdiff_path=old_path, old_value=old_value, new_value=new_value
        )
        for old_path, old_value in values_from_openmm_system(
            system,
            openmm_path=f"Forces/NonbondedForce/Particles/*/{openmm_attribute_name}",
        )
    ]

    # Handle the trickier exception changes...
    pairs_excl = {
        *{
            tuple(sorted((bond.atom1_index, bond.atom2_index)))
            for bond in molecule.bonds
        },
        *{
            tuple(sorted((angle[0].molecule_atom_index, angle[2].molecule_atom_index)))
            for angle in molecule.angles
        },
    }
    pairs_14 = {
        tuple(sorted((atom_a.molecule_atom_index, atom_b.molecule_atom_index)))
        for atom_a, atom_b in _get_14_pairs(molecule)
    }

    old_exceptions = get_old_values(system, "Forces/NonbondedForce/Exceptions/*")

    for path, exception in old_exceptions:

        exception_index = tuple(sorted((exception["p1"], exception["p2"])))

        if exception_index in pairs_excl:
            continue

        if openff_attribute_name == "epsilon":
            scale = force_field["vdW"].scale14 if exception_index in pairs_14 else 1.0
        else:
            scale = 1.0

        expected_changes.append(
            ExpectedValueChange(
                deepdiff_path=f"{path}['{openmm_attribute_name}']",
                old_value=exception[openmm_attribute_name],
                new_value=new_value * scale,
            )
        )

    return expected_changes


def get_vdw_cutoff_expected_changes(
    system: Dict[str, Any],
    perturbation: Perturbation,
) -> List[ExpectedValueChange]:

    [(cutoff_path, old_cutoff)] = get_old_values(system, "Forces/NonbondedForce/cutoff")
    [(switch_path, old_switch)] = get_old_values(
        system, "Forces/NonbondedForce/switchingDistance"
    )

    new_value = get_new_value_in_md_unit(perturbation)

    if perturbation.path == "vdWHandler/cutoff":

        new_cutoff = new_value
        new_switch = new_cutoff - (old_cutoff - old_switch)

        return [
            ExpectedValueChange(
                deepdiff_path=cutoff_path, old_value=old_cutoff, new_value=new_cutoff
            ),
            ExpectedValueChange(
                deepdiff_path=switch_path, old_value=old_switch, new_value=new_switch
            ),
        ]

    else:

        new_switch = old_cutoff - new_value

        return [
            ExpectedValueChange(
                deepdiff_path=switch_path, old_value=old_switch, new_value=new_switch
            ),
        ]


def get_scale_1_4_expected_changes(
    molecule: Molecule,
    force_field: ForceField,
    system: Dict[str, Any],
    perturbation: Perturbation,
) -> List[ExpectedValueChange]:

    pairs_14 = {
        tuple(sorted((atom_a.molecule_atom_index, atom_b.molecule_atom_index)))
        for atom_a, atom_b in _get_14_pairs(molecule)
    }

    handler_type, attribute = (
        ("vdW", "eps")
        if perturbation.path.startswith("vdWHandler")
        else ("Electrostatics", "q")
    )

    old_value = force_field._parameter_handlers[handler_type].scale14
    old_exceptions = get_old_values(system, "Forces/NonbondedForce/Exceptions/*")

    expected_changes = []

    for path, exception in old_exceptions:

        if tuple(sorted((exception["p1"], exception["p2"]))) not in pairs_14:
            continue

        expected_changes.append(
            ExpectedValueChange(
                deepdiff_path=f"{path}['{attribute}']",
                old_value=exception[attribute],
                new_value=exception[attribute] / old_value * perturbation.new_value,
            )
        )

    return expected_changes


def get_expected_changes(
    molecule: Molecule,
    force_field: ForceField,
    system: Dict[str, Any],
    perturbation: Perturbation,
) -> Optional[List[ExpectedValueChange]]:

    expected_changes = get_simple_expected_changes(system, perturbation)

    if expected_changes is not None:
        return expected_changes

    if perturbation.path in {
        "vdWHandler/vdW/epsilon",
        "vdWHandler/vdW/sigma",
        "vdWHandler/vdW/rmin_half",
    }:
        return get_vdw_parameter_excepted_changes(
            molecule, force_field, system, perturbation
        )
    elif perturbation.path in {"vdWHandler/cutoff", "vdWHandler/switch_width"}:
        return get_vdw_cutoff_expected_changes(system, perturbation)

    elif perturbation.path in {"vdWHandler/scale14", "ElectrostaticsHandler/scale14"}:
        return get_scale_1_4_expected_changes(
            molecule, force_field, system, perturbation
        )
    elif perturbation.path in {"ImproperTorsionHandler/ImproperTorsions/k1"}:
        return get_improper_k_expected_changes(system, perturbation)
    elif perturbation.path in {
        "ProperTorsionHandler/ProperTorsions/idivf1",
        "ImproperTorsionHandler/ImproperTorsions/idivf1",
    }:
        return get_torsion_idivf_expected_changes(system, perturbation)

    return None


def custom_perturbation(attribute_path: str, old_value: Any) -> Tuple[Any, bool]:

    new_values = {"ImproperTorsionHandler/ImproperTorsions/idivf1": 2}

    if attribute_path in new_values:
        return new_values[attribute_path], True

    return default_perturbation(attribute_path, old_value)


def generate_perturbations(
    topology_definition: TopologyDefinition, force_field: ForceField
) -> List[Perturbation]:

    perturbations, _ = enumerate_perturbations(force_field, custom_perturbation)

    labels = force_field.label_molecules(topology_definition.to_topology())

    all_handlers = {
        handler_key: force_field.get_parameter_handler(handler_key).__class__.__name__
        for handler_key in force_field.registered_parameter_handlers
    }
    applied_handlers = {
        all_handlers[handler_key]
        for label in labels
        for handler_key in label
        if len(label[handler_key]) > 0
        or handler_key in {"Electrostatics", "ToolkitAM1BCC"}
    }

    applied_perturbations = []

    for perturbation in perturbations:

        handler_type = perturbation.path.split("/")[0]

        if handler_type not in applied_handlers:
            continue

        applied_perturbations.append(perturbation)

    return applied_perturbations


def check_values_propagate(
    topology_definition: TopologyDefinition,
    force_field: ForceField,
    using_interchange: bool,
    comparison_settings: ComparisonSettings,
) -> List[Tuple[Perturbation, DeepDiff, List[str]]]:

    topology = topology_definition.to_topology()
    molecule = topology.reference_molecules[0]

    perturbations = generate_perturbations(topology_definition, force_field)

    original_system = openmm_system_to_dict(
        create_openmm_system(topology_definition, force_field, using_interchange)
    )

    per_perturbation_expected_changes = [
        (
            perturbation,
            get_expected_changes(molecule, force_field, original_system, perturbation),
        )
        for perturbation in perturbations
    ]
    per_perturbation_expected_changes = [
        v for v in per_perturbation_expected_changes if v[1] is not None
    ]

    perturbation_differences = []

    for perturbation, expected_changes in per_perturbation_expected_changes:

        perturbed_system = openmm_system_to_dict(
            create_openmm_system(
                topology,
                perturb_force_field(force_field, perturbation),
                using_interchange,
            )
        )

        differences, _ = compare_openmm_system_differences(
            original_system, perturbed_system, comparison_settings, []
        )
        was_system_perturbed = len(differences) != 0

        differences, warning_messages = compare_openmm_system_differences(
            original_system, perturbed_system, comparison_settings, expected_changes
        )

        if not was_system_perturbed:

            warning_messages.insert(
                0, "the original and perturbed systems are identical"
            )

        perturbation_differences.append((perturbation, differences, warning_messages))

    return perturbation_differences


@click.command()
@click.option(
    "--input",
    "input_tuples",
    help="The path to a force field to perturb and a SMILES pattern to apply the "
    "perturbed force force to.",
    type=(click.Path(exists=False, file_okay=True, dir_okay=False), str),
    multiple=True,
    required=True,
)
@click.option(
    "--using-interchange/--using-toolkit",
    "using_interchange",
    help="Whether to create the OpenMM system using OpenFF Interchange or using the "
    "legacy OpenFF toolkit exporter.",
    required=True,
)
@click.option(
    "--settings",
    "settings_path",
    help="The path to the comparison settings.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    required=False,
)
@click.option(
    "--output",
    "output_path",
    help="The path to save any differences to.",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path),
    required=True,
)
def main(
    input_tuples: List[Tuple[str, str]],
    using_interchange: bool,
    settings_path: Path,
    output_path: Path,
):

    comparison_settings = ComparisonSettings()

    if settings_path is not None:
        comparison_settings = ComparisonSettings.from_file(settings_path)

    console = get_console()
    pretty.install(console)

    attributes_perturbed = set()

    perturbation_differences = defaultdict(lambda: defaultdict(dict))

    for input_tuple in input_tuples:

        force_field_path, smiles = input_tuple

        console.rule(f"{force_field_path} + {smiles}")
        console.print(NewLine())

        force_field = ForceField(force_field_path)

        topology_definition = TopologyDefinition(
            name=smiles,
            components=[TopologyComponent(smiles=smiles, n_copies=1)],
            is_periodic=True,
        )

        for perturbation, differences, warning_messages in check_values_propagate(
            topology_definition, force_field, using_interchange, comparison_settings
        ):

            attributes_perturbed.add(perturbation.path.rstrip("1"))

            if len(warning_messages) > 0:
                console.print(
                    Padding(
                        f"[yellow]WARNING[/yellow] after perturbing "
                        f"{perturbation.path}",
                        (0, 0, 1, 0),
                    ),
                    *(Padding(message, (0, 0, 0, 4)) for message in warning_messages),
                    NewLine(),
                )

            if len(differences) == 0:
                continue

            perturbation_differences[input_tuple][perturbation.path] = {
                "differences": differences,
                "warnings": warning_messages,
            }

            console.print(
                f"[red]ERROR[/red] perturbing {perturbation.path} did not yield the "
                f"expected differences",
                NewLine(),
            )

        if len(perturbation_differences[input_tuple]) > 0:

            console.print(
                Padding(
                    f"{len(perturbation_differences[input_tuple])} perturbations did "
                    f"not yield the expected differences - see "
                    f"[repr.filename]{str(output_path)}[/repr.filename] for details",
                    (0, 0, 1, 0),
                )
            )

    console.rule()

    expected_attributes = {
        "/".join(attribute_split)
        for values in get_all_attributes().values()
        for attribute_split in values
    }

    missing_attributes = expected_attributes - attributes_perturbed

    if len(missing_attributes):

        console.print(
            Padding(
                "[yellow]WARNING[/yellow] some attributes weren't perturbed",
                (1, 0, 1, 0),
            ),
            *(
                Padding(attribute, (0, 0, 0, 4))
                for attribute in sorted(missing_attributes)
            ),
            NewLine(),
        )
        console.print(
            Padding("however these attributes were", (0, 0, 1, 0)),
            *(
                Padding(attribute, (0, 0, 0, 4))
                for attribute in sorted(attributes_perturbed)
            ),
            NewLine(),
        )

    if any(
        len(perturbation_differences[input_tuple]) > 0
        for input_tuple in perturbation_differences
    ):

        console.print(
            Padding(
                f"[red]ERROR[/red] some perturbations did not yield the expected "
                f"differences - see [repr.filename]{str(output_path)}[/repr.filename] "
                f"for details",
                (0, 0, 1, 0),
            )
        )

        with output_path.open("w") as file:
            json.dump(
                {
                    " + ".join(key): value
                    for key, value in perturbation_differences.items()
                },
                file,
                cls=DeepDiffEncoder,
                indent=2,
            )

    else:
        console.print(
            Padding(
                "all checked perturbations led to the expected changes :tada:",
                (1, 0, 1, 0),
            )
        )


if __name__ == "__main__":
    main()
