"""
Evaluate condensed-phase systems (`openmm.System`) corresponding to entires
in physical property data sets.
"""
import logging
import urllib
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Tuple

import multiprocessing_logging
import pandas as pd
import tqdm
from nonbonded.library.models.datasets import DataSet
from openff.evaluator.datasets import PhysicalPropertyDataSet
from openff.evaluator.forcefield import SmirnoffForceFieldSource
from openff.evaluator.protocols.coordinates import BuildCoordinatesPackmol
from openff.evaluator.protocols.forcefield import BuildSmirnoffSystem
from openff.evaluator.substances import Substance
from openff.interchange.components.interchange import Interchange
from openff.interchange.drivers.openmm import _get_openmm_energies
from openff.toolkit import __version__
from openff.toolkit.topology import Molecule, Topology
from openff.toolkit.typing.engines.smirnoff import ForceField
from openmm import System, app

logging.basicConfig(
    filename=f"toolkit-v{__version__}-condensed.log",
    encoding="utf-8",
    level=logging.INFO,
)

multiprocessing_logging.install_mp_handler()


def _write_csv(dataframe: pd.DataFrame, file_name: str = "data.csv"):
    final = energies.set_index("SMILES")
    final.to_csv(file_name)


def _generate_system_from_substance(substance: Substance) -> Tuple[str, System]:
    """Generate an `openmm.System` from a `Substance` using OpenFF Evaluator and Toolkit."""

    logging.info(f"starting packing {str(substance)}")

    build_coordinates = BuildCoordinatesPackmol("")
    build_coordinates.substance = substance
    try:
        build_coordinates.execute("build-coords")
    except:
        logging.info(f"packing failed on {str(substance)}")
        return

    logging.info(f"done packing {str(substance)}")

    logging.info(f"starting typing {str(substance)}")

    apply_parameters = BuildSmirnoffSystem("")
    apply_parameters.force_field_path = "force-field.json"
    apply_parameters.coordinate_file_path = build_coordinates.coordinate_file_path
    apply_parameters.substance = substance
    try:
        apply_parameters.execute("apply-params")
    except:
        logging.info(f"parameterizing failed on {str(substance)}")
        return

    logging.info(f"done typing {str(substance)}")

    def _create_openmm_system(substance, build_coordinates):
        """Hidden function for creating an `openmm.System` from Interchange"""
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

        return interchange.to_openmm(combine_nonbonded_forces=True)

    return (
        build_coordinates.coordinate_file_path,
        apply_parameters.parameterized_system.system,
    )


def get_energies_condensed_phase(substance: Substance) -> pd.DataFrame:
    try:
        coordinate_file_path, system = _generate_system_from_substance(substance)
    except TypeError:
        # TODO: Better way of short-circuiting on i.e. Packmol failure
        return

    pdb_file = app.PDBFile(coordinate_file_path)

    logging.info(f"running openmm {str(substance)}")

    toolkit_energy = _get_openmm_energies(
        system,
        box_vectors=pdb_file.topology.getPeriodicBoxVectors(),
        positions=pdb_file.getPositions(),
    )

    row = pd.DataFrame.from_dict({k: [v.m] for k, v in toolkit_energy.energies.items()})
    row["Identifier"] = substance.identifier
    return row


if __name__ == "__main__":
    Path("data/condensed-phase-systems/").mkdir(parents=True, exist_ok=True)
    Path(f"results/toolkit-v{__version__}/").mkdir(parents=True, exist_ok=True)

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/openforcefield/openff-sage/main/data-set-curation/physical-property/optimizations/data-sets/sage-train-v1.json",
        "data/condensed-phase-systems/dataset.json",
    )

    with open("force-field.json", "w") as force_field_file:
        force_field_file.write(
            SmirnoffForceFieldSource.from_object(
                ForceField("openff-2.0.0.offxml")
            ).json()
        )

    data_set: PhysicalPropertyDataSet = DataSet.parse_file(
        "data/condensed-phase-systems/dataset.json"
    ).to_evaluator()

    substances = data_set.substances

    energies = pd.DataFrame(columns=["Bond", "Angle", "Torsion", "Nonbonded", "SMILES"])

    with Pool(processes=cpu_count()) as pool:

        for row in tqdm.tqdm(
            pool.imap_unordered(get_energies_condensed_phase, substances),
            total=len(substances),
        ):
            energies = energies.append(row)

    _write_csv(
        energies,
        file_name=f"results/toolkit-v{__version__}/condensed-phase-systems.csv",
    )
