### Scripts for running small molecules comparisons

To run _all_ 9,104 molecules in the data set, run
```shell
$ zsh -i run.sh
```
or an equivalent in your shell. This may take several hours to days depending on the number
of cores on your machine and how performant they are. This will serialize two `openmm.System`
objects for each molecule, one from `reference-env` and one from `candidate-env`. Finally, it will
compare the serialized representations of each to assess if they are sufficiently similar.

Once systems are generated for all molecules (and both conda environments), compare directly their serialized representations by running

```shell
$ python diff-small-molecules.py
```

Alternatively, you can generate the serialized systems in the background and periodically run
comparisons of completed molecules before all are necessarily completed. To do this, run

```shell
$ zsh -i run_background.sh
```

and periodically check (after first waiting a few minutes for the first set of molecules to be
written) by running

```shell
$ python diff-small-molecules.py
```
