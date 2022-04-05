import json
from pathlib import Path
from typing import Any, Tuple

import click
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from rich import get_console, pretty
from rich.console import NewLine
from rich.padding import Padding

from interchange_regression_utilities.perturb import (
    default_perturbation,
    enumerate_perturbations,
)


def perturbation_function(attribute_path: str, old_value: Any) -> Tuple[Any, bool]:

    new_values = {
        "ConstraintHandler/Constraints/distance": 0.1234 * unit.angstrom,
    }

    if attribute_path in new_values:
        return new_values[attribute_path], True

    return default_perturbation(attribute_path, old_value)


@click.command()
@click.option(
    "--force-field",
    "force_field_path",
    help="The path of the force field to perturb.",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    required=True,
    default=str(Path("force-fields", "minimal-force-field.offxml")),
    show_default=True,
)
@click.option(
    "--output",
    "output_path",
    help="The path (JSON) to save the list of perturbations to apply to.",
    type=click.Path(exists=False, dir_okay=False, file_okay=True, path_type=Path),
    required=True,
)
def main(force_field_path: Path, output_path: Path):

    console = get_console()
    pretty.install(console)

    perturbations, warning_messages = enumerate_perturbations(
        ForceField(force_field_path), perturbation_function
    )

    if len(warning_messages) > 0:

        console.print(
            *(
                Padding(f"[yellow]WARNING[/yellow] {message}", (0, 0, 0, 0))
                if i == 0
                else Padding(message, (0, 0, 0, 8))
                for i, message in enumerate(warning_messages)
            ),
            NewLine(),
        )

    output_path.parent.mkdir(exist_ok=True, parents=True)

    with output_path.open("w") as file:
        json.dump([value.dict() for value in perturbations], file, indent=2)


if __name__ == "__main__":
    main()
