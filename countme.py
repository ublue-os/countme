import pandas as pd
import polars as pl
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
    "Aurora Helium (LTS)":  Light[7][5],  # Green
    "uCore":                Light[7][3],  # Sunset
    "Workstation":          "Blue",
    "Server":               "Orange",
    "KDE Plasma":           "Green",
    "CoreOS":               "Pink",
    "IoT":                  "Red"
}

def get_alt_name_hits(
        original_data: pl.LazyFrame | pl.DataFrame,
        alt_names: list[str],
        final_name: str,
    ) -> pl.LazyFrame:
    orig = original_data.lazy()

    alt_name_hits  = pl.LazyFrame(orig.select(pl.col("week_end").unique()).collect())
    for alt_name in alt_names:
        res = (
            orig
            .filter(
                pl.col("os_name") == pl.lit(alt_name)
            )
            .group_by(
                pl.col("week_end")
            )
            .agg(
                pl.col("hits").sum()
            )
            .select(
                pl.col("week_end"),
                pl.col("hits").alias(alt_name),
            )
        )

        alt_name_hits = (
            alt_name_hits
            .join(
                other=res,
                on="week_end",
                how="left",
            )
        )

    hits = (
        alt_name_hits
        .with_columns(
            pl.Series(
                alt_name_hits.collect()
                .drop("week_end")
                .to_pandas()
                .sum(axis=1, min_count=1) # Use pandas' sum since Polars' sum_horizontal() yields 0 even if summing all nulls
            )
            .alias("sum")
        )
        .select(
            pl.col("week_end"),
            pl.col("sum").alias(final_name),
        )
    )

    return hits

#
# Load data
#

print("Loading data...")
# https://data-analysis.fedoraproject.org/csv-reports/countme/totals.csv
orig = pl.scan_csv(
    "totals.csv",
    schema_overrides={
        "week_start": pl.Date,
        "week_end": pl.Date,
        # "repo_tag": pl.Categorical,
        # "os_name": pl.Categorical,
        # "os_variant": pl.Categorical,
        "os_version": pl.Categorical,
        "os_arch": pl.Categorical,
        "sys_age": pl.Categorical,
        "repo_arch": pl.Categorical,
    },
)

