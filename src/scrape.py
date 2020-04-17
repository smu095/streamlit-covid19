import os
import pathlib

import pandas as pd
import requests

DATA = {
    "cases.csv": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases.csv",  # noqa: E501
    "cases_country.csv": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases_country.csv",  # noqa: E501
    "cases_time.csv": "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/web-data/data/cases_time.csv",  # noqa: 501
}
PATH = pathlib.Path("data/")
FNAME = PATH.joinpath("last_commit.txt")


def get_last_commit_hash():
    """Returns latest commit hash from John Hopkins data repo."""
    url = "https://api.github.com/repos/CSSEGISandData/COVID-19/git/refs/heads/web-data"
    json_response = requests.get(url).json()
    commit_hash = json_response["object"]["sha"][:7]

    return commit_hash


def check_for_updates():
    """Return True if we have already downloaded data from latest commit, else False."""
    try:
        last_commit = get_last_commit_hash()
    except Exception as e:
        print("Failed to get most recent commit hash.")
        print(e)
        return False

    if not os.path.isfile(FNAME):
        with open(FNAME, "w") as file:
            file.write("")

    with open(FNAME, "r") as file:
        commit = file.read()

    if commit == last_commit:
        print(f"Data from commit '{last_commit}' already downloaded.")
        return False
    else:
        print(f"New data available. Commit '{last_commit}' saved to last_commit.txt.")
        with open(FNAME, "w") as write_file:
            write_file.write(last_commit)
        return True


def check_for_new_data():
    download = check_for_updates()
    if download:
        for fname, url in DATA.items():
            print(f"Downloading {fname}...")
            _ = pd.read_csv(url).to_csv(f"data/{fname}", index=False)
        print("Downloads complete.")
    return None
