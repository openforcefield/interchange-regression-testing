for i in `seq 1 1000`;
do
    conda activate reference-env
    python single-molecule-comparison.py
    conda activate candidate-env
    python single-molecule-comparison.py
    python diff.py
    rm smiles.txt
done
