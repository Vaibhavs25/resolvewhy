from __future__ import annotations

import itertools
import json
from typing import Any


COMPARE = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}


def version_tuple(value: str) -> tuple[int, ...]:
    if not isinstance(value, str):
        raise ValueError("version must be a string")
    parts = value.split(".")
    if not 2 <= len(parts) <= 3 or any(not p.isdigit() for p in parts):
        raise ValueError(f"unsupported version: {value!r}")
    nums = tuple(int(p) for p in parts)
    return nums + (0,) if len(nums) == 2 else nums


def compare_version(value: str, op: str, rhs: str) -> bool:
    if op not in COMPARE:
        raise ValueError(f"unsupported comparison operator: {op!r}")
    return COMPARE[op](version_tuple(value), version_tuple(rhs))


SUPPORTED_MARKERS = {
    "python_version",
    "python_full_version",
    "sys_platform",
    "platform_machine",
    "platform_python_implementation",
    "extra",
}


def eval_marker(expr: Any, env: dict[str, Any]) -> bool:
    if expr is None or isinstance(expr, bool):
        return True if expr is None else expr
    if not isinstance(expr, dict):
        raise ValueError("malformed activation condition")
    if "and" in expr:
        values = expr["and"]
        if not isinstance(values, list):
            raise ValueError("marker 'and' must be a list")
        return all(eval_marker(v, env) for v in values)
    if "or" in expr:
        values = expr["or"]
        if not isinstance(values, list):
            raise ValueError("marker 'or' must be a list")
        return any(eval_marker(v, env) for v in values)
    if "not" in expr:
        return not eval_marker(expr["not"], env)
    if set(expr) != {"variable", "op", "value"}:
        raise ValueError("malformed atomic marker")
    variable, op, value = expr["variable"], expr["op"], str(expr["value"])
    if variable not in SUPPORTED_MARKERS:
        raise ValueError(f"unsupported marker variable: {variable}")
    lhs = str(env.get(variable, ""))
    if op in {"==", "!="}:
        return COMPARE[op](lhs, value)
    if op in {"<", "<=", ">", ">="}:
        return compare_version(lhs, op, value)
    raise ValueError(f"unsupported marker operator: {op}")


def _unique_ids(items: Any, label: str) -> tuple[set[str], str | None]:
    if not isinstance(items, list):
        return set(), f"{label} must be a list"
    ids = []
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            return set(), f"invalid {label} item"
        ids.append(item["id"])
    if len(ids) != len(set(ids)):
        return set(), f"duplicate {label} IDs"
    return set(ids), None


def _evidence(t: dict[str, Any]) -> dict[str, dict[str, Any]]:
    state = t["evidence_state"]
    observations = state.get("observations", [])
    if not isinstance(observations, list):
        return {}
    out = {}
    for obs in observations:
        if not isinstance(obs, dict) or not isinstance(obs.get("id"), str):
            continue
        if obs["id"] in out:
            return {}
        supports = obs.get("supports_refs", [])
        if not isinstance(supports, list):
            return {}
        out[obs["id"]] = obs
    return out


def _provenance_cycle(prov: dict[str, dict[str, Any]]) -> bool:
    graph = {pid: [x for x in rec.get("premise_refs", []) if x in prov] for pid, rec in prov.items()}
    active, done = set(), set()

    def visit(node: str) -> bool:
        if node in active:
            return True
        if node in done:
            return False
        active.add(node)
        if any(visit(child) for child in graph[node]):
            return True
        active.remove(node)
        done.add(node)
        return False

    return any(visit(node) for node in graph)


def _provenance_reaches(
    premise: str,
    prov: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    semantic_ids: set[str],
) -> bool:
    seen: set[str] = set()

    def walk(ref: str) -> bool:
        if ref not in semantic_ids and ref not in prov:
            return False
        for rec in prov.values():
            refs = rec.get("premise_refs", [])
            if ref not in refs:
                continue
            pid = rec["id"]
            if pid in seen:
                continue
            seen.add(pid)
            for evid in rec.get("evidence_refs", []):
                obs = evidence[evid]
                if ref in set(obs.get("supports_refs", [])):
                    return True
            for nested in refs:
                if nested != ref and nested in prov and walk(nested):
                    return True
        return False

    return walk(premise)


