from __future__ import annotations

import unittest

from research.run_performance_envelope import GRAPH_PACKAGES, run


class PerformanceEnvelopeTests(unittest.TestCase):
    def test_bounded_envelope_is_reproducible_and_fails_closed(self) -> None:
        summary = run()
        graph = summary["dependency_graph"]
        limits = summary["configured_limits"]

        self.assertEqual(graph["packages"], GRAPH_PACKAGES)
        self.assertEqual(graph["dependency_edges"], GRAPH_PACKAGES - 1)
        self.assertEqual(graph["status"], "SAT")
        self.assertEqual(limits["max_trace_bytes"], summary["near_limit_payload_bytes"])
        self.assertEqual(limits["limit_exhaustion_result"], "evaluation_search_limit")
        self.assertTrue(str(summary["resource_limit_behavior"]).startswith("PASS:"))
        self.assertEqual(
            summary["scope"],
            "local sample only; not a throughput or latency guarantee",
        )


if __name__ == "__main__":
    unittest.main()
