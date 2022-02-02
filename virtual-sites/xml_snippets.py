xml_ff_virtual_sites_monovalent_match_once = """<?xml version="1.0" encoding="utf-8"?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <Bonds version="0.3" potential="harmonic" fractional_bondorder_method="AM1-Wiberg" fractional_bondorder_interpolation="linear">
        <Bond smirks="[*:1]~[*:2]" id="b999" k="500.0 * kilocalories_per_mole/angstrom**2" length="1.1 * angstrom"/>
    </Bonds>
    <VirtualSites version="0.3">
        <VirtualSite
            type="MonovalentLonePair"
            name="EP"
            smirks="[#8:1]~[#6:2]~[#6:3]"
            distance="0.1*angstrom"
            charge_increment1="0.1*elementary_charge"
            charge_increment2="0.1*elementary_charge"
            charge_increment3="0.1*elementary_charge"
            sigma="0.1*angstrom"
            epsilon="0.1*kilocalories_per_mole"
            inPlaneAngle="110.*degree"
            outOfPlaneAngle="41*degree"
            match="once" >
        </VirtualSite>
    </VirtualSites>
</SMIRNOFF>
"""

xml_tip5p = """<?xml version="1.0" encoding="utf-8"?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <LibraryCharges version="0.3">
            <LibraryCharge name="tip5p" smirks="[#1:1]-[#8X2H2+0:2]-[#1:3]" charge1="0.*elementary_charge" charge2="0.*elementary_charge" charge3="0.*elementary_charge"/>
    </LibraryCharges>
    <vdW version="0.3" potential="Lennard-Jones-12-6" combining_rules="Lorentz-Berthelot" scale12="0.0" scale13="0.0" scale14="0.5" scale15="1.0" switch_width="1.0 * angstrom" cutoff="9.0 * angstrom" method="cutoff">
            <Atom smirks="[#1:1]-[#8X2H2+0]-[#1]" epsilon="0. * mole**-1 * kilojoule" id="n35" sigma="1 * nanometer"/>
            <Atom smirks="[#1]-[#8X2H2+0:1]-[#1]" epsilon="0.66944 * mole**-1 * kilojoule" id="n35" sigma="0.312 * nanometer"/>
    </vdW>
     <Bonds version="0.3" potential="harmonic" fractional_bondorder_method="AM1-Wiberg" fractional_bondorder_interpolation="linear">
        <Bond smirks="[#1:1]-[#8X2H2+0:2]-[#1]" length="0.9572 * angstrom" k="462750.4 * nanometer**-2 * mole**-1 * kilojoule" id="b1" />   
    </Bonds>
    <Angles version="0.3" potential="harmonic">
        <Angle smirks="[#1:1]-[#8X2H2+0:2]-[#1:3]" angle="1.82421813418 * radian" k="836.8 * mole**-1 * radian**-2 * kilojoule" id="a1" />
    </Angles>
    <VirtualSites version="0.3" exclusion_policy="parents">
        <VirtualSite
            type="DivalentLonePair"
            name="EP"
            smirks="[#1:1]-[#8X2H2+0:2]-[#1:3]"
            distance="0.70 * angstrom"
            charge_increment1="0.1205*elementary_charge"
            charge_increment2="0.0*elementary_charge"
            charge_increment3="0.1205*elementary_charge"
            sigma="1.0*angstrom"
            epsilon="0.0*kilocalories_per_mole"
            outOfPlaneAngle="54.71384225*degree"
            match="all_permutations" >
        </VirtualSite>
    </VirtualSites>
    <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" scale15="1.0" switch_width="0.0 * angstrom" cutoff="9.0 * angstrom"/>
  <Constraints version="0.3">
    <Constraint smirks="[#1:1]-[#8X2H2+0:2]-[#1]" id="c1" distance="0.9572 * angstrom"/>
    <Constraint smirks="[#1:1]-[#8X2H2+0]-[#1:2]" id="c2" distance="1.5139006545247014 * angstrom"/>
  </Constraints>
</SMIRNOFF>
"""

