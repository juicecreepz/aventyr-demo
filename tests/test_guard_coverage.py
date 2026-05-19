from aventyr_ops.config import DATA_DIR
from aventyr_ops.crews.guard_coverage import (
    build_guard_coverage_crew,
    rank_guard_coverage,
)
from aventyr_ops.services.data_loader import load_guard_pool, load_site_demand


def test_guard_coverage_ranks_certified_candidates():
    shifts = load_site_demand(DATA_DIR / "site_demand.csv")
    guards = load_guard_pool(DATA_DIR / "guard_pool.csv")
    shift = next(item for item in shifts if item.shift_id == "SHIFT-7001")

    result, trace = rank_guard_coverage(shift, guards)

    assert result.required_certification == "OFA1"
    assert len(result.candidates) == 3
    assert result.candidates[0].guard_name == "Maya Singh"
    assert result.candidates[0].score > result.candidates[1].score
    assert "dispatcher keeps final assignment" in result.audit_summary
    assert trace[1].agent_name == "Ranking Agent"


def test_guard_coverage_crew_objects_are_available():
    crew = build_guard_coverage_crew()

    assert len(crew.agents) == 3
    assert crew.agents[1].role == "Ranking Agent"

