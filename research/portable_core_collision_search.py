from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ACTIVE = "python3.13/linux/x86_64/cpython"
LEGACY = "python3.9/linux/x86_64/cpython"
WINDOWS = "python3.13/windows/amd64/cpython"
ARM = "python3.13/linux/aarch64/cpython"
DOMAINS = [(ACTIVE,), (ACTIVE, LEGACY), (ACTIVE, WINDOWS), (ACTIVE, ARM)]

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
        return not env.startswith("python3.9/")
    raise ValueError(candidate.requires_python)

def activation_active(variant: int, env: str) -> bool:
    return (variant % 2 == 0) or env.startswith("python3.13/")

def artifact_compatible(candidate: Candidate, env: str) -> bool:
    if candidate.artifact == "windows-only":
        return env.startswith("python3.13/windows/")
    return True

def truth(world: dict[str, Any]) -> str:
    candidate = world["candidate"]
    for env in world["evaluation_domain"]:
        if not python_compatible(candidate, env):
            return "UNSAT"
        if not artifact_compatible(candidate, env):
            return "UNSAT"
    if not world["activation_active"]:
        return "SAT"
    if world["candidate_coverage"]["status"] != "complete":
        return "INSUFFICIENT_EVIDENCE"
    return "SAT"

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

POLICIES = (
    {"resolution_strategy": "universal", "prerelease": "disallow"},
    {"resolution_strategy": "universal", "prerelease": "allow"},
)

def make_world(family: str, domain: tuple[str, ...], variant: int) -> dict[str, Any]:
    policy = POLICIES[variant % len(POLICIES)]
    source = "index:A" if (variant % 4) < 2 else "index:B"
    candidate = Candidate(
        "numba", "0.61", ">=3.10",
        source=source,
        artifact="windows-only" if (variant % 8) == 6 else None,
    )
    coverage = {
        "status": "complete" if (variant % 5) != 4 else "partial",
        "scope": (source,),
        "attested": (variant % 3) != 2,
    }
    activation = activation_active(variant, domain[0])
    native = {
        "variant": variant,
        "decision_level": 4 + (variant % 7),
        "backjump_state": variant % 3,
        "native_note": f"resolver-{family}-{variant}",
    }
    if family == "pip":
        return {
            "root_requirements": (("app", "==1"),),
            "requirement_information": (("app==1", "numba>=0.61", activation),),
            "provider_candidate": candidate,
            "runtime": {"python": domain[0].split("/")[0].replace("python", ""), "platform": domain[0].split("/")[1]},
            "policy": policy,
            "candidate_coverage": coverage,
            "provenance": (("metadata:numba-0.61", source),),
            "evidence_state": "known_fact" if coverage["status"] == "complete" else "partial",
            "evaluation_domain": domain,
            "activation_active": activation,
            "native": native,
        }
    return {
        "root_terms": (("app", "==1"),),
        "fork_terms": (("app==1", "numba>=0.61", activation),),
        "included_version": candidate,
        "environment": {"python": domain[0].split("/")[0].replace("python", ""), "platform": domain[0].split("/")[1]},
        "resolver_policy": policy,
        "available_version_scope": coverage,
        "derivation_refs": (("uv:derive:42", "metadata:numba-0.61"),),
        "evidence_state": "known_fact" if coverage["status"] == "complete" else "partial",
        "evaluation_domain": domain,
        "activation_active": activation,
        "native": native,
    }

def current_projection(world: dict[str, Any]) -> tuple[Any, ...]:
    adapted = pip_adapter(world) if "root_requirements" in world else uv_adapter(world)
    return tuple((key, freeze(adapted[key])) for key in sorted(adapted))

def repaired_projection(world: dict[str, Any]) -> tuple[Any, ...]:
    return current_projection(world) + (
        ("evaluation_domain", tuple(world["evaluation_domain"])),
        ("proof_quantifier", "universal"),
        ("activation_active", world["activation_active"]),
    )

def collision_search() -> tuple[int, int, int, int]:
    worlds = []
    for domain in DOMAINS:
        for family in ("pip", "uv"):
            for variant in range(32):
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
        if len({truth(w) for w in items}) > 1:
            unique_patterns += 1
    return len(worlds), raw, repaired, unique_patterns

def native_deletion_check() -> bool:
    baseline_world = make_world("uv", (ACTIVE, LEGACY), 0)
    baseline = truth(baseline_world)
    for variant in range(8):
        clone = make_world("uv", (ACTIVE, LEGACY), variant)
        clone["native"] = {"variant": None, "decision_level": None}
        if truth(clone) != truth(make_world("uv", (ACTIVE, LEGACY), variant)):
            return False
    return baseline in {"SAT", "UNSAT", "INSUFFICIENT_EVIDENCE"}

if __name__ == "__main__":
    worlds, raw, repaired, unique = collision_search()
    print(f"worlds={worlds}")
    print(f"current_projection_collisions={raw}")
    print(f"unique_collision_families={unique}")
    print(f"repaired_projection_collisions={repaired}")
    print(f"native_deletion_preserves_truth={native_deletion_check()}")