xml_gbsa_ff = """<?xml version='1.0' encoding='ASCII'?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <GBSA version="0.3" gb_model="HCT" solvent_dielectric="78.5" solute_dielectric="1" sa_model="None" surface_area_penalty="5.4*calories/mole/angstroms**2" solvent_radius="1.4*angstroms">
          <Atom smirks="[*:1]" radius="0.15*nanometer" scale="0.8"/>
    </GBSA>
</SMIRNOFF>
"""

xml_charge_increment_model_ff_no_missing_cis = """
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
  <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" cutoff="9.0 * angstrom"/>
  <ChargeIncrementModel version="0.3" number_of_conformers="1" partial_charge_method="formal_charge">
    <ChargeIncrement smirks="[#6X4:1]-[#8:2]" charge_increment1="-0.06*elementary_charge" charge_increment2="0.06*elementary_charge"/>
    <ChargeIncrement smirks="[#6X4:1]-[#1:2]" charge_increment1="-0.01*elementary_charge" charge_increment2="0.01*elementary_charge"/>
    <ChargeIncrement smirks="[C:1][C:2][O:3]" charge_increment1="0.2*elementary_charge" charge_increment2="-0.1*elementary_charge" charge_increment3="-0.1*elementary_charge"/>
  </ChargeIncrementModel>
</SMIRNOFF>"""

xml_charge_increment_model_ff_one_less_ci = """
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
  <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" cutoff="9.0 * angstrom"/>
  <ChargeIncrementModel version="0.3" number_of_conformers="1" partial_charge_method="formal_charge">
    <ChargeIncrement smirks="[#6X4:1]-[#8:2]" charge_increment1="-0.06*elementary_charge" charge_increment2="0.06*elementary_charge"/>
    <ChargeIncrement smirks="[#6X4:1]-[#1:2]" charge_increment1="-0.01*elementary_charge"/>
    <ChargeIncrement smirks="[C:1][C:2][O:3]" charge_increment1="0.2*elementary_charge" charge_increment2="-0.1*elementary_charge"/>
  </ChargeIncrementModel>
</SMIRNOFF>"""

xml_charge_increment_model_ff_ethanol = """
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
  <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" cutoff="9.0 * angstrom"/>
  <ChargeIncrementModel version="0.3" number_of_conformers="1" partial_charge_method="formal_charge">
    <ChargeIncrement smirks="[#6X4:1]-[#8:2]" charge_increment1="-0.05*elementary_charge" charge_increment2="0.05*elementary_charge"/>
    <ChargeIncrement smirks="[C:1][C:2][O:3]" charge_increment1="0.2*elementary_charge" charge_increment2="-0.1*elementary_charge" charge_increment3="-0.1*elementary_charge"/>
  </ChargeIncrementModel>
</SMIRNOFF>"""

xml_charge_increment_model_ff_net_charge = """
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
  <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" cutoff="9.0 * angstrom"/>
  <ChargeIncrementModel version="0.3" number_of_conformers="1" partial_charge_method="formal_charge">
    <ChargeIncrement smirks="[#6X3:1]-[#8X1-1:2]" charge_increment1="-0.05*elementary_charge" charge_increment2="0.05*elementary_charge"/>
    <ChargeIncrement smirks="[#6X3:1]=[#8X1:2]" charge_increment1="0.2*elementary_charge" charge_increment2="-0.2*elementary_charge"/>
  </ChargeIncrementModel>
</SMIRNOFF>"""

xml_charge_increment_model_ff_override = """
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
  <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" cutoff="9.0 * angstrom"/>
  <ChargeIncrementModel version="0.3" number_of_conformers="1" partial_charge_method="formal_charge">
    <ChargeIncrement smirks="[#1:1]-[#6:2]([#1:3])([#1:4])" charge_increment1="0.123*elementary_charge" charge_increment2="0.369*elementary_charge" charge_increment3="-0.123*elementary_charge" charge_increment4="0.123*elementary_charge"/>
    <ChargeIncrement smirks="[#6X4:1]([#1:2])([#1:3])([#1:4])" charge_increment1="0.3*elementary_charge" charge_increment2="-0.1*elementary_charge" charge_increment3="-0.1*elementary_charge" charge_increment4="-0.1*elementary_charge"/>
  </ChargeIncrementModel>
</SMIRNOFF>"""

