#!/bin/bash

pip3 install -r requirements.txt

wget https://data-analysis.fedoraproject.org/csv-reports/countme/totals.csv

python3 countme.py