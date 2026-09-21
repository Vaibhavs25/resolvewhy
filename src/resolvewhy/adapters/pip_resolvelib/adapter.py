from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, TypeVar

from .capture import (
    CaptureBuffer,
    CapturedRun,
    RecordingProvider,
    RecordingReporter,
)
from .normalize import AdapterContext, SemanticAccessors, normalize_capture

RT = TypeVar("RT")
CT = TypeVar("CT")


class AdapterExecutionError(RuntimeError):
    """Raised when the resolver cannot produce a supported capture outcome."""


@dataclass(frozen=True)
class AdapterResult(Generic[RT, CT]):
    trace: Any
    resolver_result: object | None
    native_error_type: str | None
    native_status_claim: str

    @property
    def resolution_succeeded(self) -> bool:
        return self.native_status_claim == "SAT"

    @property
    def resolution_failed(self) -> bool:
        return self.native_status_claim == "UNSAT"


class PipResolvelibAdapter(Generic[RT, CT]):
    """Capture and normalize structured evidence from a resolvelib-compatible resolver.

    The adapter targets the public resolvelib provider/reporter protocol. It does
    not depend on pip's private resolver implementation. A pip caller can supply
    pip's provider/resolver objects when it intentionally accepts that private
    integration boundary; semantic extraction remains explicit and fail-closed.
    """

    def __init__(
        self,
        *,
        provider: Any,
        resolver_factory: Callable[[Any, Any], Any],
        context: AdapterContext,
        reporter: Any | None = None,
        semantics: SemanticAccessors | None = None,
        resolution_impossible_exceptions: tuple[type[BaseException], ...] = (),
    ) -> None:
        self.provider = provider
        self.resolver_factory = resolver_factory
        self.context = context
        self.reporter = reporter
        self.semantics = semantics
        self.resolution_impossible_exceptions = resolution_impossible_exceptions

    @classmethod
    def from_resolvelib(
        cls,
        *,
        provider: Any,
        context: AdapterContext,
        reporter: Any | None = None,
        semantics: SemanticAccessors | None = None,
    ) -> "PipResolvelibAdapter[Any, Any]":
        """Construct an adapter using an installed public resolvelib module."""
        try:
            import resolvelib
        except ImportError as exc:
            raise AdapterExecutionError(
                "resolvelib is not installed; install the optional "
                "'resolvewhy[pip-resolvelib]' dependency"
            ) from exc

        if reporter is None:
            reporter = resolvelib.BaseReporter()

        context = AdapterContext(
            runtime_context=context.runtime_context,
            resolution_policy=context.resolution_policy,
            evaluation_domain=context.evaluation_domain,
            candidate_domain_scopes=context.candidate_domain_scopes,
            coverage_attestations=context.coverage_attestations,
            additional_evidence=context.additional_evidence,
            resolver_name=context.resolver_name,
            resolver_version=context.resolver_version or getattr(resolvelib, "__version__", None),
            resolver_commit=context.resolver_commit,
        )
        return cls(
            provider=provider,
            resolver_factory=resolvelib.Resolver,
            context=context,
            reporter=reporter,
            semantics=semantics,
            resolution_impossible_exceptions=(resolvelib.ResolutionImpossible,),
        )

    @classmethod
    def from_resolvelib_module(
        cls,
        *,
        resolver_module: Any,
        provider: Any,
        context: AdapterContext,
        reporter: Any | None = None,
        semantics: SemanticAccessors | None = None,
    ) -> "PipResolvelibAdapter[Any, Any]":
        """Construct from either external or vendored resolvelib-compatible modules.

        This is useful for pip's vendored resolver runtime in a controlled test
        environment without importing pip's private resolver classes.
        """
        resolver_cls = getattr(resolver_module, "Resolver", None)
        reporter_cls = getattr(resolver_module, "BaseReporter", None)
        resolution_impossible = getattr(resolver_module, "ResolutionImpossible", None)
        if resolver_cls is None or reporter_cls is None or resolution_impossible is None:
            raise AdapterExecutionError(
                "resolver module does not expose the required public resolvelib surface"
            )
        if reporter is None:
            reporter = reporter_cls()
        context = AdapterContext(
            runtime_context=context.runtime_context,
            resolution_policy=context.resolution_policy,
            evaluation_domain=context.evaluation_domain,
            candidate_domain_scopes=context.candidate_domain_scopes,
            coverage_attestations=context.coverage_attestations,
            additional_evidence=context.additional_evidence,
            resolver_name=context.resolver_name,
            resolver_version=context.resolver_version or getattr(resolver_module, "__version__", None),
            resolver_commit=context.resolver_commit,
        )
        return cls(
            provider=provider,
            resolver_factory=resolver_cls,
            context=context,
            reporter=reporter,
            semantics=semantics,
            resolution_impossible_exceptions=(resolution_impossible,),
        )

    def capture(
        self,
        requirements: Iterable[RT],
        *,
        resolver_kwargs: dict[str, Any] | None = None,
    ) -> CapturedRun[RT, CT]:
        buffer: CaptureBuffer[RT, CT] = CaptureBuffer()
        recording_provider = RecordingProvider(
            self.provider,
            buffer,
            identifier_formatter=(
                self.semantics.identifier_text
                if self.semantics is not None
                else str
            ),
        )
        delegate_reporter = self.reporter
        if delegate_reporter is None:
            delegate_reporter = _NullReporter()
        recording_reporter = RecordingReporter(delegate_reporter, buffer)
        resolver = self.resolver_factory(recording_provider, recording_reporter)

        try:
            result = resolver.resolve(
                requirements,
                **(resolver_kwargs or {}),
            )
        except self.resolution_impossible_exceptions as exc:
            buffer.outcome = "resolution_impossible"
            buffer.error_type = type(exc).__qualname__
            return CapturedRun(
                buffer=buffer,
                resolver_result=None,
                native_error=exc,
            )
        except Exception:
            # Unknown resolver failures must not be relabeled as UNSAT.
            raise

        buffer.outcome = "resolved"
        return CapturedRun(
            buffer=buffer,
            resolver_result=result,
            native_error=None,
        )

    def normalize(self, captured: CapturedRun[RT, CT]):
        return normalize_capture(
            captured,
            context=self.context,
            semantics=self.semantics,
        )

    def build_trace(self, captured: CapturedRun[RT, CT]):
        return self.normalize(captured)

    def resolve(
        self,
        requirements: Iterable[RT],
        *,
        resolver_kwargs: dict[str, Any] | None = None,
    ) -> AdapterResult[RT, CT]:
        captured = self.capture(
            requirements,
            resolver_kwargs=resolver_kwargs,
        )
        trace = self.build_trace(captured)
        return AdapterResult(
            trace=trace,
            resolver_result=captured.resolver_result,
            native_error_type=captured.buffer.error_type,
            native_status_claim=(
                "UNSAT"
                if captured.buffer.outcome == "resolution_impossible"
                else "SAT"
            ),
        )


class _NullReporter:
    def starting(self) -> None:
        pass

    def starting_round(self, index: int) -> None:
        pass

    def ending_round(self, index: int, state: Any) -> None:
        pass

    def ending(self, state: Any) -> None:
        pass

    def adding_requirement(self, requirement: Any, parent: Any) -> None:
        pass

    def resolving_conflicts(self, causes: Any) -> None:
        pass

    def rejecting_candidate(self, criterion: Any, candidate: Any) -> None:
        pass

    def pinning(self, candidate: Any) -> None:
        pass
