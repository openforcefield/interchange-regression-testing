from pathlib import Path

import click
import rich
from rich import pretty

from interchange_regression_utilities.models import (
    TopologyComponent,
    TopologyDefinition,
    model_to_file,
)


@click.command()
def main():

    console = rich.get_console()
    pretty.install(console)

    smiles = [
        "c1cc(ccc1c2cc[nH+]cc2)O",
        "c1cc(ccc1c2cc[nH+]cc2)[O-]",
        "c1cc(ccc1c2ccncc2)O",
        "c1cc(ccc1c2ccncc2)[O-]",
        "c1cc(c(cc1O)Cl)c2cc[nH+]cc2",
        "c1cc(c(cc1O)Cl)c2ccncc2",
        "c1cc(c(cc1O)F)c2cc[nH+]cc2",
        "c1cc(c(cc1O)F)c2ccncc2",
        "c1cc(c(cc1[O-])Cl)c2cc[nH+]cc2",
        "c1cc(c(cc1[O-])Cl)c2ccncc2",
    ]

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

    output_path = Path("wbo-molecule", "input-topologies.json")
    output_path.parent.mkdir(exist_ok=True, parents=True)

    model_to_file(topology_definitions, output_path)


if __name__ == "__main__":
    main()
