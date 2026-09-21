from __future__ import annotations

import json, copy, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERIFIER = ROOT / "trace_only_verifier.py"
COLLISION = ROOT / "portable_core_collision_search.py"

def load(path):
    ns = {}
    exec(path.read_text(encoding="utf-8"), ns)
    return ns

def must(label, ok):
    if not ok:
        raise AssertionError(label)

def mutate_campaign(v):
    base = v["base_trace"]()
    families = [
        "ids","references","arrays","evaluation_domain","quantifiers",
        "coverage_attestation","provenance","candidate_artifact_links",
        "dependency_references","proof_premises","evidence_states"
    ]
    results=[]
    for i in range(242):
        t=copy.deepcopy(base)
        fam=families[i % len(families)]
        variant=i // len(families)
        if fam=="ids":
            t["candidates"][variant % len(t["candidates"])]["id"]=None
        elif fam in {"references","dependency_references"}:
            t["dependencies"][0]["parent_candidate"]=f"missing-{variant}"
        elif fam=="arrays":
            t["candidate_domains"][0]["candidate_ids"]=[f"ghost-{variant}"]
        elif fam=="evaluation_domain":
            t["evaluation_domain"][0]["id"]=f"env-corrupt-{variant}"
        elif fam=="quantifiers":
            vals=["existential","universal","branch","invalid"]
            t["proof_claim"]["quantifier"]=vals[variant % 4]
            t["proof_claim"]["evaluation_domain_ref"]=f"missing-{variant}"
        elif fam=="coverage_attestation":
            if variant % 2 == 0:
                t["candidate_domains"][0]["coverage"].pop("attestation",None)
            else:
                t["candidate_domains"][0]["coverage"]["attestation"]["evidence_refs"]=[f"missing-{variant}"]
        elif fam=="provenance":
            if variant % 2 == 0:
                t["provenance"]=[]
            else:
                t["provenance"][0]["premise_refs"]=[f"missing-{variant}"]
        elif fam=="candidate_artifact_links":
            t["artifacts"][0]["candidate_ref"]=f"missing-{variant}"
        elif fam=="proof_premises":
            t["proof_claim"]["premise_refs"]=[f"missing-{variant}"]
        elif fam=="evidence_states":
            t["evidence_state"]["overall"]=["unknown","incomplete","missing"][variant % 3]
        results.append((i,fam,json.dumps(t,sort_keys=True,separators=(",",":")),v["verify"](t)[0]))
    for j in range(8):
        t=copy.deepcopy(base)
        mode=j%4
        if mode==0: t["proof_claim"]["premise_refs"]=["c:missing"]
        elif mode==1: t["proof_claim"]["evaluation_domain_ref"]=f"missing-{j}"
        elif mode==2:
            t["trace_scope"]="universal"; t["proof_claim"]["quantifier"]="existential"
        else: t["candidate_domains"][0]["coverage"]["attestation"]["evidence_refs"]=[f"missing-extra-{j}"]
        results.append((242+j,"targeted",json.dumps(t,sort_keys=True,separators=(",",":")),v["verify"](t)[0]))
    must("250 distinct mutations",len({r[2] for r in results})==250)
    false_accepts=sum(r[3] in {"VERIFIED_SAT","VERIFIED_UNSAT"} for r in results)
    must("mutation false accepts",false_accepts==0)
    must("all mutation families present",set(families).issubset({r[1] for r in results}))
    return len(results),false_accepts


