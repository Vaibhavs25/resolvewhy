from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Iterable, TypeVar

RT = TypeVar("RT")
CT = TypeVar("CT")


@dataclass(frozen=True)
class RequirementEvent(Generic[RT, CT]):
    sequence: int
    requirement: RT
    parent: CT | None


@dataclass(frozen=True)
class MatchEvent(Generic[CT]):
    sequence: int
    identifier: str
    candidate: CT


@dataclass(frozen=True)
class DependencyEvent(Generic[RT, CT]):
    sequence: int
    parent: CT
    requirement: RT


@dataclass(frozen=True)
class SatisfactionEvent(Generic[RT, CT]):
    sequence: int
    requirement: RT
    candidate: CT
    satisfied: bool


@dataclass(frozen=True)
class PinEvent(Generic[CT]):
    sequence: int
    candidate: CT


@dataclass(frozen=True)
class RejectionEvent(Generic[RT, CT]):
    sequence: int
    candidate: CT
    criterion_type: str
    information: tuple[tuple[RT, CT | None], ...]


@dataclass(frozen=True)
class ConflictEvent(Generic[RT, CT]):
    sequence: int
    causes: tuple[tuple[RT, CT | None], ...]


@dataclass(frozen=True)
class RoundEvent:
    sequence: int
    kind: str
    index: int | None


@dataclass
class CaptureBuffer(Generic[RT, CT]):
    """Mutable in-memory evidence buffer. Native objects never cross the trace boundary."""

    requirements: list[RequirementEvent[RT, CT]] = field(default_factory=list)
    matches: list[MatchEvent[CT]] = field(default_factory=list)
    dependencies: list[DependencyEvent[RT, CT]] = field(default_factory=list)
    satisfactions: list[SatisfactionEvent[RT, CT]] = field(default_factory=list)
    pins: list[PinEvent[CT]] = field(default_factory=list)
    rejections: list[RejectionEvent[RT, CT]] = field(default_factory=list)
    conflicts: list[ConflictEvent[RT, CT]] = field(default_factory=list)
    rounds: list[RoundEvent] = field(default_factory=list)
    outcome: str | None = None
    error_type: str | None = None
    _sequence: int = 0

    def next_sequence(self) -> int:
        self._sequence += 1
        return self._sequence


@dataclass(frozen=True)
class CapturedRun(Generic[RT, CT]):
    buffer: CaptureBuffer[RT, CT]
    resolver_result: object | None
    native_error: BaseException | None


class RecordingProvider(Generic[RT, CT]):
    """Transparent resolvelib provider wrapper that records public provider calls."""

    def __init__(
        self,
        provider: Any,
        buffer: CaptureBuffer[RT, CT],
        *,
        identifier_formatter: Callable[[object], str] = str,
    ) -> None:
        self._provider = provider
        self._buffer = buffer
        self._identifier_formatter = identifier_formatter

    def identify(self, requirement_or_candidate: RT | CT) -> Any:
        return self._provider.identify(requirement_or_candidate)

    def get_preference(self, identifier: Any, *args: Any, **kwargs: Any) -> Any:
        return self._provider.get_preference(identifier, *args, **kwargs)

    def narrow_requirement_selection(self, identifiers: Iterable[Any], *args: Any, **kwargs: Any) -> Iterable[Any]:
        method = getattr(self._provider, "narrow_requirement_selection", None)
        if method is None:
            return identifiers
        return method(identifiers, *args, **kwargs)

    def find_matches(self, identifier: Any, requirements: Any, incompatibilities: Any) -> Any:
        matches = self._provider.find_matches(
            identifier=identifier,
            requirements=requirements,
            incompatibilities=incompatibilities,
        )
        identifier_text = self._identifier_formatter(identifier)

        if callable(matches):
            def factory() -> Iterable[CT]:
                for candidate in matches():
                    self._buffer.matches.append(
                        MatchEvent(
                            sequence=self._buffer.next_sequence(),
                            identifier=identifier_text,
                            candidate=candidate,
                        )
                    )
                    yield candidate

            return factory

        def iterable() -> Iterable[CT]:
            for candidate in matches:
                self._buffer.matches.append(
                    MatchEvent(
                        sequence=self._buffer.next_sequence(),
                        identifier=identifier_text,
                        candidate=candidate,
                    )
                )
                yield candidate

        return iterable()

    def is_satisfied_by(self, requirement: RT, candidate: CT) -> bool:
        satisfied = self._provider.is_satisfied_by(
            requirement=requirement,
            candidate=candidate,
        )
        self._buffer.satisfactions.append(
            SatisfactionEvent(
                sequence=self._buffer.next_sequence(),
                requirement=requirement,
                candidate=candidate,
                satisfied=bool(satisfied),
            )
        )
        return satisfied

    def get_dependencies(self, candidate: CT) -> Iterable[RT]:
        dependencies = self._provider.get_dependencies(candidate=candidate)

        def iterable() -> Iterable[RT]:
            for requirement in dependencies:
                self._buffer.dependencies.append(
                    DependencyEvent(
                        sequence=self._buffer.next_sequence(),
                        parent=candidate,
                        requirement=requirement,
                    )
                )
                yield requirement

        return iterable()


