import json
from multiprocessing import Pool
from pathlib import Path
from typing import List

import click
import rich
from openff.toolkit import __version__
from rich import pretty
from rich.console import NewLine
from rich.padding import Padding
from rich.progress import track

from interchange_regression_utilities.compare import compare_openmm_system_differences
from interchange_regression_utilities.models import (
    ComparisonSettings,
    ExpectedValueChange,
    model_from_file,
)
from interchange_regression_utilities.parsing.openmm import load_openmm_system_as_dict
from interchange_regression_utilities.utilities import DeepDiffEncoder

current_toolkit_version = __version__


def _compare_systems(args):

    name, system_a, system_b, comparison_settings, expected_changes = args

    differences, warning_messages = compare_openmm_system_differences(
        system_a, system_b, comparison_settings, expected_changes
    )

    return name, {**differences}, warning_messages


@click.command()
@click.option(
    "--input-dir-a",
    "input_directory_a",
    help="The path to the directory containing the first set of OpenMM system XML "
    "files to compare.",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
)
@click.option(
    "--input-dir-b",
    "input_directory_b",
    help="The path to the directory containing the second set of OpenMM system XML "
    "files to compare.",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
)
@click.option(
    "--output",
    "output_path",
    help="The path to save the names of any systems that are different to.",
    type=click.Path(exists=False, file_okay=True, dir_okay=False, path_type=Path),
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
    "--expected-changes",
    "expected_changes_path",
    help="The (optional) path to a list of expected changes to be ignored.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.option(
    "--n-procs",
    "n_processes",
    help="The number of processes to parallelize the comparisons across.",
    default=1,
    show_default=True,
    required=True,
)
def main(
    input_directory_a: Path,
    input_directory_b: Path,
    output_path: Path,
    settings_path: Path,
    expected_changes_path: Path,
    n_processes: int,
):

    console = rich.get_console()
    pretty.install(console)

    if expected_changes_path is not None:
        expected_changes = model_from_file(
            List[ExpectedValueChange], expected_changes_path
        )
    else:
        expected_changes = []

    with Pool(processes=n_processes) as pool:

        system_paths_a = [*input_directory_a.glob("*.xml")]
        systems_a = {
            system_path.stem: system_dict
            for system_path, system_dict in zip(
                system_paths_a,
                track(
                    pool.imap(load_openmm_system_as_dict, system_paths_a),
                    description=f"loading systems from "
                    f"[repr.filename]{input_directory_a}[/repr.filename]",
                    total=len(system_paths_a),
                ),
            )
        }
        system_paths_b = [*input_directory_b.glob("*.xml")]
        systems_b = {
            system_path.stem: system_dict
            for system_path, system_dict in zip(
                system_paths_b,
                track(
                    pool.imap(load_openmm_system_as_dict, system_paths_b),
                    description=f"loading systems from "
                    f"[repr.filename]{input_directory_b}[/repr.filename]",
                    total=len(system_paths_b),
                ),
            )
        }

    missing_systems_b = {*systems_a} - {*systems_b}
    missing_systems_a = {*systems_b} - {*systems_a}

    if len(missing_systems_b) > 0:
        console.print(
            f"[red]ERROR[/red] {len(missing_systems_b)} systems were found in "
            f"[repr.filename]{input_directory_a}[/repr.filename] but not found in "
            f"[repr.filename]{input_directory_b}[/repr.filename]"
        )
    if len(missing_systems_a) > 0:
        console.print(
            f"[red]ERROR[/red] {len(missing_systems_a)} systems were found in "
            f"[repr.filename]{input_directory_b}[/repr.filename] but not found in "
            f"[repr.filename]{input_directory_a}[/repr.filename]"
        )

    console.print(Padding(f"comparing {len(systems_a)} OpenMM systems", (1, 0, 1, 0)))

    comparison_settings = ComparisonSettings()

    if settings_path is not None:
        comparison_settings = ComparisonSettings.from_file(settings_path)

    system_differences = {}

    with Pool(processes=n_processes) as pool:

        for name, differences, warning_messages in track(
            pool.imap(
                _compare_systems,
                [
                    (
                        name,
                        systems_a[name],
                        systems_b[name],
                        comparison_settings,
                        expected_changes,
                    )
                    for name in systems_a
                ],
            ),
            description="progress",
            total=len(systems_a),
        ):

            if len(warning_messages) > 0:

                console.print(
                    Padding(
                        f"[yellow]WARNING[/yellow] while comparing {name}", (0, 0, 1, 0)
                    ),
                    *(Padding(message, (0, 0, 0, 4)) for message in warning_messages),
                    NewLine(),
                )

            if len(differences) == 0:
                continue

            system_differences[name] = {
                "differences": differences,
                "warnings": warning_messages,
            }

            console.print(
                f"[red]ERROR[/red] {name} has significant differences", NewLine()
            )

    if len(system_differences) > 0:

        console.print(
            Padding(
                f"{len(system_differences)} systems had significant differences - see "
                f"[repr.filename]{str(output_path)}[/repr.filename] for details",
                (1, 0, 1, 0),
            )
        )

        with output_path.open("w") as file:
            json.dump(system_differences, file, cls=DeepDiffEncoder)

    else:
        console.print(Padding("no differences were found :tada:", (1, 0, 1, 0)))


if __name__ == "__main__":
    main()
