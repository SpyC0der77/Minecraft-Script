const { spawnSync } = require("child_process");
const { readFileSync } = require("fs");
const { join } = require("path");

const packageJson = JSON.parse(
  readFileSync(join(__dirname, "..", "package.json"), "utf8")
);
const version = packageJson.version;
const repositoryUrl =
  packageJson.repository?.url?.replace(/^git\+/, "") ??
  "https://github.com/SpyC0der77/Minecraft-Script.git";
const gitUrl = repositoryUrl.replace(/\.git$/, "");
const pipSpec = `git+${gitUrl}.git@v${version}`;
const pipArgs = ["install", pipSpec];

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

const manualInstall = `  pip install git+${gitUrl}.git@v${version}\n`;

if (ranCandidate) {
  console.warn(
    "\n[minecraft-script] Failed to install the Python package from GitHub.\n" +
      "Install it manually with:\n" +
      manualInstall
  );
  return;
}

console.warn(
  "\n[minecraft-script] Python was not found, so the package was not installed.\n" +
    "Install Python 3 from https://www.python.org/downloads/ and run:\n" +
    manualInstall
);