class RecordingReporter(Generic[RT, CT]):
    """Transparent BaseReporter-compatible wrapper for structured resolver events."""

    def __init__(self, delegate: Any, buffer: CaptureBuffer[RT, CT]) -> None:
        self._delegate = delegate
        self._buffer = buffer

    def starting(self) -> None:
        self._buffer.rounds.append(
            RoundEvent(self._buffer.next_sequence(), "starting", None)
        )
        self._forward("starting")

    def starting_round(self, index: int) -> None:
        self._buffer.rounds.append(
            RoundEvent(self._buffer.next_sequence(), "starting_round", index)
        )
        self._forward("starting_round", index)

    def ending_round(self, index: int, state: Any) -> None:
        self._buffer.rounds.append(
            RoundEvent(self._buffer.next_sequence(), "ending_round", index)
        )
        self._forward("ending_round", index, state)

    def ending(self, state: Any) -> None:
        self._buffer.rounds.append(
            RoundEvent(self._buffer.next_sequence(), "ending", None)
        )
        self._forward("ending", state)

    def adding_requirement(self, requirement: RT, parent: CT | None) -> None:
        self._buffer.requirements.append(
            RequirementEvent(
                sequence=self._buffer.next_sequence(),
                requirement=requirement,
                parent=parent,
            )
        )
        self._forward("adding_requirement", requirement, parent)

    def resolving_conflicts(self, causes: Any) -> None:
        information = tuple(
            (item.requirement, item.parent)
            for item in causes
        )
        self._buffer.conflicts.append(
            ConflictEvent(
                sequence=self._buffer.next_sequence(),
                causes=information,
            )
        )
        self._forward("resolving_conflicts", causes)

    def rejecting_candidate(self, criterion: Any, candidate: CT) -> None:
        raw_information = getattr(criterion, "information", ())
        information = tuple(
            (item.requirement, item.parent)
            for item in raw_information
        )
        self._buffer.rejections.append(
            RejectionEvent(
                sequence=self._buffer.next_sequence(),
                candidate=candidate,
                criterion_type=type(criterion).__qualname__,
                information=information,
            )
        )
        self._forward("rejecting_candidate", criterion, candidate)

    def pinning(self, candidate: CT) -> None:
        self._buffer.pins.append(
            PinEvent(
                sequence=self._buffer.next_sequence(),
                candidate=candidate,
            )
        )
        self._forward("pinning", candidate)

    def _forward(self, method_name: str, *args: Any) -> None:
        method = getattr(self._delegate, method_name, None)
        if method is not None:
            method(*args)
