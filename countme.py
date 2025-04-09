import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import datetime
from dateutil.relativedelta import relativedelta
from bokeh.palettes import Light

plt.style.use("default")
plt.style.use("./ublue.mplstyle")

colors = {
    'Bazzite' :    Light[5][3], # Pink
    'Bluefin' :    Light[5][0], # Blue
    'Silverblue' : Light[5][4], # Light blue
    'Aurora' :     Light[5][1], # Orange
    'Kinoite' :    Light[5][2], # Light orange
}

#
# Load data
#

print("Loading data...")
# https://data-analysis.fedoraproject.org/csv-reports/countme/totals.csv
orig = pd.read_csv(
    "totals.csv",
    usecols=["week_end", "repo_tag", "os_variant", "hits", "os_name"],
    parse_dates=["week_end"],
    # low_memory=False,
    dtype={
        "repo_tag": "object",
        "os_variant": "category",
    },
)

# # Detailed data
# orig = pd.read_csv(
#     "totals.csv",
#     parse_dates=["week_start", "week_end"],
#     # low_memory=False,
#     dtype={
#         "repo_tag": "object",
#         "repo_arch": "object",
#         "os_name": "category",
#         "os_version": "category",
#         "os_variant": "category",
#         "os_arch": "category",
#     },
# )

# Filter bad dates
orig = orig[
    # End of year partial week
    (orig["week_end"] != pd.to_datetime("2024-12-29"))
    # & (d["week_end"] != pd.to_datetime("2023-10-23"))
]

# Select repos and filter outages
print("Plotting...")
d = orig[
    orig["repo_tag"].isin(
        [
            *[f"fedora-{v}" for v in range(30, 45)],
            # *[f"fedora-cisco-openh264-{v}" for v in range(40, 41)],
        ]
    )
]

START_DATE = datetime.datetime.now() - relativedelta(months=9)
END_DATE = datetime.datetime.now()

def number_format(x, pos):
    return f"{int(x / 1000)}k"

for fig, oss in [
    ("ublue", ["Bluefin", "Bazzite", "Aurora"]),
    ("nonbazzite", ["Bluefin", "Aurora"]),
    ("bazzite", ["Bazzite"]),
    ("global", ["Silverblue", "Kinoite", "Bluefin", "Bazzite", "Aurora"]),
]:
    
    plt.figure(figsize=(16, 9))
    for os in oss:
        mask = d["os_variant"].str.lower().str.contains(os.lower(), na=False)
        res = d[mask].groupby("week_end")["hits"].sum()
        plt.plot(
            res.index,
            res.values,
            label=f"{os} ({res[res.index.max()] / 1000:.1f}k)",
            color=colors[os],
        )  # type: ignore
        # print(res)

    plt.title("Active Users (Weekly)", fontsize=20, fontweight='bold', color='black')
    plt.ylabel("Devices", fontsize=16, fontweight='bold')

    plt.xlim([pd.to_datetime(START_DATE), pd.to_datetime(END_DATE)])

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))

    plt.xticks(rotation=45, fontsize=14, fontweight='bold')
    plt.yticks(fontsize=14, fontweight='bold')

    plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(number_format))

    plt.legend(fontsize=16)
    plt.tight_layout()

    plt.savefig(f"growth_{fig}.svg", dpi=80)
