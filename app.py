import time

import numpy as np
import streamlit as st

from src.data import (
    get_country_data,
    get_delta_confirmed,
    get_heatmap_data,
    get_interval_data,
    get_time_series_cases,
    get_world_source,
)
from src.plots import (
    COLUMN_TO_TITLE,
    create_delta_barplots,
    create_heatmap,
    create_map_plot,
    create_multiselect_line_plot,
    create_top_n_barplot,
    create_trajectory_plot,
    create_world_areaplot,
    create_world_barplot,
)
from src.text import create_country_intros, create_heatmap_text, create_world_text_intro


def main():
    with st.spinner("Loading data..."):
        time_source = get_time_series_cases()
        delta_confirmed = get_delta_confirmed(time_source)
        world_source = get_world_source(delta_confirmed)
        country_intros = create_country_intros(world_source)

    st.sidebar.title("Explore")
    options = st.sidebar.radio(
        "Choose level of data to display", ("World", "Countries")
    )

    # WORLD -----------------------------------------------
    if options == "World":
        st.sidebar.subheader("World options")
        view = st.sidebar.selectbox(
            "Which data would you like to see?",
            ["Summary", "Infection trajectory", "Infection heatmap"],
        )

        if view == "Summary":
            st.header("World")

            # Map plot
            choice = st.selectbox(
                "Choose data to display",
                list(COLUMN_TO_TITLE.keys()),
                format_func=COLUMN_TO_TITLE.get,
            )

            st.altair_chart(create_map_plot(world_source, column=choice))

            # World intro
            st.markdown(create_world_text_intro(world_source))

            # World time-series
            # TODO: Refactor to use log scale in alt.Scale?
            st.altair_chart(
                create_world_areaplot(time_source=time_source, color="continent_name")
            )

            # World summary
            st.altair_chart(create_world_barplot(world_source))

            # Most affected nations
            st.altair_chart(create_top_n_barplot(world_source))

        # Infection trajectories
        if view == "Infection trajectory":
            st.altair_chart(create_trajectory_plot(time_source))

        # World heatmap
        if view == "Infection heatmap":
            st.header("Rate of change at a glance")
            st.markdown(create_heatmap_text())

            heatmap_data, initial_countries, country_options = get_heatmap_data(
                time_source
            )
            options = st.multiselect("Select countries to display", country_options)
            heatmap_chart = st.altair_chart(
                create_heatmap(
                    heatmap_data,
                    column="scaled_confirmed",
                    width=800,
                    height=25 * (len(options) + len(initial_countries)),
                )
            )
            if len(options) > 0:
                selection = time_source[time_source["country_region"].isin(options)]
                heatmap_chart.add_rows(selection)

    # COUNTRIES -----------------------------------------------
    if options == "Countries":

        # Define sidebar options
        st.sidebar.subheader("Country options")
        country = st.sidebar.selectbox(
            "Choose country", world_source["country_region"].unique()
        )
        st.sidebar.markdown(
            "By default, start date is set to date of first registered case."
        )

        country_data, first_case, last_update = get_country_data(time_source, country)
        start = st.sidebar.date_input("Start date", first_case)
        end = st.sidebar.date_input("End date", last_update)
        interval_data = get_interval_data(
            country_data=country_data, start=start, end=end
        )

        # Main page for selected country
        st.title(country)

        # Map plot: Show position of country
        st.altair_chart(
            create_map_plot(world_source, column="confirmed", country=country)
        )

        # Country intro text
        st.markdown(country_intros[country])
        display = st.checkbox("Show data")
        if display:
            st.dataframe(interval_data)

        # Multiselect line plot: Compare country with other countries (optional)
        st.subheader("Confirmed cases since first patient")
        countries = st.multiselect(
            "Compare with:", list(time_source["country_region"].unique())
        )

        log = st.checkbox("Log scale")
        country_line_chart = st.altair_chart(
            create_multiselect_line_plot(
                interval_data=interval_data, countries=countries, log=log
            )
        )

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
        st.altair_chart(create_delta_barplots(interval_data))


if __name__ == "__main__":
    main()
