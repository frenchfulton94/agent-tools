#!/usr/bin/env python3
"""MCP server for the Unraid GraphQL API (Unraid 7.2+).

Speaks JSON-RPC 2.0 over stdio using only the standard library, so the plugin
needs no install step.

Design notes:
  - Read-only by default. The Unraid API can start and stop the array; this
    plugin exists to prevent destructive mistakes, so mutations are refused
    unless UNRAID_ALLOW_MUTATIONS is explicitly true.
  - Only three typed queries are hardcoded, and each is taken verbatim from the
    documented examples. The complete schema is published in Apollo Studio
    rather than the docs, so `introspect_schema` lets the caller discover the
    real schema at runtime instead of relying on guessed field names.
"""

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "unraid", "version": "1.0.0"}

API_URL = os.environ.get("UNRAID_API_URL", "").strip()
API_KEY = os.environ.get("UNRAID_API_KEY", "").strip()


def _flag(name):
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


ALLOW_MUTATIONS = _flag("UNRAID_ALLOW_MUTATIONS")
INSECURE_TLS = _flag("UNRAID_INSECURE_TLS")
TIMEOUT = int(os.environ.get("UNRAID_TIMEOUT", "20"))

# Documented example queries (docs.unraid.net → API → Using the Unraid API).
Q_SYSTEM_INFO = """query {
  info {
    os { platform distro release uptime }
    cpu { manufacturer brand cores threads }
  }
}"""

Q_ARRAY_STATUS = """query {
  array {
    state
    capacity { disks { free used total } }
    disks { name size status temp }
  }
}"""

Q_DOCKER_CONTAINERS = """query {
  dockerContainers { id names state status autoStart }
}"""

INTROSPECTION = """query {
  __schema {
    queryType { name }
    mutationType { name }
    types {
      name
      kind
      description
      fields { name description type { name kind ofType { name kind } } }
    }
  }
}"""

REDIRECT_CODES = (301, 302, 303, 307, 308)

MUTATION_RE = re.compile(r"(?:^|[\s{};])mutation\b", re.IGNORECASE)
COMMENT_RE = re.compile(r"#[^\n]*")

TOOLS = [
    {
        "name": "system_info",
        "description": (
            "Unraid host details: OS platform, distro, release, uptime, and CPU "
            "manufacturer, brand, core and thread counts. Use to confirm the "
            "Unraid version before giving any version-dependent procedure."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "array_status",
        "description": (
            "Parity array state plus per-disk name, size, status and temperature, "
            "and total/used/free capacity. Use to check whether the array is "
            "started, stopped or in maintenance, and to spot disabled or "
            "unmountable disks before advising."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "docker_containers",
        "description": (
            "Docker containers with id, names, state, status and autostart flag."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "introspect_schema",
        "description": (
            "Run GraphQL introspection against the server to discover the real "
            "schema — available queries, types and fields. Use this before "
            "writing a custom query, rather than guessing field names, since the "
            "full schema is not published in the Unraid docs. Optionally filter "
            "to one type by name."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "type_name": {
                    "type": "string",
                    "description": "Return only this type's fields, e.g. 'Array'.",
                }
            },
        },
    },
    {
        "name": "query",
        "description": (
            "Execute an arbitrary GraphQL query against the Unraid API. "
            "Read-only: mutations are refused unless the plugin is configured to "
            "allow them. Discover valid fields with introspect_schema first."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "GraphQL query document."},
                "variables": {
                    "type": "object",
                    "description": "Optional variables for the query.",
                },
            },
            "required": ["query"],
        },
    },
]


def _redirect_target(current, location):
    """Absolute URL to re-POST to after a redirect, or None if unsafe to follow.

    The API key travels in a header, so a redirect must not carry it anywhere
    else: never to a different host, and never down from https to plain http.
    Unraid's nginx upgrades http to https on the same host and path, which is
    the one case worth following rather than reporting.
    """
    if not location:
        return None
    target = urllib.parse.urljoin(current, location)
    here = urllib.parse.urlsplit(current)
    there = urllib.parse.urlsplit(target)
    if there.scheme not in ("http", "https"):
        return None
    if (here.hostname or "").lower() != (there.hostname or "").lower():
        return None
    if here.scheme == "https" and there.scheme == "http":
        return None
    if here.path != there.path:
        return None
    if target == current:
        return None
    return target


