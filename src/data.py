from typing import List, Tuple, Union

import janitor
import numpy as np
import pandas as pd

US_DATA = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases.csv"  # noqa: E501
CASES_WORLDWIDE = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases_country.csv"  # noqa: E501
TIME_SERIES = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases_time.csv"  # noqa: 501

# NOTE: Manually add extra dot when compiling docs. Temporary solution.
POP_DATA = "./data/worldbank-population-2018.csv"
ISO_DATA = "./data/iso-codes.csv"


def _get_world_population(path: str = POP_DATA) -> pd.DataFrame:
    """Return DataFrame of world population."""
    pop = pd.read_csv(path).rename_column("2018", "population")
    return pop


WORLD_POP = _get_world_population()


def _get_iso_codes(path: str = ISO_DATA) -> pd.DataFrame:
    """Return DataFrame of ISO 3166-1 country codes."""
    iso_codes = pd.read_csv(path)
    to_rename = {
        "Russian Federation": "Russia",
        "Bolivia (Plurinational State of)": "Bolivia",
        "Korea, Republic of": "Korea, South",
        "Brunei Darussalam": "Brunei",
        "Moldova, Republic of": "Moldova",
        "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
        "Syrian Arab Republic": "Syria",
        "Venezuela (Bolivarian Republic of)": "Venezuela",
        "Tanzania, United Republic of": "Tanzania",
        "Iran (Islamic Republic of)": "Iran",
        "Côte d'Ivoire": "Cote d'Ivoire",
        "Myanmar": "Burma",
        "Congo": "Congo (Brazzaville)",
        "Congo, Democratic Republic of the": "Congo (Kinshasa)",
        "Lao People's Democratic Republic": "Laos",
        "Taiwan, Province of China": "Taiwan*",
        "United States of America": "US",
        "Viet Nam": "Vietnam",
        "Palestine, State of": "West Bank and Gaza",
    }
    iso_codes["country_region"] = iso_codes["country_region"].replace(to_rename)
    return iso_codes


ISO_CODES = _get_iso_codes()


def _to_date(x: pd.Series) -> pd.Series:
    """Return normalised DateTime series."""
    return pd.to_datetime(x).normalize()


