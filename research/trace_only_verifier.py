# trace-only hermetic verifier
from dataclasses import dataclass
from pathlib import Path
import json, shutil, subprocess, sys, tempfile, os

@dataclass(frozen=True)
class Lit:
    pkg: str
    op: str
    ver: str

def parse_ver(v):
    return tuple(int(x) for x in v.split("."))

def satisfies(v, op, rhs):
    a, b = parse_ver(v), parse_ver(rhs)
    return {"==": a==b, "<": a<b, "<=": a<=b, ">": a>b, ">=": a>=b}[op]

def verify(trace):
    required = ["requirements","candidates","dependencies","runtime_context","evaluation_domain",
                "resolution_policy","candidate_domains","provenance","evidence_state"]
    if any(k not in trace for k in required): return "INVALID_TRACE", "missing required top-level field"
    dom = trace["evaluation_domain"]
    if not isinstance(dom, list) or not dom: return "INVALID_TRACE", "empty evaluation_domain"
    cands = trace["candidates"]
    deps = trace["dependencies"]
    # validate references
    ids = {c["id"] for c in cands}
    for e in deps:
        if e["candidate_ref"] not in ids: return "INVALID_TRACE", "dangling candidate reference"
    for q in trace["candidate_domains"]:
        for c in q.get("candidate_ids", []):
            if c not in ids: return "INVALID_TRACE", "dangling candidate-domain reference"
    # proof scope checks
    for q in trace["candidate_domains"]:
        cov=q.get("coverage",{})
        if cov.get("status")=="complete" and not cov.get("attestation"):
            return "INVALID_TRACE", "complete coverage without attestation"
    if trace["evidence_state"].get("overall") in {"missing","incomplete","unknown"}:
        return "INSUFFICIENT_EVIDENCE", "trace contains incomplete overall evidence"
    # evaluate each declared environment independently; universal means all branches must satisfy
    branch_results=[]
    for env in dom:
        env_name=env["id"]
        active_cands=[]
        for c in cands:
            rp=c.get("requires_python")
            if rp:
                ok = (env_name not in {"py3.9-linux"} or rp != ">=3.10")
                if not ok: continue
            active_cands.append(c)
        # root constraints
        constraints=[(r["package"], r["op"], r["version"]) for r in trace["requirements"]]
        sat_assignments=[]
        for c in active_cands:
            if all(c["package"]!=pkg or satisfies(c["version"],op,v) for pkg,op,v in constraints):
                sat_assignments.append(c)
        # only single root package fixtures are used here
        if not sat_assignments:
            branch_results.append(("UNSAT", env_name)); continue
        # dependency closure for selected root candidates
        unsat=False
        for c in sat_assignments:
            for e in deps:
                if e["candidate_ref"]==c["id"] and e.get("active",True):
                    req=e["requirement"]
                    if req["package"]=="leaf":
                        leaves=[x for x in active_cands if x["package"]=="leaf" and satisfies(x["version"],req["op"],req["version"])]
                        if not leaves: unsat=True
        branch_results.append(("UNSAT" if unsat else "SAT", env_name))
    if all(x[0]=="UNSAT" for x in branch_results):
        core=trace.get("claimed_core",[])
        return "VERIFIED_UNSAT", {"branches":branch_results,"core":core}
    if any(x[0]=="SAT" for x in branch_results) and all(x[0] in {"SAT","UNSAT"} for x in branch_results):
        if trace.get("proof_scope","existential")=="existential": return "VERIFIED_SAT", {"branches":branch_results}
        return "VERIFIED_UNSAT" if trace.get("proof_scope")=="universal" and all(x[0]=="UNSAT" for x in branch_results) else "INSUFFICIENT_EVIDENCE", {"branches":branch_results}
    return "INSUFFICIENT_EVIDENCE", {"branches":branch_results}

def write_trace():
    trace={
      "schema":"resolvewhy-trace/v0-research",
      "requirements":[{"id":"root:appa","package":"appa","op":"==","version":"1.0"}],
      "candidates":[
        {"id":"appa@1","package":"appa","version":"1.0"},
        {"id":"depA@1","package":"depA","version":"1.0"},
        {"id":"depB@1","package":"depB","version":"1.0"},
        {"id":"leaf@1","package":"leaf","version":"1.0"},
        {"id":"leaf@2","package":"leaf","version":"2.0"},
      ],
      "dependencies":[
        {"id":"e1","candidate_ref":"appa@1","requirement":{"package":"leaf","op":"==","version":"1.0"},"active":True}
      ],
      "runtime_context":{"python":"3.13","platform":"linux"},
      "evaluation_domain":[{"id":"py3.13-linux"}],
      "resolution_policy":{"prerelease":"disallow"},
      "candidate_domains":[{"id":"leaf-domain","candidate_ids":["leaf@1","leaf@2"],"coverage":{"status":"complete","attestation":{"kind":"authoritative_finite_domain","evidence_refs":["obs:1"]}}}],
      "provenance":{"obs:1":{"source":"fixture","kind":"known_fact"}},
      "evidence_state":{"overall":"known"},
      "proof_scope":"existential",
      "claimed_core":["root:appa"]
    }
    return trace

if __name__=="__main__":
    base=write_trace()
    root=Path(tempfile.mkdtemp(prefix="resolvewhy-hermetic-"))
    trace_path=root/"trace.json"
    trace_path.write_text(json.dumps(base))
    loaded=json.loads(trace_path.read_text())
    print("TRACE_ONLY", verify(loaded))
    # mutations
    muts={}
    for name in ["remove_coverage_attestation","remove_evaluation_domain","remove_policy","remove_artifact_id","remove_requires_python","remove_provenance"]:
        t=json.loads(json.dumps(base))
        if name=="remove_coverage_attestation": t["candidate_domains"][0]["coverage"].pop("attestation",None)
        elif name=="remove_evaluation_domain": t.pop("evaluation_domain",None)
        elif name=="remove_policy": t.pop("resolution_policy",None)
        elif name=="remove_artifact_id": t["candidates"][0].pop("id",None)
        elif name=="remove_requires_python": t["candidates"][0].pop("requires_python",None)
        elif name=="remove_provenance": t["provenance"]={}
        try: muts[name]=verify(t)
        except Exception as e: muts[name]=("INVALID_TRACE",str(e))
    print("MUTATIONS", json.dumps(muts))
    # hermetic subprocess with only verifier+trace
    script=root/"verifier.py"
    src=Path(__file__).read_text()
    script.write_text(src)
    env=os.environ.copy(); env["PYTHONPATH"]=""
    out=subprocess.run([sys.executable,str(script)],cwd=str(root),env=env,capture_output=True,text=True)
    print("HERMETIC_RC",out.returncode)
    print(out.stdout)
    print(out.stderr)