def structural(t: dict[str, Any]) -> tuple[bool, str]:
    required = [
        "schema", "trace_scope", "requirements", "candidates", "artifacts",
        "dependencies", "runtime_contexts", "evaluation_domain",
        "resolution_policy", "candidate_domains", "semantic_constraints",
        "provenance", "evidence_state", "proof_claim",
    ]
    missing = [x for x in required if x not in t]
    if missing:
        return False, "missing required fields: " + ",".join(missing)

    if t["trace_scope"] not in {"existential", "universal", "branch"}:
        return False, "invalid trace scope"

    for key in ("requirements", "candidates", "artifacts", "dependencies", "runtime_contexts",
                "evaluation_domain", "candidate_domains", "semantic_constraints", "provenance"):
        if not isinstance(t[key], list):
            return False, f"{key} must be a list"

    req_ids, err = _unique_ids(t["requirements"], "requirement")
    if err:
        return False, err
    candidate_ids, err = _unique_ids(t["candidates"], "candidate")
    if err:
        return False, err
    artifact_ids, err = _unique_ids(t["artifacts"], "artifact")
    if err:
        return False, err
    dependency_ids, err = _unique_ids(t["dependencies"], "dependency")
    if err:
        return False, err
    context_ids, err = _unique_ids(t["runtime_contexts"], "runtime context")
    if err:
        return False, err
    domain_ids, err = _unique_ids(t["evaluation_domain"], "evaluation domain")
    if err:
        return False, err
    semantic_ids, err = _unique_ids(t["semantic_constraints"], "semantic constraint")
    if err:
        return False, err

    if not isinstance(t["evidence_state"], dict):
        return False, "invalid evidence state"
    evidence = _evidence(t)
    if not evidence and t["evidence_state"].get("observations"):
        return False, "invalid evidence observations"

    claim = t["proof_claim"]
    if not isinstance(claim, dict):
        return False, "invalid proof claim"
    if claim.get("kind") != "satisfiability":
        return False, "invalid proof claim kind"
    if claim.get("quantifier") not in {"existential", "universal", "branch"}:
        return False, "invalid proof claim quantifier"
    if claim.get("evaluation_domain_ref") != "evaluation_domain":
        return False, "proof claim does not bind evaluation domain"
    if claim.get("status_claim") not in {"SAT", "UNSAT"}:
        return False, "invalid proof claim status"
    premises = claim.get("premise_refs")
    if not isinstance(premises, list) or not premises or not set(premises).issubset(semantic_ids):
        return False, "invalid proof premise references"
    if t["trace_scope"] != claim["quantifier"]:
        return False, "trace scope and proof quantifier disagree"
    if claim["quantifier"] == "branch" and claim.get("branch_ref") not in domain_ids:
        return False, "branch claim lacks valid branch_ref"

    if len(t["evaluation_domain"]) == 1:
        entry = t["evaluation_domain"][0]
        if entry.get("runtime_context_ref") not in context_ids:
            return False, "evaluation domain references unknown runtime context"
    else:
        for entry in t["evaluation_domain"]:
            if entry.get("runtime_context_ref") not in context_ids:
                return False, "evaluation domain references unknown runtime context"

    candidate_by_id = {c["id"]: c for c in t["candidates"]}
    for req in t["requirements"]:
        if not all(isinstance(req.get(k), str) for k in ("package", "op", "version")):
            return False, "malformed requirement"
    for dep in t["dependencies"]:
        if dep.get("parent_candidate") not in candidate_ids:
            return False, "dangling dependency parent"
        req = dep.get("requirement")
        if not isinstance(req, dict) or not all(isinstance(req.get(k), str) for k in ("package", "op", "version")):
            return False, "malformed dependency requirement"
        condition = dep.get("activation_condition")
        if condition is not None and not isinstance(condition, (dict, bool)):
            return False, "malformed activation condition"

    for art in t["artifacts"]:
        if art.get("candidate_ref") not in candidate_ids:
            return False, "dangling artifact candidate"

    for dom in t["candidate_domains"]:
        if not isinstance(dom.get("candidate_ids"), list) or not isinstance(dom.get("scope"), dict):
            return False, "malformed candidate domain"
        if not isinstance(dom.get("identifier"), str):
            return False, "candidate domain lacks identifier"
        if any(cid not in candidate_ids for cid in dom["candidate_ids"]):
            return False, "dangling coverage candidate"
        cov = dom.get("coverage")
        if not isinstance(cov, dict) or cov.get("status") not in {"complete", "partial", "unknown"}:
            return False, "invalid coverage status"
        sources = dom["scope"].get("sources")
        if not isinstance(sources, list):
            return False, "candidate-domain scope lacks sources"
        for cid in dom["candidate_ids"]:
            source = candidate_by_id[cid].get("source")
            if source is not None and source not in sources:
                return False, "candidate lies outside declared coverage scope"
        if cov["status"] == "complete":
            att = cov.get("attestation")
            if not isinstance(att, dict):
                return False, "complete coverage lacks attestation"
            refs = att.get("evidence_refs")
            if not isinstance(refs, list) or not refs or any(ref not in evidence for ref in refs):
                return False, "invalid coverage evidence references"
            if any(
                dom["id"] not in set(evidence[ref].get("supports_refs", []))
                for ref in refs
            ):
                return False, "coverage evidence does not support its domain"

    sem_by_id = {s["id"]: s for s in t["semantic_constraints"]}
    for s in t["semantic_constraints"]:
        kind = s.get("kind")
        if kind == "requirement" and s.get("source_ref") not in req_ids:
            return False, "dangling requirement semantic reference"
        if kind == "dependency" and s.get("source_ref") not in dependency_ids:
            return False, "dangling dependency semantic reference"
        if kind == "requires_python" and s.get("source_ref") not in candidate_ids:
            return False, "dangling requires-python semantic reference"
        if kind == "artifact_compatibility" and s.get("source_ref") not in artifact_ids:
            return False, "dangling artifact semantic reference"
        if kind not in {"requirement", "dependency", "requires_python", "artifact_compatibility"}:
            return False, f"unsupported semantic constraint kind: {kind}"

    prov = {}
    if not t["provenance"]:
        return False, "missing provenance"
    for rec in t["provenance"]:
        if not isinstance(rec, dict) or not isinstance(rec.get("id"), str):
            return False, "invalid provenance record"
        if rec["id"] in prov:
            return False, "duplicate provenance IDs"
        prov[rec["id"]] = rec
    if _provenance_cycle(prov):
        return False, "provenance cycle"
    for rec in prov.values():
        if not isinstance(rec.get("premise_refs", []), list) or not isinstance(rec.get("evidence_refs", []), list):
            return False, "invalid provenance lists"
        for ref in rec["premise_refs"]:
            if ref not in semantic_ids and ref not in prov and ref not in evidence:
                return False, "dangling provenance premise reference"
        for ref in rec["evidence_refs"]:
            if ref not in evidence:
                return False, "dangling provenance evidence reference"
        if rec["premise_refs"]:
            for ref in rec["evidence_refs"]:
                if not (set(rec["premise_refs"]) & set(evidence[ref].get("supports_refs", []))):
                    return False, "provenance evidence is unrelated to its premise"

    for premise in premises:
        if not _provenance_reaches(premise, prov, evidence, semantic_ids):
            return False, "proof premise provenance is not reachable"

    claimed_core = t.get("claimed_core")
    if claimed_core is not None and set(claimed_core) != set(premises):
        return False, "claimed_core must equal proof premises"

    return True, "ok"


