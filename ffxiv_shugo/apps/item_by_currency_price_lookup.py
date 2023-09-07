"""
Get the best ROI for a given currency based on current market board
prices for Exodus.
"""

import numpy as np
import os
import pandas as pd
import streamlit as st

from ffxiv_shugo.constants import DATA_DIR
from ffxiv_shugo.utilities import lookup_prices

# TODO: clean this code up

COLS_TO_NORMALIZE = [
    "current_average_price",
    # "min_price",
    "average_recent_price",
]
NORMALIZED_COLS = [f"normalized_{col}" for col in COLS_TO_NORMALIZE]
ALL_KEYS = [
    # from items_by_currency
    "id",
    "item_name",
    "currency_cost",
    # from lookup_prices
    *COLS_TO_NORMALIZE,
    "sale_velocity",
    "average_recent_stack_size",
    # from computation here
    *NORMALIZED_COLS,
]

def load_data() -> pd.DataFrame:
    data_path = os.path.join(DATA_DIR, "items_by_currency.csv")
    data = pd.read_csv(data_path)
    data = data.loc[data["is_untradable"] == 0].drop("is_untradable", axis=1)
    return data


def main():
    data = load_data()
    available_currencies = data["currency_type"].unique().tolist()

    st.title("FFXIV: Fetch Prices")
    st.info(
        "This app looks up current market prices so you can spend your currencies "
        "on the best ROI."
    )
    with st.form("Options", clear_on_submit=False):
        currency = st.selectbox(
            label="Currency",
            options=available_currencies,
        )
        keys_to_show = st.multiselect(
            label="Final columns to show in output",
            options=ALL_KEYS,
            default=ALL_KEYS,
        )
        sort_by_column = st.selectbox(
            label="Column to sort the output by",
            options=ALL_KEYS, # narrow this down
        )
        sort_ascending = st.selectbox(
            label="Sort output by column ascending?",
            options=["False", "True"],
        )
        submit = st.form_submit_button(label="Submit")
        display = st.empty()
        if submit:
            fetch_prices(
                data.loc[data["currency_type"] == currency],
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
) -> None:
    ids = data["id"].values.tolist()
    col_map = {
        "currentAveragePriceNQ": "current_average_price",
        "nqSaleVelocity": "sale_velocity",
        # "minPriceNQ": "min_price",
        "averageRecentHistoryStackSize": "average_recent_stack_size",
        "averageRecentPrice": "average_recent_price",
    }
    # data[col_map.values()] = np.nan
    for new_col in col_map.values():
        data[new_col] = np.nan

    price_results = lookup_prices(ids)
    for price_data in price_results:
        item_id = price_data["item_id"]
        idx = data.loc[data["id"] == item_id].index[0]
        for price_col, data_col in col_map.items():
            data[data_col][idx] = price_data[price_col]

    for col, normalized_col in zip(COLS_TO_NORMALIZE, NORMALIZED_COLS):
        data[normalized_col] = data[col] / data["currency_cost"]

    display.write(
        data.sort_values(
            by=[sort_by_column],
            ascending=str(sort_ascending).lower() == "true",
        )[keys_to_show]
    )

if __name__ == "__main__":
    main()
