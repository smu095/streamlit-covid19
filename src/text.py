import pathlib
from typing import Dict

import pandas as pd
import streamlit as st

PATH = pathlib.Path("templates/")
COUNTRY_TEXT = PATH.joinpath("country_text_template.md")
WORLD_TEXT = PATH.joinpath("world_text_template.md")
INFECTION_TEXT = PATH.joinpath("heatmap_text_template.md")

with COUNTRY_TEXT.open(mode="r") as file:
    COUNTRY_TEMPLATE = file.read()
with WORLD_TEXT.open(mode="r") as file:
    WORLD_TEMPLATE = file.read()


def create_heatmap_text() -> str:
    """Return text intro to Infection heatmap page."""
    with INFECTION_TEXT.open(mode="r") as file:
        infection_template = file.read()
    return infection_template


def create_country_text_intro(world_source: pd.DataFrame, country: str) -> str:
    # TODO: See if there is a better way to format string
    """Return string containing text introductions for use in individual country pages.

    The text is built from a standardised Markdown-file using summary statistics from the data
    to generate a brief introduction to each country.

    Parameters
    ----------
    world_source : pd.DataFrame
        Global summary infection data, resulting from `get_world_source`.

    Returns
    -------
    text_intro : str
        Brief country-specific text introducing summary statistics.
    """
    country_df = world_source[world_source["country_region"] == country]
    text_intro = COUNTRY_TEMPLATE.format(
        last_update=country_df["date"].dt.strftime("%A %B %d, %Y").values[0],
        country_region=country_df["country_region"].values[0],
        confirmed=country_df["confirmed"].values[0],
        population=country_df["population"].values[0],
        incident_rate=country_df["incident_rate"].values[0],
        deaths=country_df["deaths"].values[0],
    )
    return text_intro


@st.cache(show_spinner=False)
def create_world_text_intro(world_source) -> str:
    """Return string containing text introductions for use in world summary page.

    The text is built from a standardised Markdown-file using summary statistics from the data
    to generate a brief introduction to global situation.

    Parameters
    ----------
    world_source : pd.DataFrame
        Global summary infection data, resulting from `get_world_source`.

    Returns
    -------
    text_intro : str
        Brief ctext introducing global summary statistics.
    """
    summary = world_source[
        ["date", "population", "confirmed", "deaths", "incident_rate"]
    ].agg(
        {
            "date": "unique",
            "population": "sum",
            "confirmed": "sum",
            "deaths": "sum",
            "incident_rate": "sum",
        }
    )
    text_intro = WORLD_TEMPLATE.format(
        last_update=summary["date"].dt.strftime("%A %B %d, %Y").values[0],
        confirmed=summary["confirmed"].values[0],
        incident_rate=(summary["confirmed"].values[0] / summary["population"].values[0])
        * 10 ** 5,
        deaths=summary["deaths"].values[0],
        death_rate=(summary["deaths"].values[0] / summary["confirmed"].values[0]) * 100,
    )
    return text_intro


@st.cache(show_spinner=False)
def create_country_intros(world_source: pd.DataFrame) -> Dict:
    """Return dictionary containing text introductions of all countries.

    Parameters
    ----------
    world_source : pd.DataFrame
        Global summary infection data, resulting from `get_world_source`.

    Returns
    -------
    Dict
        Dictionary containing text intros (value) for each country (key).
    """
    return {
        country: create_country_text_intro(world_source, country)
        for country in world_source["country_region"].unique()
    }
