import numpy as np
import pyxivapi
import requests
from typing import Dict, List, Union

from ffxiv_shugo.constants import (
    EXODUS_WORLD_ID,
)

def lookup_prices(item_ids: List[int]) -> List[Dict[str, Union[float, int]]]:
    # https://docs.universalis.app/#market-board-current-data
    # GET - /api/v2/{worldDcRegion}/{itemIds}
    item_ids = ",".join(map(str, item_ids))
    response = requests.get(
        f"https://universalis.app/api/v2/{EXODUS_WORLD_ID}/{item_ids}"
    )
    data = response.json()

    results = []
    pertinent_keys = ["currentAveragePriceNQ", "nqSaleVelocity", "minPriceNQ"]
    for item_id, item_data in data["items"].items():
        this_result = {key: item_data[key] for key in pertinent_keys}
        this_result["item_id"] = int(item_id)

        recent_history = item_data["recentHistory"]
        quantities = np.array([sale["quantity"] for sale in recent_history])
        prices = np.array([sale["pricePerUnit"] for sale in recent_history])
        this_result["averageRecentHistoryStackSize"] = np.mean(quantities)
        this_result["averageRecentPrice"] = np.mean(prices)

        results.append(this_result)
    return results

async def lookup_item_by_name(
        client: pyxivapi.XIVAPIClient, item_name: str,
    ) -> Dict[str, Union[str, int]]:
    # https://github.com/xivapi/xivapi-py
    response = await client.index_search(
        indexes=["item"],
        name=item_name,
        string_algo="match",
        columns=["ID", "Name", "PriceMid", "PriceLow"],
    )
    results = response["Results"][0]
    if results["PriceLow"]:
        results["cost"] = results["PriceLow"]
    else:
        results["cost"] = results["PriceMid"]
    del results["PriceMid"], results["PriceLow"]
    return results