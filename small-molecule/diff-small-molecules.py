import glob
import json
from copy import deepcopy
from pprint import pprint

import openmm
import xmltodict
from deepdiff import DeepDiff
from openff.toolkit import __version__
from openff.toolkit.topology import *
from openff.toolkit.typing.engines.smirnoff import *


current_toolkit_version = __version__


def postprocessor(path, key, value):
    try:
        return key, int(value) if "." not in value else float(value)
    except (ValueError, TypeError):
        return key, value


def _correct_switching(diff):
    """
    PR #1198 introduces an intentional behavior change in order to follow the SMIRNOFF
    specification. Old versions (0.10.3 and older) of the OpenFF Toolkit did _not_ aply a switching
    function, but new versions (0.11.0 and newer) are intended to.
    """
    if len(diff["values_changed"]) == 0:
        return

    for key in diff["values_changed"]:
        if "useSwitchingFunction" in key:
            switching_function_key = key
            break

    switching_distance_key = switching_function_key.replace(
        "useSwitchingFunction", "switchingDistance"
    )

    assert diff["values_changed"][switching_function_key] == {
        "new_value": 1,
        "old_value": 0,
    }
    assert diff["type_changes"][switching_distance_key] == {
        "new_type": float,
        "new_value": 0.8,
        "old_type": int,
        "old_value": -1,
    }

    del diff["values_changed"][switching_function_key]
    if len(diff["values_changed"]) == 0:
        del diff["values_changed"]

    del diff["type_changes"][switching_distance_key]
    if len(diff["type_changes"]) == 0:
        del diff["type_changes"]


# smiles = json.load(open(f"results/single-molecules/toolkit-v0.10.3/indices.json", "r"))

number_systems_found = len(glob.glob("results/*/*/*/*xml"))

for index in range(number_systems_found):

    try:
        reference_path = (
            f"results/single-molecules/toolkit-v0.10.3/systems/{index:05}.xml"
        )
        with open(reference_path) as f:
            system1 = xmltodict.parse(f.read(), postprocessor=postprocessor)
    except FileNotFoundError:
        print(f"could not open {reference_path}")
        continue

    try:
        candidate_path = f"results/single-molecules/toolkit-v{current_toolkit_version}/systems/{index:05}.xml"
        with open(candidate_path) as f:
            system2 = xmltodict.parse(f.read(), postprocessor=postprocessor)
    except FileNotFoundError:
        print(f"could not open {candidate_path}")
        continue

    diff = DeepDiff(system1, system2, ignore_order=True, significant_digits=6)
    _correct_switching(diff)
    print(f"{index:05}", len(diff))
    if len(diff) > 0:
        pprint(diff)
