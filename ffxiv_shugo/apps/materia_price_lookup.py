"""
Find the going market rates for materia.
"""

import numpy as np
import os
import pandas as pd
import streamlit as st

from ffxiv_shugo.constants import (
    DATA_DIR,
    MATERIA_GRADES,
)
from ffxiv_shugo.utilities import lookup_prices

ALL_KEYS = [
    # from materia.csv
    "id",
    "grade_idx",
    "grade_name",
    "materia_type",
    "materia_name",
    "stat_boosted",
    # from lookup_prices
    "current_average_price",
    # "min_price",
    "average_recent_price",
    "sale_velocity",
    "average_recent_stack_size",
]
DEFAULT_COLS_TO_SHOW = [
    "materia_name",
    "stat_boosted",
    "average_recent_price",
    "sale_velocity",
    "average_recent_stack_size",
]
SORT_OPTIONS = [
    "average_recent_price",
    "grade_idx",
    "sale_velocity",
    "current_average_price",
    "average_recent_stack_size",
]

def load_data() -> pd.DataFrame:
    data_path = os.path.join(DATA_DIR, "materia.csv")
    data = pd.read_csv(data_path)
    return data

def main():
    data = load_data()

    available_grades = [
        name for idx, name in enumerate(MATERIA_GRADES)
        if idx in data["grade_idx"].unique()
    ]
    default_grade = available_grades

    available_types = data["materia_type"].unique().tolist()
    if "combat" in available_types:
        default_type = ["combat"]
    else:
        default_type = available_types

    st.title("FFXIV: Materia Price Lookup")
    st.info("This app looks up the going market rates for various materia.")

    with st.form("Options", clear_on_submit=False):
        keys_to_show = st.multiselect(
            label="Final columns to show in output",
            options=ALL_KEYS,
            default=DEFAULT_COLS_TO_SHOW,
        )
        sort_by_column = st.selectbox(
            label="Column to sort the output by",
            options=SORT_OPTIONS,
        )
        sort_ascending = st.selectbox(
            label="Sort output column by ascending?",
            options=["False", "True"],
        )
        materia_types = st.multiselect(
            label="The types of materia to be shown",
            options=available_types,
            default=default_type,
        )
        materia_grades = st.multiselect(
            label="The grades of materia to be shown",
            options=available_grades,
            default=default_grade,
        )
        submit = st.form_submit_button(label="Submit")
    display = st.empty()
    if submit:
        fetch_prices(
            data.loc[
                data["materia_type"].isin(materia_types) &
                data["grade_name"].isin(materia_grades)
            ],
            display,
            keys_to_show,
            sort_by_column,
            sort_ascending,
        )

def fetch_prices(
    data: pd.DataFrame,
    display: st.empty,
    keys_to_show: st.multiselect,
    sort_by_column: st.selectbox,
    sort_ascending: st.selectbox,
):
    ids = data["id"].values.tolist()
    col_map = {
        "currentAveragePriceNQ": "current_average_price",
        "nqSaleVelocity": "sale_velocity",
        # "minPriceNQ": "min_price",
        "averageRecentHistoryStackSize": "average_recent_stack_size",
        "averageRecentPrice": "average_recent_price",
    }
    for new_col in col_map.values():
        data[new_col] = np.nan

    price_results = lookup_prices(ids)
    for price_data in price_results:
        item_id = price_data["item_id"]
        idx = data.loc[data["id"] == item_id].index[0]
        for price_col, data_col in col_map.items():
            data[data_col][idx] = price_data[price_col]

    display.write(
        data.sort_values(
            by=[sort_by_column],
            ascending=str(sort_ascending).lower() == "true",
        )[keys_to_show]
    )

if __name__ == "__main__":
    main()