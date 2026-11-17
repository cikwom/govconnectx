import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoot = path.join(root, "src");
const read = relativePath => fs.readFileSync(path.join(root, relativePath), "utf8");
const css = read("src/styles.css");
const shell = read("src/components/AppShell.tsx");
const themeToggle = read("src/components/ThemeToggle.tsx");
const languageContext = read("src/state/LanguageContext.tsx");

const authPages = [
  ["login", read("src/pages/LoginPage.tsx")],
  ["registration", read("src/pages/RegisterPage.tsx")],
  ["password recovery", read("src/pages/ForgotPasswordPage.tsx")],
  ["password reset", read("src/pages/ResetPasswordPage.tsx")],
];

function sourceFiles(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const absolute = path.join(directory, entry.name);
    return entry.isDirectory() ? sourceFiles(absolute) : [absolute];
  });
}

const missingImageAlt = [];
for (const file of sourceFiles(sourceRoot).filter(file => file.endsWith(".tsx") || file.endsWith(".ts"))) {
  const source = fs.readFileSync(file, "utf8");
  for (const match of source.matchAll(/<img\b[^>]*>/gs)) {
    if (!/\balt\s*=/.test(match[0])) missingImageAlt.push(path.relative(root, file));
  }
}

const checks = [
  [":focus-visible", css.includes(":focus-visible"), "visible keyboard focus"],
  [".skip-link:focus", css.includes(".skip-link:focus") && shell.includes('className="skip-link"'), "skip navigation"],
  ["prefers-reduced-motion", css.includes("prefers-reduced-motion:reduce"), "reduced-motion support"],
  ["prefers-contrast", css.includes("prefers-contrast: more"), "increased-contrast support"],
  ["forced-colors", css.includes("forced-colors: active"), "forced-colors support"],
  ["44px controls", /min-height:\s*44px/.test(css), "minimum interactive control size"],
  ["24px checkboxes/radios", /input\[type="checkbox"\][\s\S]*?width:\s*24px/.test(css) && /input\[type="radio"\][\s\S]*?height:\s*24px/.test(css), "checkbox and radio target size"],
  ["theme toggle name", themeToggle.includes("aria-label=") && themeToggle.includes("nextTheme"), "accessible theme toggle name"],
  ["document language", languageContext.includes("document.documentElement.lang = language"), "document language follows selected language"],
  ["image alternative text", missingImageAlt.length === 0, missingImageAlt.length ? "images missing alt text: " + [...new Set(missingImageAlt)].join(", ") : "all JSX images have alt text"],
];

for (const [name, page] of authPages) {
  const controls = [...page.matchAll(/<(input|select|textarea)\b/g)].length;
  const labels = [...page.matchAll(/<label\b/g)].length;
  checks.push([name + " labelled controls", labels >= controls, name + " form controls have associated label wrappers (" + labels + " labels / " + controls + " controls)"]);
  checks.push([name + " main landmark", /<main\b/.test(page), name + " page has a main landmark"]);
  checks.push([name + " error announcement", /role="alert"/.test(page), name + " validation errors use an alert region"]);
}

const failures = checks.filter(([, passed]) => !passed);
for (const [name, passed, description] of checks) {
  console.log((passed ? "PASS: " : "FAIL: ") + description + " (" + name + ")");
}
if (failures.length) process.exitCode = 1;
else console.log("Accessibility source checks passed: " + checks.length + " checks. Automated source checks do not replace keyboard, screen-reader, contrast and manual WCAG review.");
