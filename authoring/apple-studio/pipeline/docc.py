#!/usr/bin/env python3
"""Fetch an Apple DocC JSON page and render it as readable text.

Written in Phase 6 (2026-09), where it fed eight parallel distillers.

WHY THIS EXISTS: developer.apple.com serves documentation as a JavaScript shell.
WebFetch on a human doc URL returns navigation chrome and no content. The real
content is the DocC JSON behind it:

    https://developer.apple.com/tutorials/data/documentation/<path>.json

Two endpoint traps this handles, both hit for real in Phase 6:
  - Tutorials are NOT under /documentation/. `documentation/instruments` 404s;
    the Instruments tutorial is at /tutorials/data/tutorials/instruments.json
    (use --tutorial).
  - Overloaded symbol names carry a DocC disambiguation suffix (-pt7n, -3mzv3,
    -swift.struct). The undisambiguated path may 301 or 404 more or less
    arbitrarily; --children prints the exact child URLs Apple's own navigation
    uses.

CAUTION, learned in Phase 6: a 200 here is NOT evidence a symbol exists in the
shipped SDK. The live docs were found simultaneously behind the OS (context
window) and ahead of the SDK (SystemLanguageModel.variant, documented and
absent). Compile anything you intend to ship — see typecheck_snippets.py.

Usage:  python3 docc.py FoundationModels/LanguageModelSession
        python3 docc.py --children FoundationModels/SystemLanguageModel
        python3 docc.py --tutorial instruments
"""
import json, sys, urllib.request, re

BASE_DOC = "https://developer.apple.com/tutorials/data/documentation/"
BASE_TUT = "https://developer.apple.com/tutorials/data/tutorials/"

def fetch(path, tutorial=False):
    url = (BASE_TUT if tutorial else BASE_DOC) + path + ".json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r), url

def render(o, acc, refs):
    if isinstance(o, dict):
        t = o.get("type")
        if t == "text":            acc.append(o.get("text", ""))
        elif t == "codeVoice":     acc.append("`" + o.get("code", "") + "`")
        elif t == "heading":       acc.append("\n\n### " + o.get("text", "") + "\n")
        elif t == "codeListing":   acc.append("\n```swift\n" + "\n".join(o.get("code", [])) + "\n```\n")
        elif t == "declarations":
            for d in o.get("declarations", []):
                acc.append("\n```swift\n" + "".join(x.get("text", "") for x in d.get("tokens", [])) + "\n```\n")
        elif t == "reference":
            r = refs.get(o.get("identifier"), {})
            acc.append("`" + (r.get("title") or o.get("identifier", "")) + "`")
        elif t == "paragraph":
            for v in o.get("inlineContent", []): render(v, acc, refs)
            acc.append("\n\n"); return
        elif t in ("unorderedList", "orderedList"):
            for it in o.get("items", []):
                acc.append("\n- "); render(it.get("content", []), acc, refs)
            acc.append("\n"); return
        for k, v in o.items():
            if k not in ("type", "text", "code", "declarations", "identifier", "inlineContent", "items"):
                render(v, acc, refs)
    elif isinstance(o, list):
        for v in o: render(v, acc, refs)

def main():
    args = [a for a in sys.argv[1:]]
    children = "--children" in args; args = [a for a in args if a != "--children"]
    tut = "--tutorial" in args;      args = [a for a in args if a != "--tutorial"]
    for path in args:
        try:
            d, url = fetch(path, tut)
        except Exception as e:
            print(f"\n{'='*78}\n!! FETCH FAILED {path}: {e}\n"); continue
        m = d.get("metadata", {})
        print(f"\n{'='*78}\n# {m.get('title','?')}   [{m.get('symbolKind') or m.get('roleHeading') or ''}]")
        print(f"SOURCE: {url}")
        pl = m.get("platforms") or []
        if pl:
            print("PLATFORMS: " + ", ".join(f"{p.get('name')} {p.get('introducedAt','?')}{' BETA' if p.get('beta') else ''}" for p in pl))
        ab = "".join(x.get("text", "") for x in d.get("abstract", []))
        if ab: print(f"ABSTRACT: {ab}")
        refs = d.get("references", {})
        acc = []; render(d.get("primaryContentSections", []), acc, refs)
        body = re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", "".join(acc)))
        print(body.strip())
        if children:
            print("\n--- TOPIC SECTIONS (children) ---")
            for sec in d.get("topicSections", []):
                print(f"\n## {sec.get('title')}")
                for i in sec.get("identifiers", []):
                    r = refs.get(i, {})
                    u = (r.get("url") or "").replace("/documentation/", "", 1)
                    print(f"   {r.get('title','?'):50s} {u}")
        for sec in d.get("seeAlsoSections", []) if children else []:
            print(f"\n## SEE ALSO: {sec.get('title')}")
            for i in sec.get("identifiers", []):
                r = refs.get(i, {}); print(f"   {r.get('title','?')}")

main()
