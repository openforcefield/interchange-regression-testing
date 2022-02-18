"""
Evaluate condensed-phase systems (`openmm.System`) corresponding to entires
in physical property data sets.
"""
import json
import logging
import urllib
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict, Tuple

import multiprocessing_logging
import tqdm
from nonbonded.library.models.datasets import DataSet
from openff.evaluator.datasets import PhysicalPropertyDataSet
from openff.evaluator.forcefield import SmirnoffForceFieldSource
from openff.evaluator.protocols.coordinates import BuildCoordinatesPackmol
from openff.evaluator.protocols.forcefield import BuildSmirnoffSystem
from openff.evaluator.substances import Substance
from openff.interchange.components.interchange import Interchange
from openff.toolkit import __version__
from openff.toolkit.topology import Molecule, Topology
from openff.toolkit.typing.engines.smirnoff import ForceField
from openmm import System, XmlSerializer, app

logging.basicConfig(
    filename=f"toolkit-v{__version__}-condensed.log",
    encoding="utf-8",
    level=logging.INFO,
)

multiprocessing_logging.install_mp_handler()


def _generate_system_from_substance(
    substance: Substance, use_interchange: bool
) -> Tuple[str, System]:
    """Generate an `openmm.System` from a `Substance` using OpenFF Evaluator and Toolkit."""

    logging.info(f"starting packing {str(substance)}")

    build_coordinates = BuildCoordinatesPackmol("")
    build_coordinates.substance = substance
    try:
        build_coordinates.execute("build-coords")
        logging.info(f"packing suceeded on {str(substance)}")
    except Exception as e:
        logging.info(f"packing failed on {str(substance)} with exception {str(e)}")
        return

    logging.info(f"done packing {str(substance)}")

    # apply_parameters = BuildSmirnoffSystem("")
    # apply_parameters.force_field_path = "force-field.json"
    # apply_parameters.coordinate_file_path = build_coordinates.coordinate_file_path
    # apply_parameters.substance = substance
    # try:
    #     apply_parameters.execute("apply-params")
    #     logging.info(f"parameterizing succeeded on {str(substance)}")
    # except Exception as e:
    #     logging.info(
    #         f"parameterizing failed on {str(substance)} with exception {str(e)}"
    #     )
    #     return

    logging.info(f"done typing {str(substance)}")

    def _create_openmm_system(substance, build_coordinates, use_interchange):
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

        logging.info(
            f"starting create_openmm_system call {str(substance)}, {use_interchange=}"
        )

        return force_field.create_openmm_system(use_interchange=use_interchange)

    #       interchange = Interchange.from_smirnoff(force_field, topology)
    #
    #       return interchange.to_openmm(combine_nonbonded_forces=True)

    try:
        system = _create_openmm_system(substance, build_coordinates, use_interchange)
    except:
        return

    return (
        build_coordinates.coordinate_file_path,
        system,
    )


def serialize_system_from_substance(args):
    index, substance = args

    for use_interchange in [True, False]:
        try:
            coordinate_file_path, system = _generate_system_from_substance(
                substance,
                use_interchange,
            )
        except TypeError:
            # TODO: Better way of short-circuiting on i.e. Packmol failure
            return

        pdb_file = app.PDBFile(coordinate_file_path)

        logging.info(f"serializing openmm {str(substance)}")

        with open(
            f"results/condensed-phase-systems/toolkit-v{__version__}-{use_interchange}/systems/{index}.xml",
            "w",
        ) as f:
            f.write(XmlSerializer.serialize(system))

    return


if __name__ == "__main__":

    Path("data/condensed-phase-systems/").mkdir(parents=True, exist_ok=True)
    Path(f"results/condensed-phase-systems/toolkit-v{__version__}/systems").mkdir(
        parents=True, exist_ok=True
    )
    Path(f"results/condensed-phase-systems/toolkit-v{__version__}-True/systems").mkdir(
        parents=True, exist_ok=True
    )
    Path(f"results/condensed-phase-systems/toolkit-v{__version__}-False/systems").mkdir(
        parents=True, exist_ok=True
    )

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

    indices: Dict[str, str] = {
        f"{index:05}": str(substance) for index, substance in enumerate(substances)
    }

    args_dict: Dict[str, Molecule] = {
        f"{index:05}": substance for index, substance in enumerate(substances)
    }

    with open(
        f"results/condensed-phase-systems/toolkit-v{__version__}/indices.json", "w"
    ) as f:
        json.dump(indices, f)

    with Pool(processes=int(10)) as pool:

        for row in tqdm.tqdm(
            pool.imap(serialize_system_from_substance, list(args_dict.items())),
            total=len(substances),
        ):
            pass
