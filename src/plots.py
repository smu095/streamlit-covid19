from collections import OrderedDict
from typing import List, Optional

import altair as alt
import pandas as pd
from vega_datasets import data

from src.data import _get_trajectory_data, get_most_affected

COLUMN_TO_TITLE = OrderedDict(
    [
        ("incident_rate", "Cases pr. 100.000"),
        ("mortality_rate", "Deaths pr. 100.000"),
        ("confirmed", "Confirmed cases"),
        ("delta_confirmed", "Delta confirmed cases"),
        ("recovered", "Recovered patients"),
    ]
)


def create_map_plot(
    world_source: pd.DataFrame, column: str, country: Optional[str] = None
) -> alt.Chart:
    """Return alt.Chart map of world filled by value of `column`.

    Parameters
    ----------
    world_source : pd.DataFrame
    column : str
        Column value to fill country/countries by.
    country : Optional[str], optional
        If passed a country name, `create_map_plot` will draw world plot
        with only the given country coloured. By default None.

    Returns
    -------
    final_map : alt.Chart
    """
    if country:
        world_source = world_source.loc[world_source["country_region"] == country]

    source = alt.topo_feature(data.world_110m.url, "countries")
    background = alt.Chart(source).mark_geoshape()

    foreground = (
        alt.Chart(source)
        .mark_geoshape(stroke="black", strokeWidth=0.15)
        .encode(
            color=alt.Color(
                f"{column}:N", scale=alt.Scale(scheme="lightgreyred"), legend=None,
            ),
        )
        .transform_lookup(
            lookup="id",
            from_=alt.LookupData(world_source, "uid", [f"{column}", "country_region"]),
        )
    )

    if country is None:
        foreground = foreground.encode(
            tooltip=[
                alt.Tooltip("country_region:N", title="Country"),
                alt.Tooltip(f"{column}:Q", title=COLUMN_TO_TITLE[column]),
            ],
        )

    final_map = (
        (background + foreground)
        .configure_view(strokeWidth=0)
        .properties(width=700, height=400)
        .project("naturalEarth1")
    )

    return final_map


def create_world_barplot(world_source: pd.DataFrame) -> alt.Chart:
    """
    Return alt.Chart barplot of summary statistics of confirmed
    cases, recovered patients, deaths and active cases.

    Parameters
    ----------
    world_source : pd.DataFrame

    Returns
    -------
    bar_world : alt.Chart
    """
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
            x=alt.X("count:Q", title="Count"),
            y=alt.Y("status:N", title="", sort="-x"),
            color=alt.Color("status:N"),
            tooltip=["count:Q"],
        )
        .properties(width=600, height=200)
        .configure_legend(orient="top")
    )
    return bar_world


def create_top_n_barplot(world_source: pd.DataFrame) -> alt.Chart:
    """Return alt.Chart stacked barplot of top `n` most affected countries.

    Parameters
    ----------
    world_source : pd.DataFrame

    Returns
    -------
    top_n_bar : alt.Chart
    """
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
        .properties(title="10 most affected nations", width=600, height=300)
        .configure_legend(orient="top")
    )
    return top_n_bar


