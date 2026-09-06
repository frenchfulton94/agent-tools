#!/usr/bin/env python3
"""Check a repo's TOOLS.md against the evidence in the repo.

Reports drift: commands that no longer exist, dependencies or versions that no longer
match the manifest, package-manager contradictions, directory conventions that are not
in the tree, and a manifest that changed more recently than TOOLS.md.

Exit codes: 0 clean, 1 drift found, 2 could not run (no TOOLS.md, bad path).
Stdlib only. Non-interactive. Data on stdout, diagnostics on stderr.
"""

import argparse
import json
import os
import re
import subprocess
import sys

# Lockfile -> package manager. Same table as the skill body; keep them in sync.
LOCKFILES = {
    "pnpm-lock.yaml": "pnpm",
    "package-lock.json": "npm",
    "npm-shrinkwrap.json": "npm",
    "yarn.lock": "yarn",
    "bun.lock": "bun",
    "bun.lockb": "bun",
    "uv.lock": "uv",
    "poetry.lock": "poetry",
    "Pipfile.lock": "pipenv",
    "Cargo.lock": "cargo",
    "go.sum": "go",
    "Gemfile.lock": "bundler",
    "composer.lock": "composer",
}

JS_MANAGERS = {"pnpm", "npm", "yarn", "bun"}

# Subcommands that are not script names, so `pnpm <this>` must not be read as a script.
NOT_SCRIPTS = {
    "install", "i", "add", "remove", "rm", "up", "update", "upgrade", "outdated",
    "why", "audit", "dlx", "exec", "create", "init", "link", "publish", "pack",
    "run", "test", "start", "list", "ls", "store", "prune", "dedupe", "x", "global",
}

# Lines that deliberately name things absent from the repo; excluded from existence checks.
# "no `pages/` directory exists" is a true statement about an absent path, not drift.
NEGATION = re.compile(
    r"do not (use|create|add|install)|never (use|create|add)"
    r"|\bno\s+`|does not exist|has no\b|instead of",
    re.I,
)

BACKTICK = re.compile(r"`([^`\n]+)`")
PACKAGE_LINE = re.compile(
    r"\*\*Packages?:?\*\*\s*`([^`]+)`(?:\s*`([^`]+)`)?", re.I
)
DIRPATH = re.compile(r"^[\w./@-]+/$")


def read(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def find_tools_md(root):
    """Return (path, [all case variants found]). Root-level only."""
    try:
        entries = os.listdir(root)
    except OSError as exc:
        print(f"error: cannot read {root}: {exc}", file=sys.stderr)
        sys.exit(2)
    variants = sorted(e for e in entries if e.lower() == "tools.md")
    if not variants:
        return None, []
    preferred = "TOOLS.md" if "TOOLS.md" in variants else variants[0]
    return os.path.join(root, preferred), variants


def load_package_json(root):
    raw = read(os.path.join(root, "package.json"))
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"warning: package.json is not valid JSON: {exc}", file=sys.stderr)
        return None


def load_pyproject_deps(root):
    """Best-effort dependency names from pyproject.toml. tomllib is 3.11+; regex otherwise."""
    path = os.path.join(root, "pyproject.toml")
    raw = read(path)
    if raw is None:
        return {}
    deps = {}
    try:
        import tomllib  # noqa: PLC0415 - optional, stdlib only on 3.11+
        data = tomllib.loads(raw)
        listed = data.get("project", {}).get("dependencies", []) or []
        poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {}) or {}
        for item in listed:
            # "fastapi>=0.115.0" -> name "fastapi", spec ">=0.115.0". Keeping the whole
            # requirement string would make every version comparison a false mismatch.
            name = re.split(r"[<>=!~\[ ;]", item, 1)[0].strip()
            if name:
                deps[name.lower()] = item[len(name):].strip()
        for name, spec in poetry.items():
            deps[name.lower()] = spec if isinstance(spec, str) else ""
    except Exception:
        for line in raw.splitlines():
            m = re.match(r'\s*"([A-Za-z0-9._-]+)[^"]*"\s*,?\s*$', line)
            if m:
                deps[m.group(1).lower()] = line.strip().strip('",')
    return deps


def make_targets(root):
    raw = read(os.path.join(root, "Makefile"))
    if raw is None:
        return set()
    return {m.group(1) for m in re.finditer(r"^([A-Za-z0-9_.-]+):(?!=)", raw, re.M)}


def just_recipes(root):
    for name in ("justfile", "Justfile", ".justfile"):
        raw = read(os.path.join(root, name))
        if raw is not None:
            return {m.group(1) for m in re.finditer(r"^([A-Za-z0-9_-]+)\s*:", raw, re.M)}
    return set()