def _candidate_domains(t: dict[str, Any], package: str) -> set[str]:
    matches = [d for d in t["candidate_domains"] if d["identifier"] == package]
    if not matches:
        raise PermissionError(f"missing candidate coverage for {package}")
    ids: set[str] = set()
    for dom in matches:
        if dom["coverage"]["status"] != "complete":
            raise PermissionError(f"incomplete candidate coverage for {package}")
        ids.update(dom["candidate_ids"])
    return ids


def _relevant_packages(t: dict[str, Any], selected: list[dict[str, Any]]) -> set[str]:
    candidates = {c["id"]: c for c in t["candidates"]}
    packages: set[str] = set()
    for s in selected:
        if s["kind"] == "requirement":
            req = next(r for r in t["requirements"] if r["id"] == s["source_ref"])
            packages.add(req["package"])
        elif s["kind"] == "dependency":
            dep = next(d for d in t["dependencies"] if d["id"] == s["source_ref"])
            packages.add(candidates[dep["parent_candidate"]]["package"])
            packages.add(dep["requirement"]["package"])
        elif s["kind"] == "requires_python":
            packages.add(candidates[s["source_ref"]]["package"])
        elif s["kind"] == "artifact_compatibility":
            art = next(a for a in t["artifacts"] if a["id"] == s["source_ref"])
            packages.add(candidates[art["candidate_ref"]]["package"])
    return packages


def _candidate_usable(
    candidate: dict[str, Any],
    env: dict[str, Any],
    t: dict[str, Any],
    selected: list[dict[str, Any]],
) -> bool:
    policy = t["resolution_policy"]
    allowed_sources = policy.get("allowed_sources")
    if allowed_sources is not None:
        if not isinstance(allowed_sources, list):
            raise ValueError("malformed allowed_sources")
        if candidate.get("source") not in allowed_sources:
            return False
    prerelease = candidate.get("prerelease", False)
    mode = policy.get("prerelease")
    if mode not in {"allow", "disallow"}:
        raise ValueError("unsupported prerelease policy")
    if prerelease and mode == "disallow":
        return False

    for s in selected:
        if s["kind"] == "requires_python" and s["source_ref"] == candidate["id"]:
            if not compare_version(
                str(env["python_full_version"]),
                s.get("op", ">="),
                str(s.get("version", "0")),
            ):
                return False

    for s in selected:
        if s["kind"] == "artifact_compatibility":
            art = next(a for a in t["artifacts"] if a["id"] == s["source_ref"])
            if art["candidate_ref"] == candidate["id"] and art.get("compatible") is False:
                return False
    return True


def branch_sat(t: dict[str, Any], context: dict[str, Any]) -> bool:
    selected = [
        s for s in t["semantic_constraints"]
        if s["id"] in set(t["proof_claim"]["premise_refs"])
    ]
    packages = sorted(_relevant_packages(t, selected))
    candidate_by_id = {c["id"]: c for c in t["candidates"]}
    choices: list[list[dict[str, Any] | None]] = []
    for package in packages:
        ids = _candidate_domains(t, package)
        usable = [
            candidate_by_id[cid]
            for cid in ids
            if _candidate_usable(candidate_by_id[cid], context, t, selected)
        ]
        choices.append(usable + [None])

    requirements = [
        next(r for r in t["requirements"] if r["id"] == s["source_ref"])
        for s in selected if s["kind"] == "requirement"
    ]
    dependencies = [
        next(d for d in t["dependencies"] if d["id"] == s["source_ref"])
        for s in selected if s["kind"] == "dependency"
    ]

    if not choices:
        return True

    for assignment in itertools.product(*choices):
        chosen = {pkg: cand for pkg, cand in zip(packages, assignment) if cand is not None}
        if not all(
            req["package"] in chosen
            and compare_version(chosen[req["package"]]["version"], req["op"], req["version"])
            for req in requirements
        ):
            continue

        valid = True
        for dep in dependencies:
            parent = candidate_by_id[dep["parent_candidate"]]
            selected_parent = chosen.get(parent["package"])
            if selected_parent is None or selected_parent["id"] != parent["id"]:
                continue
            if not eval_marker(dep.get("activation_condition"), context):
                continue
            target = chosen.get(dep["requirement"]["package"])
            if target is None or not compare_version(
                target["version"], dep["requirement"]["op"], dep["requirement"]["version"]
            ):
                valid = False
                break
        if valid:
            return True
    return False


