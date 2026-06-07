const { spawnSync } = require("child_process");
const { readFileSync } = require("fs");
const { join } = require("path");

const packageJson = JSON.parse(
  readFileSync(join(__dirname, "..", "package.json"), "utf8")
);
const version = packageJson.version;
const pipArgs = ["install", `minecraft-script==${version}`];

const candidates = [
  ["py", ["-3", "-m", "pip", ...pipArgs]],
  ["python", ["-m", "pip", ...pipArgs]],
  ["python3", ["-m", "pip", ...pipArgs]],
];

let ranCandidate = false;

for (const [command, args] of candidates) {
  const result = spawnSync(command, args, { stdio: "inherit" });

  if (result.error) {
    continue;
  }

  ranCandidate = true;

  if (result.status === 0) {
    return;
  }

  continue;
}

const manualInstall = `  pip install minecraft-script==${version}\n`;

if (ranCandidate) {
  console.warn(
    "\n[minecraft-script] Failed to install the Python package via pip.\n" +
      "Install it manually with:\n" +
      manualInstall
  );
  return;
}

console.warn(
  "\n[minecraft-script] Python was not found, so the PyPI package was not installed.\n" +
    "Install Python 3 from https://www.python.org/downloads/ and run:\n" +
    manualInstall
);
