"""
Generate condensed-phase systems (`openmm.System`) corresponding to entires
in physical property data sets.
"""
from typing import Generator, Tuple

from deepdiff import DeepDiff
from nonbonded.library.models.datasets import DataSet
from openff.evaluator.datasets import PhysicalPropertyDataSet
from openff.evaluator.forcefield import SmirnoffForceFieldSource
from openff.evaluator.protocols.coordinates import BuildCoordinatesPackmol
from openff.evaluator.protocols.forcefield import BuildSmirnoffSystem
from openff.evaluator.substances import Substance
from openff.interchange import Interchange
from openff.toolkit.topology import Molecule, Topology
from openff.toolkit.typing.engines.smirnoff import ForceField
from openmm import System, XmlSerializer, app


def _generate_systems_from_substance(substance: Substance) -> System:
    """Generate parallel `System`s from a `Substance` using the
    OpenFF Evaluator, Toolkit, and Interchange APIs."""

    build_coordinates = BuildCoordinatesPackmol("")
    build_coordinates.substance = substance
    build_coordinates.max_molecules = 216
    build_coordinates.execute("build-coords")

    apply_parameters = BuildSmirnoffSystem("")
    apply_parameters.force_field_path = "force-field.json"
    apply_parameters.coordinate_file_path = build_coordinates.coordinate_file_path
    apply_parameters.substance = substance
    apply_parameters.execute("apply-params")

    force_field = ForceField("openff-2.0.0.offxml")

    unique_molecules = list()

    for component in substance.components:

        molecule = Molecule.from_smiles(smiles=component.smiles)

        if molecule is None:
            raise ValueError(f"{component} could not be converted to a Molecule")

        unique_molecules.append(molecule)

    pdb_file = app.PDBFile(build_coordinates.coordinate_file_path)

    topology = Topology.from_openmm(
        pdb_file.topology,
        unique_molecules=unique_molecules,
    )

    interchange = Interchange.from_smirnoff(force_field, topology)

    system_from_interchange = interchange.to_openmm(combine_nonbonded_forces=True)

    return (
        apply_parameters.parameterized_system.system,
        system_from_interchange,
    )


def generate_systems(
    data_set_path: str,
) -> Generator[Tuple[System, System], None, None]:

    data_set: PhysicalPropertyDataSet = DataSet.parse_file(
        "sage-train-v1.json"
    ).to_evaluator()

    for property in data_set.properties:
        print(f"property {property.value}")
        yield _generate_systems_from_substance(property.substance)


if __name__ == "__main__":
    with open("force-field.json", "w") as force_field_file:
        force_field_file.write(
            SmirnoffForceFieldSource.from_object(
                ForceField("openff-2.0.0.offxml")
            ).json()
        )
    for result in generate_systems("sage-train-v1.json"):
        print(
            DeepDiff(
                XmlSerializer.serialize(result[0]),
                XmlSerializer.serialize(result[0]),
            )
        )
