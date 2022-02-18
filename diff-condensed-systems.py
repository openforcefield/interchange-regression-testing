import glob
import json
from copy import deepcopy
from pprint import pprint

import openmm
import xmltodict
from deepdiff import DeepDiff
from openff.toolkit.topology import *
from openff.toolkit.typing.engines.smirnoff import *


def postprocessor(path, key, value):
    try:
        return key, int(value) if "." not in value else float(value)
    except (ValueError, TypeError):
        return key, value


for index in range(
    max(
        len(glob.glob("results/*/*/*/*xml")),
        len(glob.glob("results/*/*/*/*xml")),
    )
):

    try:
        with open(
            f"results/condensed-phase-systems/toolkit-v0.10.2/systems/{index:05}.xml"
        ) as f:
            system1 = xmltodict.parse(f.read(), postprocessor=postprocessor)
    except FileNotFoundError:
        print(f"could not open index {index:05} reference system")
        continue

    try:
        with open(
            f"results/condensed-phase-systems/toolkit-v0.10.1+62.g80b658f6/systems/{index:05}.xml",
        ) as f:
            system2 = xmltodict.parse(f.read(), postprocessor=postprocessor)
    except FileNotFoundError:
        print(f"could not open index {index:05} candidate system")
        continue

    print(f"diffing index {index:05} candidate system")
    diff = DeepDiff(system1, system2, ignore_order=True, significant_digits=6)
    print(f"{index:05}", len(diff))
    if len(diff) > 0:
        pprint(diff)
