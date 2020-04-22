import pathlib
from typing import Dict

import pandas as pd
import streamlit as st

DATA_PATH = pathlib.Path("data/")
PATH = pathlib.Path("templates/")
HEATMAP_TEXT = PATH.joinpath("heatmap_text_template.md")
HEATMAP_INTRO = PATH.joinpath("heatmap_intro_template.md")


def read_text(filename: str) -> str:
    """Returns Markdown file as string."""
    markdown = PATH.joinpath(filename)
    with markdown.open(mode="r") as file:
        text = file.read()
    return text


COUNTRY_TEMPLATE = read_text("country_text_template.md")
WORLD_TEMPLATE = read_text("world_text_template.md")
SIDEBAR_TEMPLATE = read_text("sidebar_intro.md")


def _get_last_update():
    """Return date and time of last update."""
    with DATA_PATH.joinpath("cases_country.csv").open("r") as f:
        column = f.readline().split(",").index("Last_Update")
        last_update = f.readline().split(",")[column]
    return last_update


def create_heatmap_text() -> str:
    """Return text intro to Infection heatmap page."""
    with HEATMAP_TEXT.open(mode="r") as file:
        infection_template = file.read()
    return infection_template


def create_heatmap_intro() -> str:
    """Return intro to Heatmap section."""
    with HEATMAP_INTRO.open("r") as file:
        heatmap_intro = file.read()
    return heatmap_intro


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


@st.cache(show_spinner=False)
def create_sidebar_intro() -> str:
    """Return intro text for sidebar."""
    last_update = _get_last_update()
    sidebar_intro = SIDEBAR_TEMPLATE.format(last_update=last_update)
    return sidebar_intro


@st.cache(show_spinner=False)
def create_home_intro() -> str:
    """Return text for Home section."""
    return read_text("intro_template.md")


@st.cache(show_spinner=False)
def create_geo_intro() -> str:
    """Return text for geographic plot in World section."""
    return read_text("geo_text_template.md")


@st.cache(show_spinner=False)
def create_number_confirmed_intro() -> str:
    """Return text for number of confirmed cases plot in World section."""
    return read_text("num_cases_template.md")


@st.cache(show_spinner=False)
def create_most_affected_intro() -> str:
    """Return text for number of confirmed cases plot in World section."""
    return read_text("most_affected_template.md")


@st.cache(show_spinner=False)
def create_country_cases_intro() -> str:
    """Return text for number of confirmed cases plot in World section."""
    return read_text("country_cases_template.md")


def create_country_deltas_intro(country: str) -> str:
    """Return text for number of confirmed cases plot in World section."""
    text = read_text("country_deltas_template.md").format(country=country)
    return text


def create_country_trajectory_intro(country: str) -> str:
    """Return text for number of confirmed cases plot in World section."""
    text = read_text("country_trajectory_template.md").format(country=country)
    return text
