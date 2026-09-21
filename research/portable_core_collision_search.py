from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ACTIVE = "python3.13/linux"
LEGACY = "python3.9/linux"

@dataclass(frozen=True)
class Candidate:
    package: str
    version: str
    requires_python: str | None = None
    source: str = "index:A"
    artifact: str | None = None

def freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return tuple(sorted((k, freeze(v)) for k, v in value.items()))
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(freeze(v) for v in value)
    return value

def python_compatible(candidate: Candidate, env: str) -> bool:
    if candidate.requires_python is None:
        return True
    if candidate.requires_python == ">=3.10":
        return env != LEGACY
    raise ValueError(candidate.requires_python)

def truth(world: dict[str, Any]) -> str:
    candidate = world["candidate"]
    for env in world["evaluation_domain"]:
        if not python_compatible(candidate, env):
            return "UNSAT"
    return "SAT"

# These are deliberately different native shapes.
def pip_adapter(native: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirements": tuple(native["root_requirements"]),
        "dependency_edges": tuple(native["requirement_information"]),
        "candidate": native["provider_candidate"],
        "runtime_context": native["runtime"],
        "resolution_policy": native["policy"],
        "candidate_coverage": native["candidate_coverage"],
        "provenance": native["provenance"],
        "evidence_state": native["evidence_state"],
    }

def uv_adapter(native: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirements": tuple(native["root_terms"]),
        "dependency_edges": tuple(native["fork_terms"]),
        "candidate": native["included_version"],
        "runtime_context": native["environment"],
        "resolution_policy": native["resolver_policy"],
        "candidate_coverage": native["available_version_scope"],
        "provenance": native["derivation_refs"],
        "evidence_state": native["evidence_state"],
    }

def make_world(family: str, domain: tuple[str, ...], variant: int) -> dict[str, Any]:
    candidate = Candidate("numba", "0.61", ">=3.10")
    if family == "pip":
        return {
            "root_requirements": (("app", "==1"),),
            "requirement_information": (("app==1", "numba>=0.61", True),),
            "provider_candidate": candidate,
            "runtime": {"python": "3.13", "platform": "linux"},
            "policy": {"resolution_strategy": "universal"},
            "candidate_coverage": {"status": "complete", "scope": ("index:A",), "attested": True},
            "provenance": (("metadata:numba-0.61", "index:A"),),
            "evidence_state": "known_fact",
        } | {"evaluation_domain": domain, "native": {"variant": variant, "decision_level": 7}}
    return {
        "root_terms": (("app", "==1"),),
        "fork_terms": (("app==1", "numba>=0.61", True),),
        "included_version": candidate,
        "environment": {"python": "3.13", "platform": "linux"},
        "resolver_policy": {"resolution_strategy": "universal"},
        "available_version_scope": {"status": "complete", "scope": ("index:A",), "attested": True},
        "derivation_refs": (("uv:derive:42", "metadata:numba-0.61"),),
        "evidence_state": "known_fact",
        "evaluation_domain": domain,
        "native": {"variant": variant, "decision_level": 4},
    }

def current_projection(world: dict[str, Any]) -> tuple[Any, ...]:
    if "root_requirements" in world:
        adapted = pip_adapter(world)
    else:
        adapted = uv_adapter(world)
    return tuple((key, freeze(adapted[key])) for key in sorted(adapted))

def repaired_projection(world: dict[str, Any]) -> tuple[Any, ...]:
    return current_projection(world) + (("evaluation_domain", tuple(world["evaluation_domain"])),)

def collision_search() -> tuple[int, int, int]:
    worlds = []
    for domain in [(ACTIVE,), (ACTIVE, LEGACY)]:
        for family in ("pip", "uv"):
            for variant in range(16):
                worlds.append(make_world(family, domain, variant))
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for world in worlds:
        groups.setdefault(current_projection(world), []).append(world)
    raw = sum(1 for items in groups.values() if len({truth(w) for w in items}) > 1)
    repaired_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for world in worlds:
        repaired_groups.setdefault(repaired_projection(world), []).append(world)
    repaired = sum(1 for items in repaired_groups.values() if len({truth(w) for w in items}) > 1)
    unique_patterns = 0
    for items in groups.values():
        outcomes = {truth(w) for w in items}
        if len(outcomes) > 1:
            domains = {tuple(w["evaluation_domain"]) for w in items}
            if len(domains) > 1:
                unique_patterns += 1
    return len(worlds), raw, repaired, unique_patterns

def native_deletion_check() -> bool:
    world = make_world("uv", (ACTIVE, LEGACY), 0)
    baseline = truth(world)
    for field in ("variant", "decision_level"):
        clone = make_world("uv", (ACTIVE, LEGACY), 0)
        clone["native"][field] = None
        if truth(clone) != baseline:
            return False
    return True

if __name__ == "__main__":
    worlds, raw, repaired, unique = collision_search()
    print(f"worlds={worlds}")
    print(f"current_projection_collisions={raw}")
    print(f"unique_collision_families={unique}")
    print(f"repaired_projection_collisions={repaired}")
    print(f"native_deletion_preserves_truth={native_deletion_check()}")