def verify(t: dict[str, Any]) -> tuple[str, Any]:
    try:
        ok, why = structural(t)
        if not ok:
            return "INVALID_TRACE", why
        if t["evidence_state"].get("overall") in {"missing", "incomplete", "unknown"}:
            return "INSUFFICIENT_EVIDENCE", "proof evidence incomplete"

        results = []
        contexts = {c["id"]: c for c in t["runtime_contexts"]}
        for entry in t["evaluation_domain"]:
            results.append(branch_sat(t, contexts[entry["runtime_context_ref"]]))

        q = t["proof_claim"]["quantifier"]
        if q == "universal":
            return ("VERIFIED_SAT", results) if all(results) else ("VERIFIED_UNSAT", results)
        if q == "existential":
            return ("VERIFIED_SAT", results) if any(results) else ("VERIFIED_UNSAT", results)
        if q == "branch":
            idx = next(i for i, e in enumerate(t["evaluation_domain"]) if e["id"] == t["proof_claim"]["branch_ref"])
            return ("VERIFIED_SAT", [results[idx]]) if results[idx] else ("VERIFIED_UNSAT", [results[idx]])
        return "INVALID_TRACE", "unsupported proof quantifier"
    except PermissionError as exc:
        return "INSUFFICIENT_EVIDENCE", str(exc)
    except (KeyError, TypeError, ValueError, StopIteration, IndexError) as exc:
        return "INVALID_TRACE", f"uninterpretable semantic data: {exc}"


def minimality(t: dict[str, Any]) -> tuple[bool, list[tuple[str, str]]]:
    if verify(t)[0] != "VERIFIED_UNSAT":
        return False, []
    premises = list(t["proof_claim"]["premise_refs"])
    checks = []
    for premise in premises:
        clone = json.loads(json.dumps(t))
        clone["semantic_constraints"] = [
            s for s in clone["semantic_constraints"] if s["id"] != premise
        ]
        clone["proof_claim"]["premise_refs"] = [p for p in premises if p != premise]
        clone["claimed_core"] = list(clone["proof_claim"]["premise_refs"])
        clone["provenance"] = [
            p for p in clone["provenance"] if premise not in p.get("premise_refs", [])
        ]
        checks.append((premise, verify(clone)[0]))
    return True, checks


def _obs(ids: list[tuple[str, str]]) -> list[dict[str, Any]]:
    return [{"id": ident, "kind": kind, "supports_refs": []} for ident, kind in ids]


def base_trace() -> dict[str, Any]:
    obs = _obs([
        ("obs:req:a", "requirement"), ("obs:req:b", "requirement"),
        ("obs:dep:a", "dependency"), ("obs:dep:b", "dependency"),
        ("obs:domain:a", "candidate-domain"), ("obs:domain:b", "candidate-domain"),
        ("obs:domain:x", "candidate-domain"),
    ])
    trace = {
        "schema": "resolvewhy-trace/research-2026",
        "trace_scope": "universal",
        "requirements": [
            {"id": "req:a", "package": "a", "op": "==", "version": "1.0"},
            {"id": "req:b", "package": "b", "op": "==", "version": "1.0"},
        ],
        "candidates": [
            {"id": "cand:a1", "package": "a", "version": "1.0", "source": "index:A"},
            {"id": "cand:b1", "package": "b", "version": "1.0", "source": "index:A"},
            {"id": "cand:x1", "package": "x", "version": "1.0", "source": "index:A"},
            {"id": "cand:x2", "package": "x", "version": "2.0", "source": "index:A"},
        ],
        "artifacts": [
            {"id": "art:a1", "candidate_ref": "cand:a1", "compatible": True},
            {"id": "art:b1", "candidate_ref": "cand:b1", "compatible": True},
            {"id": "art:x1", "candidate_ref": "cand:x1", "compatible": True},
            {"id": "art:x2", "candidate_ref": "cand:x2", "compatible": True},
        ],
        "dependencies": [
            {"id": "dep:a-x", "parent_candidate": "cand:a1",
             "requirement": {"package": "x", "op": "<", "version": "2.0"},
             "activation_condition": {"and": [{"variable": "sys_platform", "op": "==", "value": "linux"}]}},
            {"id": "dep:b-x", "parent_candidate": "cand:b1",
             "requirement": {"package": "x", "op": ">=", "version": "2.0"},
             "activation_condition": {"or": [{"variable": "sys_platform", "op": "==", "value": "linux"}, False]}},
        ],
        "runtime_contexts": [{
            "id": "ctx:linux", "python_version": "3.13", "python_full_version": "3.13.5",
            "sys_platform": "linux", "platform_machine": "x86_64",
            "platform_python_implementation": "CPython", "extra": ""
        }],
        "evaluation_domain": [{"id": "env:linux", "runtime_context_ref": "ctx:linux"}],
        "resolution_policy": {"prerelease": "disallow", "allowed_sources": ["index:A"], "source_selection": "fixed"},
        "candidate_domains": [
            {"id": "domain:a", "identifier": "a", "candidate_ids": ["cand:a1"], "scope": {"sources": ["index:A"]},
             "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": ["obs:domain:a"]}}},
            {"id": "domain:b", "identifier": "b", "candidate_ids": ["cand:b1"], "scope": {"sources": ["index:A"]},
             "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": ["obs:domain:b"]}}},
            {"id": "domain:x", "identifier": "x", "candidate_ids": ["cand:x1", "cand:x2"], "scope": {"sources": ["index:A"]},
             "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": ["obs:domain:x"]}}},
        ],
        "semantic_constraints": [
            {"id": "c:root:a", "kind": "requirement", "source_ref": "req:a"},
            {"id": "c:root:b", "kind": "requirement", "source_ref": "req:b"},
            {"id": "c:dep:a-x", "kind": "dependency", "source_ref": "dep:a-x"},
            {"id": "c:dep:b-x", "kind": "dependency", "source_ref": "dep:b-x"},
        ],
        "provenance": [
            {"id": "prov:root:a", "premise_refs": ["c:root:a"], "evidence_refs": ["obs:req:a"]},
            {"id": "prov:root:b", "premise_refs": ["c:root:b"], "evidence_refs": ["obs:req:b"]},
            {"id": "prov:dep:a", "premise_refs": ["c:dep:a-x"], "evidence_refs": ["obs:dep:a"]},
            {"id": "prov:dep:b", "premise_refs": ["c:dep:b-x"], "evidence_refs": ["obs:dep:b"]},
            {"id": "prov:domain:a", "premise_refs": [], "evidence_refs": ["obs:domain:a"]},
            {"id": "prov:domain:b", "premise_refs": [], "evidence_refs": ["obs:domain:b"]},
            {"id": "prov:domain:x", "premise_refs": [], "evidence_refs": ["obs:domain:x"]},
        ],
        "evidence_state": {"overall": "known", "observations": obs},
        "proof_claim": {"id": "claim:base", "kind": "satisfiability", "quantifier": "universal",
                        "evaluation_domain_ref": "evaluation_domain", "status_claim": "UNSAT",
                        "premise_refs": ["c:root:a", "c:root:b", "c:dep:a-x", "c:dep:b-x"]},
        "claimed_core": ["c:root:a", "c:root:b", "c:dep:a-x", "c:dep:b-x"],
    }
    support = {o["id"]: [] for o in obs}
    support["obs:req:a"] = ["c:root:a"]
    support["obs:req:b"] = ["c:root:b"]
    support["obs:dep:a"] = ["c:dep:a-x"]
    support["obs:dep:b"] = ["c:dep:b-x"]
    for pkg in ("a", "b", "x"):
        support[f"obs:domain:{pkg}"] = [f"domain:{pkg}"]
    for o in trace["evidence_state"]["observations"]:
        o["supports_refs"] = support[o["id"]]
    return trace


