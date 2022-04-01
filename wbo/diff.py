import json
from pprint import pprint

import xmltodict
from deepdiff import DeepDiff

from openff.toolkit import __version__

assert __version__.startswith("0.10.1+")

def postprocessor(path, key, value):
    try:
        return key, int(value) if "." not in value else float(value)
    except (ValueError, TypeError):
        return key, value


smiles = json.load(open("results/wbo-molecules/toolkit-v0.10.3/indices.json", "r"))

for index in smiles:
    with open(f"results/wbo-molecules/toolkit-v0.10.3/systems/{index}.xml") as f:
        system1 = xmltodict.parse(f.read(), postprocessor=postprocessor)

    with open(
        f"results/wbo-molecules/toolkit-v{__version__}/systems/{index}.xml",
    ) as f:
        system2 = xmltodict.parse(f.read(), postprocessor=postprocessor)

    diff = DeepDiff(system1, system2, ignore_order=True, significant_digits=6)
    print(index, len(diff["values_changed"]))
    pprint(diff)
