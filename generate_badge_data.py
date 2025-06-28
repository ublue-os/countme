import pandas as pd
import numpy as np
import json
import datetime
import os
from dateutil.relativedelta import relativedelta

def load_and_process_data():
    orig = pd.read_csv(
        "totals.csv",
        usecols=["week_end", "repo_tag", "os_variant", "hits", "os_name", "sys_age"],
        parse_dates=["week_end"],
        dtype={
            "repo_tag": "object",
            "os_variant": "category",
            "os_name": "category",
        },
    )

    # Filter for systems older than 1 week (active users)
    orig = orig[orig["sys_age"] >= 1]

    # Filter bad dates
    orig = orig[
        (orig["week_end"] != pd.to_datetime("2024-12-29"))
    ]

    # Get recent data (last 9 months)
    START_DATE = datetime.datetime.now() - relativedelta(months=9)
    orig = orig[orig["week_end"] >= START_DATE]

    # Filter for Fedora repos
    d = orig[
        orig["repo_tag"].isin([f"fedora-{v}" for v in range(30, 45)])
    ]

    return d, orig

def calculate_os_hits(d, orig):
    """Calculate hits for each OS."""
    os_list = [
        "Silverblue", "Kinoite", "Bluefin", "Bazzite", "Aurora", "uCore",
        "Workstation", "Server", "KDE Plasma", "CoreOS", "IoT"
    ]

    # Create dataframe with one row per week, one column per OS
    os_hits = pd.DataFrame()

    for os in os_list:
        mask = d["os_variant"].str.lower().str.contains(os.lower(), na=False)
        res = d[mask].groupby("week_end")["hits"].sum()
        os_hits[os] = res

    # Handle LTS variants separately using os_name

    # Aurora LTS hits
    aurora_lts_alt_name_hits = pd.DataFrame(index=os_hits.index)
    for alt_name in ["Aurora Helium (LTS)", "Aurora Helium", "Aurora LTS"]:
        mask = orig["os_name"] == alt_name
        res = orig[mask].groupby("week_end")["hits"].sum()
        aurora_lts_alt_name_hits[alt_name] = res

    os_hits["Aurora Helium (LTS)"] = aurora_lts_alt_name_hits.sum(axis=1, min_count=1)

    # Bluefin LTS hits
    bluefin_lts_alt_name_hits = pd.DataFrame(index=os_hits.index)
    for alt_name in ["Achillobator", "Bluefin LTS"]:
        mask = orig["os_name"] == alt_name
        res = orig[mask].groupby("week_end")["hits"].sum()
        bluefin_lts_alt_name_hits[alt_name] = res

    os_hits["Bluefin LTS"] = bluefin_lts_alt_name_hits.sum(axis=1, min_count=1)

    # Fedora KDE hits
    fedora_kde_hits = pd.DataFrame(index=os_hits.index)
    for alt_name in ["Fedora Linux"]:
        mask = (orig["os_name"] == alt_name) & (orig["os_variant"] == "kde")
        res = orig[mask].groupby("week_end")["hits"].sum()
        fedora_kde_hits[alt_name] = res

    os_hits["KDE Plasma"] = fedora_kde_hits.sum(axis=1, min_count=1)

    return os_hits

def format_count(count):
    """Format count for badge display."""
    if pd.isna(count) or count == 0:
        return "0"
    elif count < 1000:
        return str(int(count))
    elif count < 10000:
        return f"{count/1000:.1f}k"
    else:
        return f"{int(count/1000)}k"

def generate_badge_data(os_hits):
    """Generate Shield.io endpoint files for each project."""
    print("Generating badge data...")

    # Get the most recent week's data
    latest_data = os_hits.iloc[-1]

    # Create badge-endpoints directory
    os.makedirs("badge-endpoints", exist_ok=True)

    # Define project mappings
    project_mappings = {
        "bazzite": {
            "name": "Bazzite",
            "os_variants": ["Bazzite"],
            "color": "6c3fc4"
        },
        "bluefin": {
            "name": "Bluefin",
            "os_variants": ["Bluefin", "Bluefin LTS"],
            "color": "0066cc"
        },
        "aurora": {
            "name": "Aurora",
            "os_variants": ["Aurora", "Aurora Helium (LTS)"],
            "color": "9b59b6"
        }
    }

    generated_projects = []

    for project_key, project_info in project_mappings.items():
        # Calculate total users for this project
        total_users = 0
        for variant in project_info["os_variants"]:
            if variant in latest_data and not pd.isna(latest_data[variant]):
                total_users += latest_data[variant]

        # Format user count for display
        users_formatted = format_count(total_users)

        # Create Shield.io endpoint data
        endpoint_data = {
            "schemaVersion": 1,
            "label": "Active Users",
            "message": users_formatted,
            "color": project_info["color"],
            "namedLogo": "linux",
            "logoColor": "white"
        }

        # Write endpoint file
        with open(f"badge-endpoints/{project_key}.json", "w") as f:
            json.dump(endpoint_data, f, indent=2)

        generated_projects.append({
            "name": project_info["name"],
            "users_formatted": users_formatted,
            "file": f"{project_key}.json"
        })

        print(f"Generated endpoint for {project_info['name']}: {users_formatted} users")

    return generated_projects

def main():
        d, orig = load_and_process_data()
        os_hits = calculate_os_hits(d, orig)

        generated_projects = generate_badge_data(os_hits)

        print(f"Generated {len(generated_projects)} project badges:")

        for project in generated_projects:
            print(f"  {project['name']}: {project['users_formatted']} users -> {project['file']}")


if __name__ == "__main__":
    main()
