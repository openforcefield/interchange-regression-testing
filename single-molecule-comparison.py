import glob
import json
from copy import deepcopy
from pprint import pprint

import openmm
import xmltodict
from deepdiff import DeepDiff
from openff.toolkit import __version__
from openff.toolkit.topology import *
from openff.toolkit.topology import Molecule
from openff.toolkit.typing.engines.smirnoff import *
from openff.units import unit
from openff.units.openmm import to_openmm
from openmm import XmlSerializer


def postprocessor(path, key, value):
    try:
        return key, int(value) if "." not in value else float(value)
    except (ValueError, TypeError):
        return key, value


molecules = Molecule.from_file("bad-angle.txt.smi", allow_undefined_stereo=True)

box_vectors = unit.Quantity([[4, 0, 0], [0, 4, 0], [0, 0, 4]], units=unit.nanometer)

force_field = ForceField("openff-1.0.0.offxml")

for index, molecule in enumerate(molecules):

    topology = molecule.to_topology()

    if __version__ == "0.10.2":
        topology.box_vectors = to_openmm(box_vectors)
    else:
        topology.box_vectors = box_vectors

    if __version__ == "0.10.2":
        system = force_field.create_openmm_system(topology)
    else:
        system = force_field.create_openmm_system(topology, use_interchange=False)

    with open(f"toolkit-v{__version__}-molecule{index}.xml", "w") as f:
        f.write(XmlSerializer.serialize(system))
