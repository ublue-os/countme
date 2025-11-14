#!/bin/bash

# Parse command line arguments
DOWNLOAD=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--download)
            DOWNLOAD=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [-d|--download]"
            echo "  -d, --download    Download the dataset (use this flag to re-download)"
            exit 1
            ;;
    esac
done

pip3 install -r requirements.txt

# Only download dataset if -d flag is provided
if [ "$DOWNLOAD" = true ]; then
    echo "Downloading dataset..."
    wget https://data-analysis.fedoraproject.org/csv-reports/countme/totals.csv
else
    echo "Skipping dataset download. Use -d flag to download fresh data."
fi

python3 countme.py
python3 generate_badge_data.py