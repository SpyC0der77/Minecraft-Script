#!/usr/bin/env node

const { spawnSync } = require("child_process");

const mcsArgs = process.argv.slice(2);
const pythonModuleArgs = ["-m", "minecraft_script", ...mcsArgs];

const candidates = [
  ["py", ["-3", ...pythonModuleArgs]],
  ["python", pythonModuleArgs],
  ["python3", pythonModuleArgs],
];

for (const [command, args] of candidates) {
  const result = spawnSync(command, args, { stdio: "inherit" });

  if (result.error) {
    continue;
  }

  if (result.status != null) {
    process.exit(result.status);
  }
}

console.error(
  "Minecraft Script requires Python 3.\n" +
    "Install Python from https://www.python.org/downloads/ and run:\n" +
    "  pip install git+https://github.com/SpyC0der77/Minecraft-Script.git@main"
);
process.exit(1);
