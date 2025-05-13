# countme
countme 


## How to run locally

```
git clone https://github.com/u-blue/countme
cd countme
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./graph.sh
```

Comment out `wget` line on graph.sh after first run if you don't want to re-download dataset every time (only changes once per day).