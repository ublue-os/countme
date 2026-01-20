from countme import generate_graphs
import data_processing
from generate_badge_data import generate_badge_data


print("Processing data")
os_hits = data_processing.calculate_os_hits()


print("Generating badge data")
generated_projects = generate_badge_data(os_hits)

print(f"Generated {len(generated_projects)} project badges:")

for project in generated_projects:
    print(f"  {project['name']}: {project['users_formatted']} users -> {project['file']}")


print("Generating graphs")
generate_graphs(os_hits)
