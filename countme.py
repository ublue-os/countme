import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from dateutil.relativedelta import relativedelta

plt.style.use("default")
plt.style.use("./ublue.mplstyle")

#
# Load data
#

print("Loading data...")
# https://data-analysis.fedoraproject.org/csv-reports/countme/totals.csv
orig = pd.read_csv(
    "totals.csv",
    usecols=["week_end", "repo_tag", "os_variant", "hits"],
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

d = d[
    # End of year partial week
    (d["week_end"] != pd.to_datetime("2024-12-29"))
    # & (d["week_end"] != pd.to_datetime("2023-10-23"))
]

START_DATE = datetime.datetime.now() - relativedelta(months=3)
END_DATE = datetime.datetime.now()

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
        plt.plot(res.index, res.values, label=f"{os} ({res[res.index.max()] / 1000:.1f}k)")  # type: ignore
        # print(res)

    plt.title("Active Devices per Week", fontsize=20, fontweight='bold')
    plt.xlabel("Week", fontsize=16, fontweight='bold')
    plt.ylabel("Hits", fontsize=16, fontweight='bold')

    plt.xlim([pd.to_datetime(START_DATE), pd.to_datetime(END_DATE)])

    plt.xticks(rotation=45, fontsize=14, fontweight='bold')
    plt.yticks(fontsize=14, fontweight='bold')

    plt.legend(fontsize=16, fontweight='bold')
    plt.tight_layout()

    plt.savefig(f"growth_{fig}.png", dpi=80)
