from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.parse import urlparse

from resolvewhy.model import (
    ArtifactSelectionStatus,
    Candidate,
    CandidateDomain,
    CandidateDomainScope,
    CandidateCoverage,
    CandidateKind,
    CoverageAttestation,
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

from .capture import (
    CaptureBuffer,
    CapturedRun,
    ConflictEvent,
    DependencyEvent,
    MatchEvent,
    RejectionEvent,
    RequirementEvent,
)


SUPPORTED_VERSION_OPERATORS = {"==", "!=", "<", "<=", ">", ">="}


class AdapterNormalizationError(ValueError):
    """Raised when the captured evidence cannot be represented safely."""


@dataclass(frozen=True)
class ArtifactView:
    origin: str | None = None
    tags: tuple[str, ...] = ()
    hash: str | None = None
    compatible: bool | None = None
    selection_status: ArtifactSelectionStatus = ArtifactSelectionStatus.UNKNOWN


@dataclass(frozen=True)
class RequirementView:
    package: str
    constraints: tuple[VersionConstraint, ...] = ()
    raw: str | None = None
    activation: MarkerExpression | None = None
    explicit_candidate: object | None = None
    complete: bool = True
    unsupported_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CandidateView:
    package: str
    version: str | None
    kind: CandidateKind
    source_ref: str | None = None
    origin: str | None = None
    artifacts: tuple[ArtifactView, ...] = ()
    requires_python: tuple[VersionConstraint, ...] = ()
    identity_complete: bool = True
    unsupported_reasons: tuple[str, ...] = ()

    @property
    def identity_key(self) -> tuple[str, str | None, str, str | None, str | None]:
        # Artifact origin is excluded for registry candidates: artifacts are a
        # separate semantic entity and must not silently split candidate identity.
        origin = self.origin if self.kind is not CandidateKind.REGISTRY else None
        return (
            self.package,
            self.version,
            self.kind.value,
            self.source_ref,
            origin,
        )


class SemanticAccessors(Protocol):
    def identifier_text(self, identifier: object) -> str:
        ...

    def requirement_view(self, requirement: object) -> RequirementView:
        ...

    def candidate_view(self, candidate: object) -> CandidateView:
        ...


def _string_value(value: object) -> str:
    return str(value)


def _read_first_attr(obj: object, names: tuple[str, ...]) -> object | None:
    for name in names:
        try:
            value = getattr(obj, name)
        except Exception:
            continue
        if value is not None:
            return value
    return None


def _specifier_constraints(specifier: object | None) -> tuple[tuple[VersionConstraint, ...], tuple[str, ...]]:
    if specifier is None:
        return (), ()

    try:
        values = list(specifier)
    except TypeError:
        values = [specifier]

    constraints: list[VersionConstraint] = []
    unsupported: list[str] = []
    for item in values:
        operator = _read_first_attr(item, ("operator",))
        version = _read_first_attr(item, ("version",))
        if operator is None or version is None:
            unsupported.append("unreadable version specifier")
            continue
        op = str(operator)
        ver = str(version)
        if op not in SUPPORTED_VERSION_OPERATORS:
            unsupported.append(f"unsupported version operator: {op}")
            continue
        if "*" in ver:
            unsupported.append(f"wildcard version is outside the tested verifier fragment: {ver}")
            continue
        constraints.append(VersionConstraint(op, ver))
    return tuple(constraints), tuple(unsupported)


def _marker_expression_from_packaging(marker: object | None) -> tuple[MarkerExpression | None, tuple[str, ...]]:
    if marker is None:
        return None, ()

    markers = getattr(marker, "_markers", None)
    if markers is None:
        return None, ("marker AST is not exposed by the supplied requirement object",)

    def atom(node: object) -> MarkerExpression:
        if not isinstance(node, tuple) or len(node) != 3:
            raise ValueError("marker atom is not a 3-tuple")
        variable, operator, value = (str(node[0]), str(node[1]), str(node[2]))
        return MarkerExpression(
            kind="atom",
            atom=MarkerAtom(variable=variable, operator=operator, value=value),
        )

    def parse(node: object) -> MarkerExpression:
        if isinstance(node, tuple):
            return atom(node)
        if not isinstance(node, list):
            raise ValueError("marker node is neither a tuple nor a list")
        if len(node) == 1:
            return parse(node[0])
        if len(node) < 3 or len(node) % 2 == 0:
            raise ValueError("marker boolean expression has invalid shape")

        expr = parse(node[0])
        index = 1
        while index < len(node):
            operator = str(node[index])
            if operator not in {"and", "or"}:
                raise ValueError(f"unsupported marker boolean operator: {operator!r}")
            right = parse(node[index + 1])
            expr = MarkerExpression(kind=operator, children=(expr, right))
            index += 2
        return expr

    try:
        return parse(markers), ()
    except (TypeError, ValueError) as exc:
        return None, (f"unsupported marker expression: {exc}",)


@dataclass(frozen=True)
class DefaultPipSemantics:
    """Best-effort pip-object adapter with explicit fail-closed gaps.

    The class uses only observable attributes and records limitations instead
    of guessing when a pip/resolvelib object does not expose enough structure.
    """

    namespace: str = "pip/resolvelib"

    def identifier_text(self, identifier: object) -> str:
        return _string_value(identifier)

    def requirement_view(self, requirement: object) -> RequirementView:
        package = _read_first_attr(requirement, ("project_name", "name"))
        if package is None:
            raise AdapterNormalizationError(
                f"requirement object {type(requirement).__qualname__} exposes no project/name attribute"
            )
        package_text = str(package)
        unsupported: list[str] = []

        raw: str | None
        try:
            raw = str(requirement)
        except Exception:
            raw = None

        specifier = _read_first_attr(requirement, ("specifier",))
        if specifier is None:
            ireq = _read_first_attr(requirement, ("_ireq",))
            parsed = _read_first_attr(ireq, ("req",)) if ireq is not None else None
            specifier = _read_first_attr(parsed, ("specifier",)) if parsed is not None else None

        constraints, constraint_unsupported = _specifier_constraints(specifier)
        unsupported.extend(constraint_unsupported)

        marker = _read_first_attr(requirement, ("marker",))
        if marker is None:
            ireq = _read_first_attr(requirement, ("_ireq",))
            parsed = _read_first_attr(ireq, ("req",)) if ireq is not None else None
            marker = _read_first_attr(parsed, ("marker",)) if parsed is not None else None

        activation, marker_unsupported = _marker_expression_from_packaging(marker)
        unsupported.extend(marker_unsupported)

        explicit_candidate = None
        lookup = getattr(requirement, "get_candidate_lookup", None)
        if callable(lookup):
            try:
                candidate, _ = lookup()
                explicit_candidate = candidate
            except Exception:
                unsupported.append("candidate lookup could not be inspected")

        extras = _read_first_attr(requirement, ("extras",))
        project_name = _read_first_attr(requirement, ("project_name",))
        if extras and project_name is not None:
            try:
                if tuple(extras):
                    unsupported.append("extras are retained as raw/native evidence; full extras semantics are outside Phase 3A")
            except TypeError:
                unsupported.append("extras could not be inspected")

        return RequirementView(
            package=package_text,
            constraints=constraints,
            raw=raw,
            activation=activation,
            explicit_candidate=explicit_candidate,
            complete=not unsupported,
            unsupported_reasons=tuple(unsupported),
        )

    def candidate_view(self, candidate: object) -> CandidateView:
        package = _read_first_attr(candidate, ("project_name", "name"))
        if package is None:
            raise AdapterNormalizationError(
                f"candidate object {type(candidate).__qualname__} exposes no project/name attribute"
            )
        package_text = str(package)

        version_value = _read_first_attr(candidate, ("version",))
        version = None if version_value is None else str(version_value)

        is_editable = bool(_read_first_attr(candidate, ("is_editable",)) or False)
        source_link = _read_first_attr(candidate, ("source_link",))
        link_url = None
        source_ref = None
        if source_link is not None:
            try:
                link_url_value = getattr(source_link, "url", None)
                link_url = None if link_url_value is None else str(link_url_value)
            except Exception:
                link_url = None
            try:
                comes_from = getattr(source_link, "comes_from", None)
                source_ref = None if comes_from is None else str(comes_from)
            except Exception:
                source_ref = None

        class_name = type(candidate).__qualname__.lower()
        if is_editable:
            kind = CandidateKind.PATH
        elif getattr(source_link, "is_vcs", False):
            kind = CandidateKind.VCS
        elif getattr(source_link, "is_file", False):
            kind = CandidateKind.PATH
        elif "directurl" in class_name or "direct_url" in class_name:
            kind = CandidateKind.DIRECT_URL
        else:
            kind = CandidateKind.REGISTRY

        artifacts: tuple[ArtifactView, ...]
        unsupported: list[str] = []
        if link_url is not None:
            tags: tuple[str, ...] = ()
            link_hash: str | None = None
            try:
                hashes = getattr(source_link, "hashes", None)
                if hashes:
                    if hasattr(hashes, "items"):
                        items = list(hashes.items())
                        if items:
                            algorithm, digest = items[0]
                            link_hash = f"{algorithm}={digest}"
                        if len(items) > 1:
                            unsupported.append("multiple artifact hashes are preserved only as first observed hash")
                    elif isinstance(hashes, str):
                        link_hash = hashes
            except Exception:
                unsupported.append("artifact hash data could not be inspected")
            artifacts = (
                ArtifactView(
                    origin=link_url,
                    tags=tags,
                    hash=link_hash,
                    compatible=None,
                    selection_status=(
                        ArtifactSelectionStatus.YANKED
                        if getattr(source_link, "yanked_reason", None)
                        else ArtifactSelectionStatus.UNKNOWN
                    ),
                ),
            )
        else:
            artifacts = ()

        requires_python_value = _read_first_attr(candidate, ("requires_python",))
        if requires_python_value is None:
            dist = _read_first_attr(candidate, ("dist",))
            requires_python_value = _read_first_attr(dist, ("requires_python",)) if dist is not None else None
        requires_python, python_unsupported = _specifier_constraints_from_value(requires_python_value)
        unsupported.extend(python_unsupported)

        identity_complete = bool(package_text and version is not None)
        if kind is not CandidateKind.REGISTRY and not (source_ref or link_url):
            identity_complete = False
            unsupported.append("non-registry candidate lacks observable source identity")

        return CandidateView(
            package=package_text,
            version=version,
            kind=kind,
            source_ref=source_ref,
            origin=link_url,
            artifacts=artifacts,
            requires_python=requires_python,
            identity_complete=identity_complete,
            unsupported_reasons=tuple(unsupported),
        )


def _specifier_constraints_from_value(value: object | None) -> tuple[tuple[VersionConstraint, ...], tuple[str, ...]]:
    if value is None:
        return (), ()
    if not isinstance(value, str):
        return _specifier_constraints(value)
    try:
        from packaging.specifiers import SpecifierSet
    except ImportError:
        return (), ("packaging is required to parse string Requires-Python metadata",)
    try:
        return _specifier_constraints(SpecifierSet(value))
    except Exception as exc:
        return (), (f"invalid Requires-Python metadata: {exc}",)


@dataclass(frozen=True)
class AdapterContext:
    runtime_context: RuntimeContext
    resolution_policy: ResolutionPolicy
    evaluation_domain: EvaluationDomain | None = None
    candidate_domain_scopes: dict[str, CandidateDomainScope] = field(default_factory=dict)
    coverage_attestations: dict[str, CoverageAttestation] = field(default_factory=dict)
    additional_evidence: tuple[EvidenceObservation, ...] = ()
    resolver_name: str = "pip/resolvelib"
    resolver_version: str | None = None
    resolver_commit: str | None = None

    def __post_init__(self) -> None:
        if self.evaluation_domain is not None:
            if self.evaluation_domain.kind is not EvaluationDomainKind.SINGLETON_ENVIRONMENT:
                raise AdapterNormalizationError(
                    "Phase 3A supports only a single-environment resolvelib observation; "
                    "multi-environment proof scope must not be inferred"
                )
            if tuple(self.evaluation_domain.environment_refs) != (self.runtime_context.id,):
                raise AdapterNormalizationError(
                    "evaluation_domain must bind exactly to the captured runtime_context"
                )


class _ObjectIds:
    def __init__(self) -> None:
        self._ids: dict[int, str] = {}

    def get(self, obj: object, prefix: str, counter: list[int]) -> str:
        key = id(obj)
        if key not in self._ids:
            counter[0] += 1
            self._ids[key] = f"{prefix}:{counter[0]:04d}"
        return self._ids[key]


def _native_ref(
    obj: object,
    kind: ReferenceKind,
    ids: _ObjectIds,
    prefix: str,
    counter: list[int],
) -> TraceRef:
    return TraceRef(kind, ids.get(obj, prefix, counter))


def normalize_capture(
    captured: CapturedRun,
    context: AdapterContext,
    semantics: SemanticAccessors | None = None,
) -> Trace:
    semantics = semantics or DefaultPipSemantics()

    buffer = captured.buffer
    counters = [0]
    candidate_ids = _ObjectIds()
    requirement_ids = _ObjectIds()

    candidate_models: list[Candidate] = []
    candidate_views: dict[str, CandidateView] = {}
    native_candidate_to_ref: dict[int, str] = {}

    def candidate_id(native: object) -> str:
        view = semantics.candidate_view(native)
        ref = candidate_ids.get(native, "cand", counters)
        native_candidate_to_ref[id(native)] = ref
        candidate_views.setdefault(ref, view)
        return ref

    # First pass: every candidate observed in matches, dependencies, pins, and rejections.
    observed_candidates: list[object] = []
    seen_candidate_keys: set[int] = set()

    def observe_candidate(native: object) -> None:
        key = id(native)
        if key in seen_candidate_keys:
            return
        seen_candidate_keys.add(key)
        observed_candidates.append(native)

    for event in buffer.matches:
        observe_candidate(event.candidate)
    for event in buffer.dependencies:
        observe_candidate(event.parent)
    for event in buffer.pins:
        observe_candidate(event.candidate)
    for event in buffer.rejections:
        observe_candidate(event.candidate)
    for event in buffer.satisfactions:
        observe_candidate(event.candidate)

    for native in observed_candidates:
        ref = candidate_id(native)
        view = candidate_views[ref]
        candidate_models.append(
            Candidate(
                id=ref,
                package=view.package,
                version=view.version,
                kind=view.kind,
                source_ref=view.source_ref,
                origin=view.origin,
            )
        )

    requirement_events: list[RequirementEvent[object, object]] = list(buffer.requirements)
    dependency_events: list[DependencyEvent[object, object]] = list(buffer.dependencies)

    requirements: list[Requirement] = []
    requirement_event_refs: list[tuple[RequirementEvent[object, object], str, RequirementView]] = []

    for event in requirement_events:
        view = semantics.requirement_view(event.requirement)
        ref = requirement_ids.get(event.requirement, "req", counters)
        parent_ref = None if event.parent is None else candidate_id(event.parent)
        requirements.append(
            Requirement(
                id=ref,
                package=view.package,
                constraint=view.constraints[0] if len(view.constraints) == 1 else None,
                raw=view.raw,
                parent_candidate_ref=parent_ref,
                activation=view.activation,
                evidence_refs=(TraceRef(ReferenceKind.EVIDENCE, f"obs:req:{ref}"),),
            )
        )
        requirement_event_refs.append((event, ref, view))

    # Requirements returned by get_dependencies() should normally be followed by
    # adding_requirement(). If not, synthesize a local requirement node from the
    # observed dependency itself and mark the trace incomplete.
    consumed_req_events: set[str] = set()

    def requirement_for_dependency(event: DependencyEvent[object, object]) -> tuple[str, RequirementView, bool]:
        parent_ref = candidate_id(event.parent)
        candidates = [
            item for item in requirement_event_refs
            if item[0].requirement is event.requirement
            and item[0].parent is event.parent
            and item[1] not in consumed_req_events
        ]
        if candidates:
            event_ref, req_ref, view = candidates[0]
            consumed_req_events.add(req_ref)
            return req_ref, view, False

        view = semantics.requirement_view(event.requirement)
        req_ref = requirement_ids.get(event.requirement, "req", counters)
        requirements.append(
            Requirement(
                id=req_ref,
                package=view.package,
                constraint=view.constraints[0] if len(view.constraints) == 1 else None,
                raw=view.raw,
                parent_candidate_ref=parent_ref,
                activation=view.activation,
                evidence_refs=(TraceRef(ReferenceKind.EVIDENCE, f"obs:req:{req_ref}"),),
            )
        )
        return req_ref, view, True

    semantic_constraints: list[SemanticConstraint] = []
    dependencies: list[DependencyEdge] = []
    evidence_observations: list[EvidenceObservation] = list(context.additional_evidence)
    provenance: list[ProvenanceRecord] = []

    def add_evidence(
        evidence_id: str,
        kind: str,
        state: EvidenceStateKind,
        supports: tuple[TraceRef, ...] = (),
    ) -> None:
        evidence_observations.append(
            EvidenceObservation(
                id=evidence_id,
                kind=kind,
                state=state,
                supports_refs=supports,
                source_namespace=semantics.namespace
                if hasattr(semantics, "namespace")
                else "pip/resolvelib",
            )
        )

    def add_requirement_constraint(
        req_ref: str,
        view: RequirementView,
        *,
        evidence_id: str,
        parent_candidate_ref: str | None,
        constraint_kind: SemanticConstraintKind,
    ) -> None:
        literals = tuple(
            SemanticLiteral(
                kind=constraint_kind,
                package=view.package,
                candidate_ref=(
                    candidate_id(view.explicit_candidate)
                    if view.explicit_candidate is not None
                    else parent_candidate_ref if constraint_kind is SemanticConstraintKind.DEPENDENCY else None
                ),
                operator=constraint.operator,
                value=constraint.version,
                activation=view.activation,
            )
            for constraint in view.constraints
        )
        if not literals:
            literals = (
                SemanticLiteral(
                    kind=constraint_kind,
                    package=view.package,
                    candidate_ref=(
                        candidate_id(view.explicit_candidate)
                        if view.explicit_candidate is not None
                        else None
                    ),
                    activation=view.activation,
                ),
            )
        constraint_ref = f"c:{req_ref}"
        semantic_constraints.append(
            SemanticConstraint(
                id=constraint_ref,
                kind=constraint_kind,
                literals=literals,
                source_refs=(TraceRef(ReferenceKind.EVIDENCE, evidence_id),),
            )
        )
        provenance.append(
            ProvenanceRecord(
                id=f"prov:{constraint_ref}",
                subject_ref=TraceRef(ReferenceKind.CONSTRAINT, constraint_ref),
                kind=ProvenanceKind.DERIVED,
                premise_refs=(TraceRef(ReferenceKind.EVIDENCE, evidence_id),),
                derivation_rule="requirement-normalization",
                source_namespace=semantics.namespace
                if hasattr(semantics, "namespace")
                else "pip/resolvelib",
            )
        )

    # Build root/dependency semantic constraints using the same normalized requirement events.
    dependency_event_to_req: dict[int, tuple[str, RequirementView, bool]] = {}
    for event in dependency_events:
        req_ref, view, synthesized = requirement_for_dependency(event)
        dependency_event_to_req[event.sequence] = (req_ref, view, synthesized)

    for event, req_ref, view in requirement_event_refs:
        evidence_id = f"obs:req:{req_ref}"
        state = (
            EvidenceStateKind.INCOMPLETE
            if not view.complete
            else EvidenceStateKind.KNOWN_FACT
        )
        add_evidence(
            evidence_id,
            "resolver-requirement",
            state,
            supports=(TraceRef(ReferenceKind.REQUIREMENT, req_ref),),
        )
        add_requirement_constraint(
            req_ref,
            view,
            evidence_id=evidence_id,
            parent_candidate_ref=(
                candidate_id(event.parent) if event.parent is not None else None
            ),
            constraint_kind=(
                SemanticConstraintKind.DEPENDENCY
                if event.parent is not None
                else SemanticConstraintKind.REQUIREMENT
            ),
        )

    existing_req_ids = {str(req.id) for req in requirements}
    for event in dependency_events:
        req_ref, view, synthesized = dependency_event_to_req[event.sequence]
        parent_ref = candidate_id(event.parent)
        edge_ref = f"dep:{event.sequence:04d}"
        edge = DependencyEdge(
            id=edge_ref,
            parent_candidate_ref=parent_ref,
            requirement_ref=req_ref,
            activation=view.activation,
            raw_dependency=view.raw,
            evidence_refs=(TraceRef(ReferenceKind.EVIDENCE, f"obs:{edge_ref}"),),
            source_namespace=semantics.namespace
            if hasattr(semantics, "namespace")
            else "pip/resolvelib",
        )
        dependencies.append(edge)
        add_evidence(
            f"obs:{edge_ref}",
            "resolver-dependency-edge",
            EvidenceStateKind.INCOMPLETE if synthesized or not view.complete else EvidenceStateKind.KNOWN_FACT,
            supports=(TraceRef(ReferenceKind.DEPENDENCY, edge_ref),),
        )
        if synthesized and req_ref not in existing_req_ids:
            existing_req_ids.add(req_ref)
            add_requirement_constraint(
                req_ref,
                view,
                evidence_id=f"obs:req:{req_ref}",
                parent_candidate_ref=parent_ref,
                constraint_kind=SemanticConstraintKind.DEPENDENCY,
            )

    # Requires-Python and artifact observations are candidate-level facts.
    artifacts = []
    seen_artifacts: set[tuple[str, str | None, tuple[str, ...], str | None, bool | None, str]] = set()
    artifact_counter = 0
    for ref, view in candidate_views.items():
        candidate_ref = ref
        candidate_obs_id = f"obs:candidate:{candidate_ref}"
        candidate_state = (
            EvidenceStateKind.INCOMPLETE
            if (not view.identity_complete or view.unsupported_reasons)
            else EvidenceStateKind.KNOWN_FACT
        )
        add_evidence(
            candidate_obs_id,
            "resolver-candidate",
            candidate_state,
            supports=(TraceRef(ReferenceKind.CANDIDATE, candidate_ref),),
        )
        for artifact_view in view.artifacts:
            key = (
                candidate_ref,
                artifact_view.origin,
                artifact_view.tags,
                artifact_view.hash,
                artifact_view.compatible,
                artifact_view.selection_status.value,
            )
            if key in seen_artifacts:
                continue
            seen_artifacts.add(key)
            artifact_counter += 1
            artifact_id = f"artifact:{artifact_counter:04d}"
            from resolvewhy.model import Artifact
            artifacts.append(
                Artifact(
                    id=artifact_id,
                    candidate_ref=candidate_ref,
                    origin=artifact_view.origin,
                    tags=artifact_view.tags,
                    hash=artifact_view.hash,
                    compatible=artifact_view.compatible,
                    selection_status=artifact_view.selection_status,
                    evidence_refs=(TraceRef(ReferenceKind.EVIDENCE, f"obs:{artifact_id}"),),
                )
            )
            add_evidence(
                f"obs:{artifact_id}",
                "resolver-artifact",
                EvidenceStateKind.KNOWN_FACT if artifact_view.origin else EvidenceStateKind.INCOMPLETE,
                supports=(TraceRef(ReferenceKind.ARTIFACT, artifact_id),),
            )
        for index, requires_python in enumerate(view.requires_python):
            constraint_id = f"c:requires-python:{candidate_ref}:{index:04d}"
            semantic_constraints.append(
                SemanticConstraint(
                    id=constraint_id,
                    kind=SemanticConstraintKind.REQUIRES_PYTHON,
                    literals=(
                        SemanticLiteral(
                            kind=SemanticConstraintKind.REQUIRES_PYTHON,
                            package="<Python>",
                            candidate_ref=candidate_ref,
                            runtime_context_ref=context.runtime_context.id,
                            operator=requires_python.operator,
                            value=requires_python.version,
                        ),
                    ),
                    source_refs=(TraceRef(ReferenceKind.EVIDENCE, candidate_obs_id),),
                )
            )
            provenance.append(
                ProvenanceRecord(
                    id=f"prov:{constraint_id}",
                    subject_ref=TraceRef(ReferenceKind.CONSTRAINT, constraint_id),
                    kind=ProvenanceKind.DERIVED,
                    premise_refs=(TraceRef(ReferenceKind.EVIDENCE, candidate_obs_id),),
                    derivation_rule="candidate-requires-python-normalization",
                    source_namespace=semantics.namespace
                    if hasattr(semantics, "namespace")
                    else "pip/resolvelib",
                )
            )

    # Candidate-domain observations are deliberately not treated as exhaustive unless
    # the caller supplies an explicit attestation.
    domain_ids: dict[str, str] = {}
    candidate_domains: list[CandidateDomain] = []
    match_groups: dict[str, list[str]] = {}
    for event in sorted(buffer.matches, key=lambda item: item.sequence):
        ref = candidate_id(event.candidate)
        match_groups.setdefault(event.identifier, [])
        if ref not in match_groups[event.identifier]:
            match_groups[event.identifier].append(ref)

    all_identifiers = list(match_groups)
    for event, _, _ in requirement_event_refs:
        identifier = semantics.identifier_text(
            getattr(event.requirement, "name", getattr(event.requirement, "project_name", event.requirement))
        )
        if identifier not in all_identifiers:
            all_identifiers.append(identifier)

    for index, identifier in enumerate(all_identifiers, start=1):
        domain_id = f"domain:{index:04d}"
        domain_ids[identifier] = domain_id
        refs = tuple(match_groups.get(identifier, ()))
        scope = context.candidate_domain_scopes.get(identifier, CandidateDomainScope())
        attestation = context.coverage_attestations.get(identifier)
        coverage = CandidateCoverage(
            status=CoverageStatus.COMPLETE if attestation is not None else CoverageStatus.UNKNOWN,
            attestation=attestation,
            evidence_refs=(
                (TraceRef(ReferenceKind.EVIDENCE, f"obs:domain:{index:04d}"),)
                if attestation is None
                else ()
            ),
        )
        candidate_domains.append(
            CandidateDomain(
                id=domain_id,
                identifier=identifier,
                requirement_refs=tuple(
                    str(req.id)
                    for req in requirements
                    if str(req.package) == identifier
                ),
                candidate_refs=refs,
                scope=scope,
                runtime_context_ref=context.runtime_context.id,
                resolution_policy_ref=context.resolution_policy.id,
                coverage=coverage,
            )
        )
        add_evidence(
            f"obs:{domain_id}",
            "candidate-domain-observation",
            EvidenceStateKind.KNOWN_FACT
            if attestation is not None
            else EvidenceStateKind.INCOMPLETE,
            supports=(TraceRef(ReferenceKind.CANDIDATE_DOMAIN, domain_id),),
        )

    # Resolver-native rejection/conflict observations.
    rejections: list[RejectionObservation] = []
    incompatibilities: list[IncompatibilityObservation] = []
    for event in buffer.rejections:
        target = candidate_id(event.candidate)
        premise_refs: list[TraceRef] = []
        for requirement, parent in event.information:
            for candidate_req_event, req_ref, _ in requirement_event_refs:
                if candidate_req_event.requirement is requirement:
                    premise_refs.append(TraceRef(ReferenceKind.REQUIREMENT, req_ref))
                    break
            if parent is not None:
                premise_refs.append(
                    TraceRef(ReferenceKind.CANDIDATE, candidate_id(parent))
                )
        rejection_id = f"reject:{event.sequence:04d}"
        rejections.append(
            RejectionObservation(
                id=rejection_id,
                target_ref=TraceRef(ReferenceKind.CANDIDATE, target),
                reason_kind="resolvelib_rejection",
                source_layer="resolver",
                evidence_status=EvidenceStateKind.REJECTED_CANDIDATE,
                premise_refs=tuple(dict.fromkeys(premise_refs)),
            )
        )
        add_evidence(
            f"obs:{rejection_id}",
            "resolver-rejection",
            EvidenceStateKind.REJECTED_CANDIDATE,
            supports=(TraceRef(ReferenceKind.REJECTION, rejection_id),),
        )

    for event in buffer.conflicts:
        term_refs: list[TraceRef] = []
        for requirement, parent in event.causes:
            for candidate_req_event, req_ref, _ in requirement_event_refs:
                if candidate_req_event.requirement is requirement:
                    term_refs.append(TraceRef(ReferenceKind.REQUIREMENT, req_ref))
                    break
            if parent is not None:
                term_refs.append(
                    TraceRef(ReferenceKind.CANDIDATE, candidate_id(parent))
                )
        incompatibility_id = f"inc:resolvelib:{event.sequence:04d}"
        incompatibilities.append(
            IncompatibilityObservation(
                id=incompatibility_id,
                semantics="resolvelib_conflict_causes",
                resolver_namespace="resolvelib",
                term_refs=tuple(dict.fromkeys(term_refs)),
            )
        )
        add_evidence(
            f"obs:{incompatibility_id}",
            "resolver-conflict-causes",
            EvidenceStateKind.KNOWN_FACT,
            supports=(TraceRef(ReferenceKind.INCOMPATIBILITY, incompatibility_id),),
        )

    # Native outcome is represented only as a non-authoritative proof claim.
    if buffer.outcome == "resolved":
        status = ProofStatus.SAT
        outcome_state = EvidenceStateKind.KNOWN_FACT
    elif buffer.outcome == "resolution_impossible":
        status = ProofStatus.UNSAT
        outcome_state = EvidenceStateKind.KNOWN_FACT
    else:
        raise AdapterNormalizationError(
            "capture has no supported resolver outcome; refusing to invent SAT/UNSAT"
        )

    add_evidence(
        "obs:resolver-outcome",
        "native-resolver-outcome",
        outcome_state,
    )

    unsupported_reasons = []
    for view in candidate_views.values():
        unsupported_reasons.extend(view.unsupported_reasons)
    for _, _, view in requirement_event_refs:
        unsupported_reasons.extend(view.unsupported_reasons)

    # Any unknown candidate-domain completeness, unsupported normalization, or incomplete
    # evidence prevents the adapter from presenting the trace as proof-complete.
    overall = (
        EvidenceStateKind.INCOMPLETE
        if unsupported_reasons or any(
            domain.coverage.status is not CoverageStatus.COMPLETE
            for domain in candidate_domains
        )
        else EvidenceStateKind.KNOWN_FACT
    )

    premise_refs = tuple(str(constraint.id) for constraint in semantic_constraints)
    claim = ProofClaim(
        id="claim:resolver-outcome",
        kind="satisfiability",
        quantifier=ProofQuantifier.EXISTENTIAL,
        evaluation_domain_ref=(
            context.evaluation_domain.id
            if context.evaluation_domain is not None
            else f"eval:{context.runtime_context.id}"
        ),
        status_claim=status,
        premise_refs=premise_refs or ("c:empty-placeholder",),
        subset_minimal_claim=False,
    )

    evaluation_domain = context.evaluation_domain or EvaluationDomain(
        id=f"eval:{context.runtime_context.id}",
        kind=EvaluationDomainKind.SINGLETON_ENVIRONMENT,
        environment_refs=(context.runtime_context.id,),
    )

    if not semantic_constraints:
        raise AdapterNormalizationError(
            "resolver emitted no semantic requirements; refusing to fabricate proof premises"
        )

    return Trace(
        schema="resolvewhy-trace/1.0",
        resolver_name=context.resolver_name,
        resolver_version=context.resolver_version,
        resolver_commit=context.resolver_commit,
        trace_scope=TraceScope.SINGLE_ENVIRONMENT,
        runtime_contexts=(context.runtime_context,),
        evaluation_domain=evaluation_domain,
        resolution_policy=context.resolution_policy,
        candidate_domains=tuple(candidate_domains),
        requirements=tuple(requirements),
        candidates=tuple(candidate_models),
        artifacts=tuple(artifacts),
        dependencies=tuple(dependencies),
        rejections=tuple(rejections),
        incompatibilities=tuple(incompatibilities),
        semantic_constraints=tuple(semantic_constraints),
        evidence_state=EvidenceState(
            overall=overall,
            observations=tuple(evidence_observations),
        ),
        provenance=tuple(provenance),
        proof_claim=claim,
    )
