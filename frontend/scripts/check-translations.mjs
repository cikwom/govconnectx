import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const contextPath = path.join(root, "src/state/LanguageContext.tsx");
const context = fs.readFileSync(contextPath, "utf8");

function dictionaryKeys(language) {
  const start = context.indexOf(`  ${language}: {`);
  const end = context.indexOf("\n  },", start);
  if (start < 0 || end < 0) throw new Error(`Missing ${language} dictionary`);
  const section = context.slice(start, end);
  const keys = [...section.matchAll(/"([^"]+)"\s*:/g)].map(match => match[1]);
  const duplicates = keys.filter((key, index) => keys.indexOf(key) !== index);
  if (duplicates.length) throw new Error(`${language} has duplicate keys: ${[...new Set(duplicates)].join(", ")}`);
  return new Set(keys);
}

function sourceFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) return sourceFiles(target);
    return /\.tsx?$/.test(entry.name) && entry.name !== "vite-env.d.ts" ? [target] : [];
  });
}

const dictionaries = Object.fromEntries(["ha", "yo", "ig"].map(language => [language, dictionaryKeys(language)]));
const files = sourceFiles(path.join(root, "src"));
const used = new Set();
for (const file of files) {
  const source = fs.readFileSync(file, "utf8");
  for (const match of source.matchAll(/\bt\("([^"]+)"\)/g)) used.add(match[1]);
}

// These values are selected dynamically from the landing-page feature list.
for (const key of [
  "Speak up where you live",
  "Report broken infrastructure, safety concerns and public-service issues in your community.",
  "See what happens next",
  "Follow your report as it is received, reviewed, assigned and resolved.",
  "Move Nigeria forward",
  "Turn everyday experiences into clear signals that institutions can act on.",
  "SUBMITTED", "UNDER_REVIEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "REJECTED",
  "system admin", "department admin", "supervisor", "field officer", "citizen",
  "LOST", "FOUND", "APPROVED", "REJECTED", "pending", "system",
]) used.add(key);

const failures = [];
for (const [language, keys] of Object.entries(dictionaries)) {
  const missing = [...used].filter(key => !keys.has(key));
  if (missing.length) failures.push(`${language}: ${missing.join("; ")}`);
}
if (failures.length) {
  process.stderr.write(`Translation coverage failed:\n${failures.join("\n")}\n`);
  process.exitCode = 1;
} else {
  process.stdout.write(`Translation coverage passed: ${used.size} interface keys exist in Hausa, Yorùbá and Igbo.\n`);
}
