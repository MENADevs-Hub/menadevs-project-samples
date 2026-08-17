#!/bin/bash
pip3 install --break-system-packages pytest==8.4.1 pytest-json-ctrf==0.3.5
mkdir -p /logs/verifier
pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA -v
python3 /tests/compute_score.py /logs/verifier/ctrf.json /logs/verifier/reward.txt
exit 0
