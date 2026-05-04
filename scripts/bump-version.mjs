import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const input = process.argv[2];

if (!input) {
  console.error("Usage: node scripts/bump-version.mjs <patch|minor|major|x.y.z>");
  process.exit(1);
}

const packageJsonPath = path.join(root, "package.json");
const packageLockPath = path.join(root, "package-lock.json");
const pluginJsonPath = path.join(root, "plugins", "oh-my-paper", ".claude-plugin", "plugin.json");
const marketplaceJsonPath = path.join(root, ".claude-plugin", "marketplace.json");
const cargoTomlPath = path.join(root, "src-tauri", "Cargo.toml");
const tauriConfigPath = path.join(root, "src-tauri", "tauri.conf.json");

const packageJson = readJson(packageJsonPath);
const currentVersion = packageJson.version;
const nextVersion = resolveNextVersion(currentVersion, input);

packageJson.version = nextVersion;
writeJson(packageJsonPath, packageJson);

if (fs.existsSync(packageLockPath)) {
  const packageLock = readJson(packageLockPath);
  packageLock.version = nextVersion;
  if (packageLock.packages?.[""]) {
    packageLock.packages[""].version = nextVersion;
  }
  writeJson(packageLockPath, packageLock);
}

// Plugin 版本同步更新
if (fs.existsSync(pluginJsonPath)) {
  const pluginJson = readJson(pluginJsonPath);
  pluginJson.version = nextVersion;
  writeJson(pluginJsonPath, pluginJson);
}

if (fs.existsSync(marketplaceJsonPath)) {
  const marketplaceJson = readJson(marketplaceJsonPath);
  marketplaceJson.metadata.version = nextVersion;
  for (const plugin of marketplaceJson.plugins || []) {
    plugin.version = nextVersion;
  }
  writeJson(marketplaceJsonPath, marketplaceJson);
}

// Tauri 配置更新（仅在文件存在时）
if (fs.existsSync(cargoTomlPath)) {
  const cargoToml = fs.readFileSync(cargoTomlPath, "utf8");
  fs.writeFileSync(
    cargoTomlPath,
    cargoToml.replace(/^version = ".*"$/m, `version = "${nextVersion}"`),
  );
}

if (fs.existsSync(tauriConfigPath)) {
  const tauriConfig = readJson(tauriConfigPath);
  tauriConfig.version = nextVersion;
  writeJson(tauriConfigPath, tauriConfig);
}

console.log(nextVersion);

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, value) {
  fs.writeFileSync(filePath, `${JSON.stringify(value, null, 2)}\n`);
}

function resolveNextVersion(current, target) {
  if (/^\d+\.\d+\.\d+$/.test(target)) {
    return target;
  }

  const match = current.match(/^(\d+)\.(\d+)\.(\d+)$/);
  if (!match) {
    throw new Error(`Unsupported current version: ${current}`);
  }

  let [major, minor, patch] = match.slice(1).map(Number);
  if (target === "patch") {
    patch += 1;
  } else if (target === "minor") {
    minor += 1;
    patch = 0;
  } else if (target === "major") {
    major += 1;
    minor = 0;
    patch = 0;
  } else {
    throw new Error(`Unsupported target version: ${target}`);
  }

  return `${major}.${minor}.${patch}`;
}