def _unreachable_message(url, reason):
    """Explain a transport failure, leading with the fix where there is one."""
    detail = str(reason)
    if "certificate verify failed" in detail.lower():
        return (
            f"TLS verification failed for {url}: {detail}\n\n"
            "The server answered, so it is reachable — its certificate is what "
            "was rejected. Unraid generates a self-signed certificate for local "
            "access, which Python refuses by default.\n\n"
            "Enable the plugin's insecure_tls option to accept it on a trusted "
            "LAN, or point api_url at the myunraid.net address, whose "
            "certificate validates: "
            "https://<lan-ip-with-dashes>.<hash>.myunraid.net/graphql"
        )
    return (
        f"Could not reach {url}: {detail}. Check the host is up and reachable, "
        "and if it uses a self-signed certificate, enable the plugin's "
        "insecure_tls option."
    )


def graphql(document, variables=None):
    """POST a GraphQL document. Returns (ok, text)."""
    if not API_URL:
        return False, (
            "No Unraid API endpoint configured. Set the plugin's api_url option "
            "(for example https://tower.local/graphql)."
        )
    if not API_KEY:
        return False, (
            "No Unraid API key configured. Create one on the server with "
            "`unraid-api apikey --create --name claude -r admin`, then set the "
            "plugin's api_key option."
        )

    body = {"query": document}
    if variables:
        body["variables"] = variables
    data = json.dumps(body).encode("utf-8")

    context = None
    if INSECURE_TLS:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    # urllib downgrades POST to GET when it follows a 301/302/303, which turns a
    # redirect into a confusing parse failure. Handle redirects here instead, so
    # the method and body survive and the key is never sent to a new host.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    handlers = [NoRedirect]
    if context is not None:
        handlers.append(urllib.request.HTTPSHandler(context=context))
    opener = urllib.request.build_opener(*handlers)

    def post(target_url):
        request = urllib.request.Request(
            target_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "x-api-key": API_KEY,
            },
            method="POST",
        )
        with opener.open(request, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))

    url = API_URL
    followed = False
    while True:
        try:
            payload = post(url)
            break
        except urllib.error.HTTPError as exc:
            if exc.code in REDIRECT_CODES:
                location = exc.headers.get("Location", "") if exc.headers else ""
                target = _redirect_target(url, location)
                if target and not followed:
                    url, followed = target, True
                    continue
                suggestion = location or "the HTTPS address"
                if location and not location.rstrip("/").endswith("/graphql"):
                    suggestion = location.rstrip("/") + "/graphql"
                return False, (
                    f"The server redirected ({exc.code}) to "
                    f"{location or 'another URL'} instead of answering, and that "
                    "redirect was not safe to follow: it leaves the host, "
                    "downgrades to plain http, or points at a different path, "
                    "any of which would send the API key where it does not "
                    "belong.\n\n"
                    f"Set the plugin's api_url option to: {suggestion}\n\n"
                    "With a self-signed certificate, also enable insecure_tls. "
                    "With a myunraid.net certificate the host looks like "
                    "https://<lan-ip-with-dashes>.<hash>.myunraid.net/graphql. "
                    "To use plain HTTP instead, run `use_ssl no` on the server — "
                    "but that disables HTTPS for the whole WebGUI."
                )
            detail = exc.read().decode("utf-8", "replace")[:800]
            hint = ""
            if exc.code in (401, 403):
                hint = (
                    " The API key was rejected. Check it, and that its role covers "
                    "this query."
                )
            elif exc.code == 404:
                hint = (
                    " Endpoint not found. The GraphQL API ships with Unraid 7.2+; "
                    "on earlier releases it comes from the Unraid Connect plugin."
                )
            return False, f"HTTP {exc.code} from {url}.{hint}\n{detail}"
        except urllib.error.URLError as exc:
            return False, _unreachable_message(url, exc.reason)
        except (TimeoutError, json.JSONDecodeError, OSError) as exc:
            return False, f"Request to {url} failed: {exc}"

    if isinstance(payload, dict) and payload.get("errors"):
        errors = [e for e in payload["errors"] if isinstance(e, dict)]
        messages = "; ".join(e.get("message", str(e)) for e in errors)
        codes = {
            (e.get("extensions") or {}).get("code")
            for e in errors
            if (e.get("extensions") or {}).get("code")
        }

        if "SANDBOX_DISABLED" in codes:
            return False, (
                "The Unraid API refused the request with SANDBOX_DISABLED.\n\n"
                "Two things produce this, and they have different fixes:\n\n"
                "1. The GraphQL sandbox is off on a build that gates the whole "
                "/graphql route behind it. Enable it with "
                "`unraid-api developer --sandbox true`, or in the WebGUI at "
                "Settings -> Management Access -> Developer Options.\n"
                "2. The request did not authenticate, so it fell through to the "
                "playground route. Confirm the api_key option is set and the key "
                "still exists (`unraid-api apikey --list`).\n\n"
                "To tell them apart, send an authenticated request by hand:\n"
                "  curl -s -X POST " + (API_URL or "http://tower.local/graphql") +
                " \\\n"
                "    -H 'Content-Type: application/json' \\\n"
                "    -H 'x-api-key: YOUR_KEY' \\\n"
                "    -d '{\"query\":\"{ info { os { release } } }\"}'\n\n"
                "If that succeeds, the key is fine and only the browser "
                "playground was blocked. If it returns SANDBOX_DISABLED too, "
                "enable the sandbox.\n\n"
                "The sandbox is an interactive query console on your LAN. Turn it "
                "off again when you are done, and never leave it on with the "
                "WebGUI reachable from the internet."
            )

        if codes & {"UNAUTHENTICATED", "FORBIDDEN"}:
            return False, (
                f"GraphQL rejected the credentials ({', '.join(sorted(codes))}): "
                f"{messages}. Check the api_key option, and that the key's role "
                "covers this query (`unraid-api apikey --list`)."
            )

        suffix = f" [{', '.join(sorted(codes))}]" if codes else ""
        return False, f"GraphQL error: {messages or payload['errors']}{suffix}"

    return True, json.dumps(payload.get("data", payload), indent=2)


