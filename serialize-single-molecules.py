"""
Evaluate gas-phase systems (`openmm.System`) corresponding to entires
in molecule data sets.
"""
import json
import logging
import urllib
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict

import multiprocessing_logging
import tqdm
from openff.toolkit import __version__
from openff.toolkit.topology import Molecule
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from openff.units.openmm import to_openmm
from openmm import XmlSerializer

logging.basicConfig(
    filename=f"toolkit-v{__version__}-gas-serialize.log",
    encoding="utf-8",
    level=logging.INFO,
)

multiprocessing_logging.install_mp_handler()

box_vectors = unit.Quantity([[4, 0, 0], [0, 4, 0], [0, 0, 4]], units=unit.nanometer)

force_field = ForceField("openff-1.0.0.offxml")


# TODO: Update this to just report the energy, not do any comparison
def serialize_system_from_molecule(
    args,  # index: str,
    # molecule: Molecule,
):
    index, molecule = args
    # Start a new thread as a timekeeper, periodically check if while inside
    # this function call the time has exceeded a timeout, raise an exception
    import threading

    def timer_function():
        import time

        now = time.time()
        while not finished:
            if time.time() - now > 1:
                raise TimeoutError
            time.sleep(0.5)

    finished = False

    timer_thread = threading.Thread(target=timer_function)

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
        timer_thread.start()
        toolkit_system = force_field.create_openmm_system(topology)
        logging.info(f"Generated OpenMM System for molecule {index}")
    except Exception as e:
        logging.info(f"Molecule {molecule.to_smiles()} raised exception {type(e)}")
        timer_thread.join()
        return

    with open(
        f"results/single-molecules/toolkit-v{__version__}/systems/{index}.xml", "w"
    ) as f:
        f.write(XmlSerializer.serialize(toolkit_system))

    return


if __name__ == "__main__":
    Path("data/single-molecules/").mkdir(parents=True, exist_ok=True)
    Path(f"results/single-molecules/toolkit-v{__version__}/systems/").mkdir(
        parents=True, exist_ok=True
    )

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/openforcefield/qca-dataset-submission/master/submissions/2021-03-30-OpenFF-Industry-Benchmark-Season-1-v1.0/dataset.smi",
        "data/single-molecules/dataset.smi",
    )

    molecules = Molecule.from_file(
        "data/single-molecules/dataset.smi", allow_undefined_stereo=True
    )

    indices: Dict[str, str] = {
        f"{index:05}": molecule.to_smiles() for index, molecule in enumerate(molecules)
    }

    args_dict: Dict[str, Molecule] = {
        f"{index:05}": molecule for index, molecule in enumerate(molecules)
    }

    with open(
        f"results/single-molecules/toolkit-v{__version__}/indices.json", "w"
    ) as f:
        json.dump(indices, f)

    with Pool(processes=int(cpu_count() * 1.2)) as pool:

        for row in tqdm.tqdm(
            pool.imap(serialize_system_from_molecule, list(args_dict.items())),
            total=len(molecules),
        ):
            pass