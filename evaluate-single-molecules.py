"""
Evaluate gas-phase systems (`openmm.System`) corresponding to entires
in molecule data sets.
"""
import logging
import urllib
from multiprocessing import Pool, cpu_count
from pathlib import Path

import multiprocessing_logging
import pandas as pd
import tqdm
from openff.interchange.drivers.openmm import _get_openmm_energies
from openff.toolkit import __version__
from openff.toolkit.topology import Molecule
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from openff.units.openmm import to_openmm

logging.basicConfig(
    filename=f"toolkit-v{__version__}-gas.log", encoding="utf-8", level=logging.INFO
)

multiprocessing_logging.install_mp_handler()

box_vectors = unit.Quantity([[4, 0, 0], [0, 4, 0], [0, 0, 4]], units=unit.nanometer)

if __version__ == "0.10.2":
    kj_mol = unit.kilojoule / unit.mol
    force_field = ForceField("openff-1.0.0.offxml")
else:
    kj_mol = unit.kilojoule / unit.mol
    force_field = ForceField("openff-1.0.0.offxml")


def _write_csv(dataframe: pd.DataFrame, file_name: str = "data.csv"):
    final = energies.set_index("SMILES")
    final.to_csv(file_name)


# TODO: Update this to just report the energy, not do any comparison
def get_energies_single_molecule(
    molecule: Molecule,
) -> pd.DataFrame:
    try:
        molecule.to_smiles()
    except:
        logging.info("Molecule.to_molecule() fails on this molecule")
        return

    logging.info(f"Starting molecule {molecule.to_smiles}")
    # if smiles in energies["SMILES"].values:
    #     print("Molecule with following SMILES already found in data.csv:" f"\t{smiles}")
    #     return

    if molecule.n_conformers == 0:
        molecule.generate_conformers(n_conformers=1)

    topology = molecule.to_topology()

    if __version__ == "0.10.2":
        positions = molecule.conformers[0]
        topology.box_vectors = to_openmm(box_vectors)
    else:
        positions = to_openmm(molecule.conformers[0])
        topology.box_vectors = box_vectors

    try:
        toolkit_system = force_field.create_openmm_system(topology)
    except Exception as e:
        logging.info(f"Molecule {molecule.to_smiles()} raised exception {type(e)}")
        return

    toolkit_energy = _get_openmm_energies(
        toolkit_system,
        box_vectors=to_openmm(box_vectors),
        positions=positions,
    )

    row = pd.DataFrame.from_dict({k: [v.m] for k, v in toolkit_energy.energies.items()})
    row["SMILES"] = molecule.to_smiles()
    return row


if __name__ == "__main__":
    Path("data/single-molecules/").mkdir(parents=True, exist_ok=True)
    Path(f"results/toolkit-v{__version__}/").mkdir(parents=True, exist_ok=True)

    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/openforcefield/qca-dataset-submission/master/submissions/2021-03-30-OpenFF-Industry-Benchmark-Season-1-v1.0/dataset.smi",
        "data/single-molecules/dataset.smi",
    )

    molecules = Molecule.from_file(
        "data/single-molecules/dataset.smi", allow_undefined_stereo=True
    )

    energies = pd.DataFrame(columns=["Bond", "Angle", "Torsion", "Nonbonded", "SMILES"])

    with Pool(processes=int(1.5 * cpu_count())) as pool:

        for row in tqdm.tqdm(
            pool.imap_unordered(get_energies_single_molecule, molecules),
            total=len(molecules),
        ):
            energies = energies.append(row)

    _write_csv(
        energies,
        file_name=f"results/toolkit-v{__version__}/single-molecule-energies.csv",
    )
