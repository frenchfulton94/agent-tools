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


def graphql(document, variables=None):
    """POST a GraphQL document. Returns (ok, text)."""
    if not API_URL:
        return False, (
            "No Unraid API endpoint configured. Set the plugin's api_url option "
            "(for example http://tower.local/graphql)."
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

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-api-key": API_KEY,
        },
        method="POST",
    )

    context = None
    if INSECURE_TLS:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT, context=context) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:800]
        hint = ""
        if exc.code in (401, 403):
            hint = (
                " The API key was rejected. Check it, and that its role covers "
                "this query."
            )
        elif exc.code == 404:
            hint = (
                " Endpoint not found. The GraphQL API ships with Unraid 7.2+; on "
                "earlier releases it comes from the Unraid Connect plugin."
            )
        return False, f"HTTP {exc.code} from {API_URL}.{hint}\n{detail}"
    except urllib.error.URLError as exc:
        return False, (
            f"Could not reach {API_URL}: {exc.reason}. Check the host is up and "
            "reachable, and if it uses a self-signed certificate, enable the "
            "plugin's insecure_tls option."
        )
    except (TimeoutError, json.JSONDecodeError, OSError) as exc:
        return False, f"Request to {API_URL} failed: {exc}"

    if isinstance(payload, dict) and payload.get("errors"):
        messages = "; ".join(
            e.get("message", str(e)) for e in payload["errors"] if isinstance(e, dict)
        )
        return False, f"GraphQL error: {messages or payload['errors']}"

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
