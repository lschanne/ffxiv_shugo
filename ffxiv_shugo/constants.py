import os
import toml
from enum import Enum

BASE_DIR = os.environ.get("BASE_DIR")
SRC_DIR = os.path.join(BASE_DIR, "ffxiv_shugo")
DATA_DIR = os.path.join(BASE_DIR, "data")

SECRETS_FILE = os.path.join(BASE_DIR, "secrets.toml")
with open(SECRETS_FILE, "r") as f:
    SECRETS = toml.load(f)

class Currency(Enum):
    POETICS = "poetics"
    GC_SEALS = "gc_seals"
    BICOLOR_GEMSTONES = "bicolor"
    MINOR_TOMESTONE = "minor_tome"
    MAJOR_TOMESTONE = "major_tome"
    MGP = "mgp"
    GIL = "gil"
    WOLF_MARKS = "wolf_marks"
    TROPHY_CRYSTAL = "trophy_crystal"
    MINOR_CRAFT = "minor_craft"
    MAJOR_CRAFT = "major_craft"
    MINOR_GATHER = "minor_gather"
    MAJOR_GATHER = "major_gather"

# https://xivapi.com/World
PRIMAL_DATACENTER_ID = 0
EXODUS_WORLD_ID = 53
XIVAPI_KEY = SECRETS["ffxivapi"]["api_key"]

# TODO: generate a lookup from this page?
# https://ffxiv.consolegameswiki.com/wiki/Materia
MATERIA_GRADES = [
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
]
MATERIA_MAP = {
    "combat": [
        ("Savage Aim", "Critical Hit"),
        ("Savage Might", "Determination"),
        ("Heavens' Eye", "Direct Hit Rate"),
        ("Quickarm", "Skill Speed"),
        ("Quicktongue", "Spell Speed"),
        ("Battledance", "Tenacity"),
        ("Piety", "Piety"),
    ],
    "gathering": [
        ("Gatherer's Grasp", "GP"),
        ("Gatherer's Guerdon", "Gathering"),
        ("Gatherer's Guile", "Perception"),
    ],
    "crafting": [
        ("Craftsman's Command", "Control"),
        ("Craftsman's Cunning", "CP"),
        ("Craftsman's Competence", "Craftsmanship"),
    ],
}