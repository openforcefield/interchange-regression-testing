from pathlib import Path

import click

from interchange_regression_utilities.models import ComparisonSettings


@click.command()
def main():

    output_directory = Path("comparison-settings")
    output_directory.mkdir(parents=True, exist_ok=True)

    ComparisonSettings(
        default_numeric_tolerance=1.0e-6,
        numeric_tolerance_overrides={
            "Forces/NonbondedForce/Particles/*/q": 5.0e-3,
            "Forces/NonbondedForce/Exceptions/*/q": 5.0e-3,
        },
    ).to_file(Path(output_directory, "default-comparison-settings.json"))


if __name__ == "__main__":
    main()
