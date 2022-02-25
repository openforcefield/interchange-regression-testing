"""
Evaluate condensed-phase systems (`openmm.System`) corresponding to entires
in physical property data sets.
"""
import json
import urllib
from pathlib import Path
from typing import Dict

import xmltodict
from deepdiff import DeepDiff
from nonbonded.library.models.datasets import DataSet
from openff.evaluator.datasets import PhysicalPropertyDataSet
from openff.evaluator.forcefield import SmirnoffForceFieldSource
from openff.evaluator.protocols.coordinates import BuildCoordinatesPackmol
from openff.toolkit import __version__
from openff.toolkit.topology import Molecule, Topology
from openff.toolkit.typing.engines.smirnoff import ForceField
from openmm import XmlSerializer, app
from tqdm import tqdm


def postprocessor(path, key, value):
    try:
        return key, int(value) if "." not in value else float(value)
    except (ValueError, TypeError):
        return key, value


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
        SmirnoffForceFieldSource.from_object(ForceField("openff-2.0.0.offxml")).json()
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

    print(f"starting create_openmm_system call {str(substance)}, {use_interchange=}")

    return force_field.create_openmm_system(topology, use_interchange=use_interchange)


for substance in tqdm(args_dict.values()):

    build_coordinates = BuildCoordinatesPackmol("")
    build_coordinates.substance = substance
    build_coordinates.max_molecules = 100

    try:
        build_coordinates.execute("build-coords")
    except Exception as e:
        raise Exception(f"packing failed on {str(substance)} with exception {str(e)}")

        assert False

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

    system1 = force_field.create_openmm_system(topology, use_interchange=False)

    system2 = force_field.create_openmm_system(topology, use_interchange=True)

    dict1 = xmltodict.parse(
        XmlSerializer.serialize(system1), postprocessor=postprocessor
    )
    dict2 = xmltodict.parse(
        XmlSerializer.serialize(system2), postprocessor=postprocessor
    )

    diff = DeepDiff(dict1, dict2, ignore_order=True, significant_digits=8)

    if len(diff) > 0:
        raise Exception(f"substance {str(substance)} failed")
    else:
        print(f"substance {str(substance)} succeeded")
