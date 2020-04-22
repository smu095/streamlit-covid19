# Introduction

The aim of this project has been to familiarise myself with [Streamlit](https://www.streamlit.io/) and [Altair](https://altair-viz.github.io/index.html).

[Streamlit](https://www.streamlit.io/) is an open-source app-framework for data science and machine learning. [Altair](https://altair-viz.github.io/index.html) is a declarative statistical visualization library for Python, based on [Vega and Vega-Lite](http://vega.github.io/).

## COVID-19 as a case study

To make the project concrete, I decided to build an interactive app based on the publicly available data recording the current [COVID-19 pandemic](https://en.wikipedia.org/wiki/Coronavirus_disease_2019).

The raw data pulled from the [2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19). Specifically, this app scrapes the data from the `web_data` branch.

## Navigation

Navigation is enabled via the sidebar to the left. The sidebar provides a couple of options.

The **World** option provides plots based on global summary statistics for each country. Clicking **World** yields two sub-options:

1. **Summary**: Gives a general overview of the worldwide situation based on aggregated statistics.

2. **Infection heatmap**: Gives a visual overview of the number of confirmed cases by time in the top 10 most affected nations.

Selecting **Countries** yields time series data for each individual country in the data set. Note that we have removed rows that do not have a valid ISO3 country code (this excludes data from e.g. the cruise ship Diamond Princess).

Clicking **Countries** will provide some additional options, namely **Start date** and **End date**, which determine the range of the time series. By default, the time series starts from the date of the first confirmed case.