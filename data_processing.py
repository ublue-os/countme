import datetime
from dateutil.relativedelta import relativedelta
import polars as pl


def _load_and_process_data(
    months: int = 9,
) -> tuple[pl.LazyFrame, pl.LazyFrame]:
    """
    Reads data from `totals.csv` and extracts two LazyFrames:
        - `fedora_repos_hits`: Contains data for Fedora repositories.
        - `orig`: Contains data for all repositories.
    """
    START_DATE = datetime.datetime.now() - relativedelta(months=months)

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
            pl.col("sys_age") != pl.lit("-1"),
            # End of year partial week
            pl.col("week_end") != pl.lit("2024-12-29", dtype=pl.Date),
            # Fedora infrastructure migration; 40% drop
            pl.col("week_end") != pl.lit("2025-07-06", dtype=pl.Date),
            # Cut out old data
            pl.col("week_end") >= pl.lit(START_DATE),
        )
        .sort(
            pl.col("week_end")
        )
        .collect().lazy()
    )

    # Select fedora repos
    fedora_repos_hits = (
        orig
        .filter(
            pl.col("repo_tag").is_in([*[f"fedora-{v}" for v in range(30, 45)]])
        )
    )

    return fedora_repos_hits, orig


def calculate_os_hits(
    months: int = 9,
) -> pl.DataFrame:
    """
    Get weekly hits for OSs.
    
    :return: A DataFrame containing one row for each week in the data,
        with one colum per OS containing its hits in the given week
    :rtype: DataFrame
    """
    fedora_repos_hits, orig = _load_and_process_data(months)


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
            pl.col("os_name").is_in(universal_blue),
        )
        .group_by(
            pl.col("week_end"),
            pl.col("os_name"),
        )
        .agg(
            pl.col("hits").sum()
        )
        .pivot(
            on="os_name",
            index="week_end",
            on_columns=universal_blue,
            values="hits"
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

    os_hits = os_hits.drop("uCore") # uCore has Fedora Linux as os_name. This solution isn't terribly elegant

    # OSs with Fedora Linux as os_name
    fedora_linux_os_name_os_variants_hits = (
        fedora_repos_hits
        .filter(
            pl.col("os_name") == pl.lit("Fedora Linux"),
            pl.col("os_variant").str.to_lowercase().is_in([x.lower() for x in fedora_linux_os_name_os_variants]),
        )
        .group_by(
            pl.col("week_end"),
            pl.col("os_variant"),
        )
        .agg(
            pl.col("hits").sum()
        )
        .pivot(
            on="os_variant",
            index="week_end",
            on_columns=[x.lower() for x in fedora_linux_os_name_os_variants],
            values="hits"
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
        .agg(pl.col("hits").sum().alias("Bluefin LTS"))
    )
    os_hits = (
            os_hits
            .join(
                other=bluefin_lts_alt_name_hits,
                on="week_end",
                how="left",
            )
        )

    return os_hits.collect()
