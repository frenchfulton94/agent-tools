#!/usr/bin/env python3
"""Lint a devcontainer.json for the errors that actually break builds.

Standard library only. Reads JSONC (comments and trailing commas allowed, as the
dev container spec permits) and reports findings as ERROR, WARN, or INFO.

Usage:
    python3 validate_devcontainer.py .devcontainer/devcontainer.json
    python3 validate_devcontainer.py <dir>          # finds the config itself
    python3 validate_devcontainer.py <path> --json  # machine-readable

Exit codes: 0 clean or warnings only, 1 errors found, 2 could not read the file.
"""

import argparse
import json
import os
import re
import sys

# Canonical first-party Features, from github.com/devcontainers/features/src.
# An ID under devcontainers/features that is not here does not exist.
FIRST_PARTY_FEATURES = {
    "anaconda", "aws-cli", "azure-cli", "common-utils", "conda", "copilot-cli",
    "desktop-lite", "docker-in-docker", "docker-outside-of-docker", "dotnet",
    "git", "git-lfs", "github-cli", "go", "hugo", "java",
    "kubectl-helm-minikube", "nix", "node", "nvidia-cuda", "oryx", "php",
    "powershell", "python", "ruby", "rust", "sshd", "terraform",
}

# Canonical first-party images, from github.com/devcontainers/images/src.
FIRST_PARTY_IMAGES = {
    "anaconda", "base-alpine", "base-debian", "base-ubuntu", "cpp", "dotnet",
    "go", "java", "java-8", "javascript-node", "jekyll", "miniconda", "php",
    "python", "ruby", "rust", "typescript-node", "universal",
}

# Tokens that indicate a process which never exits. A lifecycle command must
# terminate or container creation hangs indefinitely.
NON_EXITING = [
    "npm start", "npm run start", "npm run dev", "npm run serve", "npm run watch",
    "yarn start", "yarn dev", "pnpm dev", "pnpm start",
    "runserver", "flask run", "rails server", "rails s",
    "nodemon", "webpack serve", "vite", "next dev",
    "sleep infinity", "tail -f", "http.server", "gunicorn", "uvicorn",
]

LIFECYCLE = [
    "initializeCommand", "onCreateCommand", "updateContentCommand",
    "postCreateCommand", "postStartCommand", "postAttachCommand",
]

# Long, high-entropy literals in an env value are almost always a pasted secret.
SECRET_KEY = re.compile(
    r"(TOKEN|SECRET|PASSWORD|PASSWD|APIKEY|API_KEY|ACCESS_KEY|PRIVATE_KEY|CREDENTIAL)",
    re.I,
)


def strip_jsonc(text):
    """Remove // and /* */ comments and trailing commas, preserving string literals.

    Comment markers inside strings must survive, so this walks the text rather
    than using a regex.
    """
    out = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        c = text[i]
        if in_string:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    # Trailing commas before a closing brace or bracket.
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def is_backgrounded(cmd):
    """True when the command deliberately detaches, so it does exit.

    'nohup uvicorn app:api &' is a legitimate postStartCommand; 'uvicorn app:api'
    is not. Without this the check produces false positives on the documented
    background-service pattern.
    """
    stripped = cmd.strip()
    return (
        stripped.endswith("&")
        or "nohup " in stripped
        or " --daemon" in stripped
        or "screen -dm" in stripped
        or "tmux new-session -d" in stripped
    )


