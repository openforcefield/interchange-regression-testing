import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

reference = pd.read_csv("foo-ref.csv")  # , index_col="SMILES")
candidate = pd.read_csv("foo.csv")  # , index_col="SMILES")

merged = reference.merge(candidate, how="right").set_index("SMILES")
reference = reference.set_index("SMILES")
candidate = candidate.set_index("SMILES")

differences = pd.DataFrame(columns=["SMILES", "Bond", "Angle", "Torsion", "Nonbonded"])

for smiles in merged.index:
    try:
        differences = differences.append(
            (candidate.loc[smiles] - reference.loc[smiles]).to_frame().T
        )
    except:
        pass
    print(differences.shape)
    # print(differences.describe())

print(differences.describe())

bins = np.linspace(-1, 1, num=100) * 1e-3
# min(differences.min()), max(differences.max()), num=100)

fig, ax = plt.subplots()
for column in differences.columns:
    if column == "SMILES":
        continue
    ax.hist(differences[column], bins=bins, histtype="step", label=column)
    with open(f"bad-{column.lower()}.txt", "w") as f:
        for line in [*differences[abs(differences[column] > 1e-6)].index]:
            # for line in [*differences[abs(differences[column] > 1e-6)]["SMILES"]]:
            f.write(line + "\n")

fig.legend()
fig.savefig("differences.png")

differences.to_csv("differences.csv", index_label="SMILES")
