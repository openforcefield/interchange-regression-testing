import functools
import json
import time
import traceback
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
import pydantic
import rich
from click.exceptions import Exit
from openff.toolkit import __version__ as toolkit_version
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.toolkit.utils.exceptions import OpenFFToolkitException
from rich import pretty
from rich.console import NewLine
from rich.padding import Padding
from rich.progress import track

from interchange_regression_utilities.create import create_openmm_system
from interchange_regression_utilities.models import (
    Perturbation,
    TopologyDefinition,
    model_from_file,
)

try:
    from openff.interchange import __version__ as interchange_version
except ImportError:
    interchange_version = None

def _save_openmm_system(
    topology_definition: TopologyDefinition,
    force_field: ForceField,
    using_interchange: bool,
    output_directory: Path = None,
    perturbations: Optional[List[Perturbation]] = None,
) -> Tuple[str, Optional[Dict[int, BaseException]]]:

    output_directory.mkdir(exist_ok=True, parents=True)

    if perturbations is None:
        perturbations = [None]
        output_paths = [Path(output_directory, f"{topology_definition.name}.xml")]
    else:
        output_paths = [
            Path(output_directory, f"{topology_definition.name}-perturbation-{i}.xml")
            for i in range(len(perturbations))
        ]

    exceptions = {}

    for i, (perturbation, output_path) in enumerate(zip(perturbations, output_paths)):

        exception = None

        if Path(output_path).is_file():
            continue

        try:
            create_openmm_system(
                topology_definition,
                force_field,
                using_interchange,
                output_path,
                perturbation,
            )
        except BaseException as e:
            exception = e

        if exception is None:
            continue

        if isinstance(exception, OpenFFToolkitException):
            # toolkit exceptions can't be pickled...
            exception = RuntimeError(str(exception))

        exceptions[i] = exception

    return topology_definition.name, exceptions


@click.command()
@click.option(
    "--input",
    "input_path",
    help="The path to a serialized list of topology definitions to create OpenMM "
    "system objects for.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--force-field",
    "force_field_paths",
    help="The path to the OpenFF force field (.offxml) parameters to use when creating "
    "the systems.",
    type=click.Path(exists=False, file_okay=True, dir_okay=False),
    default=["openff-2.0.0.offxml"],
    show_default=True,
    required=True,
    multiple=True,
)
@click.option(
    "--perturbations",
    "perturbations_path",
    help="An (optional) path to a serialized list of perturbations to apply.",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    required=False,
)
@click.option(
    "--output",
    "output_directory",
    help="The parent of the directory to save the created OpenMM systems in. The "
    "systems will be XML serialized to a new `omm-systems-xxx-{xxx-version}` directory "
    "where `xxx` will depend on the `using-xxx` flag.",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
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
    "--n-procs",
    "n_processes",
    help="The number of processes to parallelize the system creation across.",
    default=1,
    show_default=True,
    required=True,
)
def main(
    input_path: Path,
    output_directory: Path,
    force_field_paths: List[str],
    perturbations_path: Path,
    using_interchange: str,
    n_processes: int,
):

    console = rich.get_console()
    pretty.install(console)

    topology_definitions = model_from_file(List[TopologyDefinition], input_path)

    if len({x.name for x in topology_definitions}) != len(topology_definitions):
        console.print("[red]ERROR[/red] topology definitions must have unique names")
        raise Exit(code=1)

    console.print(f"creating OpenMM systems for {len(topology_definitions)} topologies")

    force_field = ForceField(*force_field_paths)

    if perturbations_path is not None:
        perturbations = parse_file_as(List[Perturbation], perturbations_path)
    else:
        perturbations = None

    output_directory = Path(
        output_directory,
        f"omm-systems-interchange-{interchange_version}"
        if using_interchange
        else f"omm-systems-toolkit-{toolkit_version}",
    )
    output_directory.mkdir(parents=True, exist_ok=True)

    save_openmm_system_func = functools.partial(
        _save_openmm_system,
        force_field=force_field,
        output_directory=output_directory,
        using_interchange=using_interchange,
        perturbations=perturbations,
    )

    exceptions_by_name = {}
    start_time = time.perf_counter()

    with Pool(processes=n_processes) as pool:

        for name, exceptions in track(
            pool.imap(save_openmm_system_func, topology_definitions),
            description="creating systems",
            total=len(topology_definitions),
        ):

            if len(exceptions) == 0:
                continue

            console.print(
                Padding(
                    f"[red]ERROR[/red] cannot create all systems for {name}",
                    (0, 0, 1, 0),
                ),
                *(
                    Padding(
                        f"{'' if not perturbations else perturbations[i].path } - "
                        f"{str(exception)}",
                        (0, 0, 0, 4),
                    )
                    for i, exception in exceptions.items()
                ),
                NewLine(),
            )

            exceptions_by_name[name] = {
                i: traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
                for i, exception in exceptions.items()
            }

    end_time = time.perf_counter()

    console.print(
        Padding(
            f"creating systems took {(end_time - start_time) / 60.0} minutes",
            (1, 0, 1, 0),
        )
    )

    if len(exceptions_by_name) > 0:

        exceptions_path = Path(
            output_directory, f'errors-{time.strftime("%Y-%m-%d-%H-%M-%S")}.json'
        )

        console.print(
            Padding(
                f"finished with exceptions for {len(exceptions_by_name)} topologies - "
                f"see [repr.filename]{str(exceptions_path)}[/repr.filename] for "
                f"details",
                (0, 0, 1, 0),
            )
        )

        with exceptions_path.open("w") as file:
            json.dump(exceptions_by_name, file)

        raise Exit(code=1)


if __name__ == "__main__":
    main()