orig = orig.filter(
    pl.col("sys_age") != pl.lit("-1")
    # pl.col("sys_age") != pl.lit(-1)
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
orig = orig.filter(
    # End of year partial week
    pl.col("week_end") != pl.lit("2024-12-29", dtype=pl.Date),
    # Fedora infrastructure migration; 40% drop
    pl.col("week_end") != pl.lit("2025-07-06", dtype=pl.Date),
)

START_DATE = datetime.datetime.now() - relativedelta(months=9)
END_DATE = datetime.datetime.now()

# Cut out old data
orig = (
    orig
    .filter(
        pl.col("week_end") >= pl.lit(START_DATE, dtype=pl.Date)
    )
    .sort(
        pl.col("week_end")
    )
)

# Select repos and filter outages
d = (
    orig
    .filter(
        pl.col("repo_tag").str.contains_any(
            [
                *[f"fedora-{v}" for v in range(30, 45)],
            ]
        )
    )
)

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
os_hits = pl.LazyFrame(orig.select(pl.col("week_end").unique()).collect())
for os in set(complete_os): # Make it a set to remove duplicates
    res = (
        d
        .filter(
            pl.col("os_variant").str.contains_any([os], ascii_case_insensitive=True)
        )
        .group_by(
            pl.col("week_end")
        )
        .agg(
            pl.col("hits").sum()
        )
        .select(
            pl.col("week_end"),
            pl.col("hits").alias(os),
        )
    )

    os_hits = (
        os_hits
        .join(
            other=res,
            on="week_end",
            how="left",
        )
    )

# Drop KDE Plasma as it must be done separately
os_hits = os_hits.drop("KDE Plasma")

# LTS variants use os_name and are thus done separately and on data for all repos
# They also used different names in the begining so those values need to be counted too
aurora_lts_hits = get_alt_name_hits(
    orig,
    ["Aurora Helium (LTS)", "Aurora Helium", "Aurora LTS"],
    "Aurora Helium (LTS)",
)
os_hits = (
    os_hits
    .join(
        other=aurora_lts_hits,
        on="week_end",
        how="left",
    )
)

bluefin_lts_hits = get_alt_name_hits(
    orig,
    ["Achillobator", "Bluefin LTS"],
    "Bluefin LTS",
)
os_hits = (
    os_hits
    .join(
        other=bluefin_lts_hits,
        on="week_end",
        how="left",
    )
)

# Fedora KDE hits (other OS use kde too)
fedora_kde_hits = (
    orig
    .filter(
        pl.col("os_name") == pl.lit("Fedora Linux"),
        pl.col("os_variant") == pl.lit("kde"),
    )
    .group_by(
        pl.col("week_end")
    )
    .agg(
        pl.col("hits").sum()
    )
    .select(
        pl.col("week_end"),
        pl.col("hits").alias("KDE Plasma"),
    )
)
os_hits = (
    os_hits
    .join(
        other=fedora_kde_hits,
        on="week_end",
        how="left",
    )
)

# Ensure data is sorted by date
os_hits = os_hits.sort(pl.col("week_end"))

# Run one big collect now
os_hits = os_hits.collect()


# List of OSs ordered by most recent hits value
sorted_oss = (
    os_hits
    .drop("week_end")
    .tail(1)
    .unpivot(variable_name="os")
    .sort("value", descending=True)
    .select(pl.col("os"))
    .to_series()
    .to_list()
)

def number_format(x, pos):
    return f"{int(x / 1000)}k"

print("Plotting...")
for fig, oss in [
    ("ublue", ["Bluefin", "Bazzite", "Aurora"]),
    ("nonbazzite", ["Bluefin", "Aurora"]),
    ("bazzite", ["Bazzite"]),
    ("bazzite_purple", ["Bazzite"]),
    ("global", global_os),
    ("upstream", upstream_os),
    ("ublue_lts", ["Bluefin", "Bluefin LTS", "Aurora", "Aurora Helium (LTS)"]),
    ("bluefins", ["Bluefin", "Bluefin LTS"]),
    ("bluefins_stacked", ["Bluefin", "Bluefin LTS"]),
    ("auroras", ["Aurora", "Aurora Helium (LTS)"]),
]:
    # Take sorted_oss and only use values in oss
    #  this gives you only the OSs you care about, but ordered by most recent hits value.
    #  This way you have a sorted legend
    oss = [os for os in sorted_oss if os in oss]

    stacked = fig.split("_")[-1] == "stacked"

    plt.figure(figsize=(16, 9))
    cumsum = 0
    prev_hits = 0
    for os in oss:
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
                os_hits["week_end"],
                prev_hits,
                hits,
                color=color,
            )
            prev_hits = hits
        else:
            plt.plot(
                os_hits["week_end"],
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
        f"{os} ({os_hits.select(pl.col(os)).drop_nulls().tail(1).item() / 1000:.1f}k)" for os in oss # Add latest hits value to legend
    ]
    plt.legend(legend_lines, legend_labels, fontsize=16)

    plt.title("Active Users (Weekly)", fontsize=20, fontweight="bold", color="black")
    plt.ylabel("Devices", fontsize=16, fontweight="bold")

    plt.xlim([pd.to_datetime(START_DATE), pd.to_datetime(END_DATE)])

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))

    plt.xticks(rotation=45, fontsize=14, fontweight="bold")
    plt.yticks(fontsize=14, fontweight="bold")

    _, top = plt.ylim()
    plt.ylim(bottom=0)
    
    if top < 5000:
        plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos : f"{x / 1000:.1f}k"))
    else:
        plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(number_format))

    plt.tight_layout()

    plt.savefig(f"growth_{fig}.svg", dpi=80)
