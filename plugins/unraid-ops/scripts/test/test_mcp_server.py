"""Integration test: drives the MCP server over stdio against a fake GraphQL endpoint."""
import json, os, subprocess, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import unraid_mcp_server as mod

CALLS = []
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        CALLS.append({"query": body["query"], "api_key": self.headers.get("x-api-key")})
        q = body["query"]
        if "redirectme" in q:
            self.send_response(301); self.send_header("Location", "https://tower.local/"); self.end_headers(); return
        if "sandboxprobe" in q or "authprobe" in q:
            code = "SANDBOX_DISABLED" if "sandboxprobe" in q else "UNAUTHENTICATED"
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"errors":[{"message":"refused","extensions":{"code":code}}]}).encode()); return
        if "__schema" in q:
            data = {"__schema": {"queryType": {"name": "Query"}, "mutationType": {"name": "Mutation"},
                    "types": [{"name": "Array", "kind": "OBJECT", "description": "Array", 
                               "fields": [{"name": "state", "description": "Array state",
                                           "type": {"name": "String", "kind": "SCALAR", "ofType": None}}]}]}}
        elif "dockerContainers" in q:
            data = {"dockerContainers": [{"id": "abc", "names": ["plex"], "state": "running", "status": "Up 2 days", "autoStart": True}]}
        elif "array" in q:
            data = {"array": {"state": "STARTED", "capacity": {"disks": {"free": "1", "used": "2", "total": "3"}},
                              "disks": [{"name": "disk1", "size": "8TB", "status": "DISK_OK", "temp": 34}]}}
        elif "boom" in q:
            self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
            self.wfile.write(json.dumps({"errors":[{"message":"Cannot query field 'boom'"}]}).encode()); return
        else:
            data = {"info": {"os": {"platform": "linux", "distro": "Unraid", "release": "7.3.2", "uptime": "5d"},
                             "cpu": {"manufacturer": "AMD", "brand": "Ryzen", "cores": 8, "threads": 16}}}
        self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers()
        self.wfile.write(json.dumps({"data": data}).encode())

