import asyncio
import os
import pandas as pd
import pyxivapi
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from typing import Any, Dict, List

from ffxiv_shugo.constants import (
    Currency,
    DATA_DIR,
    MATERIA_MAP,
    XIVAPI_KEY,
)

VENDOR_ID_REGEX = re.compile(r"^vendor\d+$")

# Sometimes they get lazy with the name
# e.g. they use "Combat materia VII" as a catch-all
def map_item_name(item_name: str) -> List[str]:
   if item_name.lower().startswith("combat materia"):
      grade = item_name.split()[-1]
      return [
         f"{materia} Materia {grade}"
         for materia, _ in MATERIA_MAP["combat"]
      ]
   else:
      return [item_name]

def extract_item_names(html_text: str) -> List[str]:
   # row.text looks like "\xa0\xa0{item_name}"
   return map_item_name(html_text.rsplit("\xa0", 1)[-1])

def extract_item_cost(html_text: str) -> int:
   # row.text looks like "\xa0{item_cost}\n"
   # the value can contain commas, but should always be an integer
   return int(html_text.strip().rsplit("\xa0", 1)[-1].replace(",", ""))

def add_rows(
   data: List[Dict[str, Any]],
   client: pyxivapi.XIVAPIClient,
   name_col: BeautifulSoup,
   cost_col: BeautifulSoup,
   currency: Currency,
) -> None:
   item_names = extract_item_names(name_col.text)
   item_cost = extract_item_cost(cost_col.text)
   for item_name in item_names:
      row = {
         "item_name": item_name,
         "currency_cost": item_cost,
         "currency_type": currency.value,
      }
      async def get_xivapi_data():
         response = await client.index_search(
            indexes=["item"],
            name=row["item_name"],
            string_algo="match",
            columns=["ID", "IsUntradable"],
         )
         try:
            results = response["Results"][0]
         except IndexError:
            row["id"] = None
            row["is_untradable"] = None
         else:
            row["id"] = results["ID"]
            row["is_untradable"] = results["IsUntradable"]

      loop = asyncio.get_event_loop()
      loop.run_until_complete(get_xivapi_data())
      data.append(row)

def handle_sortable_tables(
      data: List[Dict[str, Any]],
      client: pyxivapi.XIVAPIClient,
      url: str,
      currency: Currency,
      is_craft: bool=False,
      is_gather: bool=False,
   ) -> None:
   """
   A lot of the pages on the site are pretty cookie cutter thankfully.
   """
   soup = init_soup(url)
   if is_craft and is_gather:
      raise Exception("is_craft and is_gather are mutually exclusive args")
   if is_craft:
      major, minor = Currency.MAJOR_CRAFT, Currency.MINOR_CRAFT
   elif is_gather:
      major, minor = Currency.MAJOR_GATHER, Currency.MINOR_GATHER

   for table in soup.find_all("table", "npc", "sortable"):
      for row in table.find_all("tr"):
         if not VENDOR_ID_REGEX.match(row.get("id", "")):
            continue
         cols = row.find_all("td")
         name_col, cost_col = cols[0], cols[-1]
         if is_craft or is_gather:
            if cost_col.get("data-sort-value").lower().startswith("purple"):
               currency = major
            else:
               currency = minor
         add_rows(data, client, name_col, cost_col, currency)

def init_soup(url: str) -> BeautifulSoup:
   options = webdriver.ChromeOptions()
   options.add_argument("--log-level=3")
   options.add_argument("--ignore-certificate-errors")
   options.add_argument("--incognito")
   options.add_argument("--headless")

   driver = webdriver.Chrome(options)
   driver.get(url)
   page_source = driver.page_source
   driver.close()
   soup = BeautifulSoup(page_source, "lxml")
   return soup

# TOMES OF POETICS
def add_poetics(data: List[Dict[str, Any]], client: pyxivapi.XIVAPIClient):
   soup = init_soup(
      "https://ffxiv.consolegameswiki.com/wiki/Allagan_Tomestone_of_Poetics"
   )
   item_tables = soup.find_all(class_="item table")
   for table in item_tables:
      # row[0] is is the name of the expansion to which the item table belongs
      # from then on, we have rows proceeding like this:
      # item_name, item_type, item_cost, item_name, item_type, item_cost, etc.
      for idx, row in enumerate(table.findChildren("td")[1:]):
         row_type = idx % 3
         if row_type == 0:
               name_col = row
         elif row_type == 1:
               pass
         else:
               cost_col = row
               add_rows(data, client, name_col, cost_col, Currency.POETICS)

