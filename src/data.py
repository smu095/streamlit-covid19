import pathlib
from typing import List, Tuple

import janitor
import numpy as np
import pandas as pd
import streamlit as st

from src.scrape import check_for_new_data

_ = check_for_new_data()

PATH = pathlib.Path("data/")
US_DATA = PATH.joinpath("cases.csv")
CASES_WORLDWIDE = PATH.joinpath("cases_country.csv")
TIME_SERIES = PATH.joinpath("cases_time.csv")


def _to_date(x: pd.Series) -> pd.Series:
    """Return normalised DateTime series."""
    return pd.to_datetime(x).normalize()


@st.cache(show_spinner=False)
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


@st.cache(show_spinner=False)
def get_most_affected(world_source: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Return DataFrame of top n most affected countries (as measured by number
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


@st.cache(show_spinner=False)
def _get_worldwide_cases(csv: pathlib.Path = CASES_WORLDWIDE) -> pd.DataFrame:
    """Return DataFrame of most recent worldwide cumulative infection data."""
    # Read and perform basic cleaning
    cases = pd.read_csv(csv)
    cleaned = (
        cases.clean_names()
        .rename_column("long_", "lon")
        .rename_column("last_update", "date")
        .transform_column("date", _to_date)
        .sort_values(by="country_region")
    )

    # Remove rows that are not countries
    worldwide = cleaned[~cleaned["iso3"].isna()]

    # Infer population
    worldwide["population"] = worldwide["confirmed"] / (
        worldwide["incident_rate"] / 10 ** 5
    )

    return worldwide


def _get_us_cases(time_source: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame of aggregated US cases."""
    us = time_source.filter_on("country_region == 'US'")
    population = us["population"].mean()
    cols = list(us.columns)
    grouped = us.groupby("date")

    # Aggregate state-level information
    sum_cols = [
        "confirmed",
        "deaths",
        "recovered",
        "active",
        "delta_confirmed",
        "delta_recovered",
        "people_tested",
        "people_hospitalized",
    ]
    max_cols = ["report_date"]
    agg_df = pd.concat(
        (grouped[sum_cols].sum(), grouped[max_cols].max()), axis=1
    ).reset_index()

    # Replace columns lost in aggregation
    agg_df["country_region"] = "US"
    agg_df["population"] = population
    agg_df["uid"] = 840
    agg_df["iso3"] = "USA"
    agg_df["incident_rate"] = (agg_df["confirmed"] / agg_df["population"]) * 10 ** 5

    # Return columns in correct order
    us_data = agg_df[cols]

    return us_data


@st.cache(show_spinner=False)
def get_time_series_cases(csv: pathlib.Path = TIME_SERIES) -> pd.DataFrame:
    """Return time-series data of worldwide infections."""
    time_series = pd.read_csv(csv)
    cleaned = (
        time_series.clean_names()
        .rename_column("report_date_string", "report_date")
        .rename_column("last_update", "date")
        .transform_columns(["date", "report_date"], _to_date)
        .remove_columns(["fips", "province_state"])
    )

    # Remove rows that are not countries
    cleaned = cleaned[~cleaned["iso3"].isna()]

    # Get population data
    worldwide = _get_worldwide_cases()
    cleaned = cleaned.merge(worldwide[["iso3", "population"]], how="left", on="iso3")

    # Aggregate US data
    us_cases = _get_us_cases(cleaned)
    world = cleaned.filter_on("country_region == 'US'", complement=True)
    time_series = pd.concat((world, us_cases), axis=0)
    time_series = time_series.sort_values(by=["country_region", "date"]).reset_index(
        drop=True
    )

    # Adding columns: scaled_confirmed, delta_deaths, log_confirmed, log_delta_confirmed, mortality_rate, delta_pr_100k
    time_series["scaled_confirmed"] = time_series.groupby("country_region")[
        "confirmed"
    ].transform(lambda x: (x - x.min()) / (x.max() - x.min()))
    time_series["delta_deaths"] = time_series.groupby("country_region")[
        "deaths"
    ].transform(lambda x: x.diff(1).fillna(0))
    time_series["log_confirmed"] = np.where(
        time_series["confirmed"] >= 1,
        np.log(time_series["confirmed"]),
        time_series["confirmed"],
    )
    time_series["log_delta_confirmed"] = np.where(
        time_series["delta_confirmed"] >= 1,
        np.log(time_series["delta_confirmed"]),
        time_series["delta_confirmed"],
    )
    time_series["mortality_rate"] = (
        time_series["deaths"] / time_series["population"]
    ) * 10 ** 5
    time_series["delta_pr_100k"] = (
        time_series["delta_confirmed"] / time_series["population"]
    ) * 10 ** 5

    return time_series


@st.cache(show_spinner=False)
def get_world_source(delta_confirmed: pd.DataFrame) -> pd.DataFrame:
    # TODO: Write docstring
    """[summary]

    Parameters
    ----------
    delta_confirmed : pd.DataFrame
        [description]

    Returns
    -------
    pd.DataFrame
        [description]
    """
    worldwide = _get_worldwide_cases()
    world_source = worldwide.merge(
        delta_confirmed[["delta_confirmed", "country_region"]],
        on="country_region",
        how="left",
    )
    world_source["delta_pr_100k"] = (
        world_source["delta_confirmed"] / world_source["population"]
    ) * 10 ** 5
    return world_source


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
    country_summary = world_source[
        world_source["country_region"] == country
    ].select_columns(
        [
            "country_region",
            "date",
            "population",
            "confirmed",
            "deaths",
            "incident_rate",
        ]
    )
    return country_summary


def get_interval_data(
    country_data: pd.DataFrame, start: pd.DatetimeIndex, end: pd.DatetimeIndex
) -> pd.DataFrame:
    # TODO: Write docstring
    """[summary]

    Parameters
    ----------
    country_data : pd.DataFrame
        [description]
    start : pd.DatetimeIndex
        [description]
    end : pd.DatetimeIndex
        [description]

    Returns
    -------
    pd.DataFrame
        [description]
    """
    date_mask = (country_data["date"].dt.date >= start) & (
        country_data["date"].dt.date <= end
    )
    return country_data[date_mask]


def get_weekly_avg(time_source: pd.DataFrame, countries: List[str]) -> pd.DataFrame:
    """[summary]

    Parameters
    ----------
    time_source : pd.DataFrame
        [description]
    countries : List[str]
        [description]

    Returns
    -------
    pd.DataFrame
        [description]
    """
    # TODO: Write docstring
    # TODO: Refactor to use original scale, but use scale="log" in alt.Chart?
    weekly_avg = (
        time_source[time_source["country_region"].isin(countries)]
        .set_index("date")
        .filter_on("country_region == 'Guyana'", complement=True)
        .groupby("country_region")
        .resample("W")
        .agg({"log_confirmed": "max", "log_delta_confirmed": "mean"})
        .reset_index()
    )
    return weekly_avg


@st.cache(show_spinner=False)
def _get_trajectory_data(time_source: pd.DataFrame) -> pd.DataFrame:
    """[summary]

    Parameters
    ----------
    time_source : pd.DataFrame
        [description]

    Returns
    -------
    pd.DataFrame
        [description]
    """
    # TODO: Write docstring
    top_10 = (
        time_source[time_source["date"] == time_source["date"].max()]
        .sort_values(by="confirmed")["country_region"]
        .tail(10)
    )
    time_source_top_10 = time_source[time_source["country_region"].isin(top_10)]
    time_source_top_10["week"] = time_source_top_10["date"].dt.week

    return time_source_top_10
