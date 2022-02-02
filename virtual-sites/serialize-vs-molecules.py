"""
Evaluate WBO systems (`openmm.System`) corresponding to entires
in molecule data sets.
"""
import json
import logging
from pathlib import Path
from typing import Dict

from openff.toolkit import __version__
from openff.toolkit.tests.create_molecules import *
from openff.toolkit.topology import Molecule
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from openff.units.openmm import to_openmm
from openmm import XmlSerializer
from xml_snippets import *

logging.basicConfig(
    filename=f"toolkit-v{__version__}-vs-serialize.log",
    encoding="utf-8",
    level=logging.INFO,
)

box_vectors = unit.Quantity([[4, 0, 0], [0, 4, 0], [0, 0, 4]], units=unit.nanometer)


# TODO: Update this to just report the energy, not do any comparison
def serialize_system_from_molecule(
    index: str,
    molecule: Molecule,
    snippet: str,
):

    force_field = ForceField("openff-2.0.0.offxml", snippet)

    logging.info(f"Starting molecule {index}")

    #     if molecule.n_conformers == 0:
    #         molecule.generate_conformers(n_conformers=1)
    #         logging.info(f"Generated conformers for molecule {index}")

    topology = molecule.to_topology()

    if __version__ == "0.10.2":
        topology.box_vectors = to_openmm(box_vectors)
    else:
        topology.box_vectors = box_vectors

    try:
        toolkit_system = force_field.create_openmm_system(topology)
        logging.info(f"Generated OpenMM System for molecule {index}")
    except Exception as e:
        logging.info(f"Molecule {molecule.to_smiles()} raised exception {type(e)}")
        return

    with open(
        f"results/vs-molecules/toolkit-v{__version__}/systems/{index:05}.xml", "w"
    ) as f:
        f.write(XmlSerializer.serialize(toolkit_system))

    return


if __name__ == "__main__":
    # Path("data/vs-molecules/").mkdir(parents=True, exist_ok=True)
    Path(f"results/vs-molecules/toolkit-v{__version__}/systems/").mkdir(
        parents=True, exist_ok=True
    )

    molecules, snippets = zip(
        (create_dinitrogen(), xml_ff_virtual_sites_bondcharge_match_once),
        (create_dioxygen(), xml_ff_virtual_sites_bondcharge_match_once),
        (create_dioxygen(), xml_ff_virtual_sites_bondcharge_match_all),
        (create_dioxygen(), xml_ff_virtual_sites_bondcharge_match_once_two_names),
        (create_acetaldehyde(), xml_ff_virtual_sites_monovalent_match_once),
        (create_water(), xml_ff_virtual_sites_divalent_match_all),
        (create_ammonia(), xml_ff_virtual_sites_trivalent_match_once),
    )

    indices: Dict[str, str] = {
        f"{index:05}": molecule.to_smiles() for index, molecule in enumerate(molecules)
    }

    with open(f"results/vs-molecules/toolkit-v{__version__}/indices.json", "w") as f:
        json.dump(indices, f)

    for index, (molecule, snippet) in enumerate(zip(molecules, snippets)):
        serialize_system_from_molecule(index, molecule, snippet)