def git_mtime(root, relpath):
    """Last commit timestamp for a path, falling back to filesystem mtime."""
    full = os.path.join(root, relpath)
    if not os.path.exists(full):
        return None
    try:
        out = subprocess.run(
            ["git", "-C", root, "log", "-1", "--format=%ct", "--", relpath],
            capture_output=True, text=True, timeout=10, check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return int(out.stdout.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    try:
        return int(os.path.getmtime(full))
    except OSError:
        return None


def content_lines(text):
    """Lines eligible for existence checks.

    Skips fenced code blocks, negation lines, and the Unknowns section, all of which
    legitimately name things that are absent from the repo.
    """
    out, fenced, in_unknowns = [], False, False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            fenced = not fenced
            continue
        if stripped.startswith("#"):
            in_unknowns = "unknown" in stripped.lower()
        if fenced or in_unknowns or NEGATION.search(line):
            continue
        out.append(line)
    return out


def normalize_version(spec):
    return re.sub(r"^[\^~>=<\s v]+", "", str(spec)).strip()


def section(text, name):
    """Lines under the heading whose title contains `name`, up to the next heading.

    Capability paths are checked section-scoped: `.env` appears in the deploy section
    and must never be read as a path that ought to exist.
    """
    out, inside = [], False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            inside = name.lower() in stripped.lower()
            continue
        if inside:
            out.append(line)
    return out


def check(root):
    findings = []

    def add(kind, message):
        findings.append({"kind": kind, "message": message})

    tools_path, variants = find_tools_md(root)
    if tools_path is None:
        print(f"error: no TOOLS.md at {os.path.abspath(root)}", file=sys.stderr)
        sys.exit(2)
    if len(variants) > 1:
        add("drift", f"multiple case variants of TOOLS.md at root: {', '.join(variants)}; keep one")

    text = read(tools_path)
    if text is None:
        print(f"error: cannot read {tools_path}", file=sys.stderr)
        sys.exit(2)
    lines = content_lines(text)
    body = "\n".join(lines)
    ticks = [m.group(1).strip() for line in lines for m in BACKTICK.finditer(line)]

    # --- package manager -------------------------------------------------
    present = [lf for lf in LOCKFILES if os.path.exists(os.path.join(root, lf))]
    js_locks = [lf for lf in present if LOCKFILES[lf] in JS_MANAGERS]
    expected = {LOCKFILES[lf] for lf in present}

    if len(js_locks) > 1:
        add("drift", f"more than one JS lockfile at root ({', '.join(js_locks)}); "
                     "the package manager is ambiguous")

    pkg = load_package_json(root)
    if pkg:
        declared = str(pkg.get("packageManager", "")).split("@")[0]
        if declared and js_locks and declared not in {LOCKFILES[lf] for lf in js_locks}:
            add("drift", f"packageManager field says {declared} but the lockfile is "
                         f"{', '.join(js_locks)}")

    expected_js = {LOCKFILES[lf] for lf in js_locks}
    if expected_js:
        # Collapse to one finding per wrong manager: a manager swap touches every
        # command line, and 30 identical findings bury the rest of the report.
        wrong = {}
        for cmd in ticks:
            head = cmd.split()[0] if cmd.split() else ""
            if head in JS_MANAGERS and head not in expected_js:
                wrong.setdefault(head, []).append(cmd)
        for manager, cmds in sorted(wrong.items()):
            sample = ", ".join(f"`{c}`" for c in cmds[:3])
            more = f" and {len(cmds) - 3} more" if len(cmds) > 3 else ""
            add("drift", f"TOOLS.md uses {manager} in {len(cmds)} command(s) ({sample}{more}) "
                         f"but this repo uses {'/'.join(sorted(expected_js))}")

    # --- commands --------------------------------------------------------
    scripts = set((pkg or {}).get("scripts", {}) or {})
    targets, recipes = make_targets(root), just_recipes(root)

    for cmd in ticks:
        parts = cmd.split()
        # `pnpm add <pkg>` documents a form, not a specific script; skip placeholders.
        if len(parts) < 2 or "<" in cmd or ">" in cmd:
            continue
        head, rest = parts[0], parts[1:]
        if head in JS_MANAGERS and pkg is not None:
            if rest[0] == "run" and len(rest) > 1:
                name = rest[1]
            elif head != "npm" and rest[0] not in NOT_SCRIPTS:
                name = rest[0]
            else:
                continue
            if scripts and name not in scripts:
                add("drift", f"`{cmd}` refers to script '{name}', which is not in "
                             "package.json scripts")
        elif head == "make" and targets and rest[0] not in targets:
            add("drift", f"`{cmd}` refers to Make target '{rest[0]}', which is not in the Makefile")
        elif head == "just" and recipes and rest[0] not in recipes:
            add("drift", f"`{cmd}` refers to just recipe '{rest[0]}', which is not in the justfile")

    # --- dependencies and versions ---------------------------------------
    deps = {}
    if pkg:
        for field in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            deps.update({k.lower(): v for k, v in (pkg.get(field) or {}).items()})
    deps.update(load_pyproject_deps(root))

    if deps:
        for line in lines:
            m = PACKAGE_LINE.search(line)
            if not m:
                continue
            name, version = m.group(1).strip().lower(), m.group(2)
            if name not in deps:
                add("drift", f"TOOLS.md lists dependency '{name}', which is not in the manifest")
            elif version:
                want, have = normalize_version(version), normalize_version(deps[name])
                if want and have and want != have and not have.startswith(want):
                    add("drift", f"'{name}' is {deps[name]} in the manifest but "
                                 f"{version} in TOOLS.md")

        for tick in ticks:
            if tick.startswith("@") and "/" in tick and " " not in tick:
                if tick.lower() not in deps:
                    add("drift", f"TOOLS.md names `{tick}`, which is not in the manifest")

    # --- directory conventions -------------------------------------------
    for tick in ticks:
        if DIRPATH.match(tick) and not tick.startswith("."):
            if not os.path.isdir(os.path.join(root, tick.rstrip("/"))):
                add("warn", f"TOOLS.md names directory `{tick}`, which does not exist")

    # --- agent capabilities ------------------------------------------------
    # Parsed by cell, not by line: the third column is prose and routinely contains
    # words like "instead of" that the negation filter would otherwise swallow,
    # taking the whole row's path check with it.
    for line in section(text, "Agent capabilities"):
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.count("|") < 4:
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 3 or not cells[0] or cells[0].startswith("-"):
            continue
        if cells[0].lower().startswith("capability") or cells[0].startswith("["):
            continue

        for tick in BACKTICK.findall(cells[1]):
            tick = tick.strip()
            if not (tick.startswith(".") or "/" in tick) or " " in tick:
                continue
            # A glob names a shape, so its parent is the most that can be verified.
            # An exact path must exist outright, or a deleted capability slips through.
            if "*" in tick:
                target = os.path.join(root, os.path.dirname(tick.replace("*", "")))
            else:
                target = os.path.join(root, tick.rstrip("/"))
            if not os.path.exists(target):
                add("drift", f"capability '{cells[0]}' points at `{tick}`, "
                             "which is not in the repo")

        if not cells[2]:
            add("warn", f"capability '{cells[0]}' has no reach-for-it-when line")

    # --- recency ----------------------------------------------------------
    tools_rel = os.path.relpath(tools_path, root)
    tools_ts = git_mtime(root, tools_rel)
    watched = ["package.json", "pyproject.toml", "go.mod", "Cargo.toml",
               "Gemfile", "composer.json"] + list(LOCKFILES)
    if tools_ts:
        newer = [f for f in watched
                 if (git_mtime(root, f) or 0) > tools_ts]
        if newer:
            add("warn", f"changed more recently than {tools_rel}: {', '.join(sorted(newer))}; "
                        "re-verify the affected lines")

    # --- shape ------------------------------------------------------------
    if not re.search(r"^#+\s*Unknowns", text, re.M | re.I):
        add("warn", "no Unknowns section; an empty one means 'checked and resolved', "
                    "a missing one means 'never checked'")
    if re.search(r"\[[A-Za-z][^\]]*\]", body) and "](" not in body:
        add("warn", "unfilled [bracketed] template placeholders remain")

    return tools_path, findings


def main():
    parser = argparse.ArgumentParser(
        description="Check TOOLS.md against the repo it describes.")
    parser.add_argument("root", nargs="?", default=".", help="repo root (default: .)")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    if not os.path.isdir(args.root):
        print(f"error: not a directory: {args.root}", file=sys.stderr)
        sys.exit(2)

    tools_path, findings = check(args.root)
    drift = [f for f in findings if f["kind"] == "drift"]

    if args.json:
        print(json.dumps({"file": tools_path, "findings": findings,
                          "drift_count": len(drift)}, indent=2))
    elif not findings:
        print(f"OK  {tools_path} matches the repo.")
    else:
        print(f"{tools_path}")
        for f in findings:
            print(f"  {f['kind'].upper():5} {f['message']}")
        print(f"\n{len(drift)} drift, {len(findings) - len(drift)} warning(s).")

    sys.exit(1 if drift else 0)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        # Output was piped into something that closed early (head, tee). Not an error.
        os._exit(0)
