XML snippets are taken from the [toolkit test suite](https://github.com/openforcefield/openff-toolkit/blob/c29c935935edd1cda8ebe2458744315b580a1caa/openff/toolkit/tests/test_forcefield.py#L482-L706)

Cases currently included
1. Molecular nitrogen, `BondChargeVirtualSite`, `match="once"`
1. Molecular oxygen, `BondChargeVirtualSite`, `match="once"`
1. Molecular oxygen, `BondChargeVirtualSite`, `match="all"`
1. Molecular oxygen, `BondChargeVirtualSite`, `match="once"`, two names
1. Acetaldehyde, `MonovalentLonePair`, `match="once"`
1. Water (TIP5P), `DivalentLonePair`, `match="all"`
1. Ammonia, `TrivalentLonePair`, `match="once"`
