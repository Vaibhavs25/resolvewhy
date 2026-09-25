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
    for x in explanation.constraints: lines.append(f"- [{x.id}] {x.description}")
    if explanation.dependency_paths:
        lines += ["","Dependency relationships:"]
        for x in explanation.dependency_paths:
            chain=tuple(v for v in (x.parent_candidate_ref,x.dependency_ref,x.requirement_ref) if v)
            lines.append(f"- [{x.id}] "+" -> ".join(chain))
    if explanation.candidates:
        lines += ["","Relevant candidates:"]
        for x in explanation.candidates: lines.append(f"- [{x.id}] {x.package}=={x.version or 'unknown-version'} ({x.source_ref or 'unknown-source'})")
    if explanation.artifacts:
        lines += ["","Relevant artifacts:"]
        for x in explanation.artifacts: lines.append(f"- [{x.id}] candidate={x.candidate_ref}; compatible={'unknown' if x.compatible is None else str(x.compatible).lower()}; status={x.selection_status}")
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