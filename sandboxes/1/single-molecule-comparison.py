import pathlib
import random
from typing import Optional, Union

from openff.toolkit import __version__
from openff.toolkit.topology import Molecule
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from openff.units.openmm import to_openmm
from openmm import XmlSerializer


def postprocessor(path, key, value):
    try:
        return key, int(value) if "." not in value else float(value)
    except (ValueError, TypeError):
        return key, value


box_vectors = unit.Quantity(
    [[4, 0, 0], [0, 4, 0], [0, 0, 4]], units=unit.nanometer
)

force_field = ForceField("openff-1.0.0.offxml")


def serialize_single_molecule(
    molecule: Union[str, Molecule], index: Optional[int] = None
):
    if isinstance(molecule, str):
        smiles = molecule
        print(smiles)
        molecule = Molecule.from_smiles(smiles, allow_undefined_stereo=True)
    elif isinstance(molecule, Molecule):
        pass
    else:
        raise Exception

    topology = molecule.to_topology()

    if __version__ == "0.10.2":
        topology.box_vectors = to_openmm(box_vectors)
    else:
        topology.box_vectors = box_vectors

    if __version__ == "0.10.2":
        system = force_field.create_openmm_system(topology)
    else:
        system = force_field.create_openmm_system(
            topology, use_interchange=True,
        )

    with open(f"toolkit-v{__version__}-index{index}-repro.xml", "w") as f:
        f.write(XmlSerializer.serialize(system))

    with open("smiles.txt", "w") as f:
        f.write(smiles)


if pathlib.Path("smiles.txt").is_file():
    smiles = open("smiles.txt").readlines()[0].strip()
else:
    number_of_lines = len(open("bad-angle.smi").readlines())
    random_line_number = random.randint(0, number_of_lines)
    smiles = open("bad-torsion.smi").readlines()[random_line_number].strip()

serialize_single_molecule(
    molecule=smiles,
    index=0,
)
