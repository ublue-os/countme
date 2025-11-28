import pandas as pd
import numpy as np
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import datetime
from dateutil.relativedelta import relativedelta
from bokeh.palettes import Light

plt.style.use("default")
plt.style.use("./ublue.mplstyle")

colors = {
    "Bazzite":              "#6c3fc4",  # Purple
    "Bluefin":              Light[5][0],  # Blue
    "Silverblue":           Light[5][4],  # Light blue
    "Aurora":               Light[5][1],  # Orange
    "Kinoite":              Light[5][2],  # Light orange
    "Bluefin LTS":          Light[7][1],  # Orange
    "uCore":                Light[7][3],  # Sunset
    "Workstation":          "Blue",
    "Server":               "Orange",
    "KDE Plasma":           "Green",
    "CoreOS":               "Pink",
    "IoT":                  "Red"
}

#
# Load data
#

print("Loading data...")
# https://data-analysis.fedoraproject.org/csv-reports/countme/totals.csv
orig = pd.read_csv(
    "totals.csv",
    usecols=["week_end", "repo_tag", "os_variant", "hits", "os_name", "sys_age"],
    parse_dates=["week_end"],
    # low_memory=False,
    dtype={
        "repo_tag": "object",
        "os_variant": "category",
        "os_name": "category",
    },
)

orig = orig[
    orig["sys_age"] >= 1
]

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
    # Fedora infrastructure migration; 40% drop
    & (orig["week_end"] != pd.to_datetime("2025-07-06"))
    # & (fedora_repos_hits["week_end"] != pd.to_datetime("2023-10-23"))
]

START_DATE = datetime.datetime.now() - relativedelta(months=9)
END_DATE = datetime.datetime.now()

# Cut out old data
orig = orig[orig["week_end"] >= START_DATE]

# Select repos and filter outages
print("Plotting...")
fedora_repos_hits = orig[
    orig["repo_tag"].isin(
        [
            *[f"fedora-{v}" for v in range(30, 45)],
            # *[f"fedora-cisco-openh264-{v}" for v in range(40, 41)],
        ]
    )
]

global_os = [
    "Silverblue",
    "Kinoite",
    "Bluefin",
    "Bazzite",
    "Aurora",
    "uCore"
]

upstream_os = [
    "Silverblue",
    "Kinoite",
    "Workstation",
    "Server",
    "KDE Plasma",
    "CoreOS",
    "IoT"
]

complete_os = upstream_os + global_os

# Dataframe with one row per week in time range, one column per OS
os_hits = pd.DataFrame()
for os in complete_os:
    mask = fedora_repos_hits["os_variant"].str.lower().str.contains(os.lower(), na=False)
    res = fedora_repos_hits[mask].groupby("week_end")["hits"].sum()

    os_hits[os] = res

# LTS variants use os_name and are thus done separately and on data for all repos
# They also used different names in the begining so those values need to be counted too

# Bluefin LTS hits by alt name
bluefin_lts_alt_name_hits  = pd.DataFrame(index = os_hits.index)
for alt_name in ["Achillobator", "Bluefin LTS"]:
    mask = orig["os_name"] == alt_name
    res = orig[mask].groupby("week_end")["hits"].sum()

    bluefin_lts_alt_name_hits[alt_name] = res

os_hits["Bluefin LTS"] = bluefin_lts_alt_name_hits.sum(axis=1, min_count=1)

# Fedora KDE hits (other OS use kde too)
fedora_kde_hits = pd.DataFrame(index=os_hits.index)
for alt_name in ["Fedora Linux"]:
    mask = (fedora_repos_hits["os_name"] == alt_name) & (fedora_repos_hits["os_variant"] == "kde")
    res = fedora_repos_hits[mask].groupby("week_end")["hits"].sum()

    fedora_kde_hits[alt_name] = res

os_hits["KDE Plasma"] = fedora_kde_hits.sum(axis=1, min_count=1)


# List of OSs ordered by most recent hits value
sorted_oss = os_hits.iloc[[-1]].melt().sort_values(by='value', ascending=False)['variable'].tolist()

def number_format(x, pos):
    return f"{int(x / 1000)}k"

for fig, oss in [
    ("ublue", ["Bluefin", "Bazzite", "Aurora"]),
    ("nonbazzite", ["Bluefin", "Aurora"]),
    ("bazzite", ["Bazzite"]),
    ("bazzite_purple", ["Bazzite"]),
    ("global", global_os),
    ("upstream", upstream_os),
    ("bluefins", ["Bluefin"]),
    ("bluefins_dark", ["Bluefin"]),
    # ("bluefins_stacked", ["Bluefin", "Bluefin LTS"]),
    ("aurora", ["Aurora"]),
]:
    # Take sorted_oss and only use values in oss
    #  this gives you only the OSs you care about, but ordered by most recent hits value.
    #  This way you have a sorted legend
    oss = [os for os in sorted_oss if os in oss]

    stacked = fig.split('_')[-1] == 'stacked'

    plt.figure(figsize=(16, 9))
    cumsum = 0
    prev_hits = 0
    for os in oss:
        os_latest_hits = os_hits[os].loc[os_hits[os].index.max()]

        if fig == "bazzite_purple":
            color="#6c3fc4"
        else:
            color=colors[os]

        if stacked:
            cumsum = cumsum + os_hits[os]
            hits = cumsum
        else:
            hits = os_hits[os]

        if stacked:
            plt.fill_between(
                os_hits.index,
                prev_hits,
                hits,
                color=color,
            )
            prev_hits = hits
        else:
            plt.plot(
                os_hits.index,
                hits,
                # label=f"{os} ({os_latest_hits / 1000:.1f}k)",
                color=color,
            )

        # print(res)

    # Manually create legend to allow consistent legends with stacked charts
    # Reverse legend order if stakced
    if stacked:
        oss = oss[::-1]
    legend_lines = [
        Line2D([0], [0], color=colors[os]) for os in oss
    ]
    legend_labels = [
        f"{os} ({os_hits[os].loc[os_hits[os].index.max()] / 1000:.1f}k)" for os in oss # Add latest hits value to legend
    ]
    plt.legend(legend_lines, legend_labels, fontsize=16)

    plt.title("Active Users (Weekly)", fontsize=20, fontweight='bold', color='black')
    plt.ylabel("Devices", fontsize=16, fontweight='bold')

    plt.xlim([pd.to_datetime(START_DATE), pd.to_datetime(END_DATE)])

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))

    plt.xticks(rotation=45, fontsize=14, fontweight='bold')
    plt.yticks(fontsize=14, fontweight='bold')

    _, top = plt.ylim()
    plt.ylim(bottom=0)

    if fig == "bluefins_dark":
        plt.gcf().patch.set_facecolor("#0c1016")
        plt.gca().set_facecolor("#0c1016")
    
    if top < 5000:
        plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos : f"{x / 1000:.1f}k"))
    else:
        plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(number_format))

    plt.tight_layout()

    plt.savefig(f"growth_{fig}.svg", dpi=80)