def sat_fixture() -> dict[str, Any]:
    t = base_trace()
    t["proof_claim"]["premise_refs"] = ["c:root:a"]
    t["claimed_core"] = ["c:root:a"]
    t["proof_claim"]["status_claim"] = "SAT"
    return t


def prerelease_fixture() -> dict[str, Any]:
    t = base_trace()
    t["requirements"] = [{"id": "req:foo", "package": "foo", "op": "<", "version": "2.0"}]
    t["candidates"] = [{"id": "cand:foo", "package": "foo", "version": "1.0", "prerelease": True, "source": "index:A"}]
    t["artifacts"] = [{"id": "art:foo", "candidate_ref": "cand:foo", "compatible": True}]
    t["dependencies"] = []
    t["candidate_domains"] = [{
        "id": "domain:foo", "identifier": "foo", "candidate_ids": ["cand:foo"],
        "scope": {"sources": ["index:A"]},
        "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": ["obs:domain:foo"]}}
    }]
    t["evidence_state"]["observations"] = [
        {"id": "obs:req:foo", "kind": "requirement", "supports_refs": ["c:foo"]},
        {"id": "obs:domain:foo", "kind": "candidate-domain", "supports_refs": ["domain:foo"]},
    ]
    t["provenance"] = [
        {"id": "prov:foo", "premise_refs": ["c:foo"], "evidence_refs": ["obs:req:foo"]},
        {"id": "prov:domain:foo", "premise_refs": [], "evidence_refs": ["obs:domain:foo"]},
    ]
    t["semantic_constraints"] = [{"id": "c:foo", "kind": "requirement", "source_ref": "req:foo"}]
    t["proof_claim"]["premise_refs"] = ["c:foo"]
    t["claimed_core"] = ["c:foo"]
    t["proof_claim"]["status_claim"] = "UNSAT"
    return t


