import polars as pl
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import datetime
from dateutil.relativedelta import relativedelta
from bokeh.palettes import Light

from data_processing import os_groups


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

def generate_graphs(
    os_hits: pl.DataFrame,
    months: int = 9,
):
    START_DATE = datetime.datetime.now() - relativedelta(months=months)
    END_DATE = datetime.datetime.now()


    global_os = os_groups["universal_blue"] + os_groups["fedora_atomic_desktops"]


    # List of OSs ordered by most recent hits value
    sorted_oss = (
        os_hits
        .lazy()
        .filter(
            pl.col("week_end") == pl.col("week_end").max(),
        )
        .drop('week_end')
        .unpivot()
        .sort(
            pl.col("value"),
            descending=True,
        )
        .drop_nulls()
        .select("variable")
        .collect()
        .to_series()
    )


    def number_format(x, pos):
        return f"{int(x / 1000)}k"

    print("Plotting")
    for fig, oss in [
        ("ublue", ["Bluefin", "Bazzite", "Aurora"]),
        ("nonbazzite", ["Bluefin", "Aurora"]),
        ("bazzite", ["Bazzite"]),
        ("bazzite_purple", ["Bazzite"]),
        ("global", global_os),
        ("upstream", os_groups["upstream_os"]),
        ("bluefins", ["Bluefin"]),
        # ("bluefins_stacked", ["Bluefin", "Bluefin LTS"]),
        ("aurora", ["Aurora"]),
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
            os_latest_hits = (
                os_hits
                .filter(
                    pl.col("week_end") == pl.col("week_end").max(),
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
                    os_hits.select("week_end"),
                    prev_hits,
                    hits,
                    color=color,
                )
                prev_hits = hits
            else:
                plt.plot(
                    os_hits.select("week_end"),
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

        plt.xlim([START_DATE, END_DATE])

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
