import polars as pl
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
    "KDE":                  "Green",
    "CoreOS":               "Pink",
    "IoT":                  "Red"
}

#
# Load data
#

print("Loading data...")
START_DATE = datetime.datetime.now() - relativedelta(months=9)
END_DATE = datetime.datetime.now()

orig = (
    pl.scan_csv(
        "totals.csv",
        schema_overrides={
            "week_start": pl.Date,
            "week_end": pl.Date,
            "repo_tag": pl.Categorical,
            "os_version": pl.Categorical,
            "os_arch": pl.Categorical,
            "sys_age": pl.Categorical,
            "repo_arch": pl.Categorical,
        },
    )
    .filter(
        pl.col('sys_age') != pl.lit('-1'),
        # End of year partial week
        pl.col("week_end") != pl.lit("2024-12-29", dtype=pl.Date),
        # Fedora infrastructure migration; 40% drop
        pl.col("week_end") != pl.lit("2025-07-06", dtype=pl.Date),
        # Cut out old data
        pl.col('week_end') >= pl.lit(START_DATE),
    )
    .sort(
        pl.col('week_end')
    )
    .collect().lazy()
)

# Select fedora repos
fedora_repos_hits = (
    orig
    .filter(
        pl.col('repo_tag').is_in([*[f"fedora-{v}" for v in range(30, 45)]])
    )
)


fedora_atomic_desktops = [
    "Silverblue",
    "Kinoite",
]

universal_blue = [
    "Bluefin",
    "Bazzite",
    "Aurora",
    "uCore",
]

upstream_os = [
    "Workstation",
    "Server",
    "KDE",
    "CoreOS",
    "IoT",
]

global_os = universal_blue + fedora_atomic_desktops

upstream_os = upstream_os + fedora_atomic_desktops

fedora_linux_os_name_os_variants = (
    upstream_os +
    ["uCore"] # uCore uses Fedora Linux as os_name
)


# Dataframe with one row per week in time range, one column per OS
os_hits = pl.LazyFrame(orig.select(pl.col("week_end").unique()).collect())
# OSs with custom os_name
universal_blue_hits = (
    fedora_repos_hits
    .filter(
        pl.col('os_name').is_in(universal_blue),
    )
    .group_by(
        pl.col("week_end"),
        pl.col('os_name'),
    )
    .agg(
        pl.col("hits").sum()
    )
    .pivot(
        on='os_name',
        index='week_end',
        on_columns=universal_blue,
        values='hits'
    )
)

os_hits = (
    os_hits
    .join(
        other=universal_blue_hits,
        on="week_end",
        how="left",
    )
)

os_hits = os_hits.drop('uCore') # uCore has Fedora Linux as os_name. This solution isn't terribly elegant

# OSs with Fedora Linux as os_name
fedora_linux_os_name_os_variants_hits = (
    fedora_repos_hits
    .filter(
        pl.col('os_name') == pl.lit('Fedora Linux'),
        pl.col('os_variant').str.to_lowercase().is_in([x.lower() for x in fedora_linux_os_name_os_variants]),
    )
    .group_by(
        pl.col("week_end"),
        pl.col('os_variant'),
    )
    .agg(
        pl.col("hits").sum()
    )
    .pivot(
        on='os_variant',
        index='week_end',
        on_columns=[x.lower() for x in fedora_linux_os_name_os_variants],
        values='hits'
    )
    # Restore the original pretty names
    .rename(
        {x.lower(): x for x in fedora_linux_os_name_os_variants}
    )
)

os_hits = (
    os_hits
    .join(
        other=fedora_linux_os_name_os_variants_hits,
        on="week_end",
        how="left",
    )
)

# Bluefin LTS uses os_name and its data is not gathered from fedora repos
# It also used different names in the begining so those values need to be counted too
# Bluefin LTS hits by alt name
bluefin_lts_alt_name_hits = (
    orig
    .filter(pl.col("os_name").is_in(["Achillobator", "Bluefin LTS"]))
    .group_by("week_end")
    .agg(pl.col("hits").sum().alias('Bluefin LTS'))
)

os_hits = (
        os_hits
        .join(
            other=bluefin_lts_alt_name_hits,
            on="week_end",
            how="left",
        )
    )


os_hits = os_hits.collect()


# List of OSs ordered by most recent hits value
sorted_oss = (
    os_hits
    .lazy()
    .filter(
        pl.col('week_end') == pl.col('week_end').max(),
    )
    .unpivot()
    .sort(
        pl.col('value'),
        descending=True,
    )
    .drop_nulls()
    .select('variable')
    .collect()
    .to_series()
)


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
        os_latest_hits = (
            os_hits
            .filter(
                pl.col('week_end') == pl.col('week_end').max(),
            )
            .select(
                pl.col(os)
            )
            .item()
        )

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
                os_hits.select('week_end'),
                prev_hits,
                hits,
                color=color,
            )
            prev_hits = hits
        else:
            plt.plot(
                os_hits.select('week_end'),
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

    plt.title("Active Users (Weekly)", fontsize=20, fontweight='bold', color='black')
    plt.ylabel("Devices", fontsize=16, fontweight='bold')

    plt.xlim([START_DATE, END_DATE])

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m/%Y"))

    plt.xticks(rotation=45, fontsize=14, fontweight='bold')
    plt.yticks(fontsize=14, fontweight='bold')

    _, top = plt.ylim()
    plt.ylim(bottom=0)
    
    if top < 5000:
        plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos : f"{x / 1000:.1f}k"))
    else:
        plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(number_format))

    plt.tight_layout()

    plt.savefig(f"growth_{fig}.svg", dpi=80)
