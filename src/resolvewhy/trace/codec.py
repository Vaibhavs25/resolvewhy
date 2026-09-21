from __future__ import annotations

import json
from collections import deque
from typing import Any, Iterable

from resolvewhy.model import (
    Artifact,
    ArtifactSelectionStatus,
    Candidate,
    CandidateCoverage,
    CandidateDomain,
    CandidateDomainScope,
    CandidateKind,
    CoverageAttestation,
    CoverageAttestationKind,
    CoverageStatus,
    DependencyEdge,
    EvaluationDomain,
    EvaluationDomainKind,
    EvidenceObservation,
    EvidenceState,
    EvidenceStateKind,
    IncompatibilityObservation,
    MarkerAtom,
    MarkerExpression,
    ProofClaim,
    ProofQuantifier,
    ProofStatus,
    ProvenanceKind,
    ProvenanceRecord,
    ReferenceKind,
    RejectionObservation,
    Requirement,
    ResolutionPolicy,
    RuntimeContext,
    SemanticConstraint,
    SemanticConstraintKind,
    SemanticLiteral,
    Trace,
    TraceRef,
    TraceScope,
    VersionConstraint,
)

SCHEMA = "resolvewhy-trace/1.0"
MAX_TRACE_BYTES = 2 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_JSON_NODES = 200_000


class TraceSerializationError(ValueError):
    """Base error for production trace serialization/deserialization."""


class TraceDecodeError(TraceSerializationError):
    """Raised when serialized input cannot be safely reconstructed."""


def _enum(value: Any, enum_type: type, path: str) -> str:
    if not isinstance(value, enum_type):
        raise TraceSerializationError(f"{path} is not a valid {enum_type.__name__}")
    return value.value


def _require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TraceDecodeError(f"{path} must be an object")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise TraceDecodeError(f"{path} must be an array")
    return value


