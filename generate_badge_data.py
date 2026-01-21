import json
import os
import polars as pl


def format_count(count: int) -> str:
    """Format count for badge display."""
    if count is None or count == 0:
        return "0"
    elif count < 1000:
        return str(int(count))
    elif count < 10000:
        return f"{count/1000:.1f}k"
    else:
        return f"{int(count/1000)}k"

def generate_badge_data(os_hits: pl.DataFrame | pl.LazyFrame):
    """Generate Shield.io endpoint files for each project."""
    print("Generating badge data...")

    # Get the most recent week's data
    latest_data = os_hits.sort('week_end').lazy().last().collect()

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
            "os_variants": ["Bluefin"],
            "color": "0066cc"
        },
        # centos countme data is broken, remove for now.
        # "bluefin-lts": {
        #     "name": "Bluefin LTS",
        #     "os_variants": ["Bluefin LTS"],
        #     "color": "67563e"
        # },
        "aurora": {
            "name": "Aurora",
            "os_variants": ["Aurora"],
            "color": "9b59b6"
        }
    }

    generated_projects = []

    for project_key, project_info in project_mappings.items():
        # Calculate total users for this project
        total_users = (
            latest_data
            .select(
                [variant for variant in project_info["os_variants"]]
            )
            .sum_horizontal()
            .item()
        )

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
