"""Reusable finite semantic solver and minimal-core engine."""

__all__ = [
    "CoreResult",
    "CoreVerificationResult",
    "SemanticProblem",
    "SolveResult",
    "SolveStatus",
    "minimal_unsat_core",
    "solve",
    "verify_unsat_core",
]


def __getattr__(name: str):
    if name == "SemanticProblem":
        from .problem import SemanticProblem
        return SemanticProblem
    if name in {"SolveResult", "SolveStatus", "solve"}:
        from .solver import SolveResult, SolveStatus, solve
        return {"SolveResult": SolveResult, "SolveStatus": SolveStatus, "solve": solve}[name]
    if name in {"CoreResult", "CoreVerificationResult", "minimal_unsat_core", "verify_unsat_core"}:
        from .core import CoreResult, CoreVerificationResult, minimal_unsat_core, verify_unsat_core
        return {
            "CoreResult": CoreResult,
            "CoreVerificationResult": CoreVerificationResult,
            "minimal_unsat_core": minimal_unsat_core,
            "verify_unsat_core": verify_unsat_core,
        }[name]
    raise AttributeError(name)
