# countme
countme 


## How to run locally

```
git clone https://github.com/ublue-os/countme
cd countme
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./graph.sh
```

Comment out `wget` line on graph.sh after first run if you don't want to re-download dataset every time (only changes once per day).