import altair as alt
import janitor
import numpy as np
import pandas as pd
import streamlit as st
from vega_datasets import data

US_DATA = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases.csv"  # noqa: E501
CASES_WORLDWIDE = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases_country.csv"  # noqa: E501
TIME_SERIES = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases_time.csv"  # noqa: 501


def _get_world_population():
    pop = pd.read_csv("./data/worldbank-population-2018.csv").rename_column(
        "2018", "population"
    )
    return pop


def _get_iso_codes():
    iso_codes = pd.read_csv("./data/iso-codes.csv")
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


def _to_date(x):
    return pd.to_datetime(x).normalize()


@st.cache
def get_us_cases(url: str = US_DATA):
    cases = pd.read_csv(url)
    cleaned = (
        cases.clean_names()
        .transform_column("last_update", _to_date)
        .filter_on("country_region == 'US'")
    )
    return cleaned


@st.cache
def get_worldwide_cases(url: str = CASES_WORLDWIDE):
    cases = pd.read_csv(url)
    cleaned = (
        cases.clean_names()
        .rename_column("long_", "lon")
        .transform_column("last_update", _to_date)
        .filter_on("country_region == 'Diamond Princess'", complement=True)
        .filter_on("country_region == 'Holy See'", complement=True)
        .sort_values(by="country_region")
    )
    iso_join = cleaned.merge(_get_iso_codes(), on="country_region")
    pop_join = iso_join.merge(_get_world_population(), on="country_region")

    pop_join["sick_per_100k"] = (
        pop_join["confirmed"] / pop_join["population"]
    ) * 10 ** 5

    return pop_join


@st.cache
def get_time_series_cases(url: str = TIME_SERIES):
    time_series = pd.read_csv(url)
    cleaned = (
        time_series.clean_names()
        .rename_column("last_update", "date")
        .transform_column("date", _to_date)
        .remove_columns(["recovered", "active", "delta_recovered"])
    )
    cleaned["norm_confirmed"] = cleaned.groupby("country_region")["confirmed"].apply(
        lambda x: x / x.max()
    )
    unique_countries = tuple(cleaned["country_region"].unique())
    return cleaned, unique_countries


def get_most_affected(world_source, n: int = 10):
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


def get_country_data(time_source, country):
    time_data = time_source[time_source["country_region"] == country]

    first_case = time_data.loc[time_data["confirmed"] > 0, "date"].min()
    last_update = time_data["date"].max()

    return time_data, first_case, last_update


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
            source = alt.topo_feature(data.world_110m.url, "countries")
            background = alt.Chart(source).mark_geoshape(fill="white")

            foreground = (
                alt.Chart(source)
                .mark_geoshape(stroke="black", strokeWidth=0.15)
                .encode(
                    color=alt.Color(
                        "sick_per_100k:N",
                        scale=alt.Scale(scheme="lightgreyred"),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("country_region:N", title="Country"),
                        alt.Tooltip("sick_per_100k:Q", title="Cases pr. 100k"),
                    ],
                )
                .transform_lookup(
                    lookup="id",
                    from_=alt.LookupData(
                        world_source, "id", ["sick_per_100k", "country_region"]
                    ),
                )
            )

            final_map = (
                (background + foreground)
                .configure_view(strokeWidth=0)
                .properties(width=700, height=400)
                .project("naturalEarth1")
            )
            st.altair_chart(final_map)

            # World summary
            world_summary = (
                world_source[["confirmed", "active", "deaths", "recovered"]]
                .sum()
                .reset_index(name="count")
                .rename_column("index", "status")
            )
            bar_world = (
                alt.Chart(world_summary)
                .mark_bar()
                .encode(
                    y=alt.Y("status:N", title="", sort="-x"),
                    x=alt.X("count:Q", title="Count"),
                    color=alt.Color("status:N"),
                    tooltip=["count:Q"],
                )
                .interactive()
                .properties(title="Summary statistics", width=600, height=200)
                .configure_legend(orient="top")
            )
            st.altair_chart(bar_world)

            # Most affected nations
            most_affected = get_most_affected(world_source, n=10)
            top_n_bar = (
                alt.Chart(most_affected)
                .mark_bar()
                .encode(
                    y=alt.Y("country_region:N", title="", sort="-x"),
                    x=alt.X("sum(count):Q", title="Count"),
                    color=alt.Color("status:N", scale=alt.Scale(scheme="tableau20")),
                    tooltip=[
                        alt.Tooltip("country_region:N", title="Country"),
                        alt.Tooltip("sum(count):Q", title="Count"),
                        alt.Tooltip("status:N", title="Status"),
                    ],
                )
                .interactive()
                .properties(title="10 most affected nations", width=600, height=300)
                .configure_legend(orient="top")
            )
            st.altair_chart(top_n_bar)

            # World time-series
            highlight = alt.selection(
                type="single", on="mouseover", fields=["country_region"], nearest=True
            )
            time_base = (
                alt.Chart(time_source)
                .mark_line()
                .encode(
                    x=alt.X("date:T", title="Date"),
                    y=alt.Y("confirmed:Q", title="Confirmed cases"),
                    color=alt.Color("country_region:N", legend=None),
                )
            )
            time_points = (
                time_base.mark_circle()
                .encode(
                    opacity=alt.value(0),
                    tooltip=[
                        alt.Tooltip("country_region:N", title="Country"),
                        alt.Tooltip("confirmed:N", title="Confirmed cases"),
                    ],
                )
                .add_selection(highlight)
            )
            time_lines = time_base.mark_line().encode(
                size=alt.condition(~highlight, alt.value(1), alt.value(3))
            )
            time_chart = (
                (time_points + time_lines)
                .interactive()
                .properties(title="Timeline of confirmed cases", width=600, height=300)
            )
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
