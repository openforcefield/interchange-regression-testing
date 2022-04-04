import json
from pathlib import Path

import click

from interchange_regression_utilities.models import ExpectedValueChange


def create_toolkit_0_10_x_to_0_11_x_changes():
    """
    PR #1198 introduces an intentional behavior change in order to follow the SMIRNOFF
    specification. Old versions (0.10.3 and older) of the OpenFF Toolkit did _not_ aply
    a switching function, but new versions (0.11.0 and newer) are intended to.
    """

    return [
        ExpectedValueChange(
            openmm_path="Forces/NonbondedForce/useSwitchingFunction",
            old_value=0,
            new_value=1,
        ),
        ExpectedValueChange(
            openmm_path="Forces/NonbondedForce/switchingDistance",
            old_value=-1.0,
            new_value=0.8,
        ),
    ]


def create_toolkit_0_11_x_to_interchange_0_2_xchanges():
    """
    PR #1198 introduces an intentional behavior change in order to follow the SMIRNOFF
    specification. Old versions (0.10.3 and older) of the OpenFF Toolkit did _not_ aply
    a switching function, but new versions (0.11.0 and newer) are intended to.
    """

    return [
        ExpectedValueChange(
            openmm_path="Forces/NonbondedForce/useSwitchingFunction",
            old_value=1,
            new_value=0,
        ),
        ExpectedValueChange(
            openmm_path="Forces/NonbondedForce/switchingDistance",
            old_value=0.8,
            new_value=-1,
        ),
    ]


@click.command()
def main():

    output_directory = Path("expected-changes")
    output_directory.mkdir(parents=True, exist_ok=True)

    with Path(output_directory, "toolkit-0-10-x-to-0-11-x.json").open("w") as file:
        json.dump(
            [c.dict() for c in create_toolkit_0_10_x_to_0_11_x_changes()],
            file,
            indent=2,
        )

    with Path(output_directory, "toolkit-0-11-x-to-interchange-0-2-x.json").open(
        "w"
    ) as file:
        json.dump(
            [c.dict() for c in create_toolkit_0_11_x_to_interchange_0_2_xchanges()],
            file,
            indent=2,
        )


if __name__ == "__main__":
    main()
