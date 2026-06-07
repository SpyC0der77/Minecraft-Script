import json
from pathlib import Path
from uuid import uuid4 as _uuid4

version = "0.3.4"
module_folder = str(Path(__file__).resolve().parent)

# load Minecraft-Script configuration
with open(f"{module_folder}/config.json", "rt", encoding="utf-8") as file:
    COMMON_CONFIG: dict = json.loads(file.read())


def generate_uuid() -> str:
    return str(_uuid4())
