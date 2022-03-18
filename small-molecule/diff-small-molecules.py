import glob
import json
from copy import deepcopy
from pprint import pprint
from collections import OrderedDict

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
        if type(value) == OrderedDict:
            return key, dict(value)
        else:
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


def _tolerate_charges(diff):
    """
    Tolerate errors on the order of 0.0001 in partial charges due to stochasticity of AM1-BCC
    calculations. If charges differ by less than a small value, remove them from the DeepDiff
    object.
    """
    try:
        if len(diff["values_changed"]) == 0:
            return
    except KeyError:
        return

    tolerated_exceptions = list()
    tolerated_charges = list()

    for key in diff["values_changed"]:
        if "Exceptions" in key and key.endswith("['@q']"):
            exception_key = key
            difference = abs(
                diff["values_changed"][exception_key]["old_value"]
                - diff["values_changed"][exception_key]["new_value"]
            )
            if difference < 5e-3:
                tolerated_exceptions.append(exception_key)
        elif "Particles" in key and "Force" in key:
            particle_key = key
            # if not particle_key.endswith("['@q']"):
            #     assert '@q' in diff["values_changed"][particle_key]['new_value'].keys()
            # # at this point we have some confidence that the only difference is the charge
            particle_diff3 = DeepDiff(
                diff["values_changed"][particle_key]["new_value"],
                diff["values_changed"][particle_key]["old_value"],
                significant_digits=3,
                ignore_order=True,
            )
            if len(particle_diff3) == 0:
                print("Allowing the following charge difference to pass:")
                print(f"particle key is {particle_key}")
                pprint(diff["values_changed"][particle_key])
                tolerated_charges.append(particle_key)
            elif len(particle_diff3) == 1:
                # DeepDiff uses string rounding and does it *before* comparing values,
                # so it sometimes reports failures with `significant_digits=3` even when
                # the difference between values is less than 1e-3.
                # https://zepworks.com/deepdiff/current/numbers.html#significant-digits
                # >>> from deepdiff import DeepDiff
                # >>> x = 0.08071666666666666
                # >>> y = 0.0817
                # >>> DeepDiff(x, y)
                # {'values_changed': {'root': {'new_value': 0.0817, 'old_value': 0.08071666666666666}}}
                # >>> abs(x - y) < 1e-3
                # True
                q_diff = (
                    particle_diff3["values_changed"]["root['@q']"]["new_value"]
                    - particle_diff3["values_changed"]["root['@q']"]["old_value"]
                )
                if abs(q_diff) < 1e-3:
                    tolerated_charges.append(particle_key)

    for key in tolerated_exceptions:
        del diff["values_changed"][key]

    for key in tolerated_charges:
        del diff["values_changed"][key]


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
    _tolerate_charges(diff)
    print(f"{index:05}", len(diff))
    if len(diff) > 0:
        pprint(diff)
