for i in {1..10}
do
    echo "on i = $i ..."
    conda activate reference-env
    python serialize-condensed-phase-system.py $i
    conda deactivate
    conda activate candidate-env
    python serialize-condensed-phase-system.py $i
    python diff-condensed-phase-system.py $i
    conda deactivate
done
