# COVID-19 Streamlit App

The aim of this project has been to familiarise myself with [Streamlit](https://www.streamlit.io/) and [Altair](https://altair-viz.github.io/index.html).

[Streamlit](https://www.streamlit.io/) is an open-source app-framework for data science and machine learning. [Altair](https://altair-viz.github.io/index.html) is a declarative statistical visualization library for Python, based on [Vega and Vega-Lite](http://vega.github.io/).

To make the project concrete, I decided to build an interactive app based on the publicly available data recording the current [COVID-19 pandemic](https://en.wikipedia.org/wiki/Coronavirus_disease_2019).

The raw data pulled from the [2019 Novel Coronavirus COVID-19 (2019-nCoV) Data Repository by Johns Hopkins CSSE](https://github.com/CSSEGISandData/COVID-19). Specifically, this app scrapes the data from the `web_data` branch.

## Setup

### Run locally

Clone into the repository using the follow command in your terminal:

```bash
$ git clone https://github.com/smu095/streamlit-covid19.git
```

Navigate to the local repository, create a new virtual environment and install the required packages in a virtual environment, e.g.:

```bash
$ cd path/to/local/repo
$ python3 -m venv .venv
$ source .venv/bin/activate
(venv)$ pip install -r requirements.txt
```

Next, download the most recent data and run the streamlit app by running the following commands:

```bash
$ python3 src/scrape.py
$ streamlit run app.py
```

You can also simply run the following shell script:

```bash
$ ./start.sh
```

### Run containerised version

Alternatively, run the containerised version of the app. To do this, first make sure you have [Docker](https://www.docker.com/get-started) installed. Once installed, navigate to the local repository and run the `run.sh` shell script, like this:

```bash
$ cd path/to/local/repo
$ ./run.sh
```

Finally, open your favourite browser and go to `http://localhost:8501` to open the app.

## Known issues

* The heatbar subplot for countries doesn't appear to be interactive in the containerised version. It is unclear why.
