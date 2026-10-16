from __future__ import annotations

from .model import Explanation


def render_explanation(explanation:Explanation)->str:
    lines=["resolvewhy explanation",f"Result: {explanation.kind.value}",
           f"Proof scope: {explanation.scope.quantifier.value if explanation.scope.quantifier else 'unknown'}",
           f"Evaluation domain: {explanation.scope.evaluation_domain_id or 'unknown'}",
           f"Runtime contexts: {', '.join(explanation.scope.runtime_context_refs) or 'none'}"]
    if explanation.kind.value=="VERIFIED_UNSAT": lines += ["","Verified semantic premises:"]
    elif explanation.kind.value=="VERIFIED_SAT": lines += ["","Verified semantic information:"]
    elif explanation.kind.value=="INSUFFICIENT_EVIDENCE": lines += ["","Evidence status:","The available evidence is insufficient for an independent SAT/UNSAT conclusion."]
    else: lines += ["","Trace validation:","The trace failed structural or semantic validation; resolver outcome fields are not proof."]
    for constraint in explanation.constraints: lines.append(f"- [{constraint.id}] {constraint.description}")
    if explanation.dependency_paths:
        lines += ["","Dependency relationships:"]
        for path in explanation.dependency_paths:
            chain=tuple(v for v in (path.parent_candidate_ref,path.dependency_ref,path.requirement_ref) if v)
            context=(f" [extra: {', '.join(path.extra_context)}]" if path.extra_context else "")
            lines.append(f"- [{path.id}] "+" -> ".join(chain)+context)
    if explanation.candidates:
        lines += ["","Relevant candidates:"]
        for candidate in explanation.candidates: lines.append(f"- [{candidate.id}] {candidate.package}=={candidate.version or 'unknown-version'} ({candidate.source_ref or 'unknown-source'})")
    if explanation.artifacts:
        lines += ["","Relevant artifacts:"]
        for artifact in explanation.artifacts: lines.append(f"- [{artifact.id}] candidate={artifact.candidate_ref}; compatible={'unknown' if artifact.compatible is None else str(artifact.compatible).lower()}; status={artifact.selection_status}")
    if explanation.policy_facts:
        lines += ["","Policy facts:"]+[f"- {x.key}={x.value}" for x in explanation.policy_facts]
    if explanation.evidence_facts:
        lines += ["","Evidence facts:"]+[f"- [{x.ref}] {x.kind}={x.state}" for x in explanation.evidence_facts]
    if explanation.core:
        lines += ["","Verified subset-minimal core: "+", ".join(explanation.core.constraint_refs)]
    if explanation.issues:
        lines += ["","Verification issues:"]+[f"- {x.code}{' ['+x.ref+']' if x.ref else ''}: {x.message}" for x in explanation.issues]
    if explanation.warnings: lines += ["","Notes:"]+[f"- {x}" for x in explanation.warnings]
    if explanation.kind.value=="VERIFIED_UNSAT": lines += ["","Verified UNSAT."]
    elif explanation.kind.value=="VERIFIED_SAT": lines += ["","Verified SAT."]
    return "\n".join(lines)
