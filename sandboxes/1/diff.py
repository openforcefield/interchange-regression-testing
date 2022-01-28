from pprint import pprint

import xmltodict
from deepdiff import DeepDiff


def postprocessor(path, key, value):
    try:
        return key, int(value) if "." not in value else float(value)
    except (ValueError, TypeError):
        return key, value


try:
    with open("toolkit-v0.10.2-index0-repro.xml") as f:
        system1 = xmltodict.parse(f.read(), postprocessor=postprocessor)
except FileNotFoundError:
    print("uh oh")

try:
    with open(
        "toolkit-v0.10.1+42.gd7f02367-index0-repro.xml",
    ) as f:
        system2 = xmltodict.parse(f.read(), postprocessor=postprocessor)
except FileNotFoundError:
    print("uh oh")

diff = DeepDiff(system1, system2, ignore_order=True, significant_digits=6)
pprint(diff)
# print(index, len(diff['values_changed']))
