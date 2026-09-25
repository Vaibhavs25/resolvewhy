from __future__ import annotations
from resolvewhy.model import ReferenceKind, VerificationStatus
from resolvewhy.solving.problem import SemanticProblem
from resolvewhy.verification.result import VerificationResult
from .model import *
def _constraint_description(c):
    parts=[]
    for l in c.literals:
        target=l.package or "<global>"
        if l.candidate_ref is not None: target=f"{target} [{l.candidate_ref}]"
        if l.artifact_ref is not None: target=f"{target} artifact={l.artifact_ref}"
        if l.runtime_context_ref is not None: target=f"{target} @ {l.runtime_context_ref}"
        expr=f" {l.operator} {l.value}" if l.operator is not None else ""
        parts.append(f"{target}{expr}")
    return f"{c.kind.value}: "+ "; ".join(parts)
def _relevant_constraints(problem,result):
    wanted=set(result.premise_ids); by={str(x.id):x for x in problem.semantic_constraints}
    return tuple(by[x] for x in sorted(wanted) if x in by)
def _dependency_paths(problem,constraints):
    reqs={str(x.id):x for x in problem.requirements}; edges={str(x.id):x for x in problem.dependencies}
    out={}
    for c in constraints:
        for ref in c.source_refs:
            rr=dd=parent=None
            if ref.kind is ReferenceKind.REQUIREMENT:
                rr=str(ref.id); r=reqs.get(rr)
                parent=str(r.parent_candidate_ref) if r and r.parent_candidate_ref else None
            elif ref.kind is ReferenceKind.DEPENDENCY:
                dd=str(ref.id); e=edges.get(dd)
                if e: rr=str(e.requirement_ref); parent=str(e.parent_candidate_ref)
            else: continue
            pid=f"path:{c.id}:{dd or rr}"
            out[pid]=ExplanationDependencyPath(pid,str(c.id),rr,dd,parent)
    return tuple(out[x] for x in sorted(out))
def _referenced_ids(problem,constraints,paths):
    cids=set(); aids=set()
    for c in constraints:
        for l in c.literals:
            if l.candidate_ref is not None:cids.add(str(l.candidate_ref))
            if l.artifact_ref is not None:aids.add(str(l.artifact_ref))
    for p in paths:
        if p.parent_candidate_ref:cids.add(p.parent_candidate_ref)
    for a in problem.artifacts:
        if str(a.candidate_ref) in cids:aids.add(str(a.id))
    cb={str(x.id) for x in problem.candidates}; ab={str(x.id) for x in problem.artifacts}
    return tuple(sorted(cids&cb)),tuple(sorted(aids&ab))
def _policy_facts(problem):
    p=problem.resolution_policy
    vals={"id":str(p.id),"prerelease_mode":p.prerelease_mode,"universal_strategy":p.universal_strategy,
          "version_selection":p.version_selection or "unspecified","source_selection":",".join(p.source_selection) or "none",
          "format_policy":",".join(p.format_policy) or "none","hash_policy":",".join(p.hash_policy) or "none"}
    return tuple(ExplanationPolicyFact(k,vals[k]) for k in sorted(vals))
def _evidence_facts(problem,constraints):
    wanted={str(r.id) for c in constraints for r in c.source_refs if r.kind is ReferenceKind.EVIDENCE}
    obs={str(x.id):x for x in problem.evidence_state.observations}
    return tuple(ExplanationEvidenceFact(r,obs[r].state.value,obs[r].kind) for r in sorted(wanted) if r in obs)
def build_explanation(problem:SemanticProblem,verification_result:VerificationResult)->Explanation:
    if not isinstance(problem,SemanticProblem): raise TypeError("build_explanation expects a SemanticProblem")
    if not isinstance(verification_result,VerificationResult): raise TypeError("build_explanation expects a VerificationResult")
    auth={VerificationStatus.VERIFIED_SAT,VerificationStatus.VERIFIED_UNSAT}
    if verification_result.status in auth and not verification_result.independently_verified: raise ValueError("authoritative explanation requires an independently verified result")
    if verification_result.status not in auth and verification_result.independently_verified: raise ValueError("non-decision verification states cannot be marked independently verified")
    kind=ExplanationKind(verification_result.status.value)
    scope=ExplanationScope(verification_result.quantifier,verification_result.evaluation_domain_id,tuple(sorted(verification_result.evaluation_domain)))
    constraints=_relevant_constraints(problem,verification_result); paths=_dependency_paths(problem,constraints)
    cids,aids=_referenced_ids(problem,constraints,paths)
    cb={str(x.id):x for x in problem.candidates}; ab={str(x.id):x for x in problem.artifacts}
    econs=tuple(ExplanationConstraint(str(c.id),c.kind.value,_constraint_description(c),tuple(sorted(str(r.id) for r in c.source_refs))) for c in constraints)
    ecands=tuple(ExplanationCandidate(i,cb[i].package,cb[i].version,cb[i].source_ref) for i in cids)
    earts=tuple(ExplanationArtifact(i,str(ab[i].candidate_ref),ab[i].compatible,ab[i].selection_status.value) for i in aids)
    core=None
    if verification_result.status is VerificationStatus.VERIFIED_UNSAT and verification_result.core_ids and verification_result.core_verified and verification_result.minimality_verified:
        core=ExplanationCore(tuple(sorted(verification_result.core_ids)),True)
    warnings=[]
    if verification_result.status is VerificationStatus.VERIFIED_UNSAT and verification_result.core_ids and core is None:
        warnings.append("A supplied core exists but subset-minimality was not independently verified.")
    if verification_result.status is VerificationStatus.VERIFIED_SAT:
        warnings.append("No satisfying assignment is shown because the current solver result does not expose a complete assignment.")
    issues=tuple(ExplanationIssue(i.code,i.message,str(i.ref.id) if i.ref else None) for i in verification_result.issues)
    return Explanation(kind,scope,econs,paths,ecands,earts,_policy_facts(problem),_evidence_facts(problem,constraints),core,issues,tuple(sorted(warnings)))