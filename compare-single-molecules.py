from multiprocessing import Pool, cpu_count

import pandas as pd
import tqdm
from openff.interchange.components.interchange import Interchange
from openff.interchange.drivers.openmm import _get_openmm_energies, get_openmm_energies
from openff.toolkit.topology import Molecule
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from openff.units.openmm import to_openmm

kj_mol = unit.kilojoule / unit.mol
force_field = ForceField("openff-1.0.0.offxml")
box_vectors = unit.Quantity([[4, 0, 0], [0, 4, 0], [0, 0, 4]], units=unit.nanometer)


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
        print("Molecule.to_molecule() fails on this molecule")
        return

    # if smiles in energies["SMILES"].values:
    #     print("Molecule with following SMILES already found in data.csv:" f"\t{smiles}")
    #     return

    if molecule.n_conformers == 0:
        molecule.generate_conformers(n_conformers=1)

    topology = molecule.to_topology()
    topology.box_vectors = box_vectors

    try:
        toolkit_system = force_field.create_openmm_system(topology)
    except Exception as e:
        print(f"Molecule {molecule.to_smiles()} raised exception {type(e)}")
        return

    toolkit_energy = _get_openmm_energies(
        toolkit_system,
        box_vectors=to_openmm(box_vectors),
        positions=to_openmm(molecule.conformers[0]),
    )

    interchange = Interchange.from_smirnoff(force_field=force_field, topology=topology)
    interchange.positions = molecule.conformers[0]
    # import ipdb; ipdb.set_trace()
    system_energy = get_openmm_energies(interchange, combine_nonbonded_forces=True)

    energy_difference = system_energy - toolkit_energy
    row = pd.DataFrame.from_dict({k: [v.m] for k, v in energy_difference.items()})
    row["SMILES"] = molecule.to_smiles()
    return row


if __name__ == "__main__":
    molecules = Molecule.from_file("dataset.smi", allow_undefined_stereo=True)

    energies = pd.DataFrame(columns=["Bond", "Angle", "Torsion", "Nonbonded", "SMILES"])

    with Pool(processes=int(1.5 * cpu_count())) as pool:

        for row in tqdm.tqdm(
            pool.imap_unordered(get_energies_single_molecule, molecules),
            total=len(molecules),
        ):
            energies = energies.append(row)

    _write_csv(energies)
