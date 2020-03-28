from collections import OrderedDict

import altair as alt
import pandas as pd
from vega_datasets import data

from src.data import get_most_affected

MAPPINGS = [
    ("sick_pr_100k", "Cases pr. 100.000"),
    ("deaths_pr_100k", "Deaths pr. 100.000"),
    ("confirmed", "Confirmed cases"),
    ("recovered", "Recovered patients"),
]
COLUMN_TO_TITLE = OrderedDict(MAPPINGS)
TITLE_TO_COLUMN = OrderedDict((title, col) for col, title in COLUMN_TO_TITLE.items())


def create_map_plot(world_source, column, country=None):

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
            from_=alt.LookupData(world_source, "id", [f"{column}", "country_region"]),
        )
    )

    if not country:
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


def create_world_barplot(world_source):
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
    return bar_world


def create_top_n_barplot(world_source):
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
    return top_n_bar


def create_world_lineplot(time_source):
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
    return time_chart


def create_heatmap(selection, column):
    heatmap = (
        alt.Chart(selection)
        .mark_rect()
        .encode(
            alt.X("monthdate(date):T", title="Date"),
            alt.Y("country_region:N", title=""),
            color=alt.Color(
                f"{column}:Q", legend=None, scale=alt.Scale(scheme="yelloworangered"),
            ),
            tooltip=[
                alt.Tooltip("country_region:N", title="Country"),
                alt.Tooltip(f"{column}:Q", title="Cases pr. 100k"),
            ],
        )
        .properties(title="Proportion of confirmed cases", width=800)
    )
    return heatmap
