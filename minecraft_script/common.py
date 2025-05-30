import json
from uuid import uuid4 as _uuid4
import platform
os = platform.system().lower()

version = "0.2.2"
module_folder = ""
if os == "windows":
    print("Detected Windows OS")
    module_folder = "/".join(__file__.split('\\')[:-1])
elif os == "darwin":
    print("Detected macOS")
    module_folder = "/".join(__file__.split('/')[:-1])


# load Minecraft-Script configuration
with open(f"{module_folder}/config.json", "rt", encoding="utf-8") as file:
    COMMON_CONFIG: dict = json.loads(file.read())


def generate_uuid() -> str:
    return str(_uuid4())