srv = HTTPServer(("127.0.0.1", 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/graphql"

def run(msgs, allow_mutations=False, api_url=None):
    env = dict(os.environ, UNRAID_API_URL=api_url or url, UNRAID_API_KEY="test-key-123",
               UNRAID_ALLOW_MUTATIONS="true" if allow_mutations else "false")
    p = subprocess.run([sys.executable, "scripts/unraid_mcp_server.py"],
                       input="\n".join(json.dumps(m) for m in msgs) + "\n",
                       capture_output=True, text=True, env=env, timeout=30)
    return [json.loads(l) for l in p.stdout.strip().split("\n") if l.strip()], p.stderr

INIT = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}
NOTE = {"jsonrpc":"2.0","method":"notifications/initialized"}
def call(i, name, args=None):
    return {"jsonrpc":"2.0","id":i,"method":"tools/call","params":{"name":name,"arguments":args or {}}}

fails = 0
def check(label, cond, detail=""):
    global fails
    print(("PASS " if cond else "FAIL ") + label + ("" if cond else f"  <- {detail}"))
    if not cond: fails += 1

out, err = run([INIT, NOTE, {"jsonrpc":"2.0","id":2,"method":"tools/list"}])
check("initialize returns protocolVersion + serverInfo",
      out[0]["result"]["protocolVersion"]=="2024-11-05" and out[0]["result"]["serverInfo"]["name"]=="unraid", out[0])
check("initialized notification produces no response", len(out)==2, out)
names = [t["name"] for t in out[1]["result"]["tools"]]
check("tools/list exposes 5 tools", len(names)==5, names)
check("every tool has an inputSchema", all("inputSchema" in t for t in out[1]["result"]["tools"]))

out, _ = run([INIT, call(2,"system_info"), call(3,"array_status"), call(4,"docker_containers")])
check("system_info returns data", "7.3.2" in out[1]["result"]["content"][0]["text"], out[1])
check("array_status returns data", "STARTED" in out[2]["result"]["content"][0]["text"])
check("docker_containers returns data", "plex" in out[3]["result"]["content"][0]["text"])
check("api key sent as x-api-key header", all(c["api_key"]=="test-key-123" for c in CALLS), CALLS[:1])

out, _ = run([INIT, call(2,"introspect_schema"), call(3,"introspect_schema",{"type_name":"Array"}),
              call(4,"introspect_schema",{"type_name":"Nope"})])
check("introspect returns full schema", "__schema" in out[1]["result"]["content"][0]["text"])
check("introspect filters to a type", '"name": "Array"' in out[2]["result"]["content"][0]["text"])
check("unknown type is an error listing options", out[3]["result"].get("isError") is True)

MUT = 'mutation { startArray { state } }'
out, _ = run([INIT, call(2,"query",{"query":MUT})])
check("mutation refused by default", out[1]["result"].get("isError") is True and "read-only" in out[1]["result"]["content"][0]["text"])
out, _ = run([INIT, call(2,"query",{"query":MUT})], allow_mutations=True)
check("mutation allowed when explicitly enabled", not out[1]["result"].get("isError"), out[1])
out, _ = run([INIT, call(2,"query",{"query":"query { array { state } } # not a mutation"})])
check("comment mentioning mutation is not blocked", not out[1]["result"].get("isError"))

out, _ = run([INIT, call(2,"query",{"query":"query { boom }"})])
check("graphql errors surface as isError", out[1]["result"].get("isError") is True and "boom" in out[1]["result"]["content"][0]["text"])
out, _ = run([INIT, call(2,"query",{"query":"   "})])
check("empty query rejected", out[1]["result"].get("isError") is True)

out, _ = run([INIT, call(2,"query",{"query":"query { sandboxprobe }"})])
check("SANDBOX_DISABLED explains both causes", out[1]["result"].get("isError") is True
      and "unraid-api developer --sandbox true" in out[1]["result"]["content"][0]["text"], out[1])
out, _ = run([INIT, call(2,"query",{"query":"query { authprobe }"})])
check("UNAUTHENTICATED points at the api key", out[1]["result"].get("isError") is True
      and "apikey --list" in out[1]["result"]["content"][0]["text"], out[1])
out, _ = run([INIT, call(2,"query",{"query":"query { redirectme }"})])
check("redirect reported with the https endpoint, not followed", out[1]["result"].get("isError") is True
      and "https://tower.local/graphql" in out[1]["result"]["content"][0]["text"], out[1])
out, _ = run([INIT, {"jsonrpc":"2.0","id":9,"method":"nonsense/method"}])
check("unknown method returns -32601", out[1]["error"]["code"]==-32601)
out, _ = run([INIT, {"jsonrpc":"2.0","id":9,"method":"ping"}])
check("ping answered", out[1]["result"]=={})

env = dict(os.environ); env.pop("UNRAID_API_KEY", None)
p = subprocess.run([sys.executable,"scripts/unraid_mcp_server.py"],
                   input=json.dumps(INIT)+"\n"+json.dumps(call(2,"system_info"))+"\n",
                   capture_output=True,text=True,env=dict(env,UNRAID_API_URL=url,UNRAID_API_KEY=""),timeout=30)
o=[json.loads(l) for l in p.stdout.strip().split("\n") if l.strip()]
check("missing api key gives actionable error", o[1]["result"].get("isError") is True and "unraid-api apikey" in o[1]["result"]["content"][0]["text"])

# A redirect must never carry the API key to another host, or down to plain http.
FOLLOW = [
    ("upgrades http to https on the same host and path",
     "http://tower.local/graphql", "https://tower.local:443/graphql", "https://tower.local:443/graphql"),
    ("follows a same-host port change",
     "http://tower.local/graphql", "http://tower.local:8080/graphql", "http://tower.local:8080/graphql"),
    ("resolves a relative Location against the current url",
     "http://tower.local:80/graphql", "//tower.local:443/graphql", "http://tower.local:443/graphql"),
]
REFUSE = [
    ("refuses another host", "http://tower.local/graphql", "https://evil.example/graphql"),
    ("refuses an https to http downgrade", "https://tower.local/graphql", "http://tower.local/graphql"),
    ("refuses a different path", "http://tower.local/graphql", "https://tower.local/"),
    ("refuses a redirect to itself", "http://tower.local/graphql", "http://tower.local/graphql"),
    ("refuses a non-http scheme", "http://tower.local/graphql", "file:///etc/passwd"),
    ("refuses an empty Location", "http://tower.local/graphql", ""),
]
for label, current, location, expected in FOLLOW:
    got = mod._redirect_target(current, location)
    check("redirect " + label, got == expected, got)
for label, current, location in REFUSE:
    got = mod._redirect_target(current, location)
    check("redirect " + label, got is None, got)

# The certificate case must lead with the fix, not with "check the host is up".
cert = mod._unreachable_message("https://tower.local/graphql",
                                "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate")
check("cert failure names insecure_tls", "insecure_tls" in cert, cert)
check("cert failure does not blame reachability", "host is up" not in cert, cert)
other = mod._unreachable_message("https://tower.local/graphql", "[Errno 61] Connection refused")
check("non-cert failure still suggests checking the host", "host is up" in other, other)

# End to end: a same-host redirect is followed as a POST, key intact.
class Redirector(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        self.send_response(302); self.send_header("Location", url); self.end_headers()

rsrv = HTTPServer(("127.0.0.1", 0), Redirector)
threading.Thread(target=rsrv.serve_forever, daemon=True).start()
CALLS.clear()
out, _ = run([INIT, call(2, "system_info")],
             api_url=f"http://127.0.0.1:{rsrv.server_address[1]}/graphql")
check("same-host redirect is followed and answered",
      "7.3.2" in out[1]["result"]["content"][0]["text"], out[1])
check("followed redirect still sends the api key",
      CALLS and CALLS[-1]["api_key"] == "test-key-123", CALLS[-1:])


print(f"\nfailures: {fails}")
sys.exit(1 if fails else 0)