def command_strings(value):
    """Flatten a lifecycle property (string, array, or object) to a list of strings."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [" ".join(str(v) for v in value)]
    if isinstance(value, dict):
        result = []
        for v in value.values():
            result.extend(command_strings(v))
        return result
    return []


def locate(path):
    """Accept a file or a directory and return the config path."""
    if os.path.isfile(path):
        return path
    if os.path.isdir(path):
        for candidate in (
            os.path.join(path, ".devcontainer", "devcontainer.json"),
            os.path.join(path, ".devcontainer.json"),
            os.path.join(path, "devcontainer.json"),
        ):
            if os.path.isfile(candidate):
                return candidate
    return None


class Report:
    def __init__(self):
        self.findings = []

    def add(self, level, prop, message, fix=None):
        self.findings.append(
            {"level": level, "property": prop, "message": message, "fix": fix}
        )

    error = lambda self, p, m, f=None: self.add("ERROR", p, m, f)  # noqa: E731
    warn = lambda self, p, m, f=None: self.add("WARN", p, m, f)  # noqa: E731
    info = lambda self, p, m, f=None: self.add("INFO", p, m, f)  # noqa: E731

    @property
    def error_count(self):
        return sum(1 for f in self.findings if f["level"] == "ERROR")


def check_base(cfg, r):
    bases = []
    if "image" in cfg:
        bases.append("image")
    if isinstance(cfg.get("build"), dict) and "dockerfile" in cfg["build"]:
        bases.append("build.dockerfile")
    if "dockerComposeFile" in cfg:
        bases.append("dockerComposeFile")

    if not bases:
        r.error(
            "image",
            "No base defined.",
            "Add one of: image, build.dockerfile, or dockerComposeFile.",
        )
    elif len(bases) > 1:
        r.error(
            "/".join(bases),
            "More than one base defined: " + ", ".join(bases) + ".",
            "Keep exactly one. Compose bases cannot also set image or build.",
        )

    if "dockerfile" in cfg:
        r.error(
            "dockerfile",
            "Top-level 'dockerfile' is not a spec property.",
            'Use "build": { "dockerfile": "Dockerfile" }.',
        )

    if "dockerComposeFile" in cfg:
        if "service" not in cfg:
            r.error(
                "service",
                "dockerComposeFile is set but 'service' is missing.",
                "Add the service the editor should attach to.",
            )
        if "workspaceFolder" not in cfg:
            r.warn(
                "workspaceFolder",
                "Compose config without workspaceFolder defaults to '/'.",
                'Set it explicitly, e.g. "/workspaces/${localWorkspaceFolderBasename}".',
            )


def check_image(cfg, r):
    image = cfg.get("image")
    if not isinstance(image, str):
        return

    if image.startswith("mcr.microsoft.com/vscode/devcontainers/"):
        r.warn(
            "image",
            "Deprecated image path 'mcr.microsoft.com/vscode/devcontainers/'.",
            "Use mcr.microsoft.com/devcontainers/ instead.",
        )

    ref = image.split("@")[0]
    tag = ref.rsplit(":", 1)[1] if ":" in ref.rsplit("/", 1)[-1] else None
    if tag is None:
        r.warn("image", "Image tag is not pinned.", "Pin a version, e.g. ':1-22-bookworm'.")
    elif tag == "latest":
        r.warn("image", "Image pinned to ':latest', which moves.", "Pin a real version tag.")

    for prefix in ("mcr.microsoft.com/devcontainers/", "mcr.microsoft.com/vscode/devcontainers/"):
        if image.startswith(prefix):
            name = image[len(prefix):].split(":")[0].split("@")[0]
            if name not in FIRST_PARTY_IMAGES:
                r.error(
                    "image",
                    "'" + name + "' is not a first-party dev container image.",
                    "Known: " + ", ".join(sorted(FIRST_PARTY_IMAGES)) + ".",
                )
            break

    if "alpine" in image.lower():
        r.info(
            "image",
            "Alpine base: extensions with native code may fail on musl.",
            "Prefer a Debian or Ubuntu variant unless image size is critical.",
        )


def check_features(cfg, r):
    features = cfg.get("features")
    if features is None:
        return
    if not isinstance(features, dict):
        r.error("features", "'features' must be an object of ID -> options.")
        return

    for fid in features:
        ref = fid.split("@")[0]
        last = ref.rsplit("/", 1)[-1]
        if ":" not in last:
            r.warn(
                "features",
                "Feature '" + fid + "' has no version pin.",
                "Append ':1' to pin the major version.",
            )
        name = last.split(":")[0]
        if ref.startswith("ghcr.io/devcontainers/features/"):
            if name not in FIRST_PARTY_FEATURES:
                r.error(
                    "features",
                    "'" + name + "' is not a first-party Feature; the build will fail "
                    "with a manifest error.",
                    "Check the list in references/features.md, or use the full "
                    "publisher path if this is a community Feature.",
                )
        elif "/" not in ref:
            r.error(
                "features",
                "Feature '" + fid + "' is not a valid OCI reference.",
                "Use the full path, e.g. ghcr.io/devcontainers/features/node:1.",
            )

    if len(features) >= 5:
        r.info(
            "features",
            str(len(features)) + " Features will run on every fresh build.",
            "Consider prebuilding an image; see references/compose-and-advanced.md.",
        )


def check_customizations(cfg, r):
    for legacy in ("extensions", "settings"):
        if legacy in cfg:
            r.error(
                legacy,
                "Top-level '" + legacy + "' is the pre-2022 schema and is ignored.",
                'Move it under "customizations": { "vscode": { "' + legacy + '": ... } }.',
            )

    cust = cfg.get("customizations")
    if cust is not None and not isinstance(cust, dict):
        r.error("customizations", "'customizations' must be an object.")


def check_workspace(cfg, r):
    has_folder = "workspaceFolder" in cfg
    has_mount = "workspaceMount" in cfg
    is_compose = "dockerComposeFile" in cfg
    if is_compose:
        if has_mount:
            r.warn(
                "workspaceMount",
                "workspaceMount has no effect with a Compose base.",
                "Declare the mount in the compose file's 'volumes' instead.",
            )
        return
    if has_folder != has_mount:
        missing = "workspaceMount" if has_folder else "workspaceFolder"
        r.error(
            missing,
            "workspaceFolder and workspaceMount must be set together.",
            "Add " + missing + ", or remove the one that is set.",
        )


def check_lifecycle(cfg, r):
    for prop in LIFECYCLE:
        if prop not in cfg:
            continue
        for cmd in command_strings(cfg[prop]):
            if is_backgrounded(cmd):
                continue
            low = cmd.lower()
            for token in NON_EXITING:
                if token in low:
                    if prop == "postStartCommand" and token == "sleep infinity":
                        continue
                    r.error(
                        prop,
                        "Command looks like it never exits ('" + token + "'); this "
                        "hangs container creation.",
                        "Run long-lived processes from a task or terminal instead.",
                    )
                    break

    if "initializeCommand" in cfg:
        for cmd in command_strings(cfg["initializeCommand"]):
            if any(t in cmd for t in ("apt-get", "apt ", "npm ci", "npm install",
                                      "pip install", "bundle install", "yum ")):
                r.error(
                    "initializeCommand",
                    "initializeCommand runs on the HOST, not in the container.",
                    "Move installs to onCreateCommand or postCreateCommand.",
                )
                break

    for cmd in command_strings(cfg.get("postStartCommand", "")):
        if any(t in cmd for t in ("npm ci", "npm install", "pip install", "bundle install")):
            r.warn(
                "postStartCommand",
                "Dependency install in postStartCommand runs on every start.",
                "Use postCreateCommand for one-time setup.",
            )
            break

    for cmd in command_strings(cfg.get("postCreateCommand", "")):
        if "nvm " in cmd and "-i" not in cmd:
            r.warn(
                "postCreateCommand",
                "nvm is a shell function and is unavailable in a non-interactive shell.",
                "Use: bash -i -c 'nvm install --lts'",
            )
            break


def check_secrets(cfg, r):
    for scope in ("containerEnv", "remoteEnv", "build"):
        block = cfg.get(scope)
        if scope == "build" and isinstance(block, dict):
            block = block.get("args")
        if not isinstance(block, dict):
            continue
        for key, value in block.items():
            if not isinstance(value, str):
                continue
            if "${" in value:
                continue
            if SECRET_KEY.search(key) and len(value) >= 12:
                r.error(
                    scope,
                    "'" + key + "' looks like a hardcoded secret in a committed file.",
                    'Read it from the host: "${localEnv:' + key + '}".',
                )


def check_ports(cfg, r):
    if "appPort" in cfg and "forwardPorts" in cfg:
        r.info(
            "appPort",
            "Both appPort and forwardPorts are set.",
            "forwardPorts is preferred; appPort publishes and requires binding 0.0.0.0.",
        )
    fp = cfg.get("forwardPorts")
    if isinstance(fp, list):
        for p in fp:
            if isinstance(p, int) and not (1 <= p <= 65535):
                r.error("forwardPorts", str(p) + " is not a valid port number.")


def check_user(cfg, r):
    image = cfg.get("image", "")
    known_user_image = isinstance(image, str) and image.startswith(
        "mcr.microsoft.com/devcontainers/"
    )
    if cfg.get("remoteUser") == "root":
        r.warn(
            "remoteUser",
            "Running as root means files written to a bind mount are root-owned on "
            "the host (Linux).",
            "Use a non-root user such as 'vscode' or 'node'.",
        )
    elif "remoteUser" not in cfg and not known_user_image and "dockerComposeFile" not in cfg:
        r.info(
            "remoteUser",
            "No remoteUser set and the base image is not a known first-party image.",
            "Set remoteUser to a non-root user to avoid root-owned files.",
        )
    if cfg.get("privileged") is True:
        r.warn(
            "privileged",
            "privileged grants broad host access.",
            "Prefer the docker-in-docker or docker-outside-of-docker Feature.",
        )


def main():
    parser = argparse.ArgumentParser(
        description="Lint a devcontainer.json for common build-breaking errors."
    )
    parser.add_argument("path", help="devcontainer.json, or a folder containing one")
    parser.add_argument("--json", action="store_true", help="emit JSON on stdout")
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as errors in the exit code"
    )
    args = parser.parse_args()

    path = locate(args.path)
    if path is None:
        print("error: no devcontainer.json found at " + args.path, file=sys.stderr)
        return 2

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        print("error: cannot read " + path + ": " + str(exc), file=sys.stderr)
        return 2

    try:
        cfg = json.loads(strip_jsonc(raw))
    except json.JSONDecodeError as exc:
        print(
            "error: " + path + " is not valid JSON/JSONC: line "
            + str(exc.lineno) + ", " + exc.msg,
            file=sys.stderr,
        )
        return 2

    if not isinstance(cfg, dict):
        print("error: top level of " + path + " must be an object", file=sys.stderr)
        return 2

    r = Report()
    for check in (check_base, check_image, check_features, check_customizations,
                  check_workspace, check_lifecycle, check_secrets, check_ports,
                  check_user):
        check(cfg, r)

    warn_count = sum(1 for f in r.findings if f["level"] == "WARN")

    if args.json:
        json.dump(
            {"path": path, "findings": r.findings,
             "errors": r.error_count, "warnings": warn_count},
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        print(path)
        if not r.findings:
            print("  clean - no issues found")
        for f in r.findings:
            print("  [" + f["level"] + "] " + f["property"] + ": " + f["message"])
            if f["fix"]:
                print("          -> " + f["fix"])
        print(
            "\n" + str(r.error_count) + " error(s), " + str(warn_count) + " warning(s)"
        )

    if r.error_count or (args.strict and warn_count):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