def rw09_fixture() -> dict[str, Any]:
    t = base_trace()
    t["requirements"] = [{"id": "req:app", "package": "app", "op": "==", "version": "1.0"}]
    t["candidates"] = [
        {"id": "cand:app1", "package": "app", "version": "1.0", "source": "index:A"},
        {"id": "cand:numba", "package": "numba", "version": "0.61.0", "requires_python": ">=3.10", "source": "index:A"},
    ]
    t["artifacts"] = [
        {"id": "art:app", "candidate_ref": "cand:app1", "compatible": True},
        {"id": "art:numba", "candidate_ref": "cand:numba", "compatible": True},
    ]
    t["dependencies"] = [{"id": "dep:app-numba", "parent_candidate": "cand:app1",
                          "requirement": {"package": "numba", "op": "==", "version": "0.61.0"},
                          "activation_condition": True}]
    t["runtime_contexts"] = [
        {"id": "ctx:py3.12", "python_version": "3.12", "python_full_version": "3.12.0", "sys_platform": "linux", "platform_machine": "x86_64", "platform_python_implementation": "CPython", "extra": ""},
        {"id": "ctx:py3.9", "python_version": "3.9", "python_full_version": "3.9.18", "sys_platform": "linux", "platform_machine": "x86_64", "platform_python_implementation": "CPython", "extra": ""},
    ]
    t["evaluation_domain"] = [
        {"id": "env:py3.12", "runtime_context_ref": "ctx:py3.12"},
        {"id": "env:py3.9", "runtime_context_ref": "ctx:py3.9"},
    ]
    t["candidate_domains"] = [
        {"id": "domain:app", "identifier": "app", "candidate_ids": ["cand:app1"], "scope": {"sources": ["index:A"]},
         "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": ["obs:domain:app"]}}},
        {"id": "domain:numba", "identifier": "numba", "candidate_ids": ["cand:numba"], "scope": {"sources": ["index:A"]},
         "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": ["obs:domain:numba"]}}},
    ]
    t["evidence_state"]["observations"] = [
        {"id": "obs:req:app", "kind": "requirement", "supports_refs": ["c:root"]},
        {"id": "obs:dep:app-numba", "kind": "dependency", "supports_refs": ["c:dep"]},
        {"id": "obs:python:numba", "kind": "metadata", "supports_refs": ["c:python"]},
        {"id": "obs:domain:app", "kind": "candidate-domain", "supports_refs": ["domain:app"]},
        {"id": "obs:domain:numba", "kind": "candidate-domain", "supports_refs": ["domain:numba"]},
    ]
    t["semantic_constraints"] = [
        {"id": "c:root", "kind": "requirement", "source_ref": "req:app"},
        {"id": "c:dep", "kind": "dependency", "source_ref": "dep:app-numba"},
        {"id": "c:python", "kind": "requires_python", "source_ref": "cand:numba", "op": ">=", "version": "3.10"},
    ]
    t["provenance"] = [
        {"id": "prov:root", "premise_refs": ["c:root"], "evidence_refs": ["obs:req:app"]},
        {"id": "prov:dep", "premise_refs": ["c:dep"], "evidence_refs": ["obs:dep:app-numba"]},
        {"id": "prov:python", "premise_refs": ["c:python"], "evidence_refs": ["obs:python:numba"]},
        {"id": "prov:domain:app", "premise_refs": [], "evidence_refs": ["obs:domain:app"]},
        {"id": "prov:domain:numba", "premise_refs": [], "evidence_refs": ["obs:domain:numba"]},
    ]
    t["proof_claim"] = {"id": "claim:rw09", "kind": "satisfiability", "quantifier": "universal",
                        "evaluation_domain_ref": "evaluation_domain", "status_claim": "UNSAT",
                        "premise_refs": ["c:root", "c:dep", "c:python"]}
    t["claimed_core"] = t["proof_claim"]["premise_refs"][:]
    return t


def rw14_fixture() -> dict[str, Any]:
    t = base_trace()
    t["requirements"] = [
        {"id": "req:appa", "package": "appa", "op": "==", "version": "1.0"},
        {"id": "req:depB", "package": "depB", "op": "==", "version": "1.0"},
    ]
    t["candidates"] = [
        {"id": "cand:appa1", "package": "appa", "version": "1.0", "source": "index:A"},
        {"id": "cand:depB1", "package": "depB", "version": "1.0", "source": "index:A"},
        {"id": "cand:depA1", "package": "depA", "version": "1.0", "source": "index:A"},
        {"id": "cand:depA2", "package": "depA", "version": "2.0", "source": "index:A"},
        {"id": "cand:leaf1", "package": "leaf", "version": "1.0", "source": "index:A"},
        {"id": "cand:leaf2", "package": "leaf", "version": "2.0", "source": "index:A"},
    ]
    t["artifacts"] = [{"id": f"art:{c['id']}", "candidate_ref": c["id"], "compatible": True} for c in t["candidates"]]
    t["dependencies"] = [
        {"id": "dep:appa-depA", "parent_candidate": "cand:appa1", "requirement": {"package": "depA", "op": "<", "version": "2.0"}, "activation_condition": {"variable": "sys_platform", "op": "==", "value": "linux"}},
        {"id": "dep:depA1-leaf", "parent_candidate": "cand:depA1", "requirement": {"package": "leaf", "op": "==", "version": "1.0"}, "activation_condition": True},
        {"id": "dep:depA2-leaf", "parent_candidate": "cand:depA2", "requirement": {"package": "leaf", "op": "==", "version": "2.0"}, "activation_condition": True},
        {"id": "dep:depB1-leaf", "parent_candidate": "cand:depB1", "requirement": {"package": "leaf", "op": "==", "version": "2.0"}, "activation_condition": True},
    ]
    t["candidate_domains"] = []
    for pkg in ("appa", "depB", "depA", "leaf"):
        ids = [c["id"] for c in t["candidates"] if c["package"] == pkg]
        t["candidate_domains"].append({
            "id": f"domain:{pkg}", "identifier": pkg, "candidate_ids": ids, "scope": {"sources": ["index:A"]},
            "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": [f"obs:domain:{pkg}"]}}
        })
    constraints = [
        ("c:root:appa", "requirement", "req:appa", "obs:req:appa"),
        ("c:root:depB", "requirement", "req:depB", "obs:req:depB"),
        ("c:appa-depA", "dependency", "dep:appa-depA", "obs:dep:appa-depA"),
        ("c:depA1-leaf", "dependency", "dep:depA1-leaf", "obs:dep:depA1-leaf"),
        ("c:depA2-leaf", "dependency", "dep:depA2-leaf", "obs:dep:depA2-leaf"),
        ("c:depB1-leaf", "dependency", "dep:depB1-leaf", "obs:dep:depB1-leaf"),
    ]
    t["semantic_constraints"] = [{"id": a, "kind": b, "source_ref": c} for a, b, c, _ in constraints]
    t["evidence_state"]["observations"] = [
        {"id": obs, "kind": "fact", "supports_refs": [cid]}
        for cid, _, _, obs in constraints
    ] + [
        {"id": f"obs:domain:{pkg}", "kind": "candidate-domain", "supports_refs": [f"domain:{pkg}"]}
        for pkg in ("appa", "depB", "depA", "leaf")
    ]
    t["provenance"] = [
        {"id": f"prov:{cid}", "premise_refs": [cid], "evidence_refs": [obs]}
        for cid, _, _, obs in constraints
    ] + [
        {"id": f"prov:domain:{pkg}", "premise_refs": [], "evidence_refs": [f"obs:domain:{pkg}"]}
        for pkg in ("appa", "depB", "depA", "leaf")
    ]
    core = ["c:root:appa", "c:root:depB", "c:appa-depA", "c:depA1-leaf", "c:depB1-leaf"]
    t["proof_claim"] = {"id": "claim:rw14", "kind": "satisfiability", "quantifier": "universal",
                        "evaluation_domain_ref": "evaluation_domain", "status_claim": "UNSAT", "premise_refs": core}
    t["claimed_core"] = core[:]
    return t


