from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Iterable

from resolvewhy.model import (
    ArtifactSelectionStatus,
    Candidate,
    CandidateDomain,
    CandidateKind,
    DependencyEdge,
    MarkerExpression,
    ProofQuantifier,
    Requirement,
    ResolutionPolicy,
    RuntimeContext,
    SemanticConstraint,
    SemanticConstraintKind,
    SemanticLiteral,
    Trace,
)

_VERSION_RE = re.compile(r"^(\d+(?:\.\d+){1,2})(?:(a|b|rc)(\d+))?$")


class BranchOutcome(str, Enum):
    SAT = "SAT"
    UNSAT = "UNSAT"
    UNKNOWN = "UNKNOWN"


class SemanticGap(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


class EvaluationLimit(SemanticGap):
    pass


@dataclass(frozen=True)
class VersionKey:
    release: tuple[int, int, int]
    pre_rank: int
    pre_number: int


@dataclass(frozen=True)
class CandidateState:
    known: bool


def parse_version(value: str) -> VersionKey:
    match = _VERSION_RE.fullmatch(value)
    if match is None:
        raise SemanticGap(
            "unsupported_version_semantics",
            f"version {value!r} is outside the validated production fragment",
        )
    release = tuple(int(part) for part in match.group(1).split("."))
    if len(release) == 2:
        release = release + (0,)
    if len(release) != 3:
        raise SemanticGap("unsupported_version_semantics", f"unsupported version {value!r}")
    tag = match.group(2)
    number = int(match.group(3) or 0)
    return VersionKey(
        release=release,
        pre_rank={"a": 0, "b": 1, "rc": 2, None: 3}[tag],
        pre_number=number,
    )


def version_satisfies(value: str, operator: str, rhs: str) -> bool:
    if operator not in {"==", "!=", "<", "<=", ">", ">="}:
        raise SemanticGap(
            "unsupported_version_semantics",
            f"unsupported version operator {operator!r}",
        )
    left = parse_version(value)
    right = parse_version(rhs)
    if operator == "==":
        return left == right
    if operator == "!=":
        return left != right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    return left >= right


def _marker_value(context: RuntimeContext, variable: str) -> str:
    values = dict(context.marker_values)
    if variable in values:
        return values[variable]
    fallbacks = {
        "python_version": context.python_version,
        "sys_platform": context.os,
        "platform_machine": context.architecture,
        "platform_python_implementation": context.python_implementation,
    }
    if variable in fallbacks:
        return fallbacks[variable]
    raise SemanticGap(
        "unsupported_marker_semantics",
        f"runtime context {context.id} does not provide marker variable {variable!r}",
    )


def eval_marker(marker: MarkerExpression | None, context: RuntimeContext) -> bool:
    if marker is None:
        return True

    def evaluate(expr: MarkerExpression) -> bool:
        if expr.kind == "atom":
            assert expr.atom is not None
            variable = expr.atom.variable
            op = expr.atom.operator
            value = expr.atom.value
            lhs = _marker_value(context, variable)
            if variable in {"python_version", "python_full_version"}:
                if op in {"==", "!=", "<", "<=", ">", ">="}:
                    return version_satisfies(lhs, op, value)
                raise SemanticGap(
                    "unsupported_marker_semantics",
                    f"unsupported marker operator {op!r}",
                )
            if op == "==":
                return lhs == value
            if op == "!=":
                return lhs != value
            raise SemanticGap(
                "unsupported_marker_semantics",
                f"unsupported marker operator {op!r} for {variable!r}",
            )

        if expr.kind == "not":
            return not evaluate(expr.children[0])
        if expr.kind == "and":
            return all(evaluate(child) for child in expr.children)
        if expr.kind == "or":
            return any(evaluate(child) for child in expr.children)
        raise SemanticGap(
            "unsupported_marker_semantics",
            f"unsupported marker expression kind {expr.kind!r}",
        )

    return evaluate(marker)


def _effective_activation(
    constraint: SemanticConstraint,
    literal: SemanticLiteral,
    source_activation: MarkerExpression | None,
    context: RuntimeContext,
) -> bool:
    values = []
    if source_activation is not None:
        values.append(eval_marker(source_activation, context))
    if literal.activation is not None:
        values.append(eval_marker(literal.activation, context))
    return all(values) if values else True


def _policy_is_supported(policy: ResolutionPolicy) -> None:
    unsupported = {
        "source_selection": policy.source_selection,
        "format_policy": policy.format_policy,
        "hash_policy": policy.hash_policy,
        "version_selection": policy.version_selection,
        "cutoff_exclusions": policy.cutoff_exclusions,
        "lockfile_preferences": policy.lockfile_preferences,
    }
    active = [name for name, value in unsupported.items() if value not in (None, ())]
    if active:
        raise SemanticGap(
            "unsupported_policy_semantics",
            "policy fields outside the validated fragment are populated: "
            + ", ".join(active),
        )
    if policy.prerelease_mode not in {"allow", "disallow", "only", "unspecified"}:
        raise SemanticGap(
            "unsupported_policy_semantics",
            f"unsupported prerelease mode {policy.prerelease_mode!r}",
        )


def _candidate_version_state(candidate: Candidate, policy: ResolutionPolicy) -> CandidateState:
    if candidate.version is None:
        return CandidateState(known=False)
    version = parse_version(candidate.version)
    is_prerelease = version.pre_rank < 3
    if policy.prerelease_mode == "disallow" and is_prerelease:
        return CandidateState(known=True)
    if policy.prerelease_mode == "only" and not is_prerelease:
        return CandidateState(known=True)
    if policy.prerelease_mode == "unspecified" and is_prerelease:
        return CandidateState(known=False)
    return CandidateState(known=True)


def _candidate_allowed(candidate: Candidate, policy: ResolutionPolicy) -> tuple[bool, bool]:
    state = _candidate_version_state(candidate, policy)
    if not state.known:
        return False, True
    assert candidate.version is not None
    version = parse_version(candidate.version)
    is_prerelease = version.pre_rank < 3
    if policy.prerelease_mode == "disallow" and is_prerelease:
        return False, False
    if policy.prerelease_mode == "only" and not is_prerelease:
        return False, False
    return True, False


def _semantic_source_ref(
    trace: Trace,
    constraint: SemanticConstraint,
    kind: str,
) -> str:
    direct = [
        ref.id
        for ref in constraint.source_refs
        if ref.kind.value == kind
    ]
    if len(set(direct)) == 1:
        return direct[0]

    evidence_by_id = {
        str(item.id): item
        for item in trace.evidence_state.observations
    }
    supported: set[str] = set()
    for ref in constraint.source_refs:
        if ref.kind.value != "evidence":
            continue
        observation = evidence_by_id.get(str(ref.id))
        if observation is None:
            continue
        for supported_ref in observation.supports_refs:
            if supported_ref.kind.value == kind:
                supported.add(str(supported_ref.id))
    if len(supported) == 1:
        return next(iter(supported))
    if not supported:
        raise SemanticGap(
            "invalid_semantic_binding",
            f"constraint {constraint.id} has no uniquely supported {kind} source",
        )
    raise SemanticGap(
        "invalid_semantic_binding",
        f"constraint {constraint.id} has ambiguous {kind} sources",
    )


def _constraint_source(
    trace: Trace,
    constraint: SemanticConstraint,
) -> Requirement | DependencyEdge | Candidate | object:
    literal_kind = constraint.kind
    if literal_kind is SemanticConstraintKind.REQUIREMENT:
        source_ref = _semantic_source_ref(trace, constraint, "requirement")
        source = next(
            (item for item in trace.requirements if str(item.id) == str(source_ref)),
            None,
        )
        if source is not None:
            return source

        packages = {
            literal.package
            for literal in constraint.literals
            if literal.package is not None
        }
        if len(packages) != 1 or len(constraint.literals) != 1:
            raise SemanticGap(
                "invalid_semantic_binding",
                f"requirement constraint {constraint.id} has no unique requirement source",
            )
        literal = constraint.literals[0]
        matches = [
            item
            for item in trace.requirements
            if (
                item.package == next(iter(packages))
                and item.constraint is not None
                and item.constraint.operator == literal.operator
                and item.constraint.version == literal.value
            )
        ]
        if len(matches) == 1:
            return matches[0]
        raise SemanticGap(
            "invalid_semantic_binding",
            f"requirement constraint {constraint.id} has no unique requirement source",
        )
    if literal_kind is SemanticConstraintKind.DEPENDENCY:
        source_ref = _semantic_source_ref(trace, constraint, "dependency")
        source = next(
            (item for item in trace.dependencies if str(item.id) == str(source_ref)),
            None,
        )
        if source is None:
            raise SemanticGap(
                "invalid_semantic_binding",
                f"dependency constraint {constraint.id} has no dependency source reference",
            )
        return source
    if literal_kind is SemanticConstraintKind.REQUIRES_PYTHON:
        candidate_ref = next(
            (literal.candidate_ref for literal in constraint.literals if literal.candidate_ref is not None),
            None,
        )
        if candidate_ref is None:
            raise SemanticGap(
                "invalid_semantic_binding",
                f"Requires-Python constraint {constraint.id} lacks candidate identity",
            )
        source = next(
            (item for item in trace.candidates if str(item.id) == str(candidate_ref)),
            None,
        )
        if source is None:
            raise SemanticGap(
                "invalid_semantic_binding",
                f"Requires-Python constraint {constraint.id} references missing candidate",
            )
        return source
    if literal_kind is SemanticConstraintKind.ARTIFACT_COMPATIBILITY:
        artifact_ref = next(
            (literal.artifact_ref for literal in constraint.literals if literal.artifact_ref is not None),
            None,
        )
        if artifact_ref is None:
            raise SemanticGap(
                "invalid_semantic_binding",
                f"artifact constraint {constraint.id} lacks artifact identity",
            )
        source = next(
            (item for item in trace.artifacts if str(item.id) == str(artifact_ref)),
            None,
        )
        if source is None:
            raise SemanticGap(
                "invalid_semantic_binding",
                f"artifact constraint {constraint.id} references missing artifact",
            )
        return source
    raise SemanticGap(
        "unsupported_semantics",
        f"semantic constraint kind {literal_kind.value!r} is outside the supported fragment",
    )


def _candidate_domain_map(
    trace: Trace,
    context: RuntimeContext,
) -> dict[str, tuple[Candidate, ...]]:
    candidate_by_id = {str(item.id): item for item in trace.candidates}
    result: dict[str, list[Candidate]] = {}

    domains = [
        domain
        for domain in trace.candidate_domains
        if str(domain.runtime_context_ref) == str(context.id)
    ]
    for domain in domains:
        bucket = result.setdefault(domain.identifier, [])
        for ref in domain.candidate_refs:
            candidate = candidate_by_id.get(str(ref))
            if candidate is None:
                raise SemanticGap(
                    "invalid_candidate_domain",
                    f"candidate domain {domain.id} references missing candidate {ref}",
                )
            if candidate.package != domain.identifier:
                raise SemanticGap(
                    "invalid_candidate_domain",
                    f"candidate {ref} does not belong to domain {domain.identifier!r}",
                )
            if candidate not in bucket:
                bucket.append(candidate)
    return {package: tuple(values) for package, values in result.items()}


def _constraint_packages(
    trace: Trace,
    constraints: Iterable[SemanticConstraint],
) -> set[str]:
    candidates = {str(item.id): item for item in trace.candidates}
    artifacts = {str(item.id): item for item in trace.artifacts}
    requirements = {str(item.id): item for item in trace.requirements}
    dependencies = {str(item.id): item for item in trace.dependencies}

    packages: set[str] = set()
    for constraint in constraints:
        if constraint.kind is SemanticConstraintKind.REQUIREMENT:
            source_ref = _semantic_source_ref(trace, constraint, "requirement")
            requirement = requirements.get(str(source_ref))
            if requirement is None:
                raise SemanticGap("invalid_semantic_binding", f"constraint {constraint.id} has no requirement source")
            packages.add(requirement.package)
        elif constraint.kind is SemanticConstraintKind.DEPENDENCY:
            source_ref = _semantic_source_ref(trace, constraint, "dependency")
            dependency = dependencies.get(str(source_ref))
            if dependency is None:
                raise SemanticGap("invalid_semantic_binding", f"constraint {constraint.id} has no dependency source")
            parent = candidates.get(str(dependency.parent_candidate_ref))
            if parent is None:
                raise SemanticGap("invalid_semantic_binding", f"dependency {dependency.id} references missing parent")
            packages.add(parent.package)
            for literal in constraint.literals:
                if literal.package is None:
                    raise SemanticGap("invalid_semantic_binding", f"dependency {constraint.id} has an unscoped literal")
                packages.add(literal.package)
        elif constraint.kind is SemanticConstraintKind.REQUIRES_PYTHON:
            candidate_ref = next(
                (literal.candidate_ref for literal in constraint.literals if literal.candidate_ref is not None),
                None,
            )
            candidate = candidates.get(str(candidate_ref))
            if candidate is None:
                raise SemanticGap("invalid_semantic_binding", f"Requires-Python {constraint.id} has no candidate")
            packages.add(candidate.package)
        elif constraint.kind is SemanticConstraintKind.ARTIFACT_COMPATIBILITY:
            artifact_ref = next(
                (literal.artifact_ref for literal in constraint.literals if literal.artifact_ref is not None),
                None,
            )
            artifact = artifacts.get(str(artifact_ref))
            if artifact is None:
                raise SemanticGap("invalid_semantic_binding", f"artifact constraint {constraint.id} has no artifact")
            candidate = candidates.get(str(artifact.candidate_ref))
            if candidate is None:
                raise SemanticGap("invalid_semantic_binding", f"artifact {artifact.id} has no candidate")
            packages.add(candidate.package)
        else:
            raise SemanticGap("unsupported_semantics", f"unsupported semantic constraint kind {constraint.kind.value!r}")
    return packages


def _candidate_is_explicitly_selected(
    assignment: dict[str, Candidate | None],
    candidate: Candidate,
) -> bool:
    return assignment.get(candidate.package) is not None and assignment[candidate.package].id == candidate.id


def _literal_version_ok(candidate: Candidate, literal: SemanticLiteral) -> bool:
    if literal.operator is None and literal.value is None:
        return True
    if candidate.version is None:
        raise SemanticGap(
            "incomplete_candidate_metadata",
            f"candidate {candidate.id} has no version",
        )
    if not isinstance(literal.value, str):
        raise SemanticGap(
            "unsupported_semantics",
            f"version comparison for {candidate.id} has non-string value",
        )
    return version_satisfies(candidate.version, literal.operator or "", literal.value)


def _validate_constraint_shape(
    trace: Trace,
    constraint: SemanticConstraint,
    source: object,
) -> None:
    if not constraint.literals:
        raise SemanticGap(
            "invalid_semantic_binding",
            f"constraint {constraint.id} has no literals",
        )
    for literal in constraint.literals:
        if literal.kind is not constraint.kind:
            raise SemanticGap(
                "invalid_semantic_binding",
                f"constraint {constraint.id} contains a literal with mismatched kind",
            )
        if constraint.kind in {SemanticConstraintKind.REQUIREMENT, SemanticConstraintKind.DEPENDENCY}:
            package = getattr(source, "package", None)
            if package is None and isinstance(source, DependencyEdge):
                package = literal.package
            if literal.package is None:
                raise SemanticGap(
                    "invalid_semantic_binding",
                    f"constraint {constraint.id} has a literal without package identity",
                )
            if constraint.kind is SemanticConstraintKind.REQUIREMENT:
                if literal.package != package:
                    raise SemanticGap(
                        "invalid_semantic_binding",
                        f"requirement constraint {constraint.id} targets {literal.package!r}, expected {package!r}",
                    )
            else:
                requirement = next(
                    (
                        item
                        for item in trace.requirements
                        if str(item.id) == str(source.requirement_ref)
                    ),
                    None,
                )
                if requirement is not None and literal.package != requirement.package:
                    raise SemanticGap(
                        "invalid_semantic_binding",
                        f"dependency constraint {constraint.id} targets {literal.package!r}, expected {requirement.package!r}",
                    )
                if literal.candidate_ref is None or str(literal.candidate_ref) != str(source.parent_candidate_ref):
                    raise SemanticGap(
                        "invalid_semantic_binding",
                        f"dependency constraint {constraint.id} is not bound to its parent candidate",
                    )
        elif constraint.kind is SemanticConstraintKind.REQUIRES_PYTHON:
            if literal.candidate_ref is None or literal.runtime_context_ref is None:
                raise SemanticGap(
                    "invalid_semantic_binding",
                    f"Requires-Python literal in {constraint.id} lacks candidate/runtime binding",
                )
            if literal.package not in {"<Python>", None}:
                raise SemanticGap(
                    "invalid_semantic_binding",
                    f"Requires-Python literal in {constraint.id} has unexpected package",
                )
        elif constraint.kind is SemanticConstraintKind.ARTIFACT_COMPATIBILITY:
            if literal.artifact_ref is None:
                raise SemanticGap(
                    "invalid_semantic_binding",
                    f"artifact compatibility literal in {constraint.id} lacks artifact identity",
                )
        elif constraint.kind is SemanticConstraintKind.CANDIDATE_ADMISSIBILITY:
            raise SemanticGap(
                "unsupported_semantics",
                "candidate_admissibility semantic literals do not have a sufficiently specified production predicate",
            )


def _constraint_applies(
    trace: Trace,
    constraint: SemanticConstraint,
    literal: SemanticLiteral,
    context: RuntimeContext,
) -> bool:
    source = _constraint_source(trace, constraint)
    activation = getattr(source, "activation", None)
    return _effective_activation(constraint, literal, activation, context)


def _check_constraint(
    trace: Trace,
    constraint: SemanticConstraint,
    context: RuntimeContext,
    assignment: dict[str, Candidate | None],
) -> tuple[bool, bool]:
    """Return (violated, unknown).

    A true unknown means this partial assignment cannot yet be certified because a
    proof-relevant semantic fact is not fully represented.
    """
    source = _constraint_source(trace, constraint)
    _validate_constraint_shape(trace, constraint, source)

    if constraint.kind is SemanticConstraintKind.REQUIREMENT:
        requirement = source
        assert isinstance(requirement, Requirement)
        selected = assignment.get(requirement.package)
        for literal in constraint.literals:
            if not _constraint_applies(trace, constraint, literal, context):
                continue
            if selected is None:
                return True, False
            if literal.candidate_ref is not None and not _candidate_is_explicitly_selected(assignment, next(
                candidate for candidate in trace.candidates if str(candidate.id) == str(literal.candidate_ref)
            )):
                return True, False
            try:
                if not _literal_version_ok(selected, literal):
                    return True, False
            except SemanticGap as exc:
                if exc.code == "incomplete_candidate_metadata":
                    return False, True
                raise
        return False, False

    if constraint.kind is SemanticConstraintKind.DEPENDENCY:
        dependency = source
        assert isinstance(dependency, DependencyEdge)
        parent = next(
            candidate
            for candidate in trace.candidates
            if str(candidate.id) == str(dependency.parent_candidate_ref)
        )
        selected_parent = assignment.get(parent.package)
        if selected_parent is None:
            return False, False
        if str(selected_parent.id) != str(parent.id):
            return False, False
        for literal in constraint.literals:
            if not _constraint_applies(trace, constraint, literal, context):
                continue
            target = assignment.get(literal.package or "")
            if target is None:
                return True, False
            try:
                if not _literal_version_ok(target, literal):
                    return True, False
            except SemanticGap as exc:
                if exc.code == "incomplete_candidate_metadata":
                    return False, True
                raise
        return False, False

    if constraint.kind is SemanticConstraintKind.REQUIRES_PYTHON:
        candidate_by_id = {str(item.id): item for item in trace.candidates}
        for literal in constraint.literals:
            if str(literal.runtime_context_ref) != str(context.id):
                continue
            candidate = candidate_by_id[str(literal.candidate_ref)]
            selected = assignment.get(candidate.package)
            if selected is None or str(selected.id) != str(candidate.id):
                continue
            try:
                python_version = _marker_value(context, "python_full_version")
                if literal.operator is None or not version_satisfies(
                    python_version,
                    literal.operator,
                    str(literal.value),
                ):
                    return True, False
            except SemanticGap as exc:
                if exc.code in {"unsupported_version_semantics", "unsupported_marker_semantics", "incomplete_candidate_metadata"}:
                    return False, True
                raise
        return False, False

    if constraint.kind is SemanticConstraintKind.ARTIFACT_COMPATIBILITY:
        artifacts = {str(item.id): item for item in trace.artifacts}
        candidates = {str(item.id): item for item in trace.candidates}
        for literal in constraint.literals:
            artifact = artifacts[str(literal.artifact_ref)]
            candidate = candidates[str(artifact.candidate_ref)]
            if not _candidate_is_explicitly_selected(assignment, candidate):
                continue
            if artifact.compatible is None:
                return False, True
            if artifact.compatible is False:
                return True, False
        return False, False

    raise SemanticGap(
        "unsupported_semantics",
        f"unsupported semantic constraint kind {constraint.kind.value!r}",
    )


def _candidate_options(
    trace: Trace,
    context: RuntimeContext,
    domains: dict[str, tuple[Candidate, ...]],
    package: str,
) -> tuple[Candidate | None, ...]:
    values = list(domains.get(package, ()))
    result: list[Candidate | None] = []
    for candidate in values:
        allowed, unknown = _candidate_allowed(candidate, trace.resolution_policy)
        if unknown:
            result.append(candidate)
        elif allowed:
            result.append(candidate)
    result.append(None)
    return tuple(result)


def evaluate_branch(
    trace: Trace,
    constraints: tuple[SemanticConstraint, ...],
    context: RuntimeContext,
    *,
    max_states: int = 100_000,
) -> BranchOutcome:
    _policy_is_supported(trace.resolution_policy)
    domains = _candidate_domain_map(trace, context)
    packages = sorted(_constraint_packages(trace, constraints))
    package_options = {
        package: _candidate_options(trace, context, domains, package)
        for package in packages
    }

    for package in packages:
        if package not in domains:
            raise SemanticGap(
                "incomplete_candidate_coverage",
                f"no candidate domain is declared for package {package!r} in {context.id}",
            )

    states = 0
    unknown_possible = False
    assignment: dict[str, Candidate | None] = {}

    def search(index: int) -> bool:
        nonlocal states, unknown_possible
        states += 1
        if states > max_states:
            raise EvaluationLimit(
                "evaluation_search_limit",
                f"evaluation exceeded {max_states} search states",
            )

        if index == len(packages):
            for constraint in constraints:
                violated, unknown = _check_constraint(trace, constraint, context, assignment)
                if violated:
                    return False
                if unknown:
                    unknown_possible = True
                    return False
            return True

        package = packages[index]
        for candidate in package_options[package]:
            assignment[package] = candidate
            if candidate is not None:
                allowed, unknown = _candidate_allowed(candidate, trace.resolution_policy)
                if unknown:
                    unknown_possible = True
                    assignment.pop(package, None)
                    continue
                if not allowed:
                    assignment.pop(package, None)
                    continue

            rejected = False
            local_unknown = False
            for constraint in constraints:
                involved = _constraint_packages(trace, (constraint,))
                if not involved.issubset(assignment):
                    continue
                violated, unknown = _check_constraint(trace, constraint, context, assignment)
                if violated:
                    rejected = True
                    break
                if unknown:
                    local_unknown = True
                    unknown_possible = True
                    rejected = True
                    break

            if not rejected:
                if search(index + 1):
                    return True
            elif local_unknown:
                unknown_possible = True

            assignment.pop(package, None)
        return False

    if search(0):
        return BranchOutcome.SAT
    if unknown_possible:
        return BranchOutcome.UNKNOWN
    return BranchOutcome.UNSAT