xml_charge_increment_model_ff_both_apply = """
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
  <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" cutoff="9.0 * angstrom"/>
  <ChargeIncrementModel version="0.3" number_of_conformers="0" partial_charge_method="formal_charge">
    <ChargeIncrement smirks="[#6X4:1]([#1:2])([#1:3])([#1:4])" charge_increment1="0.3*elementary_charge" charge_increment2="-0.1*elementary_charge" charge_increment3="-0.1*elementary_charge" charge_increment4="-0.1*elementary_charge"/>
    <ChargeIncrement smirks="[#6X4:1][#6X4:2][#8]" charge_increment1="0.05*elementary_charge" charge_increment2="-0.05*elementary_charge"/>
  </ChargeIncrementModel>
</SMIRNOFF>"""

xml_charge_increment_model_ff_match_once = """
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
  <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" cutoff="9.0 * angstrom"/>
  <ChargeIncrementModel version="0.3" number_of_conformers="1" partial_charge_method="formal_charge">
    <ChargeIncrement smirks="[#6X4:1]([#1:2])[#6][#8]" charge_increment1="0.1*elementary_charge" charge_increment2="-0.1*elementary_charge"/>
  </ChargeIncrementModel>
</SMIRNOFF>"""

xml_charge_increment_model_ff_match_two = """
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
  <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" cutoff="9.0 * angstrom"/>
  <ChargeIncrementModel version="0.3" number_of_conformers="1" partial_charge_method="formal_charge">
    <ChargeIncrement smirks="[#6X4:1]([#1:2])([#1:3])[#6][#8]" charge_increment1="0.1*elementary_charge" charge_increment2="-0.05*elementary_charge" charge_increment3="-0.05*elementary_charge"/>
  </ChargeIncrementModel>
</SMIRNOFF>"""

xml_charge_increment_model_ff_match_all = """
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
  <Electrostatics version="0.3" method="PME" scale12="0.0" scale13="0.0" scale14="0.833333" cutoff="9.0 * angstrom"/>
  <ChargeIncrementModel version="0.3" number_of_conformers="1" partial_charge_method="formal_charge">
    <ChargeIncrement smirks="[#6X4:1]([#1:2])([#1:3])([#1:4])" charge_increment1="0.3*elementary_charge" charge_increment2="-0.1*elementary_charge" charge_increment3="-0.1*elementary_charge" charge_increment4="-0.1*elementary_charge"/>
  </ChargeIncrementModel>
</SMIRNOFF>"""

xml_ff_virtual_sites_bondcharge_match_once = """<?xml version="1.0" encoding="utf-8"?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <VirtualSites version="0.3">
        <VirtualSite
            type="BondCharge"
            name="EP1"
            smirks="[*:1]~[*:2]"
            distance="0.111*angstrom"
            charge_increment1="0.1*elementary_charge"
            charge_increment2="0.1*elementary_charge"
            sigma="0.1*angstrom"
            epsilon="0.1*kilocalories_per_mole"
            match="once" >
        </VirtualSite>
        <VirtualSite
            type="BondCharge"
            name="EP2"
            smirks="[#7:1]~[#7:2]"
            distance="0.222*angstrom"
            charge_increment1="0.2*elementary_charge"
            charge_increment2="0.2*elementary_charge"
            sigma="0.2*angstrom"
            epsilon="0.2*kilocalories_per_mole"
            match="all_permutations" >
        </VirtualSite>
        <VirtualSite
            type="BondCharge"
            name="EP3"
            smirks="[#7:1]~[#7:2]"
            distance="0.333*angstrom"
            charge_increment1="0.2*elementary_charge"
            charge_increment2="0.2*elementary_charge"
            sigma="0.2*angstrom"
            epsilon="0.2*kilocalories_per_mole"
            match="once" >
        </VirtualSite>
    </VirtualSites>
</SMIRNOFF>
"""

