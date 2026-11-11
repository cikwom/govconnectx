import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const css = fs.readFileSync(path.join(root, "src/styles.css"), "utf8");
const shell = fs.readFileSync(path.join(root, "src/components/AppShell.tsx"), "utf8");
const themeToggle = fs.readFileSync(path.join(root, "src/components/ThemeToggle.tsx"), "utf8");

const checks = [
  [":focus-visible", css.includes(":focus-visible"), "visible keyboard focus"],
  [".skip-link:focus", css.includes(".skip-link:focus") && shell.includes('className="skip-link"'), "skip navigation"],
  ["prefers-reduced-motion", css.includes("prefers-reduced-motion:reduce"), "reduced-motion support"],
  ["prefers-contrast", css.includes("prefers-contrast: more"), "increased-contrast support"],
  ["forced-colors", css.includes("forced-colors: active"), "forced-colors support"],
  ["44px controls", /min-height:\s*44px/.test(css), "minimum interactive control size"],
  ["24px checkboxes/radios", /input\[type="checkbox"\][\s\S]*?width:\s*24px/.test(css) && /input\[type="radio"\][\s\S]*?height:\s*24px/.test(css), "checkbox and radio target size"],
  ["theme toggle name", themeToggle.includes("aria-label=") && themeToggle.includes("nextTheme"), "accessible theme toggle name"],
];

const failures = checks.filter(([, passed]) => !passed);
for (const [name, passed, description] of checks) {
  console.log((passed ? "PASS: " : "FAIL: ") + description + " (" + name + ")");
}
if (failures.length) process.exitCode = 1;
else console.log("Accessibility foundation checks passed: " + checks.length + " checks. Manual WCAG review is still required.");