def _require_str(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TraceDecodeError(f"{path} must be a non-empty string")
    return value


def _optional_str(value: Any, path: str) -> str | None:
    if value is None:
        return None
    return _require_str(value, path)


def _optional_bool(value: Any, path: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise TraceDecodeError(f"{path} must be a boolean or null")
    return value


def _check_keys(
    value: dict[str, Any],
    *,
    required: Iterable[str],
    optional: Iterable[str] = (),
    path: str,
) -> None:
    required_set = set(required)
    allowed = required_set | set(optional)
    missing = sorted(key for key in required_set if key not in value)
    unknown = sorted(key for key in value if key not in allowed)
    if missing:
        raise TraceDecodeError(f"{path} missing required fields: {', '.join(missing)}")
    if unknown:
        raise TraceDecodeError(f"{path} contains unknown fields: {', '.join(unknown)}")


def _string_array(value: Any, path: str) -> tuple[str, ...]:
    values = _require_list(value, path)
    return tuple(_require_str(item, f"{path}[{index}]") for index, item in enumerate(values))


def _serialize_ref(ref: TraceRef) -> dict[str, Any]:
    return {"kind": _enum(ref.kind, ReferenceKind, "reference.kind"), "id": ref.id}


def _deserialize_ref(value: Any, path: str) -> TraceRef:
    obj = _require_dict(value, path)
    _check_keys(obj, required=("kind", "id"), path=path)
    try:
        kind = ReferenceKind(_require_str(obj["kind"], f"{path}.kind"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.kind has invalid reference kind") from exc
    return TraceRef(kind, _require_str(obj["id"], f"{path}.id"))


def _serialize_marker(marker: MarkerExpression | None) -> dict[str, Any] | None:
    if marker is None:
        return None
    result: dict[str, Any] = {"kind": marker.kind}
    if marker.kind == "atom":
        assert marker.atom is not None
        result["atom"] = {
            "variable": marker.atom.variable,
            "operator": marker.atom.operator,
            "value": marker.atom.value,
        }
    else:
        result["atom"] = None
        result["children"] = [_serialize_marker(child) for child in marker.children]
    return result


def _deserialize_marker(value: Any, path: str) -> MarkerExpression | None:
    if value is None:
        return None
    obj = _require_dict(value, path)
    _check_keys(obj, required=("kind",), optional=("atom", "children"), path=path)
    kind = _require_str(obj["kind"], f"{path}.kind")
    if kind == "atom":
        atom = _require_dict(obj.get("atom"), f"{path}.atom")
        _check_keys(atom, required=("variable", "operator", "value"), path=f"{path}.atom")
        if "children" in obj and obj["children"] not in (None, []):
            raise TraceDecodeError(f"{path}.children must be absent/empty for atom expressions")
        return MarkerExpression(
            kind="atom",
            atom=MarkerAtom(
                _require_str(atom["variable"], f"{path}.atom.variable"),
                _require_str(atom["operator"], f"{path}.atom.operator"),
                _require_str(atom["value"], f"{path}.atom.value"),
            ),
        )
    if kind not in {"and", "or", "not"}:
        raise TraceDecodeError(f"{path}.kind has unsupported marker expression kind: {kind!r}")
    if obj.get("atom") is not None:
        raise TraceDecodeError(f"{path}.atom must be null for {kind} marker expressions")
    children = _require_list(obj.get("children"), f"{path}.children")
    child_values = tuple(
        _deserialize_marker(child, f"{path}.children[{index}]")
        for index, child in enumerate(children)
    )
    try:
        return MarkerExpression(kind=kind, children=child_values)
    except ValueError as exc:
        raise TraceDecodeError(f"{path} is malformed") from exc


def _serialize_requirement(value: Requirement) -> dict[str, Any]:
    return {
        "id": value.id,
        "package": value.package,
        "constraint": None
        if value.constraint is None
        else {"operator": value.constraint.operator, "version": value.constraint.version},
        "raw": value.raw,
        "parent_candidate_ref": value.parent_candidate_ref,
        "activation": _serialize_marker(value.activation),
        "evidence_refs": [_serialize_ref(ref) for ref in value.evidence_refs],
    }


def _deserialize_requirement(value: Any, path: str) -> Requirement:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=("id", "package", "constraint", "raw", "parent_candidate_ref", "activation", "evidence_refs"),
        path=path,
    )
    constraint_value = obj["constraint"]
    if constraint_value is None:
        constraint = None
    else:
        c = _require_dict(constraint_value, f"{path}.constraint")
        _check_keys(c, required=("operator", "version"), path=f"{path}.constraint")
        operator = _require_str(c["operator"], f"{path}.constraint.operator")
        if operator not in {"==", "!=", "<", "<=", ">", ">="}:
            raise TraceDecodeError(f"{path}.constraint.operator is unsupported")
        constraint = VersionConstraint(operator, _require_str(c["version"], f"{path}.constraint.version"))
    try:
        return Requirement(
            id=_require_str(obj["id"], f"{path}.id"),
            package=_require_str(obj["package"], f"{path}.package"),
            constraint=constraint,
            raw=_optional_str(obj["raw"], f"{path}.raw"),
            parent_candidate_ref=_optional_str(obj["parent_candidate_ref"], f"{path}.parent_candidate_ref"),
            activation=_deserialize_marker(obj["activation"], f"{path}.activation"),
            evidence_refs=tuple(
                _deserialize_ref(item, f"{path}.evidence_refs[{index}]")
                for index, item in enumerate(_require_list(obj["evidence_refs"], f"{path}.evidence_refs"))
            ),
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path} is malformed") from exc


def _serialize_candidate(value: Candidate) -> dict[str, Any]:
    return {
        "id": value.id,
        "package": value.package,
        "version": value.version,
        "kind": _enum(value.kind, CandidateKind, "candidate.kind"),
        "source_ref": value.source_ref,
        "origin": value.origin,
        "metadata_ref": None if value.metadata_ref is None else _serialize_ref(value.metadata_ref),
    }


def _deserialize_candidate(value: Any, path: str) -> Candidate:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=("id", "package", "version", "kind", "source_ref", "origin", "metadata_ref"),
        path=path,
    )
    try:
        kind = CandidateKind(_require_str(obj["kind"], f"{path}.kind"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.kind has invalid candidate kind") from exc
    return Candidate(
        id=_require_str(obj["id"], f"{path}.id"),
        package=_require_str(obj["package"], f"{path}.package"),
        version=_optional_str(obj["version"], f"{path}.version"),
        kind=kind,
        source_ref=_optional_str(obj["source_ref"], f"{path}.source_ref"),
        origin=_optional_str(obj["origin"], f"{path}.origin"),
        metadata_ref=None
        if obj["metadata_ref"] is None
        else _deserialize_ref(obj["metadata_ref"], f"{path}.metadata_ref"),
    )


def _serialize_artifact(value: Artifact) -> dict[str, Any]:
    return {
        "id": value.id,
        "candidate_ref": value.candidate_ref,
        "origin": value.origin,
        "tags": list(value.tags),
        "hash": value.hash,
        "metadata_ref": None if value.metadata_ref is None else _serialize_ref(value.metadata_ref),
        "compatible": value.compatible,
        "selection_status": _enum(
            value.selection_status, ArtifactSelectionStatus, "artifact.selection_status"
        ),
        "evidence_refs": [_serialize_ref(ref) for ref in value.evidence_refs],
    }


def _deserialize_artifact(value: Any, path: str) -> Artifact:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=(
            "id",
            "candidate_ref",
            "origin",
            "tags",
            "hash",
            "metadata_ref",
            "compatible",
            "selection_status",
            "evidence_refs",
        ),
        path=path,
    )
    try:
        status = ArtifactSelectionStatus(
            _require_str(obj["selection_status"], f"{path}.selection_status")
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.selection_status has invalid value") from exc
    return Artifact(
        id=_require_str(obj["id"], f"{path}.id"),
        candidate_ref=_require_str(obj["candidate_ref"], f"{path}.candidate_ref"),
        origin=_optional_str(obj["origin"], f"{path}.origin"),
        tags=_string_array(obj["tags"], f"{path}.tags"),
        hash=_optional_str(obj["hash"], f"{path}.hash"),
        metadata_ref=None
        if obj["metadata_ref"] is None
        else _deserialize_ref(obj["metadata_ref"], f"{path}.metadata_ref"),
        compatible=_optional_bool(obj["compatible"], f"{path}.compatible"),
        selection_status=status,
        evidence_refs=tuple(
            _deserialize_ref(item, f"{path}.evidence_refs[{index}]")
            for index, item in enumerate(_require_list(obj["evidence_refs"], f"{path}.evidence_refs"))
        ),
    )


def _serialize_runtime_context(value: RuntimeContext) -> dict[str, Any]:
    return {
        "id": value.id,
        "python_implementation": value.python_implementation,
        "python_version": value.python_version,
        "os": value.os,
        "architecture": value.architecture,
        "marker_values": [[key, item] for key, item in value.marker_values],
    }


def _deserialize_runtime_context(value: Any, path: str) -> RuntimeContext:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=(
            "id",
            "python_implementation",
            "python_version",
            "os",
            "architecture",
            "marker_values",
        ),
        path=path,
    )
    raw_pairs = _require_list(obj["marker_values"], f"{path}.marker_values")
    pairs = []
    for index, item in enumerate(raw_pairs):
        pair = _require_list(item, f"{path}.marker_values[{index}]")
        if len(pair) != 2:
            raise TraceDecodeError(f"{path}.marker_values[{index}] must contain exactly two values")
        pairs.append(
            (
                _require_str(pair[0], f"{path}.marker_values[{index}][0]"),
                _require_str(pair[1], f"{path}.marker_values[{index}][1]"),
            )
        )
    try:
        return RuntimeContext(
            id=_require_str(obj["id"], f"{path}.id"),
            python_implementation=_require_str(
                obj["python_implementation"], f"{path}.python_implementation"
            ),
            python_version=_require_str(obj["python_version"], f"{path}.python_version"),
            os=_require_str(obj["os"], f"{path}.os"),
            architecture=_require_str(obj["architecture"], f"{path}.architecture"),
            marker_values=tuple(pairs),
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path} is malformed") from exc


def _serialize_evaluation_domain(value: EvaluationDomain) -> dict[str, Any]:
    return {
        "id": value.id,
        "kind": _enum(value.kind, EvaluationDomainKind, "evaluation_domain.kind"),
        "environment_refs": list(value.environment_refs),
        "evidence_refs": [_serialize_ref(ref) for ref in value.evidence_refs],
    }


def _deserialize_evaluation_domain(value: Any, path: str) -> EvaluationDomain:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=("id", "kind", "environment_refs", "evidence_refs"),
        path=path,
    )
    try:
        kind = EvaluationDomainKind(_require_str(obj["kind"], f"{path}.kind"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.kind has invalid value") from exc
    try:
        return EvaluationDomain(
            id=_require_str(obj["id"], f"{path}.id"),
            kind=kind,
            environment_refs=tuple(
                _require_str(item, f"{path}.environment_refs[{index}]")
                for index, item in enumerate(
                    _require_list(obj["environment_refs"], f"{path}.environment_refs")
                )
            ),
            evidence_refs=tuple(
                _deserialize_ref(item, f"{path}.evidence_refs[{index}]")
                for index, item in enumerate(_require_list(obj["evidence_refs"], f"{path}.evidence_refs"))
            ),
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path} is malformed") from exc


def _serialize_policy(value: ResolutionPolicy) -> dict[str, Any]:
    return {
        "id": value.id,
        "prerelease_mode": value.prerelease_mode,
        "source_selection": list(value.source_selection),
        "format_policy": list(value.format_policy),
        "hash_policy": list(value.hash_policy),
        "version_selection": value.version_selection,
        "universal_strategy": value.universal_strategy,
        "cutoff_exclusions": list(value.cutoff_exclusions),
        "lockfile_preferences": list(value.lockfile_preferences),
    }


def _deserialize_policy(value: Any, path: str) -> ResolutionPolicy:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=(
            "id",
            "prerelease_mode",
            "source_selection",
            "format_policy",
            "hash_policy",
            "version_selection",
            "universal_strategy",
            "cutoff_exclusions",
            "lockfile_preferences",
        ),
        path=path,
    )
    prerelease_mode = _require_str(obj["prerelease_mode"], f"{path}.prerelease_mode")
    universal_strategy = _require_str(obj["universal_strategy"], f"{path}.universal_strategy")
    try:
        return ResolutionPolicy(
            id=_require_str(obj["id"], f"{path}.id"),
            prerelease_mode=prerelease_mode,
            source_selection=_string_array(obj["source_selection"], f"{path}.source_selection"),
            format_policy=_string_array(obj["format_policy"], f"{path}.format_policy"),
            hash_policy=_string_array(obj["hash_policy"], f"{path}.hash_policy"),
            version_selection=_optional_str(obj["version_selection"], f"{path}.version_selection"),
            universal_strategy=universal_strategy,
            cutoff_exclusions=_string_array(
                obj["cutoff_exclusions"], f"{path}.cutoff_exclusions"
            ),
            lockfile_preferences=_string_array(
                obj["lockfile_preferences"], f"{path}.lockfile_preferences"
            ),
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path} is malformed") from exc


def _serialize_candidate_domain_scope(value: CandidateDomainScope) -> dict[str, Any]:
    return {
        "sources": list(value.sources),
        "queries": list(value.queries),
        "artifact_policy_ref": value.artifact_policy_ref,
    }


def _deserialize_candidate_domain_scope(value: Any, path: str) -> CandidateDomainScope:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=("sources", "queries", "artifact_policy_ref"),
        path=path,
    )
    return CandidateDomainScope(
        sources=_string_array(obj["sources"], f"{path}.sources"),
        queries=_string_array(obj["queries"], f"{path}.queries"),
        artifact_policy_ref=_optional_str(
            obj["artifact_policy_ref"], f"{path}.artifact_policy_ref"
        ),
    )


def _serialize_coverage_attestation(value: CoverageAttestation | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "kind": _enum(value.kind, CoverageAttestationKind, "coverage.attestation.kind"),
        "evidence_refs": [_serialize_ref(ref) for ref in value.evidence_refs],
    }


def _deserialize_coverage_attestation(value: Any, path: str) -> CoverageAttestation | None:
    if value is None:
        return None
    obj = _require_dict(value, path)
    _check_keys(obj, required=("kind", "evidence_refs"), path=path)
    try:
        kind = CoverageAttestationKind(_require_str(obj["kind"], f"{path}.kind"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.kind has invalid value") from exc
    return CoverageAttestation(
        kind=kind,
        evidence_refs=tuple(
            _deserialize_ref(item, f"{path}.evidence_refs[{index}]")
            for index, item in enumerate(_require_list(obj["evidence_refs"], f"{path}.evidence_refs"))
        ),
    )


def _serialize_coverage(value: CandidateCoverage) -> dict[str, Any]:
    return {
        "status": _enum(value.status, CoverageStatus, "coverage.status"),
        "attestation": _serialize_coverage_attestation(value.attestation),
        "evidence_refs": [_serialize_ref(ref) for ref in value.evidence_refs],
    }


def _deserialize_coverage(value: Any, path: str) -> CandidateCoverage:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=("status", "attestation", "evidence_refs"),
        path=path,
    )
    try:
        status = CoverageStatus(_require_str(obj["status"], f"{path}.status"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.status has invalid value") from exc
    return CandidateCoverage(
        status=status,
        attestation=_deserialize_coverage_attestation(obj["attestation"], f"{path}.attestation"),
        evidence_refs=tuple(
            _deserialize_ref(item, f"{path}.evidence_refs[{index}]")
            for index, item in enumerate(_require_list(obj["evidence_refs"], f"{path}.evidence_refs"))
        ),
    )


def _serialize_candidate_domain(value: CandidateDomain) -> dict[str, Any]:
    return {
        "id": value.id,
        "identifier": value.identifier,
        "requirement_refs": list(value.requirement_refs),
        "candidate_refs": list(value.candidate_refs),
        "scope": _serialize_candidate_domain_scope(value.scope),
        "runtime_context_ref": value.runtime_context_ref,
        "resolution_policy_ref": value.resolution_policy_ref,
        "coverage": _serialize_coverage(value.coverage),
    }


def _deserialize_candidate_domain(value: Any, path: str) -> CandidateDomain:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=(
            "id",
            "identifier",
            "requirement_refs",
            "candidate_refs",
            "scope",
            "runtime_context_ref",
            "resolution_policy_ref",
            "coverage",
        ),
        path=path,
    )
    try:
        return CandidateDomain(
            id=_require_str(obj["id"], f"{path}.id"),
            identifier=_require_str(obj["identifier"], f"{path}.identifier"),
            requirement_refs=tuple(
                _require_str(item, f"{path}.requirement_refs[{index}]")
                for index, item in enumerate(
                    _require_list(obj["requirement_refs"], f"{path}.requirement_refs")
                )
            ),
            candidate_refs=tuple(
                _require_str(item, f"{path}.candidate_refs[{index}]")
                for index, item in enumerate(
                    _require_list(obj["candidate_refs"], f"{path}.candidate_refs")
                )
            ),
            scope=_deserialize_candidate_domain_scope(obj["scope"], f"{path}.scope"),
            runtime_context_ref=_require_str(
                obj["runtime_context_ref"], f"{path}.runtime_context_ref"
            ),
            resolution_policy_ref=_require_str(
                obj["resolution_policy_ref"], f"{path}.resolution_policy_ref"
            ),
            coverage=_deserialize_coverage(obj["coverage"], f"{path}.coverage"),
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path} is malformed") from exc


def _serialize_dependency(value: DependencyEdge) -> dict[str, Any]:
    return {
        "id": value.id,
        "parent_candidate_ref": value.parent_candidate_ref,
        "requirement_ref": value.requirement_ref,
        "activation": _serialize_marker(value.activation),
        "raw_dependency": value.raw_dependency,
        "evidence_refs": [_serialize_ref(ref) for ref in value.evidence_refs],
        "source_namespace": value.source_namespace,
    }


def _deserialize_dependency(value: Any, path: str) -> DependencyEdge:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=(
            "id",
            "parent_candidate_ref",
            "requirement_ref",
            "activation",
            "raw_dependency",
            "evidence_refs",
            "source_namespace",
        ),
        path=path,
    )
    try:
        return DependencyEdge(
            id=_require_str(obj["id"], f"{path}.id"),
            parent_candidate_ref=_require_str(
                obj["parent_candidate_ref"], f"{path}.parent_candidate_ref"
            ),
            requirement_ref=_require_str(obj["requirement_ref"], f"{path}.requirement_ref"),
            activation=_deserialize_marker(obj["activation"], f"{path}.activation"),
            raw_dependency=_optional_str(obj["raw_dependency"], f"{path}.raw_dependency"),
            evidence_refs=tuple(
                _deserialize_ref(item, f"{path}.evidence_refs[{index}]")
                for index, item in enumerate(_require_list(obj["evidence_refs"], f"{path}.evidence_refs"))
            ),
            source_namespace=_optional_str(
                obj["source_namespace"], f"{path}.source_namespace"
            ),
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path} is malformed") from exc


def _serialize_literal(value: SemanticLiteral) -> dict[str, Any]:
    return {
        "kind": _enum(value.kind, SemanticConstraintKind, "literal.kind"),
        "package": value.package,
        "candidate_ref": value.candidate_ref,
        "artifact_ref": value.artifact_ref,
        "runtime_context_ref": value.runtime_context_ref,
        "operator": value.operator,
        "value": value.value,
        "activation": _serialize_marker(value.activation),
    }


def _deserialize_literal(value: Any, path: str) -> SemanticLiteral:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=(
            "kind",
            "package",
            "candidate_ref",
            "artifact_ref",
            "runtime_context_ref",
            "operator",
            "value",
            "activation",
        ),
        path=path,
    )
    try:
        kind = SemanticConstraintKind(_require_str(obj["kind"], f"{path}.kind"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.kind has invalid value") from exc

    operator = _optional_str(obj["operator"], f"{path}.operator")
    literal_value = obj["value"]
    if operator is None and literal_value is not None:
        raise TraceDecodeError(f"{path}.value requires {path}.operator")
    if operator is not None and literal_value is None:
        raise TraceDecodeError(f"{path}.operator requires {path}.value")
    if literal_value is not None and not isinstance(literal_value, (str, bool)):
        raise TraceDecodeError(f"{path}.value must be a string, boolean, or null")

    return SemanticLiteral(
        kind=kind,
        package=_optional_str(obj["package"], f"{path}.package"),
        candidate_ref=_optional_str(obj["candidate_ref"], f"{path}.candidate_ref"),
        artifact_ref=_optional_str(obj["artifact_ref"], f"{path}.artifact_ref"),
        runtime_context_ref=_optional_str(
            obj["runtime_context_ref"], f"{path}.runtime_context_ref"
        ),
        operator=operator,
        value=literal_value,
        activation=_deserialize_marker(obj["activation"], f"{path}.activation"),
    )


def _serialize_constraint(value: SemanticConstraint) -> dict[str, Any]:
    return {
        "id": value.id,
        "kind": _enum(value.kind, SemanticConstraintKind, "constraint.kind"),
        "literals": [_serialize_literal(literal) for literal in value.literals],
        "source_refs": [_serialize_ref(ref) for ref in value.source_refs],
    }


def _deserialize_constraint(value: Any, path: str) -> SemanticConstraint:
    obj = _require_dict(value, path)
    _check_keys(obj, required=("id", "kind", "literals", "source_refs"), path=path)
    try:
        kind = SemanticConstraintKind(_require_str(obj["kind"], f"{path}.kind"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.kind has invalid value") from exc
    try:
        return SemanticConstraint(
            id=_require_str(obj["id"], f"{path}.id"),
            kind=kind,
            literals=tuple(
                _deserialize_literal(item, f"{path}.literals[{index}]")
                for index, item in enumerate(_require_list(obj["literals"], f"{path}.literals"))
            ),
            source_refs=tuple(
                _deserialize_ref(item, f"{path}.source_refs[{index}]")
                for index, item in enumerate(_require_list(obj["source_refs"], f"{path}.source_refs"))
            ),
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path} is malformed") from exc


def _serialize_evidence_observation(value: EvidenceObservation) -> dict[str, Any]:
    return {
        "id": value.id,
        "kind": value.kind,
        "state": _enum(value.state, EvidenceStateKind, "evidence.observation.state"),
        "supports_refs": [_serialize_ref(ref) for ref in value.supports_refs],
        "source_namespace": value.source_namespace,
    }


def _deserialize_evidence_observation(value: Any, path: str) -> EvidenceObservation:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=("id", "kind", "state", "supports_refs", "source_namespace"),
        path=path,
    )
    try:
        state = EvidenceStateKind(_require_str(obj["state"], f"{path}.state"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.state has invalid value") from exc
    return EvidenceObservation(
        id=_require_str(obj["id"], f"{path}.id"),
        kind=_require_str(obj["kind"], f"{path}.kind"),
        state=state,
        supports_refs=tuple(
            _deserialize_ref(item, f"{path}.supports_refs[{index}]")
            for index, item in enumerate(_require_list(obj["supports_refs"], f"{path}.supports_refs"))
        ),
        source_namespace=_optional_str(
            obj["source_namespace"], f"{path}.source_namespace"
        ),
    )


def _serialize_evidence_state(value: EvidenceState) -> dict[str, Any]:
    return {
        "overall": _enum(value.overall, EvidenceStateKind, "evidence_state.overall"),
        "observations": [
            _serialize_evidence_observation(item) for item in value.observations
        ],
    }


def _deserialize_evidence_state(value: Any, path: str) -> EvidenceState:
    obj = _require_dict(value, path)
    _check_keys(obj, required=("overall", "observations"), path=path)
    try:
        overall = EvidenceStateKind(_require_str(obj["overall"], f"{path}.overall"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.overall has invalid value") from exc
    return EvidenceState(
        overall=overall,
        observations=tuple(
            _deserialize_evidence_observation(item, f"{path}.observations[{index}]")
            for index, item in enumerate(_require_list(obj["observations"], f"{path}.observations"))
        ),
    )


def _serialize_provenance(value: ProvenanceRecord) -> dict[str, Any]:
    return {
        "id": value.id,
        "subject_ref": _serialize_ref(value.subject_ref),
        "kind": _enum(value.kind, ProvenanceKind, "provenance.kind"),
        "premise_refs": [_serialize_ref(ref) for ref in value.premise_refs],
        "derivation_rule": value.derivation_rule,
        "source_namespace": value.source_namespace,
    }


def _deserialize_provenance(value: Any, path: str) -> ProvenanceRecord:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=(
            "id",
            "subject_ref",
            "kind",
            "premise_refs",
            "derivation_rule",
            "source_namespace",
        ),
        path=path,
    )
    try:
        kind = ProvenanceKind(_require_str(obj["kind"], f"{path}.kind"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.kind has invalid value") from exc
    try:
        return ProvenanceRecord(
            id=_require_str(obj["id"], f"{path}.id"),
            subject_ref=_deserialize_ref(obj["subject_ref"], f"{path}.subject_ref"),
            kind=kind,
            premise_refs=tuple(
                _deserialize_ref(item, f"{path}.premise_refs[{index}]")
                for index, item in enumerate(_require_list(obj["premise_refs"], f"{path}.premise_refs"))
            ),
            derivation_rule=_optional_str(obj["derivation_rule"], f"{path}.derivation_rule"),
            source_namespace=_optional_str(
                obj["source_namespace"], f"{path}.source_namespace"
            ),
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path} is malformed") from exc


def _serialize_rejection(value: RejectionObservation) -> dict[str, Any]:
    return {
        "id": value.id,
        "target_ref": _serialize_ref(value.target_ref),
        "reason_kind": value.reason_kind,
        "source_layer": value.source_layer,
        "evidence_status": _enum(
            value.evidence_status, EvidenceStateKind, "rejection.evidence_status"
        ),
        "premise_refs": [_serialize_ref(ref) for ref in value.premise_refs],
    }


def _deserialize_rejection(value: Any, path: str) -> RejectionObservation:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=("id", "target_ref", "reason_kind", "source_layer", "evidence_status", "premise_refs"),
        path=path,
    )
    try:
        evidence_status = EvidenceStateKind(
            _require_str(obj["evidence_status"], f"{path}.evidence_status")
        )
    except ValueError as exc:
        raise TraceDecodeError(f"{path}.evidence_status has invalid value") from exc
    return RejectionObservation(
        id=_require_str(obj["id"], f"{path}.id"),
        target_ref=_deserialize_ref(obj["target_ref"], f"{path}.target_ref"),
        reason_kind=_require_str(obj["reason_kind"], f"{path}.reason_kind"),
        source_layer=_require_str(obj["source_layer"], f"{path}.source_layer"),
        evidence_status=evidence_status,
        premise_refs=tuple(
            _deserialize_ref(item, f"{path}.premise_refs[{index}]")
            for index, item in enumerate(_require_list(obj["premise_refs"], f"{path}.premise_refs"))
        ),
    )


def _serialize_incompatibility(value: IncompatibilityObservation) -> dict[str, Any]:
    return {
        "id": value.id,
        "semantics": value.semantics,
        "resolver_namespace": value.resolver_namespace,
        "term_refs": [_serialize_ref(ref) for ref in value.term_refs],
        "derivation_refs": list(value.derivation_refs),
    }


def _deserialize_incompatibility(value: Any, path: str) -> IncompatibilityObservation:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=("id", "semantics", "resolver_namespace", "term_refs", "derivation_refs"),
        path=path,
    )
    return IncompatibilityObservation(
        id=_require_str(obj["id"], f"{path}.id"),
        semantics=_require_str(obj["semantics"], f"{path}.semantics"),
        resolver_namespace=_require_str(
            obj["resolver_namespace"], f"{path}.resolver_namespace"
        ),
        term_refs=tuple(
            _deserialize_ref(item, f"{path}.term_refs[{index}]")
            for index, item in enumerate(_require_list(obj["term_refs"], f"{path}.term_refs"))
        ),
        derivation_refs=tuple(
            _require_str(item, f"{path}.derivation_refs[{index}]")
            for index, item in enumerate(
                _require_list(obj["derivation_refs"], f"{path}.derivation_refs")
            )
        ),
    )


def _serialize_proof_claim(value: ProofClaim) -> dict[str, Any]:
    return {
        "id": value.id,
        "kind": value.kind,
        "quantifier": _enum(value.quantifier, ProofQuantifier, "proof_claim.quantifier"),
        "evaluation_domain_ref": value.evaluation_domain_ref,
        "status_claim": _enum(value.status_claim, ProofStatus, "proof_claim.status_claim"),
        "premise_refs": list(value.premise_refs),
        "branch_ref": value.branch_ref,
        "claimed_core_refs": list(value.claimed_core_refs),
        "subset_minimal_claim": value.subset_minimal_claim,
    }


def _deserialize_proof_claim(value: Any, path: str) -> ProofClaim:
    obj = _require_dict(value, path)
    _check_keys(
        obj,
        required=(
            "id",
            "kind",
            "quantifier",
            "evaluation_domain_ref",
            "status_claim",
            "premise_refs",
            "branch_ref",
            "claimed_core_refs",
            "subset_minimal_claim",
        ),
        path=path,
    )
    kind = _require_str(obj["kind"], f"{path}.kind")
    if kind != "satisfiability":
        raise TraceDecodeError(f"{path}.kind must be 'satisfiability'")
    try:
        quantifier = ProofQuantifier(_require_str(obj["quantifier"], f"{path}.quantifier"))
        status_claim = ProofStatus(_require_str(obj["status_claim"], f"{path}.status_claim"))
    except ValueError as exc:
        raise TraceDecodeError(f"{path} contains an invalid proof enum") from exc
    subset_minimal_claim = obj["subset_minimal_claim"]
    if not isinstance(subset_minimal_claim, bool):
        raise TraceDecodeError(f"{path}.subset_minimal_claim must be a boolean")
    return ProofClaim(
        id=_require_str(obj["id"], f"{path}.id"),
        kind=kind,
        quantifier=quantifier,
        evaluation_domain_ref=_require_str(
            obj["evaluation_domain_ref"], f"{path}.evaluation_domain_ref"
        ),
        status_claim=status_claim,
        premise_refs=tuple(
            _require_str(item, f"{path}.premise_refs[{index}]")
            for index, item in enumerate(_require_list(obj["premise_refs"], f"{path}.premise_refs"))
        ),
        branch_ref=_optional_str(obj["branch_ref"], f"{path}.branch_ref"),
        claimed_core_refs=tuple(
            _require_str(item, f"{path}.claimed_core_refs[{index}]")
            for index, item in enumerate(
                _require_list(obj["claimed_core_refs"], f"{path}.claimed_core_refs")
            )
        ),
        subset_minimal_claim=subset_minimal_claim,
    )


def _serialize_trace(trace: Trace) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "resolver": {
            "name": trace.resolver_name,
            "version": trace.resolver_version,
            "commit": trace.resolver_commit,
        },
        "trace_scope": _enum(trace.trace_scope, TraceScope, "trace_scope"),
        "runtime_contexts": [_serialize_runtime_context(item) for item in trace.runtime_contexts],
        "evaluation_domain": _serialize_evaluation_domain(trace.evaluation_domain),
        "resolution_policy": _serialize_policy(trace.resolution_policy),
        "candidate_domains": [_serialize_candidate_domain(item) for item in trace.candidate_domains],
        "requirements": [_serialize_requirement(item) for item in trace.requirements],
        "candidates": [_serialize_candidate(item) for item in trace.candidates],
        "artifacts": [_serialize_artifact(item) for item in trace.artifacts],
        "dependencies": [_serialize_dependency(item) for item in trace.dependencies],
        "rejections": [_serialize_rejection(item) for item in trace.rejections],
        "incompatibilities": [
            _serialize_incompatibility(item) for item in trace.incompatibilities
        ],
        "semantic_constraints": [
            _serialize_constraint(item) for item in trace.semantic_constraints
        ],
        "evidence_state": _serialize_evidence_state(trace.evidence_state),
        "provenance": [_serialize_provenance(item) for item in trace.provenance],
        "proof_claim": _serialize_proof_claim(trace.proof_claim),
    }


def _deserialize_trace(value: Any) -> Trace:
    obj = _require_dict(value, "$")
    _check_keys(
        obj,
        required=(
            "schema",
            "resolver",
            "trace_scope",
            "runtime_contexts",
            "evaluation_domain",
            "resolution_policy",
            "candidate_domains",
            "requirements",
            "candidates",
            "artifacts",
            "dependencies",
            "rejections",
            "incompatibilities",
            "semantic_constraints",
            "evidence_state",
            "provenance",
            "proof_claim",
        ),
        path="$",
    )
    schema = _require_str(obj["schema"], "$.schema")
    if schema != SCHEMA:
        raise TraceDecodeError(
            f"unsupported schema {schema!r}; this loader supports {SCHEMA!r} only"
        )

    resolver = _require_dict(obj["resolver"], "$.resolver")
    _check_keys(
        resolver,
        required=("name", "version", "commit"),
        path="$.resolver",
    )
    try:
        trace_scope = TraceScope(_require_str(obj["trace_scope"], "$.trace_scope"))
    except ValueError as exc:
        raise TraceDecodeError("$.trace_scope has invalid value") from exc

    try:
        return Trace(
            schema=schema,
            resolver_name=_require_str(resolver["name"], "$.resolver.name"),
            resolver_version=_optional_str(resolver["version"], "$.resolver.version"),
            resolver_commit=_optional_str(resolver["commit"], "$.resolver.commit"),
            trace_scope=trace_scope,
            runtime_contexts=tuple(
                _deserialize_runtime_context(item, f"$.runtime_contexts[{index}]")
                for index, item in enumerate(_require_list(obj["runtime_contexts"], "$.runtime_contexts"))
            ),
            evaluation_domain=_deserialize_evaluation_domain(
                obj["evaluation_domain"], "$.evaluation_domain"
            ),
            resolution_policy=_deserialize_policy(
                obj["resolution_policy"], "$.resolution_policy"
            ),
            candidate_domains=tuple(
                _deserialize_candidate_domain(item, f"$.candidate_domains[{index}]")
                for index, item in enumerate(
                    _require_list(obj["candidate_domains"], "$.candidate_domains")
                )
            ),
            requirements=tuple(
                _deserialize_requirement(item, f"$.requirements[{index}]")
                for index, item in enumerate(_require_list(obj["requirements"], "$.requirements"))
            ),
            candidates=tuple(
                _deserialize_candidate(item, f"$.candidates[{index}]")
                for index, item in enumerate(_require_list(obj["candidates"], "$.candidates"))
            ),
            artifacts=tuple(
                _deserialize_artifact(item, f"$.artifacts[{index}]")
                for index, item in enumerate(_require_list(obj["artifacts"], "$.artifacts"))
            ),
            dependencies=tuple(
                _deserialize_dependency(item, f"$.dependencies[{index}]")
                for index, item in enumerate(_require_list(obj["dependencies"], "$.dependencies"))
            ),
            rejections=tuple(
                _deserialize_rejection(item, f"$.rejections[{index}]")
                for index, item in enumerate(_require_list(obj["rejections"], "$.rejections"))
            ),
            incompatibilities=tuple(
                _deserialize_incompatibility(item, f"$.incompatibilities[{index}]")
                for index, item in enumerate(
                    _require_list(obj["incompatibilities"], "$.incompatibilities")
                )
            ),
            semantic_constraints=tuple(
                _deserialize_constraint(item, f"$.semantic_constraints[{index}]")
                for index, item in enumerate(
                    _require_list(obj["semantic_constraints"], "$.semantic_constraints")
                )
            ),
            evidence_state=_deserialize_evidence_state(
                obj["evidence_state"], "$.evidence_state"
            ),
            provenance=tuple(
                _deserialize_provenance(item, f"$.provenance[{index}]")
                for index, item in enumerate(_require_list(obj["provenance"], "$.provenance"))
            ),
            proof_claim=_deserialize_proof_claim(obj["proof_claim"], "$.proof_claim"),
        )
    except (TypeError, ValueError) as exc:
        raise TraceDecodeError("trace contains malformed semantic data") from exc


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TraceDecodeError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise TraceDecodeError(f"non-standard JSON constant is not allowed: {value}")


def _check_shape_limits(root: Any) -> None:
    queue = deque([(root, 1)])
    nodes = 0
    while queue:
        value, depth = queue.popleft()
        nodes += 1
        if nodes > MAX_JSON_NODES:
            raise TraceDecodeError("trace exceeds maximum JSON node count")
        if depth > MAX_JSON_DEPTH:
            raise TraceDecodeError("trace exceeds maximum JSON nesting depth")
        if isinstance(value, dict):
            for key, child in value.items():
                if not isinstance(key, str):
                    raise TraceDecodeError("JSON object keys must be strings")
                queue.append((child, depth + 1))
        elif isinstance(value, list):
            queue.extend((child, depth + 1) for child in value)


def _parse_json(data: str | bytes | bytearray) -> dict[str, Any]:
    if isinstance(data, str):
        raw = data.encode("utf-8")
    elif isinstance(data, (bytes, bytearray)):
        raw = bytes(data)
    else:
        raise TraceDecodeError("trace data must be str, bytes, or bytearray")
    if len(raw) > MAX_TRACE_BYTES:
        raise TraceDecodeError(
            f"trace exceeds maximum size of {MAX_TRACE_BYTES} bytes"
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TraceDecodeError("trace must be valid UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except TraceDecodeError:
        raise
    except (TypeError, ValueError, RecursionError) as exc:
        raise TraceDecodeError("invalid JSON trace") from exc
    _check_shape_limits(value)
    if not isinstance(value, dict):
        raise TraceDecodeError("top-level trace must be a JSON object")
    return value


def serialize_trace(trace: Trace) -> bytes:
    """Return canonical UTF-8 JSON bytes for a production Trace."""
    if not isinstance(trace, Trace):
        raise TraceSerializationError("serialize_trace expects a resolvewhy.model.Trace")
    if trace.schema != SCHEMA:
        raise TraceSerializationError(
            f"unsupported trace schema {trace.schema!r}; expected {SCHEMA!r}"
        )

    # Never emit an artifact that the production structural validator would reject.
    from resolvewhy.validation import validate_trace

    issues = validate_trace(trace)
    if issues:
        details = "; ".join(issue.message for issue in issues)
        raise TraceSerializationError(f"trace failed structural validation: {details}")

    payload = _serialize_trace(trace)
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def serialize_trace_json(trace: Trace) -> str:
    """Return canonical UTF-8 JSON text for a production Trace."""
    return serialize_trace(trace).decode("utf-8")


def deserialize_trace(data: str | bytes | bytearray) -> Trace:
    """Safely reconstruct a production Trace from canonical/non-canonical JSON."""
    payload = _parse_json(data)
    trace = _deserialize_trace(payload)

    # Import locally to keep the trace codec independent of the validator's module
    # initialization path and to validate the fully reconstructed object.
    from resolvewhy.validation import validate_trace

    issues = validate_trace(trace)
    if issues:
        details = "; ".join(issue.message for issue in issues)
        raise TraceDecodeError(f"trace failed structural validation: {details}")
    return trace
