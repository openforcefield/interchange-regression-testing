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
def main():

    console = rich.get_console()
    pretty.install(console)

    download_url = (
        "https://raw.githubusercontent.com/openforcefield/qca-dataset-submission/"
        "master/submissions/2021-03-30-OpenFF-Industry-Benchmark-Season-1-v1.0/"
        "dataset.smi"
    )
    download_contents = download_file_contents(download_url, "downloading smiles")

    smiles = [pattern for pattern in download_contents.split("\n") if len(pattern) > 0]

    topology_definitions = [
        TopologyDefinition(
            name=str(i),
            components=[TopologyComponent(smiles=pattern, n_copies=1)],
            # Needed until 'Combination of non-bonded cutoff methods 9.0 A (vdW) and
            # pme (Electrostatics) not currently supported with
            # `combine_nonbonded_forces=True` and `.box=None`' error is fixed
            is_periodic=True,
        )
        for i, pattern in enumerate(smiles)
    ]

    output_path = Path("small-molecule", "input-topologies.json")
    output_path.parent.mkdir(exist_ok=True, parents=True)

    model_to_file(topology_definitions, output_path)


if __name__ == "__main__":
    main()
