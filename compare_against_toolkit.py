from openeye import oechem
from openff.interchange.components.interchange import Interchange
from openff.interchange.drivers.openmm import _get_openmm_energies, get_openmm_energies
from openff.toolkit.topology import Molecule
from openff.toolkit.typing.engines.smirnoff import ForceField
from openff.units import unit
from openmm import unit as openmm_unit

kj_mol = unit.kilojoule / unit.mol
force_field = ForceField("openff-1.0.0.offxml")
box_vectors = openmm_unit.Quantity(
    [[4, 0, 0], [0, 4, 0], [0, 0, 4]], unit=openmm_unit.nanometer
)

input_stream = oechem.oemolistream()

input_stream.open("NCI-molecules.sdf")

for oemol in input_stream.GetOEMols():
    molecule = Molecule.from_openeye(oemol, allow_undefined_stereo=True)
    try:
        molecule.generate_conformers(n_conformers=1)
    except Exception as e:
        print(f"Molecule {molecule.to_smiles()} raised exception {type(e)}")
        continue

    topology = molecule.to_topology()
    topology.box_vectors = box_vectors

    try:
        toolkit_system = force_field.create_openmm_system(topology)
    except Exception as e:
        print(f"Molecule {molecule.to_smiles()} raised exception {type(e)}")
        continue

    toolkit_energy = _get_openmm_energies(
        toolkit_system, box_vectors=box_vectors, positions=molecule.conformers[0]
    )

    interchange = Interchange.from_smirnoff(force_field=force_field, topology=topology)
    interchange.positions = molecule.conformers[0]
    system_energy = get_openmm_energies(interchange, combine_nonbonded_forces=True)

    energy_difference = system_energy - toolkit_energy
    print({k: v.m for k, v in energy_difference.items()})