def looks_like_mutation(document):
    return bool(MUTATION_RE.search(COMMENT_RE.sub("", document)))


def call_tool(name, args):
    if name == "system_info":
        return graphql(Q_SYSTEM_INFO)
    if name == "array_status":
        return graphql(Q_ARRAY_STATUS)
    if name == "docker_containers":
        return graphql(Q_DOCKER_CONTAINERS)

    if name == "introspect_schema":
        ok, text = graphql(INTROSPECTION)
        if not ok:
            return ok, text
        wanted = (args or {}).get("type_name")
        if not wanted:
            return True, text
        try:
            types = json.loads(text)["__schema"]["types"]
        except (KeyError, ValueError, TypeError):
            return True, text
        match = [t for t in types if (t.get("name") or "").lower() == wanted.lower()]
        if not match:
            names = sorted(
                t["name"] for t in types if not (t.get("name") or "").startswith("__")
            )
            return False, f"No type named {wanted!r}. Available: {', '.join(names)}"
        return True, json.dumps(match[0], indent=2)

    if name == "query":
        document = (args or {}).get("query", "")
        if not document.strip():
            return False, "No query supplied."
        if looks_like_mutation(document) and not ALLOW_MUTATIONS:
            return False, (
                "This document contains a mutation, and mutations are disabled. "
                "The Unraid API can start and stop the array and control "
                "containers and VMs, so this server is read-only by default. "
                "Perform the action in the WebGUI, or enable the plugin's "
                "allow_mutations option deliberately."
            )
        return graphql(document, (args or {}).get("variables"))

    return False, f"Unknown tool: {name}"


def respond(request_id, result=None, error=None):
    message = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        message["error"] = error
    else:
        message["result"] = result
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = message.get("method")
        request_id = message.get("id")

        if method == "initialize":
            requested = (message.get("params") or {}).get("protocolVersion")
            respond(
                request_id,
                {
                    "protocolVersion": requested or PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": SERVER_INFO,
                },
            )
        elif method in ("notifications/initialized", "notifications/cancelled"):
            continue  # Notifications take no response.
        elif method == "ping":
            respond(request_id, {})
        elif method == "tools/list":
            respond(request_id, {"tools": TOOLS})
        elif method == "tools/call":
            params = message.get("params") or {}
            ok, text = call_tool(params.get("name", ""), params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": text}]}
            if not ok:
                result["isError"] = True
            respond(request_id, result)
        elif request_id is not None:
            respond(
                request_id,
                error={"code": -32601, "message": f"Method not found: {method}"},
            )


if __name__ == "__main__":
    main()
