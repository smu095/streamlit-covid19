import datetime
from typing import Optional

import altair as alt
import janitor
import numpy as np
import pandas as pd
import streamlit as st

from src.data import (
    _get_time_series_cases,
    _get_us_cases,
    _get_worldwide_cases,
    create_country_text_intro,
    create_world_text_intro,
    get_country_data,
    get_country_summary,
    get_delta_confirmed,
)
from src.plots import (
    COLUMN_TO_TITLE,
    TITLE_TO_COLUMN,
    create_country_barplot,
    create_heatmap,
    create_lineplot,
    create_map_plot,
    create_top_n_barplot,
    create_world_barplot,
)


@st.cache
def get_us_cases(url: Optional[str] = None) -> pd.DataFrame:
    """
    Return DataFrame of US cases.

    Raw data available @ https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases.csv

    Parameters
    ----------
    url : Optional[str], optional
        URL to John Hopkins data, by default None

    Returns
    -------
    us : pd.DataFrame
    """
    if url:
        us = _get_us_cases(url)
    else:
        us = _get_us_cases()
    return us


@st.cache
def get_worldwide_cases(url: Optional[str] = None) -> pd.DataFrame:
    """Return DataFrame of US cases.

    Raw data available @ https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases_country.csv

    Parameters
    ----------
    url : Optional[str], optional
        URL to John Hopkins data, by default None

    Returns
    -------
    world : pd.DataFrame
    """
    if url:
        world = _get_worldwide_cases(url)
    else:
        world = _get_worldwide_cases()
    return world


@st.cache
def get_time_series_cases(url: Optional[str] = None) -> pd.DataFrame:
    """Return DataFrame of time-series describing worldwide cases.

    Raw data available @ https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases_time.csv

    Parameters
    ----------
    url : Optional[str], optional
        URL to John Hopkins data, by default None

    Returns
    -------
    time_series : pd.DataFrame
    """
    if url:
        time_series = _get_time_series_cases(url)
    else:
        time_series = _get_time_series_cases()
    return time_series


def main():
    us_source = get_us_cases()
    world_source = get_worldwide_cases()
    time_source, unique_countries = get_time_series_cases()
    delta_confirmed = get_delta_confirmed(time_source)
    top_10 = world_source.sort_values(by="confirmed")["country_region"].tail(10)

    world_source = world_source.merge(delta_confirmed, on="country_region", how="left")
    world_source["delta_pr_100k"] = (
        world_source["delta_confirmed"] / world_source["population"]
    ) * 10 ** 5

    st.sidebar.title("Explore")
    options = st.sidebar.radio(
        "Choose level of data to display", ("World", "Countries")
    )

    # WORLD -----------------------------------------------
    if options == "World":
        st.sidebar.subheader("World options")
        view = st.sidebar.selectbox(
            "Which data would you like to see?", ["Summary", "Infection heatmap"]
        )

        if view == "Summary":
            st.header("World")

            # Map plot
            choice = st.selectbox(
                "Choose data to display", list(TITLE_TO_COLUMN.keys())
            )
            column = TITLE_TO_COLUMN[choice]
            world_map = create_map_plot(world_source, column=column)
            st.altair_chart(world_map)
            world_intro = create_world_text_intro(world_source)
            st.markdown(world_intro)

            # World time-series
            log = st.checkbox("Log scale")
            time_chart = create_lineplot(time_source, log=log)
            st.altair_chart(time_chart)

            # World summary
            bar_world = create_world_barplot(world_source)
            st.altair_chart(bar_world)

            # Most affected nations
            top_n_bar = create_top_n_barplot(world_source)
            st.altair_chart(top_n_bar)

        # World heatmap
        if view == "Infection heatmap":
            st.header("Rate of change at a glance")
            st.markdown(
                "The infection heatmap shows the daily change in confirmed cases per 100.000 (also called delta). The more red, the higher the delta. By default the heatmap displays the top 10 most affected countries. To add more countries, use the multiselect box."
            )
            options = st.multiselect("Select countries to display", unique_countries)
            top_10_countries = time_source[time_source["country_region"].isin(top_10)]
            heatmap = create_heatmap(
                top_10_countries,
                column="delta_pr_100k",
                width=800,
                height=25
                * (len(options) + top_10_countries["country_region"].nunique()),
            )
            heatmap_chart = st.altair_chart(heatmap)

            if len(options) > 0:
                selection = time_source[time_source["country_region"].isin(options)]
                heatmap_chart.add_rows(selection)

    # COUNTRIES -----------------------------------------------
    if options == "Countries":

        # Define sidebar options
        st.sidebar.subheader("Country options")
        country = st.sidebar.selectbox("Choose country", unique_countries)
        st.sidebar.markdown(
            "By default, start date is set to date of first registered case."
        )

        country_data, first_case, last_update = get_country_data(time_source, country)
        start = st.sidebar.date_input("Start date", first_case)
        end = st.sidebar.date_input("End date", last_update)
        date_mask = (country_data["date"].dt.date >= start) & (
            country_data["date"].dt.date <= end
        )

        # Get selected country data
        interval_data = country_data[date_mask]

        # Main page for selected country
        st.title(country)

        # Map plot: Show position of country
        country_map = create_map_plot(world_source, column="confirmed", country=country)
        st.altair_chart(country_map)

        # Show tabular summary
        country_summary = get_country_summary(world_source, country)
        country_intro = create_country_text_intro(country_summary)
        st.markdown(country_intro)

        display = st.checkbox("Show data")
        if display:
            st.dataframe(interval_data)

        # Multiselect line plot: Compare country with other countries (optional)
        st.subheader("Confirmed cases since first patient")
        countries = st.multiselect(
            "Compare with:", list(time_source["country_region"].unique())
        )

        log = st.checkbox("Log scale")
        country_time_series = create_lineplot(interval_data, x_label=None, log=log)
        heatbar = create_heatmap(
            interval_data,
            column="delta_pr_100k",
            title="",
            width=600,
            height=20 * (len(countries) + 1),
            x_label="Daily change in confirmed cases per 100.000",
            x_orient="bottom",
        )
        c = alt.vconcat(country_time_series, heatbar)
        country_line_chart = st.altair_chart(c)

        if len(countries) > 0:
            for c in countries:
                compare_data, _, _ = get_country_data(time_source, c)
                compare_mask = (compare_data["date"].dt.date >= start) & (
                    compare_data["date"].dt.date <= end
                )
                compare_country = compare_data[compare_mask]
                country_line_chart.add_rows(compare_country)

        # Barplots: Delta confirmed and delta deaths
        st.subheader("Number of daily confirmed cases and deaths since first patient")
        delta_confirmed = create_country_barplot(
            interval_data=interval_data,
            y="delta_confirmed",
            x_label="",
            y_label="Delta confirmed",
        )
        delta_deaths = create_country_barplot(
            interval_data=interval_data,
            y="delta_deaths",
            x_label="Date",
            y_label="Delta deaths",
            colour=True,
        )
        st.altair_chart(alt.vconcat(delta_confirmed, delta_deaths))


if __name__ == "__main__":
    main()