def rw15_fixture() -> dict[str, Any]:
    t = base_trace()
    t["requirements"] = [{"id": "req:pkg", "package": "pkg", "op": "==", "version": "1.0"}]
    t["candidates"] = [{"id": "cand:pkg", "package": "pkg", "version": "1.0", "source": "index:A"}]
    t["artifacts"] = [{"id": "art:pkg-win", "candidate_ref": "cand:pkg", "compatible": False, "tags": ["win_amd64"]}]
    t["dependencies"] = []
    t["candidate_domains"] = [{"id": "domain:pkg", "identifier": "pkg", "candidate_ids": ["cand:pkg"], "scope": {"sources": ["index:A"]},
                               "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": ["obs:domain:pkg"]}}}]
    t["evidence_state"]["observations"] = [
        {"id": "obs:req:pkg", "kind": "requirement", "supports_refs": ["c:root"]},
        {"id": "obs:artifact:pkg", "kind": "artifact", "supports_refs": ["c:artifact"]},
        {"id": "obs:domain:pkg", "kind": "candidate-domain", "supports_refs": ["domain:pkg"]},
    ]
    t["semantic_constraints"] = [
        {"id": "c:root", "kind": "requirement", "source_ref": "req:pkg"},
        {"id": "c:artifact", "kind": "artifact_compatibility", "source_ref": "art:pkg-win"},
    ]
    t["provenance"] = [
        {"id": "prov:root", "premise_refs": ["c:root"], "evidence_refs": ["obs:req:pkg"]},
        {"id": "prov:artifact", "premise_refs": ["c:artifact"], "evidence_refs": ["obs:artifact:pkg"]},
        {"id": "prov:domain", "premise_refs": [], "evidence_refs": ["obs:domain:pkg"]},
    ]
    t["proof_claim"]["premise_refs"] = ["c:root", "c:artifact"]
    t["claimed_core"] = t["proof_claim"]["premise_refs"][:]
    return t


def rw16_fixture() -> dict[str, Any]:
    t = rw15_fixture()
    t["candidates"] = [{"id": "cand:pkg", "package": "pkg", "version": "1.0", "requires_python": ">=4.0", "source": "index:A"}]
    t["artifacts"] = [{"id": "art:pkg", "candidate_ref": "cand:pkg", "compatible": True}]
    t["evidence_state"]["observations"] = [
        {"id": "obs:req:pkg", "kind": "requirement", "supports_refs": ["c:root"]},
        {"id": "obs:python:pkg", "kind": "metadata", "supports_refs": ["c:python"]},
        {"id": "obs:domain:pkg", "kind": "candidate-domain", "supports_refs": ["domain:pkg"]},
    ]
    t["semantic_constraints"] = [
        {"id": "c:root", "kind": "requirement", "source_ref": "req:pkg"},
        {"id": "c:python", "kind": "requires_python", "source_ref": "cand:pkg", "op": ">=", "version": "4.0"},
    ]
    t["provenance"] = [
        {"id": "prov:root", "premise_refs": ["c:root"], "evidence_refs": ["obs:req:pkg"]},
        {"id": "prov:python", "premise_refs": ["c:python"], "evidence_refs": ["obs:python:pkg"]},
        {"id": "prov:domain", "premise_refs": [], "evidence_refs": ["obs:domain:pkg"]},
    ]
    t["proof_claim"]["premise_refs"] = ["c:root", "c:python"]
    t["claimed_core"] = t["proof_claim"]["premise_refs"][:]
    return t


def rw17_fixture() -> dict[str, Any]:
    t = rw15_fixture()
    t["requirements"] = [{"id": "req:foo", "package": "foo", "op": "<", "version": "2.0"}]
    t["candidates"] = [{"id": "cand:foo", "package": "foo", "version": "1.0", "prerelease": True, "source": "index:A"}]
    t["artifacts"] = [{"id": "art:foo", "candidate_ref": "cand:foo", "compatible": True}]
    t["candidate_domains"] = [{"id": "domain:foo", "identifier": "foo", "candidate_ids": ["cand:foo"], "scope": {"sources": ["index:A"]},
                               "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": ["obs:domain:foo"]}}}]
    t["evidence_state"]["observations"] = [
        {"id": "obs:req:foo", "kind": "requirement", "supports_refs": ["c:foo"]},
        {"id": "obs:domain:foo", "kind": "candidate-domain", "supports_refs": ["domain:foo"]},
    ]
    t["semantic_constraints"] = [{"id": "c:foo", "kind": "requirement", "source_ref": "req:foo"}]
    t["provenance"] = [
        {"id": "prov:foo", "premise_refs": ["c:foo"], "evidence_refs": ["obs:req:foo"]},
        {"id": "prov:domain", "premise_refs": [], "evidence_refs": ["obs:domain:foo"]},
    ]
    t["proof_claim"]["premise_refs"] = ["c:foo"]
    t["claimed_core"] = ["c:foo"]
    return t