def create_lineplot(
    time_source: pd.DataFrame,
    x_label: str = "Date",
    color: str = "country_region",
    log: bool = False,
) -> alt.Chart:
    """Return animated alt.Chart lineplot of confirmed cases by date.

    Parameters
    ----------
    time_source : pd.DataFrame

    Returns
    -------
    time_chart : alt.Chart
    """
    confirmed = "log_confirmed" if log else "confirmed"
    highlight = alt.selection(
        type="single", on="mouseover", fields=[f"{color}"], nearest=True
    )
    time_base = (
        alt.Chart(time_source)
        .mark_line()
        .encode(
            x=alt.X("date:T", title=x_label),
            y=alt.Y(f"{confirmed}:Q", title="Confirmed cases"),
            color=alt.Color(f"{color}:N", legend=None),
        )
    )
    time_points = (
        time_base.mark_circle()
        .encode(
            opacity=alt.value(0),
            tooltip=[
                alt.Tooltip(f"{color}:N", title="Country"),
                alt.Tooltip(f"{confirmed}:N", title="Confirmed cases"),
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
    return time_chart


def create_heatmap(
    selection: pd.DataFrame,
    column: str = "scaled_delta_confirmed",
    title: str = None,
    x_label: str = "",
    x_orient: str = "top",
    y_orient: str = "right",
    width=600,
    height=400,
) -> alt.Chart:
    """
    Return alt.Chart heatmap displaying different transformations
    of confirmed cases.

    Parameters
    ----------
    selection : pd.DataFrame
        Countries to compare, passed by st.multiselect in `app.py`.
    column : str
        Value to plot. Default is 'scaled_confirmed', which is the standardised number
        of confirmed cases.

    Returns
    -------
    heatmap : alt.Chart
    """
    tooltip_title = column.replace("_", " ").capitalize()
    heatmap = (
        alt.Chart(selection)
        .mark_rect()
        .encode(
            alt.X("monthdate(date):T", title=x_label, axis=alt.Axis(orient=x_orient)),
            alt.Y("country_region:N", title="", axis=alt.Axis(orient=y_orient)),
            color=alt.Color(
                f"{column}:Q", legend=None, scale=alt.Scale(scheme="lightgreyred"),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip(f"{column}:Q", title=f"{tooltip_title}"),
            ],
        )
    )

    if title:
        final = heatmap.properties(title=title, width=width, height=height,)
    else:
        final = heatmap.properties(width=width, height=height,)

    return final


def create_country_barplot(
    interval_data: pd.DataFrame,
    y: str,
    x_label: str,
    y_label: str,
    colour: bool = False,
) -> alt.Chart:
    """Return alt.Chart barplot of column given by `y`.

    Parameters
    ----------
    interval_data : pd.DataFrame
    y : str
        Column to plot.
    x_label : str
        Label for x-axis.
    y_label : str
        Label for y-axis.
    colour : bool, optional
        Make barplot orange, by default False (resulting in blue barplot)

    Returns
    -------
    barplot : alt.Chart
    """
    base = (
        alt.Chart(interval_data)
        .mark_bar()
        .encode(x=alt.X("date:T", title=x_label), y=alt.Y(f"{y}:Q", title=y_label))
    )

    if colour:
        base = base.encode(color=alt.value("#ef8e3b"))

    barplot = base.properties(height=150, width=600)

    return barplot


def create_multiselect_line_plot(
    interval_data: pd.DataFrame, countries: List, log: bool
) -> alt.Chart:
    """
    Return alt.Chart of multi-select lineplot of number of confirmed cases
    with a corresponding heatbar for each country.

    Parameters
    ----------
    interval_data : pd.DataFrame
        Time series for a given interval.
    countries : List
        List of country names.
    log : bool
        Display number of confirmed cases on log scale.

    Returns
    -------
    multiline : alt.Chart
    """
    country_time_series = create_lineplot(interval_data, x_label="", log=log)
    heatbar = create_heatmap(
        interval_data,
        column="delta_pr_100k",
        title="",
        width=600,
        height=20 * (len(countries) + 1),
        x_label="New confirmed cases per 100.000",
        x_orient="bottom",
    )
    multiline = alt.vconcat(country_time_series, heatbar)
    return multiline


def create_delta_barplots(interval_data: pd.DataFrame) -> alt.Chart:
    """Return alt.Chart barplot of `delta_confirmed`.

    Parameters
    ----------
    interval_data : pd.DataFrame
        Time series data in given interval.

    Returns
    -------
    delta_chart : alt.Chart
    """
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
    delta_chart = alt.vconcat(delta_confirmed, delta_deaths)
    return delta_chart


def create_trajectory_plot(time_source: pd.DataFrame) -> alt.Chart:
    """Return alt.Chart trajectory plot for top 10 most affected countries.

    See https://www.youtube.com/watch?v=54XLXg4fYsc for inspiration.

    Returns
    -------
    chart : alt.Chart
    """
    time_source_top_10 = _get_trajectory_data(time_source)

    nearest = alt.selection(
        type="single", nearest=True, on="mouseover", fields=["country_region"],
    )

    base = (
        alt.Chart(time_source_top_10)
        .mark_line()
        .encode(
            x=alt.X(
                "mean_confirmed:Q",
                scale=alt.Scale(type="log"),
                title="Avg. weekly increase in confirmed cases",
            ),
            y=alt.Y(
                "mean_delta_confirmed:Q",
                scale=alt.Scale(type="log"),
                title="Avg. weekly confirmed cases",
            ),
            tooltip=["country_region"],
            size=alt.condition(~nearest, alt.value(1), alt.value(3)),
            color=alt.Color("country_region:N", legend=None),
        )
        .transform_filter((alt.datum.confirmed > 0) & (alt.datum.delta_confirmed > 0))
        .transform_aggregate(
            mean_confirmed="mean(confirmed)",
            mean_delta_confirmed=("mean(delta_confirmed)"),
            groupby=["country_region", "week"],
        )
    )

    points = base.mark_circle().encode(opacity=alt.value(0)).add_selection(nearest)

    chart = (
        (base + points)
        .interactive()
        .properties(
            width=600,
            height=400,
            title="Trajectory of infection in top 10 most affected countries",
        )
        .configure_axis(gridOpacity=0.3)
    )

    return chart


def create_world_areaplot(
    time_source: pd.DataFrame, x_label: str = "Date", color: str = "continent_name",
) -> pd.DataFrame:
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
    time_continent = (
        time_source.groupby(["continent_name", "date"])[["confirmed", "log_confirmed"]]
        .sum()
        .reset_index()
    )

    world_areaplot = (
        alt.Chart(time_continent)
        .mark_area()
        .encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("confirmed:Q", title="Confirmed cases",),
            color="continent_name:N",
            tooltip=[
                alt.Tooltip("continent_name:N"),
                alt.Tooltip("date:T"),
                alt.Tooltip("confirmed:Q"),
            ],
        )
        .properties(width=600, height=200)
    )

    world_areaplot_norm = (
        alt.Chart(time_continent)
        .mark_area()
        .encode(
            x=alt.X("date:T", title=x_label),
            y=alt.Y(
                "confirmed:Q",
                stack="normalize",
                title="Percentage of confirmed cases",
                axis=alt.Axis(format=".0%"),
            ),
            color="continent_name:N",
        )
        .properties(width=600, height=200)
    )

    world_area = (
        alt.vconcat(world_areaplot, world_areaplot_norm)
        .configure_legend(orient="top", title=None)
        .properties(title="Total number of confirmed cases worldwide")
        .configure_title(anchor="middle", offset=20)
    )

    return world_area
