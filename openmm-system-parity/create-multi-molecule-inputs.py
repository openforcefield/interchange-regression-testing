import json
from pathlib import Path

import click
import rich
from rich import pretty

from interchange_regression_utilities.models import (
    TopologyComponent,
    TopologyDefinition,
    model_to_file,
)
from interchange_regression_utilities.utilities import download_file_contents


@click.command()
@click.option(
    "--n-molecules",
    help="The maximum total number of molecules to include in the topology.",
    type=int,
    default=64,
    show_default=True,
)
def main(n_molecules):

    console = rich.get_console()
    pretty.install(console)

    download_url = (
        "https://raw.githubusercontent.com/openforcefield/openff-sage/main/"
        "data-set-curation/physical-property/optimizations/data-sets/sage-train-v1.json"
    )
    download_contents = download_file_contents(download_url, "downloading data set")

    data_set_raw = json.loads(download_contents)

    topology_definitions = [
        TopologyDefinition(
            name=entry["id"],
            components=[
                TopologyComponent(
                    smiles=component["smiles"],
                    n_copies=(
                        max(1, int(component["mole_fraction"] * n_molecules))
                        + int(component["exact_amount"])
                    ),
                )
                for component in entry["components"]
            ],
            is_periodic=True,
        )
        for entry in data_set_raw["entries"]
    ]

    output_path = Path("multi-molecule", "input-topologies.json")
    output_path.parent.mkdir(exist_ok=True, parents=True)

    model_to_file(topology_definitions, output_path)


if __name__ == "__main__":
    main()