def get_most_affected(world_source: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Return DataFrame of top n most affected countries (as measued by number
    of confirmed cases).

    Note that the data is returned in tidy format.

    Parameters
    ----------
    world_source : pd.DataFrame
        DataFrame resulting from `_get_worldwide_cases()`.
    n : int, optional
        Number of countries to include, by default 10

    Returns
    -------
    melted : pd.DataFrame
        DataFrame of top `n` most affected countries.
    """
    most_affected = (
        world_source.sort_values(by="confirmed", ascending=False)
        .head(10)
        .select_columns(
            ["country_region", "confirmed", "active", "recovered", "deaths"]
        )
    )
    most_affected["active"] = np.where(
        most_affected[["confirmed", "deaths", "recovered"]].sum(axis=1)
        != most_affected["confirmed"],
        most_affected["confirmed"] - most_affected[["deaths", "recovered"]].sum(axis=1),
        most_affected["active"],
    )
    melted = most_affected.remove_columns("confirmed").melt(
        id_vars="country_region", var_name="status", value_name="count"
    )
    return melted


def get_country_data(time_source: pd.DataFrame, country: str) -> Tuple:
    """
    Return DataFrame of worldwide time-series statistics on confirmed cases, deaths,
    recovered, etc. for a given country.

    Parameters
    ----------
    time_source : pd.DataFrame
        DataFrame resulting from `_get_time_series_cases()`.
    country : str
        Country name.

    Returns
    -------
    time_data, first_case, last_update : Tuple
        Tuple consisting of `time_data` (DataFrame), first_case (Timestamp) and last_update (Timestamp)
    """
    time_data = time_source[time_source["country_region"] == country]

    first_case = time_data.loc[time_data["confirmed"] > 0, "date"].min()
    last_update = time_data["date"].max()

    return time_data, first_case, last_update


def _get_us_cases(url: str = US_DATA) -> pd.DataFrame:
    """Return DataFrame of US most recent cumulative infection data."""
    cases = pd.read_csv(url)
    cleaned = (
        cases.clean_names()
        .transform_column("last_update", _to_date)
        .filter_on("country_region == 'US'")
    )
    return cleaned


def _get_worldwide_cases(url: str = CASES_WORLDWIDE) -> pd.DataFrame:
    """Return DataFrame of most recent worldwide cumulative infection data."""
    cases = pd.read_csv(url)
    cleaned = (
        cases.clean_names()
        .rename_column("long_", "lon")
        .transform_column("last_update", _to_date)
        .filter_on("country_region == 'Diamond Princess'", complement=True)
        .filter_on("country_region == 'Holy See'", complement=True)
        .sort_values(by="country_region")
    )

    iso_join = cleaned.merge(ISO_CODES, on="country_region")
    pop_join = iso_join.merge(WORLD_POP, on="country_region")

    pop_join["sick_pr_100k"] = (
        pop_join["confirmed"] / pop_join["population"]
    ) * 10 ** 5
    pop_join["deaths_pr_100k"] = (pop_join["deaths"] / pop_join["population"]) * 10 ** 5

    return pop_join


def _get_time_series_cases(url: str = TIME_SERIES) -> pd.DataFrame:
    """Return time-series data of worldwide infections."""
    time_series = pd.read_csv(url)
    cleaned = (
        time_series.clean_names()
        .rename_column("last_update", "date")
        .transform_column("date", _to_date)
        .remove_columns(["recovered", "active", "delta_recovered"])
    )

    # Adding columns: delta_deaths, log_confirmed, log_delta_confirmed, days
    cleaned["delta_deaths"] = cleaned.groupby("country_region")["deaths"].transform(
        lambda x: x.diff(1).fillna(0)
    )
    cleaned["log_confirmed"] = np.where(
        cleaned["confirmed"] >= 1, np.log(cleaned["confirmed"]), cleaned["confirmed"]
    )
    cleaned["log_delta_confirmed"] = np.where(
        cleaned["delta_confirmed"] >= 1,
        np.log(cleaned["delta_confirmed"]),
        cleaned["delta_confirmed"],
    )

    # Merging population data
    pop_join = cleaned.merge(WORLD_POP, how="left", on="country_region")

    # Adding columns: sick_pr_100k, std_confirmed (std. dev.), norm_confirmed (normalised)
    pop_join["sick_pr_100k"] = (
        pop_join["confirmed"] / pop_join["population"]
    ) * 10 ** 5
    pop_join["std_confirmed"] = pop_join.groupby("country_region")["confirmed"].apply(
        lambda x: (x - x.mean()) / x.std()
    )
    pop_join["norm_confirmed"] = pop_join.groupby("country_region")["confirmed"].apply(
        lambda x: x / x.max()
    )

    unique_countries = tuple(pop_join["country_region"].unique())

    return pop_join, unique_countries


def get_delta_confirmed(time_source: pd.DataFrame) -> pd.DataFrame:
    """
    Return DataFrame of most recent delta confirmed (i.e. change in number) of
    confirmed cases compared to previous day.

    Parameters
    ----------
    time_source : pd.DataFrame
        DataFrame returned from `_get_time_series_cases()`.

    Returns
    -------
    delta_confirmed : pd.DateFrame
        DataFrame of most recent delta confirmed by country.
    """
    delta_confirmed = time_source.loc[
        time_source.groupby("country_region")["date"].idxmax(),
        ["country_region", "date", "delta_confirmed"],
    ].reset_index(drop=True)
    return delta_confirmed


def get_country_summary(world_source: pd.DataFrame, country: str) -> pd.DataFrame:
    """Return DataFrame with summary statistics for a given country.

    Parameters
    ----------
    world_source : pd.DataFrame
        DataFrame returned from `_get_worldwide_cases()`.
    country : str
        Country to summarise.

    Returns
    -------
    country_summary : pd.DataFrame
    """
    country_summary = (
        world_source[world_source["country_region"] == country]
        .remove_columns(["lat", "lon", "id", "date"])
        .select_columns(
            [
                "country_region",
                "population",
                "confirmed",
                "delta_confirmed",
                "deaths",
                "recovered",
                "active",
                "sick_pr_100k",
                "delta_pr_100k",
                "deaths_pr_100k",
            ]
        )
        .set_index("country_region")
    )
    return country_summary
