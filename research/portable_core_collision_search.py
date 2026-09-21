from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ACTIVE = "python3.13/linux/x86_64/cpython"
LEGACY = "python3.9/linux/x86_64/cpython"
WINDOWS = "python3.13/windows/amd64/cpython"
ARM = "python3.13/linux/aarch64/cpython"

DOMAINS = [
    (ACTIVE,),
    (ACTIVE, LEGACY),
    (ACTIVE, WINDOWS),
    (ACTIVE, ARM),
]
FAMILIES = ("pip", "uv")
QUANTIFIERS = ("universal", "existential", "branch", "universal")


@dataclass(frozen=True)
class Candidate:
    package: str
    version: str
    requires_python: str | None = None
    source: str = "index:A"
    artifact: str | None = None
    prerelease: bool = False


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
    if candidate.requires_python == ">=4.0":
        return False
    raise ValueError(candidate.requires_python)


def artifact_compatible(candidate: Candidate, env: str) -> bool:
    if candidate.artifact == "windows-only":
        return env.startswith("python3.13/windows/")
    return True


def branch_truth(world: dict[str, Any], env: str) -> bool:
    if not world["activation_active"]:
        return True
    candidate = world["candidate"]
    if candidate.prerelease and world["resolution_policy"]["prerelease"] == "disallow":
        return False
    return python_compatible(candidate, env) and artifact_compatible(candidate, env)


def truth(world: dict[str, Any]) -> str:
    if world["candidate_coverage"]["status"] != "complete" or not world["candidate_coverage"]["attested"]:
        return "INSUFFICIENT_EVIDENCE"
    if world["evidence_state"] != "known_fact":
        return "INSUFFICIENT_EVIDENCE"

    results = [branch_truth(world, env) for env in world["evaluation_domain"]]
    q = world["proof_quantifier"]
    if q == "universal":
        return "VERIFIED_UNSAT" if not all(results) else "SAT"
    if q == "existential":
        return "SAT" if any(results) else "VERIFIED_UNSAT"
    if q == "branch":
        result = results[world["branch_index"]]
        return "SAT" if result else "VERIFIED_UNSAT"
    raise ValueError(q)


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


def make_world(
    family: str,
    domain: tuple[str, ...],
    quantifier: str,
    variant: int,
) -> dict[str, Any]:
    policy = {
        "resolution_strategy": "universal" if quantifier != "branch" else "branch",
        "prerelease": "allow" if variant & 1 else "disallow",
    }
    source = "index:B" if variant & 2 else "index:A"
    candidate = Candidate(
        package="numba",
        version="0.61",
        requires_python=">=3.10" if variant & 4 else None,
        source=source,
        artifact="windows-only" if variant & 2 else None,
        prerelease=bool(variant & 1),
    )
    coverage = {
        "status": "complete" if variant not in {5, 6} else "partial",
        "scope": (source,),
        "attested": variant not in {6, 7},
    }
    activation = not bool(variant & 2)
    branch_index = variant % len(domain)
    provenance = ((f"source:{family}", f"variant:{variant}"),)
    evidence_state = "known_fact" if variant not in {6, 7} else "partial"
    native = {
        "decision_level": 4 + (variant % 7),
        "backjump_state": variant % 3,
        "native_note": f"{family}:{variant}",
    }

    common = {
        "candidate_coverage": coverage,
        "provenance": provenance,
        "evidence_state": evidence_state,
        "evaluation_domain": domain,
        "proof_quantifier": quantifier,
        "branch_index": branch_index,
        "activation_active": activation,
        "candidate": candidate,
        "resolution_policy": policy,
        "native": native,
    }
    if family == "pip":
        common.update({
            "root_requirements": (("app", "==1"),),
            "requirement_information": (("app==1", "numba>=0.61", activation),),
            "provider_candidate": candidate,
            "runtime": {
                "python": domain[0].split("/")[0].replace("python", ""),
                "platform": domain[0].split("/")[1],
            },
            "policy": policy,
        })
    else:
        common.update({
            "root_terms": (("app", "==1"),),
            "fork_terms": (("app==1", "numba>=0.61", activation),),
            "included_version": candidate,
            "environment": {
                "python": domain[0].split("/")[0].replace("python", ""),
                "platform": domain[0].split("/")[1],
            },
            "resolver_policy": policy,
            "available_version_scope": coverage,
            "derivation_refs": provenance,
        })
    return common


def current_projection(world: dict[str, Any]) -> tuple[Any, ...]:
    adapted = pip_adapter(world) if "root_requirements" in world else uv_adapter(world)
    return tuple((key, freeze(adapted[key])) for key in sorted(adapted))


def repaired_projection(world: dict[str, Any]) -> tuple[Any, ...]:
    return current_projection(world) + (
        ("evaluation_domain", freeze(world["evaluation_domain"])),
        ("proof_quantifier", world["proof_quantifier"]),
        ("branch_index", world["branch_index"]),
        ("activation_active", world["activation_active"]),
    )


def collision_search() -> tuple[int, int, int, int]:
    worlds = [
        make_world(family, domain, quantifier, variant)
        for domain in DOMAINS
        for family in FAMILIES
        for quantifier in QUANTIFIERS
        for variant in range(8)
    ]
    assert len(worlds) == 256

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for world in worlds:
        groups.setdefault(current_projection(world), []).append(world)
    raw = sum(1 for items in groups.values() if len({truth(w) for w in items}) > 1)

    repaired_groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for world in worlds:
        repaired_groups.setdefault(repaired_projection(world), []).append(world)
    repaired = sum(1 for items in repaired_groups.values() if len({truth(w) for w in items}) > 1)

    return len(worlds), raw, repaired, raw


def native_deletion_check() -> bool:
    for variant in range(8):
        world = make_world("uv", (ACTIVE, LEGACY), "universal", variant)
        baseline = truth(world)
        clone = make_world("uv", (ACTIVE, LEGACY), "universal", variant)
        clone["native"] = {
            "decision_level": None,
            "backjump_state": None,
            "native_note": None,
        }
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
