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
    get_country_data,
)
from src.plots import (
    create_map_plot,
    create_top_n_barplot,
    create_world_barplot,
    create_world_lineplot,
)


@st.cache
def get_us_cases(url: Optional[str] = None):
    if url:
        return _get_us_cases(url)
    else:
        return _get_us_cases()


@st.cache
def get_worldwide_cases(url: Optional[str] = None):
    if url:
        return _get_worldwide_cases(url)
    else:
        return _get_worldwide_cases()


@st.cache
def get_time_series_cases(url: Optional[str] = None):
    if url:
        return _get_time_series_cases(url)
    else:
        return _get_time_series_cases()


def main():
    us_source = get_us_cases()
    world_source = get_worldwide_cases()
    time_source, unique_countries = get_time_series_cases()

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
            world_map = create_map_plot(world_source)
            st.altair_chart(world_map)

            # World summary
            bar_world = create_world_barplot(world_source)
            st.altair_chart(bar_world)

            # Most affected nations
            top_n_bar = create_top_n_barplot(world_source)
            st.altair_chart(top_n_bar)

            # World time-series
            time_chart = create_world_lineplot(time_source)
            st.altair_chart(time_chart)

        # World heatmap
        if view == "Infection heatmap":
            heatmap = (
                alt.Chart(time_source)
                .mark_rect()
                .encode(
                    alt.X("monthdate(date):T", title="Date"),
                    alt.Y("country_region:N", title=""),
                    color=alt.Color(
                        "norm_confirmed:Q",
                        legend=None,
                        scale=alt.Scale(scheme="lightgreyred"),
                    ),
                    tooltip=[
                        alt.Tooltip("country_region:N", title="Country"),
                        alt.Tooltip(
                            "norm_confirmed:Q", title="Proportion of confirmed cases"
                        ),
                    ],
                )
                .properties(title="Test", width=800)
            )
            st.altair_chart(heatmap)

    # COUNTRIES -----------------------------------------------
    if options == "Countries":
        st.sidebar.subheader("Country options")
        country = st.sidebar.selectbox("Choose country", unique_countries)
        country_data, first_case, last_update = get_country_data(time_source, country)
        st.sidebar.markdown(
            "By default, start date is set to date of first registered case."
        )

        start = st.sidebar.date_input("Start date", first_case)
        end = st.sidebar.date_input("End date", last_update)
        date_mask = (country_data["date"].dt.date >= start) & (
            country_data["date"].dt.date <= end
        )
        interval_data = country_data[date_mask]

        st.title(country)
        # TODO: Add map here?
        # TODO: With optional checkbox for comparison with world?

        country_summary = (
            world_source[world_source["country_region"] == country]
            .remove_columns(["lat", "lon"])
            .set_index("country_region")
        )
        st.write(country_summary)

        display = st.checkbox("Show data")
        if display:
            st.dataframe(interval_data)

        # TODO: Stacked area not correct here. Need to figure out proportions.
        line_chart = (
            alt.Chart(interval_data)
            .mark_line()
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("confirmed:Q", title="Confirmed"),
            )
            .properties(height=300, width=600)
        )
        st.altair_chart(line_chart)


if __name__ == "__main__":
    main()
