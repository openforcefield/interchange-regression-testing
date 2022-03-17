conda activate reference-env
python serialize-small-molecules.py
conda deactivate
conda activate candidate-env
python serialize-small-molecules.py
python diff-small-molecules.py
