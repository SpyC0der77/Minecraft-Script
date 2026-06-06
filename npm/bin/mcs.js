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

  if (result.error?.code === "ENOENT") {
    continue;
  }

  process.exit(result.status ?? 1);
}

console.error(
  "Minecraft Script requires Python 3.\n" +
    "Install Python from https://www.python.org/downloads/ and run:\n" +
    "  pip install minecraft-script"
);
process.exit(1);