def rw18_fixture() -> dict[str, Any]:
    t = rw15_fixture()
    t["requirements"] = [{"id": "req:foo", "package": "foo", "op": "==", "version": "1.0"}]
    t["candidates"] = [
        {"id": "cand:fooA", "package": "foo", "version": "1.0", "source": "index:A"},
        {"id": "cand:fooB", "package": "foo", "version": "1.0", "source": "index:B"},
    ]
    t["artifacts"] = [
        {"id": "art:fooA", "candidate_ref": "cand:fooA", "compatible": True},
        {"id": "art:fooB", "candidate_ref": "cand:fooB", "compatible": True},
    ]
    t["candidate_domains"] = [{"id": "domain:foo", "identifier": "foo", "candidate_ids": ["cand:fooA", "cand:fooB"],
                               "scope": {"sources": ["index:A", "index:B"]},
                               "coverage": {"status": "complete", "attestation": {"kind": "authoritative_finite_domain", "evidence_refs": ["obs:domain:foo"]}}}]
    t["evidence_state"]["observations"] = [
        {"id": "obs:req:foo", "kind": "requirement", "supports_refs": ["c:foo"]},
        {"id": "obs:domain:foo", "kind": "candidate-domain", "supports_refs": ["domain:foo"]},
    ]
    t["semantic_constraints"] = [{"id": "c:foo", "kind": "requirement", "source_ref": "req:foo"}]
    t["provenance"] = [
        {"id": "prov:foo", "premise_refs": ["c:foo"], "evidence_refs": ["obs:req:foo"]},
        {"id": "prov:domain", "premise_refs": [], "evidence_refs": ["obs:domain:foo"]},
    ]
    t["proof_claim"]["premise_refs"] = ["c:foo"]
    t["proof_claim"]["status_claim"] = "SAT"
    t["claimed_core"] = ["c:foo"]
    t["resolution_policy"]["allowed_sources"] = ["index:A", "index:B"]
    return t


def corpus_cases() -> list[dict[str, Any]]:
    insufficient = {
        "RW-03": "VCS/constraint evidence incomplete",
        "RW-04": "causal contradiction not established",
        "RW-05": "Requires-Python evidence omitted",
        "RW-06": "source scope incomplete",
        "RW-07": "inactive-marker attack fixture has incomplete source coverage",
        "RW-08": "source authentication failure prevents exhaustion proof",
        "RW-10": "cutoff/prerelease interaction evidence incomplete",
        "RW-11": "yank policy semantics not fully established",
        "RW-12": "artifact-level yank evidence incomplete",
        "RW-13": "marker-conditioned source split evidence incomplete",
    }
    builders = {
        "RW-01": base_trace, "RW-02": sat_fixture, "RW-09": rw09_fixture,
        "RW-14": rw14_fixture, "RW-15": rw15_fixture, "RW-16": rw16_fixture,
        "RW-17": rw17_fixture, "RW-18": rw18_fixture,
    }
    expected = {
        "RW-01": "VERIFIED_UNSAT", "RW-02": "VERIFIED_SAT",
        "RW-09": "VERIFIED_UNSAT", "RW-14": "VERIFIED_UNSAT",
        "RW-15": "VERIFIED_UNSAT", "RW-16": "VERIFIED_UNSAT",
        "RW-17": "VERIFIED_UNSAT", "RW-18": "VERIFIED_SAT",
    }
    out = []
    for i in range(1, 19):
        cid = f"RW-{i:02d}"
        if cid in builders:
            trace = builders[cid]()
        else:
            trace = base_trace()
            trace["evidence_state"]["overall"] = "incomplete"
            trace["evidence_state"]["reason"] = insufficient[cid]
        trace["case_id"] = cid
        trace["fixture_expectation"] = expected.get(cid, "INSUFFICIENT_EVIDENCE")
        out.append({"case_id": cid, "expected_result": trace["fixture_expectation"], "trace": trace})
    return out


def mutate(t: dict[str, Any], name: str) -> dict[str, Any]:
    x = json.loads(json.dumps(t))
    if name == "coverage_attestation":
        x["candidate_domains"][0]["coverage"].pop("attestation", None)
    elif name == "evaluation_domain":
        x.pop("evaluation_domain", None)
    elif name == "resolution_policy":
        x.pop("resolution_policy", None)
    elif name == "candidate_identity":
        x["candidates"][0]["id"] = "missing-candidate-id"
    elif name == "provenance":
        x["provenance"] = []
    elif name == "dependency_semantics":
        x["dependencies"][0]["requirement"].pop("version", None)
    elif name == "candidate_coverage":
        x["candidate_domains"][0]["coverage"]["status"] = "partial"
    elif name == "dangling_ref":
        x["dependencies"][0]["parent_candidate"] = "missing-parent"
    elif name == "evidence_state":
        x["evidence_state"]["overall"] = "unknown"
    return x
