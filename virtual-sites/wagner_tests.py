import numpy as np
import openmm
import openmm.app
from openff.toolkit import ForceField, Molecule
from openff.units import unit
from openmm import unit as openmm_unit


def _get_energy_openmm(system: openmm.System, toplogy: openmm.app.Topology, positions):
    integrator = openmm.VerletIntegrator(1.0 * openmm_unit.femtoseconds)

    simulation = openmm.app.Simulation(toplogy, system, integrator)
    simulation.context.setPositions(positions)
    simulation.context.computeVirtualSites()

    return simulation.context.getState(
        getEnergy=True, getPositions=True
    ).getPotentialEnergy()


def get_energy_toolkit(molecule: Molecule, force_field: ForceField):
    from openff.toolkit.topology.molecule import Atom

    omm_sys, ret_top = force_field.create_openmm_system(
        molecule.to_topology(),
        return_topology=True,
        charge_from_molecules=[molecule],
        use_interchange=False,
    )

    omm_top = ret_top.to_openmm()

    # to_openmm doesn't handle virtualsites yet, so we add them manually to the openmm topology here
    for particle in ret_top.topology_particles:
        if isinstance(particle, Atom):
            continue

        omm_top.addAtom(
            particle.virtual_site.name,
            openmm.app.Element.getByMass(0),
            [i for i in omm_top.residues()][0],
        )

    # heuristic that vsites come at the end; applies to OpenFF
    n_vptl = ret_top.n_topology_particles - ret_top.n_topology_atoms
    vsite_pad = np.arange(n_vptl * 3).reshape(n_vptl, 3)
    conformer_nm = molecule.conformers[0].m_as(unit.nanometer)
    conformer_w_vsite_pad_nm = np.vstack([conformer_nm, vsite_pad])

    return _get_energy_openmm(omm_sys, omm_top, conformer_w_vsite_pad_nm)


def get_energy_interchange(molecule: Molecule, force_field: ForceField):
    from openff.interchange import Interchange

    topology = molecule.to_topology()
    topology.box_vectors = unit.Quantity([10, 10, 10], unit.nanometer)

    interchange = Interchange.from_smirnoff(
        force_field=force_field, topology=topology, charge_from_molecules=[molecule]
    )

    openmm_system = interchange.to_openmm(combine_nonbonded_forces=True)

    openmm_topology = interchange.to_openmm_topology()

    positions = interchange.positions.m_as(unit.nanometer)
    virtual_site_padding = np.zeros((len(interchange["VirtualSites"].slot_map), 3))
    padded_positions = np.vstack([positions, virtual_site_padding])

    return _get_energy_openmm(openmm_system, openmm_topology, padded_positions)


if __name__ == "__main__":
    indices = range(1, 6)
exclusion_policies = ["none", "minimal", "parents"]

for index in indices:
    print(f"{index=}")
    for exclusion_policy in exclusion_policies:
        print(f"{exclusion_policy=}")
        mol = Molecule.from_file(f"test_inputs/test{index}.sdf")
        ff = ForceField(f"test_inputs/test{index}_{exclusion_policy}.offxml")
        print(
            round(get_energy_toolkit(mol, ff)._value, 3),
            round(get_energy_interchange(mol, ff)._value, 3),
        )
