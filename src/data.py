import pandas as pd
import janitor
from datetime import datetime
from urllib.error import HTTPError

_URL = "https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-"
_TODAY = datetime.today().strftime("%Y-%m-%d")


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
    to_cat = dict.fromkeys(list(cleaned.select_dtypes("object")), "category")

    processed = (
        cleaned.rename_column("daterep", "date")
        .remove_columns(["day", "month", "year"])
        .astype(to_cat)
        .sort_values(by=["geoid", "date"])
    )

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
        .set_index("date")
    )

    # TODO: Write a test for expected columns
    # TODO: Maybe chance to learn great expectations?

    return final