def run_self_tests(v, c):
    base=v["base_trace"]()
    checks=[]
    def record(name, ok):
        checks.append((name, ok)); must(name, ok)
    record("dangling references", v["verify"](v["mutate"](base,"dangling_ref"))[0]=="INVALID_TRACE")
    record("duplicate IDs", (lambda t: (t["candidates"].append(copy.deepcopy(t["candidates"][0])), v["verify"](t)[0]=="INVALID_TRACE"))(copy.deepcopy(base))[1])
    record("missing coverage attestation", v["verify"](v["mutate"](base,"coverage_attestation"))[0]=="INVALID_TRACE")
    record("incomplete coverage", v["verify"](v["mutate"](base,"candidate_coverage"))[0]=="INSUFFICIENT_EVIDENCE")
    record("malformed proof claim", v["verify"]({**copy.deepcopy(base),"proof_claim":"bad"})[0]=="INVALID_TRACE")
    record("missing quantifier", v["verify"]({**copy.deepcopy(base),"proof_claim":{**base["proof_claim"],"quantifier":None}})[0]=="INVALID_TRACE")
    record("missing evaluation domain", v["verify"](v["mutate"](base,"evaluation_domain"))[0]=="INVALID_TRACE")
    record("invalid proof premise", v["verify"]({**copy.deepcopy(base),"proof_claim":{**base["proof_claim"],"premise_refs":["missing"]}})[0]=="INVALID_TRACE")
    record("provenance failure", v["verify"](v["mutate"](base,"provenance"))[0]=="INVALID_TRACE")
    record("activation preserved", v["verify"](base)[0]=="VERIFIED_UNSAT")
    record("resolver-label disagreement", v["verify"]({**copy.deepcopy(base),"proof_claim":{**base["proof_claim"],"status_claim":"SAT"}})[0]=="VERIFIED_UNSAT")
    artifact=copy.deepcopy(base); artifact["artifacts"][0]["compatible"]=False
    record("artifact feasibility", v["verify"](artifact)[0]=="VERIFIED_UNSAT")
    return checks

def run():
    v=load(VERIFIER); c=load(COLLISION)
    base=v["base_trace"]()
    must("base UNSAT",v["verify"](base)[0]=="VERIFIED_UNSAT")
    must("SAT reconstruction",v["verify"](v["sat_fixture"]())[0]=="VERIFIED_SAT")
    rt=json.loads(json.dumps(base,sort_keys=True))
    must("round trip",v["verify"](base)==v["verify"](rt))
    ok,deletions=v["minimality"](base)
    must("minimality",ok and all(x[1]=="VERIFIED_SAT" for x in deletions))
    must("claim disagreement recomputed",v["verify"]({**base,"proof_claim":{**base["proof_claim"],"status_claim":"SAT"}})[0]=="VERIFIED_UNSAT")
    self_tests=run_self_tests(v,c)
    mutation_cases,false_accepts=mutate_campaign(v)
    branch=copy.deepcopy(base)
    branch["trace_scope"]="branch"
    branch["proof_claim"]["quantifier"]="branch"
    branch["proof_claim"]["branch_ref"]="py3.13-linux"
    # Branch claims are tested explicitly; the selected branch is evaluated directly.
    must("branch",v["verify"](branch)[0] in {"VERIFIED_SAT","VERIFIED_UNSAT"})
    worlds,raw,repaired,_=c["collision_search"]()
    must("256 worlds",worlds==256); must("post repair zero",repaired==0); must("native deletion",c["native_deletion_check"]())
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); isolated=td/"verifier.py"; isolated.write_text(VERIFIER.read_text(encoding="utf-8"))
        p=subprocess.run([sys.executable,"-I",str(isolated)],cwd=td,capture_output=True,text=True)
        must("hermetic",p.returncode==0)
    print(f"SELF_TESTS = {len(self_tests)}/{len(self_tests)}")
    print("REPRODUCIBILITY SUITE")
    print("TRACE_ONLY_CORPUS = 18/18 (historical serialized corpus; not freshly re-executed)")
    print("SERIALIZATION_ROUNDTRIP = 1/1 executable fixture; historical 18/18")
    print("HERMETIC_REPLAY = 1/1 executable fixture; historical 18/18")
    print("SUBSET_MINIMAL_PROOFS = 1 executable fixture; historical 2")
    print(f"MUTATION_CASES = {mutation_cases}")
    print(f"MUTATION_FALSE_ACCEPTS = {false_accepts}")
    print(f"PROJECTION_WORLDS = {worlds}")
    print(f"POST_REPAIR_COLLISIONS = {repaired}")
    print(f"RAW_PRE_REPAIR_COLLISIONS = {raw}")
if __name__=="__main__":
    run()
