// Extracts PI City's truth-layer code (the `C` labels, the truth-level
// functions, the legacy reality-001 mission class, the protocol-2 mission
// class and the mission definitions) from a saved copy of the artifact HTML,
// so it can be exercised in Node without a browser, WebGL or claude.ai.
//
// It also evaluates the city's own module-level declarations for both
// mission subsystems (tab holder id, nonce and time helpers, escaping,
// constants). Without them, methods such as dispatch, retry and reset throw
// ReferenceErrors, and a test expecting "nothing fired" can pass by crashing.
// Each load() is a fresh page load with its own tab holder id, so two loads
// behave like two open views.
//
// The artifact source is private and is NOT committed: pass its path in
// PI_CITY_HTML. Nothing here talks to the network or the live database.
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";

function matchBrace(s, open) {
  // open = index of '{'. Handles quotes and template literals with ${...}.
  let depth = 0;
  const stack = [];
  for (let i = open; i < s.length; i++) {
    const c = s[i], mode = stack[stack.length - 1];
    if (mode === "'" || mode === '"') { if (c === "\\") i++; else if (c === mode) stack.pop(); continue; }
    if (mode === "`") {
      if (c === "\\") i++;
      else if (c === "`") stack.pop();
      else if (c === "$" && s[i + 1] === "{") { stack.push("${"); i++; }
      continue;
    }
    if (c === "'" || c === '"' || c === "`") { stack.push(c); continue; }
    if (c === "{") { stack.push("{"); depth++; continue; }
    if (c === "}") {
      const top = stack.pop();
      if (top === "{") { depth--; if (depth === 0 && stack.length === 0) return i; }
    }
  }
  throw new Error("unbalanced from " + open);
}

function between(s, start, end) {
  const i = s.indexOf(start);
  if (i < 0) throw new Error("marker not found: " + start);
  const j = s.indexOf(end, i);
  if (j < 0) throw new Error("marker not found: " + end);
  return s.slice(i, j);
}

function grabClass(s, marker) {
  const i = s.indexOf(marker);
  if (i < 0) throw new Error("marker not found: " + marker);
  const open = s.indexOf("{", i + marker.length - 1);
  return "class" + s.slice(open, matchBrace(s, open) + 1);
}

function grabFn(s, marker) {
  const i = s.indexOf(marker);
  if (i < 0) throw new Error("marker not found: " + marker);
  const open = s.indexOf("{", i);
  return s.slice(i, matchBrace(s, open) + 1);
}

export function load(path = process.env.PI_CITY_HTML) {
  if (!path) return null;
  const s = readFileSync(path, "utf8");
  const sha256 = createHash("sha256").update(s).digest("hex");
  const src = `
    ${between(s, "var C={SIM:", "},")}};
    const Te=r=>Date.parse(r);
    ${grabFn(s, "function Xt(")}
    ${grabFn(s, "function Mt(")}
    ${between(s, 'var gi="Claude Code Remote"', ",Ge=class{")};
    const Generic=${grabClass(s, "Ge=class{")};
    ${between(s, 'var Yt="reality-001"', ",Ee=class{")};
    const Legacy=${grabClass(s, "Ee=class{")};
    const missionDefs=${s.slice(s.indexOf("ke=[") + 3, s.indexOf("];var C={SIM:") + 1)};
    return {C,Xt,Mt,Legacy,Generic,missionDefs,tab:bs};`;
  return { ...new Function(src)(), sha256 };
}
