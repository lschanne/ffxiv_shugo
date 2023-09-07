import asyncio
import os
import pandas as pd
import pyxivapi

from ffxiv_shugo.constants import (
    DATA_DIR,
    MATERIA_GRADES,
    MATERIA_MAP,
    XIVAPI_KEY,
)

data = []
client = pyxivapi.XIVAPIClient(api_key=XIVAPI_KEY)
for grade_idx, grade_name in enumerate(MATERIA_GRADES):
    for materia_type, materia_list in MATERIA_MAP.items():
        for name, stat_boosted in materia_list:
            full_name = f"{name} Materia {grade_name}"
            row = {
                "grade_idx": grade_idx,
                "grade_name": grade_name,
                "materia_type": materia_type,
                "materia_name": full_name,
                "stat_boosted": stat_boosted,
            }

            async def get_xivapi_data():
                response = await client.index_search(
                    indexes=["item"],
                    name=row["materia_name"],
                    string_algo="match",
                    columns=["ID"],
                )
                row["id"] = response["Results"][0]["ID"]
            
            loop = asyncio.get_event_loop()
            loop.run_until_complete(get_xivapi_data())

            data.append(row)

df = pd.DataFrame(data)
df.to_csv(os.path.join(DATA_DIR, "materia.csv"))
