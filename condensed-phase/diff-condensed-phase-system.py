import glob
import json
import sys
from copy import deepcopy
from pprint import pprint

from openmm import XmlSerializer
import xmltodict
from deepdiff import DeepDiff
from openff.toolkit.topology import *
from openff.toolkit import __version__
from openff.toolkit.typing.engines.smirnoff import *


def postprocessor(path, key, value):
    try:
        return key, int(value) if "." not in value else float(value)
    except (ValueError, TypeError):
        return key, value


i = sys.argv[1]

for index in range(
    1,
    len(glob.glob("results/condensed-phase-systems/toolkit-v0.10.3/systems/*.xml")) + 1,
):

    if index != int(i):
        continue

    index = f"{index:05}"
    with open(
        f"results/condensed-phase-systems/toolkit-v0.10.3/systems/{index}.xml", "r"
    ) as f1:
        _f1 = f1.read()
        dict1 = xmltodict.parse(_f1, postprocessor=postprocessor)
        system1 = XmlSerializer.deserialize(_f1)

    with open(
        f"results/condensed-phase-systems/toolkit-v{__version__}/systems/{index}.xml",
        "r",
    ) as f2:
        _f2 = f2.read()
        dict2 = xmltodict.parse(_f2, postprocessor=postprocessor)
        system2 = XmlSerializer.deserialize(_f2)

    diff = DeepDiff(dict1, dict2, ignore_order=True, significant_digits=8)
    print(diff)

    if len(diff) > 0:
        from openff.toolkit.tests.utils import compare_system_parameters

        compare_system_parameters(system1, system2)
    else:
        print(f"index {i} passed")
