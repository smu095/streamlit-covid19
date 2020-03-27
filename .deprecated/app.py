import altair as alt
import numpy as np
import pandas as pd
import janitor
from datetime import datetime
from urllib.error import HTTPError
import streamlit as st

_URL = "https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-"
_TODAY = datetime.today().strftime("%Y-%m-%d")


@st.cache
def process_data(date: str = _TODAY) -> pd.DataFrame:
    """Returns DataFrame of worldwide COVID-19 data.

    The data contains the following columns:

        - date
        - country or territory name
        - geoid
        - population
        - cases
        - deaths
        - cumulative cases
        - cumulative deaths

    Data downloaded from the European Centre for Disease Prevention and Control (ECDP).

    Parameters
    ----------
    date : str, optional
        Date for ECDP data, by default _TODAY

    Returns
    -------
    pd.DataFrame
    """
    # Reading data from URL
    try:
        data_url = _URL + date + ".xlsx"
        raw = pd.read_excel(data_url)
    except HTTPError:
        raise ValueError(f"Could not find data for {date}.")

    # Simple preprocessing
    cleaned = raw.clean_names()
    # to_cat = dict.fromkeys(list(cleaned.select_dtypes("object")), "category")

    processed = (
        cleaned.rename_column("daterep", "date").remove_columns(
            ["day", "month", "year"]
        )
        # .astype(to_cat)
        .sort_values(by=["geoid", "date"])
    )

    processed["countries_and_territories"] = processed[
        "countries_and_territories"
    ].str.replace("_", " ")

    # Adding cumulative counts
    cumulatives = (
        processed.groupby("countries_and_territories")[["cases", "deaths"]]
        .cumsum()
        .rename_columns({"cases": "cumulative_cases", "deaths": "cumulative_deaths"})
    )

    final = (
        processed.join(cumulatives)
        .select_columns(
            [
                "date",
                "countries_and_territories",
                "geoid",
                "pop_data_2018",
                "cases",
                "cumulative_cases",
                "deaths",
                "cumulative_deaths",
            ]
        )
        .reset_index(drop=True)
    )

    # TODO: Write a test for expected columns
    # TODO: Maybe chance to learn great expectations?

    return final


def relative_change(df: pd.DataFrame, col_name: str) -> pd.Series:
    """Return relative change compared to previous day.

    Parameters
    ----------
    df : pd.DataFrame
    col_name : str

    Returns
    -------
    pd.Series
    """
    relative_change = 1 - (df[col_name].shift(1) / df[col_name])
    relative_change *= 100
    return relative_change


def main():
    """Run the app."""
    # TODO: Create radio buttons that divide themes into reasonable sections
    source = process_data("2020-03-25")
    unique_countries = tuple(source["countries_and_territories"].unique())

    st.sidebar.title("Explore")
    st.sidebar.markdown(
        "By default, start date is set to date of first registered case."
    )
    country = st.sidebar.selectbox("Choose country", unique_countries)
    data = source[source["countries_and_territories"] == country]

    first_registered_case = data.loc[data["cumulative_cases"] > 0, "date"].min()
    most_recent_date = data["date"].max()

    start = st.sidebar.date_input("Start date", first_registered_case)
    end = st.sidebar.date_input("End date", most_recent_date)
    date_mask = (data["date"].dt.date >= start) & (data["date"].dt.date <= end)
    interval_data = data[date_mask]

    st.title(country)

    st.subheader("At a glance")

    # TODO: Functionalise
    summary = interval_data.agg(
        {
            "countries_and_territories": "unique",
            "pop_data_2018": "unique",
            "cases": "sum",
            "deaths": "sum",
        }
    )
    summary["death_rate"] = summary["deaths"] / summary["cases"]
    summary["infected_per_capita"] = summary["cases"] / summary["pop_data_2018"]
    summary["time_since_first_registered_case"] = (
        most_recent_date - first_registered_case
    )

    summary = summary.rename_columns({"pop_data_2018": "population"})
    summary.columns = [col.capitalize().replace("_", " ") for col in summary.columns]

    # TODO: Add same statistics for rest of world for comparison
    st.table(summary.set_index("Countries and territories"))

    display = st.checkbox("Show data")
    if display:
        st.dataframe(interval_data)

    # TODO: Stacked area not correct here. Need to figure out proportions.
    cumulative_df = interval_data.select_columns(
        ["date", "cumulative_cases", "cumulative_deaths"]
    ).melt(
        "date",
        value_vars=["cumulative_cases", "cumulative_deaths"],
        var_name="statistic",
    )

    cumulative_chart = (
        alt.Chart(cumulative_df, height=300, width=600)
        .mark_area(fillOpacity=0.7)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("value:Q", title="Cumulative cases"),
            color=alt.Color("statistic:N", legend=alt.Legend(title="Statistics")),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("statistic:N", title="Category"),
                alt.Tooltip("value:Q", title="Total"),
            ],
        )
        .properties(title="Total number of confirmed cases and deaths")
        .interactive()
    )

    # type="log" argument in alt.Scale doesn't seem to work for some reason, temporary hack follows
    log_df = cumulative_df.copy().transform_column("value", np.log)
    ymax = log_df.groupby("statistic")["value"].max().sum()
    yrange = (0, ymax)

    log_chart = (
        alt.Chart(log_df, height=300, width=600)
        .mark_area(fillOpacity=0.7)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y(
                "value:Q",
                title="Cumulative cases (log-scale)",
                scale=alt.Scale(domain=yrange),
            ),
            color=alt.Color("statistic:N", legend=alt.Legend(title="Statistics")),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("statistic:N", title="Category"),
                alt.Tooltip("value:Q", title="Total"),
            ],
        )
        .properties(title="Total number of confirmed cases and deaths (log-scale)")
        .interactive()
    )

    st.subheader("Cumulative statistics")
    st.write(cumulative_chart)
    st.write(log_chart)

    cases_chart = (
        alt.Chart(interval_data, height=300, width=600)
        .mark_bar()
        .encode(x=alt.X("date:T", title="Date"), y=alt.Y("cases:Q", title="Cases"),)
        .properties(title="Number of new cases per day")
    )

    deaths_chart = (
        alt.Chart(interval_data, height=300, width=600)
        .mark_bar()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("deaths:Q", title="Deaths"),
            color=alt.value("orange"),
        )
        .properties(title="Number of deaths per day")
    )

    interval_data["relative_change_cases"] = relative_change(
        interval_data, "cumulative_cases"
    ).fillna(0)

    interval_data["relative_change_deaths"] = relative_change(
        interval_data, "cumulative_deaths"
    ).fillna(0)

    rate_of_change_cases = (
        alt.Chart(interval_data, height=300, width=600)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("relative_change_cases:Q", title="Change in %"),
        )
        .properties(title="Relative change in number of cases compared previous day")
    )

    rate_of_change_deaths = (
        alt.Chart(interval_data, height=300, width=600)
        .mark_line()
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y("relative_change_deaths:Q", title="Change in %"),
            color=alt.value("orange"),
        )
        .properties(title="Relative change in number of deaths compared previous day")
    )

    # TODO: Compare to rest of world

    st.subheader("Daily summaries")
    st.write(cases_chart)
    st.write(deaths_chart)
    st.write(rate_of_change_cases)
    st.write(rate_of_change_deaths)


if __name__ == "__main__":
    main()
