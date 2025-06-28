# countme

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

## Badge System

This repository generates Shield.io compatible badge endpoints that display active user counts for Universal Blue projects. Add user count badges to your repository using these Shield.io endpoint URLs:

### Available Badges

- **Aurora**: ![Aurora Users](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ublue-os/countme/main/badge-endpoints/aurora.json)
- **Bazzite**: ![Bazzite Users](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ublue-os/countme/main/badge-endpoints/bazzite.json)
- **Bluefin**: ![Bluefin Users](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ublue-os/countme/main/badge-endpoints/bluefin.json)

### Markdown Code

Add these to your README.md:

```markdown
![Aurora Users](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ublue-os/countme/main/badge-endpoints/aurora.json)
![Bazzite Users](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ublue-os/countme/main/badge-endpoints/bazzite.json)
![Bluefin Users](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/ublue-os/countme/main/badge-endpoints/bluefin.json)
```

## Badge Data Format

The system generates Shield.io compatible endpoint files:
- `badge-endpoints/aurora.json`
- `badge-endpoints/bazzite.json`
- `badge-endpoints/bluefin.json`

Each file contains:
```json
{
  "schemaVersion": 1,
  "label": "Active Users",
  "message": "15.2k",
  "color": "6c3fc4",
  "namedLogo": "linux",
  "logoColor": "white"
}
```