xml_ff_virtual_sites_bondcharge_match_all = """<?xml version="1.0" encoding="utf-8"?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <Bonds version="0.3" potential="harmonic" fractional_bondorder_method="AM1-Wiberg" fractional_bondorder_interpolation="linear">
      <Bond smirks="[*:1]~[*:2]" id="b999" k="500.0 * kilocalories_per_mole/angstrom**2" length="1.1 * angstrom"/>
    </Bonds>
    <VirtualSites version="0.3">
        <VirtualSite
            type="BondCharge"
            name="EP"
            smirks="[*:1]~[*:2]"
            distance="0.1*angstrom"
            charge_increment1="0.1*elementary_charge"
            charge_increment2="0.1*elementary_charge"
            sigma="0.1*angstrom"
            epsilon="0.1*kilocalories_per_mole"
            match="once" >
        </VirtualSite>
        <VirtualSite
            type="BondCharge"
            name="EP"
            smirks="[#7:1]~[#7:2]"
            distance="0.2*angstrom"
            charge_increment1="0.2*elementary_charge"
            charge_increment2="0.2*elementary_charge"
            sigma="0.2*angstrom"
            epsilon="0.2*kilocalories_per_mole"
            match="once" >
        </VirtualSite>
        <VirtualSite
            type="BondCharge"
            name="EP"
            smirks="[#7:1]~[#7:2]"
            distance="0.2*angstrom"
            charge_increment1="0.2*elementary_charge"
            charge_increment2="0.2*elementary_charge"
            sigma="0.2*angstrom"
            epsilon="0.2*kilocalories_per_mole"
            match="all_permutations" >
        </VirtualSite>
    </VirtualSites>
</SMIRNOFF>
"""

xml_ff_virtual_sites_bondcharge_match_once_two_names = """<?xml version="1.0" encoding="utf-8"?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <Bonds version="0.3" potential="harmonic" fractional_bondorder_method="AM1-Wiberg" fractional_bondorder_interpolation="linear">
      <Bond smirks="[*:1]~[*:2]" id="b999" k="500.0 * kilocalories_per_mole/angstrom**2" length="1.1 * angstrom"/>
    </Bonds>
    <VirtualSites version="0.3">
        <VirtualSite
            type="BondCharge"
            name="EP1"
            smirks="[*:1]~[*:2]"
            distance="0.1*angstrom"
            charge_increment1="0.1*elementary_charge"
            charge_increment2="0.1*elementary_charge"
            sigma="0.1*angstrom"
            epsilon="0.1*kilocalories_per_mole"
            match="once" >
        </VirtualSite>
        <VirtualSite
            type="BondCharge"
            name="EP2"
            smirks="[*:1]~[*:2]"
            distance="0.2*angstrom"
            charge_increment1="0.2*elementary_charge"
            charge_increment2="0.2*elementary_charge"
            sigma="0.2*angstrom"
            epsilon="0.2*kilocalories_per_mole"
            match="once" >
        </VirtualSite>
    </VirtualSites>
</SMIRNOFF>
"""

xml_ff_virtual_sites_monovalent_match_once = """<?xml version="1.0" encoding="utf-8"?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <Bonds version="0.3" potential="harmonic" fractional_bondorder_method="AM1-Wiberg" fractional_bondorder_interpolation="linear">
      <Bond smirks="[*:1]~[*:2]" id="b999" k="500.0 * kilocalories_per_mole/angstrom**2" length="1.1 * angstrom"/>
    </Bonds>
    <VirtualSites version="0.3">
        <VirtualSite
            type="MonovalentLonePair"
            name="EP"
            smirks="[#8:1]~[#6:2]~[#6:3]"
            distance="0.1*angstrom"
            charge_increment1="0.1*elementary_charge"
            charge_increment2="0.1*elementary_charge"
            charge_increment3="0.1*elementary_charge"
            sigma="0.1*angstrom"
            epsilon="0.1*kilocalories_per_mole"
            inPlaneAngle="110.*degree"
            outOfPlaneAngle="41*degree"
            match="once" >
        </VirtualSite>
        <VirtualSite
            type="MonovalentLonePair"
            name="EP"
            smirks="[#8:1]=[#6:2]-[#6:3]"
            distance="0.2*angstrom"
            charge_increment1="0.2*elementary_charge"
            charge_increment2="0.2*elementary_charge"
            charge_increment3="0.2*elementary_charge"
            sigma="0.2*angstrom"
            epsilon="0.2*kilocalories_per_mole"
            inPlaneAngle="120.*degree"
            outOfPlaneAngle="42*degree"
            match="once" >
        </VirtualSite>
    </VirtualSites>
</SMIRNOFF>
"""