# GC Seals
def add_gc_seals(data: List[Dict[str, Any]], client: pyxivapi.XIVAPIClient):
   handle_sortable_tables(
      data,
      client,
      "https://ffxiv.consolegameswiki.com/wiki/Flame_Quartermaster",
      Currency.GC_SEALS,
   )

# Bicolor gems
def add_bicolor_gems(
   data: List[Dict[str, Any]], client: pyxivapi.XIVAPIClient,
):
   soup = init_soup(
      "https://ffxiv.consolegameswiki.com/wiki/Bicolor_Gemstone"
   )
   for table in soup.find_all("table", "pve", "sortable"):
      if "jquery-tablesorter" in table.get("class"):
         continue
      # first row is the header
      for row in table.find_all("tr")[1:]:
         cols = row.find_all("td")
         # there are some subheaders for the zones that have only 1 column
         if len(cols) < 3:
            continue
         name_col, cost_col = cols[0], cols[1]
         add_rows(data, client, name_col, cost_col, Currency.BICOLOR_GEMSTONES)

# Minor tomestones
def add_minor_tomestones(
   data: List[Dict[str, Any]], client: pyxivapi.XIVAPIClient,
):
   soup = init_soup(
      "https://ffxiv.consolegameswiki.com/wiki/Allagan_Tomestone_of_Causality"
   )
   for table in soup.find_all("table", "item", "sortable"):
      for row in table.find_all("tr")[1:]:
         cols = row.find_all("td")
         name_col, cost_col = cols[0], cols[-1]
         add_rows(data, client, name_col, cost_col, Currency.MINOR_TOMESTONE)

# Wolf marks
def add_wolf_marks(
   data: List[Dict[str, Any]], client: pyxivapi.XIVAPIClient,
):
   soup = init_soup(
      "https://ffxiv.consolegameswiki.com/wiki/"
      "Mark_Quartermaster/Wolf_Marks_(Other)#Miscellaneous"
   )
   for table in soup.find_all("table", "npc", "sortable"):
      for row in table.find_all("tr")[1:]:
         cols = row.find_all("td")
         name_col, cost_col = cols[0], cols[-1]
         add_rows(data, client, name_col, cost_col, Currency.WOLF_MARKS)
   
# Major/minor craft
def add_crafting(
   data: List[Dict[str, Any]], client: pyxivapi.XIVAPIClient,
):
   for url in (
      (
         "https://ffxiv.consolegameswiki.com/wiki/Scrip_Exchange_(Radz-at-Han)"
         "/Crafters%27_Scrip_(Gear)"
      ),
      (
         "https://ffxiv.consolegameswiki.com/wiki/Scrip_Exchange_(Radz-at-Han)/"
         "Crafters%27_Scrip_(Materia)"
      ),
      (
         "https://ffxiv.consolegameswiki.com/wiki/Scrip_Exchange_(Radz-at-Han)/"
         "Crafters%27_Scrip_(Gear)_-_Purple_Scrip_Exchange"
      ),
   ):
      handle_sortable_tables(data, client, url, currency=None, is_craft=True)

# Major/minor gathering
def add_gathering(data: List[Dict[str, Any]], client: pyxivapi.XIVAPIClient):
   for url in (
      (
         "https://ffxiv.consolegameswiki.com/wiki/Scrip_Exchange_(Radz-at-Han)/"
         "Gatherers%27_Scrip_(Gear)"
      ),
      (
         "https://ffxiv.consolegameswiki.com/wiki/Scrip_Exchange_(Radz-at-Han)/"
         "Gatherers%27_Scrip_(Materials/Misc.)"
      ),
      (
         "https://ffxiv.consolegameswiki.com/wiki/Scrip_Exchange_(Radz-at-Han)/"
         "Gatherers%27_Scrip_(Materia)"
      )
   ):
      handle_sortable_tables(data, client, url, currency=None, is_gather=True)

def main():
   client = pyxivapi.XIVAPIClient(api_key=XIVAPI_KEY)
   data = []
   data_loaders = [
      add_bicolor_gems,
      add_crafting,
      add_gathering,
      add_gc_seals,
      add_minor_tomestones,
      add_poetics,
      add_wolf_marks,
   ]
   for loader in data_loaders:
      loader(data, client)

   loop = asyncio.get_event_loop()
   loop.run_until_complete(client.session.close())

   df = pd.DataFrame(data)
   if not os.path.exists(DATA_DIR):
      os.mkdir(DATA_DIR)
   df.to_csv(os.path.join(DATA_DIR, "items_by_currency.csv"))

if __name__ == "__main__":
   main()