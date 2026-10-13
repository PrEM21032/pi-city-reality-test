// Extracts PI City's truth-layer code (Xt/Mt/C, the legacy reality-001 mission
// class and the protocol-2 mission class) from a saved copy of the artifact
// HTML, so it can be exercised in Node without a browser, WebGL or claude.ai.
// The artifact source is private and is NOT committed: pass its path in
// PI_CITY_HTML. Nothing here talks to the network or the live database.
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";

function matchBrace(s, open) {
  // open = index of '{'. Handles quotes and template literals with ${...}.
  let depth = 0, i = open, stack = [];
  for (; i < s.length; i++) {
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
      continue;
    }
  }
  throw new Error("unbalanced from " + open);
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
  const C = s.slice(s.indexOf("var C={SIM:") + 6, s.indexOf("}", s.indexOf("var C={SIM:")) + 1);
  const src = `
    const C=${C}; const Te=r=>Date.parse(r);
    const je=()=>require_nonce(), kt=()=>new Date().toISOString(), Ot=kt, xs=je;
    ${grabFn(s, "function Xt(")}
    ${grabFn(s, "function Mt(")}
    const wi=r=>Number(r)>=200&&Number(r)<300;
    const ws=(r,t)=>r.result==="exit_code"?{ok:t.exit_code===0,status:\`exit \${t.exit_code}\`}:{ok:wi(t.http_status),status:t.http_status};
    const bi=/^trig_[A-Za-z0-9]{10,60}$/;
    const Legacy=${grabClass(s, "Ee=class{")};
    const Generic=${grabClass(s, "Ge=class{")};
    const missionDefs=${s.slice(s.indexOf("ke=[") + 3, s.indexOf("];var C={SIM:") + 1)};
    return {C,Xt,Mt,Legacy,Generic,missionDefs};`;
  const require_nonce = () => Array.from(crypto.getRandomValues(new Uint8Array(12)), (b) => b.toString(16).padStart(2, "0")).join("");
  const mod = new Function("require_nonce", src)(require_nonce);
  return { ...mod, sha256 };
}