xml_ff_virtual_sites_divalent_match_all = """<?xml version="1.0" encoding="ASCII"?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <Bonds version="0.3" potential="harmonic" fractional_bondorder_method="AM1-Wiberg" fractional_bondorder_interpolation="linear">
      <Bond smirks="[*:1]~[*:2]" id="b999" k="500.0 * kilocalories_per_mole/angstrom**2" length="1.1 * angstrom"/>
    </Bonds>
    <VirtualSites version="0.3">
        <VirtualSite
            type="DivalentLonePair"
            name="EP"
            smirks="[#1:1]-[#8X2H2+0:2]-[#1:3]"
            distance="0.70 * angstrom"
            charge_increment1="0.241*elementary_charge"
            charge_increment2="0.0*elementary_charge"
            charge_increment3="0.241*elementary_charge"
            sigma="3.12*angstrom"
            epsilon="0.16*kilocalories_per_mole"
            outOfPlaneAngle="54.71384225*degree"
            match="all_permutations" >
        </VirtualSite>
    </VirtualSites>
</SMIRNOFF>
"""

xml_ff_virtual_sites_trivalent_match_once = """<?xml version="1.0" encoding="ASCII"?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <Bonds version="0.3" potential="harmonic" fractional_bondorder_method="AM1-Wiberg" fractional_bondorder_interpolation="linear">
      <Bond smirks="[*:1]~[*:2]" id="b999" k="500.0 * kilocalories_per_mole/angstrom**2" length="1.1 * angstrom"/>
    </Bonds>
    <VirtualSites version="0.3">
        <VirtualSite
            type="TrivalentLonePair"
            name="EP"
            smirks="[*:1]-[#7X3:2](-[*:3])-[*:4]"
            distance="0.50 * angstrom"
            charge_increment1="0.0*elementary_charge"
            charge_increment2="1.0*elementary_charge"
            charge_increment3="0.0*elementary_charge"
            charge_increment4="0.0*elementary_charge"
            sigma="0.0*angstrom"
            epsilon="0.0*kilocalories_per_mole"
            match="once" >
        </VirtualSite>
    </VirtualSites>
</SMIRNOFF>
"""

xml_ff_virtual_sites_trivalent_match_all = """
<?xml version="1.0" encoding="ASCII"?>
<SMIRNOFF version="0.3" aromaticity_model="OEAroModel_MDL">
    <Bonds version="0.3" potential="harmonic" fractional_bondorder_method="AM1-Wiberg" fractional_bondorder_interpolation="linear">
      <Bond smirks="[*:1]~[*:2]" id="b999" k="500.0 * kilocalories_per_mole/angstrom**2" length="1.1 * angstrom"/>
    </Bonds>
    <VirtualSites version="0.3">
        <VirtualSite
            type="TrivalentLonePair"
            name="EP"
            smirks="[*:1]-[#7X3:2]-([*:3])-[*:4]"
            distance="0.70 * angstrom"
            charge_increment1="0.1*elementary_charge"
            charge_increment2="0.1*elementary_charge"
            charge_increment3="0.1*elementary_charge"
            charge_increment4="0.1*elementary_charge"
            sigma="0.1*angstrom"
            epsilon="0.1*kilocalories_per_mole"
            match="once" >
        </VirtualSite>
    </VirtualSites>
</SMIRNOFF>
"""
