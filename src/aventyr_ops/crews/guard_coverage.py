from __future__ import annotations

from crewai import Agent, Crew, Process, Task

from aventyr_ops.models import (
    CrewTraceStep,
    GuardCandidate,
    GuardCoverageResult,
    GuardProfile,
    SiteDemand,
)

NEARBY_CITY_POINTS = {
    "Surrey": {"Surrey", "Burnaby", "Langley", "Coquitlam"},
    "Langley": {"Langley", "Surrey", "Abbotsford"},
    "Coquitlam": {"Coquitlam", "Burnaby", "Surrey"},
}


def build_guard_coverage_crew() -> Crew:
    coverage_agent = Agent(
        role="Coverage Gap Agent",
        goal="Find uncovered site shifts that need dispatcher review.",
        backstory="A coverage assistant focused on shift risk, certifications, and site continuity.",
        llm=None,
    )
    ranking_agent = Agent(
        role="Ranking Agent",
        goal="Rank available guards by certification, proximity, site history, and rotation fairness.",
        backstory="A dispatcher support agent that explains tradeoffs instead of making silent assignments.",
        llm=None,
    )
    summary_agent = Agent(
        role="Dispatcher Summary Agent",
        goal="Prepare a clear top-three candidate list for human assignment.",
        backstory="A human-in-the-loop assistant that keeps final assignment with the dispatcher.",
        llm=None,
    )
    return Crew(
        agents=[coverage_agent, ranking_agent, summary_agent],
        tasks=[
            Task(
                description="Review open site demand for an uncovered shift.",
                expected_output="A shift needing coverage review.",
                agent=coverage_agent,
            ),
            Task(
                description="Rank available guards by fit and fairness.",
                expected_output="Top candidate list with rationale.",
                agent=ranking_agent,
            ),
            Task(
                description="Prepare dispatcher-ready recommendation summary.",
                expected_output="Top three candidates and audit summary.",
                agent=summary_agent,
            ),
        ],
        process=Process.sequential,
        verbose=False,
    )


def rank_guard_coverage(
    shift: SiteDemand,
    guards: list[GuardProfile],
) -> tuple[GuardCoverageResult, list[CrewTraceStep]]:
    candidates: list[GuardCandidate] = []
    for guard in guards:
        if guard.available_date != shift.date:
            continue
        if shift.required_certification not in guard.certifications:
            continue
        candidates.append(score_guard(shift, guard))

    candidates.sort(key=lambda candidate: (-candidate.score, candidate.hourly_rate, candidate.guard_name))
    result = GuardCoverageResult(
        shift_id=shift.shift_id,
        site_name=shift.site_name,
        required_certification=shift.required_certification,
        candidates=candidates[:3],
        audit_summary=(
            f"Ranked {len(candidates)} eligible guards for {shift.site_name}; "
            "dispatcher keeps final assignment control."
        ),
    )
    trace = [
        CrewTraceStep(
            step="1",
            agent_name="Coverage Gap Agent",
            action="Loaded uncovered shift demand.",
            result=f"{shift.shift_id} requires {shift.required_certification}.",
        ),
        CrewTraceStep(
            step="2",
            agent_name="Ranking Agent",
            action="Filtered guards by certification and scored eligible candidates.",
            result=f"{len(candidates)} eligible guards ranked.",
        ),
        CrewTraceStep(
            step="3",
            agent_name="Dispatcher Summary Agent",
            action="Prepared human assignment shortlist.",
            result=f"Top candidate: {result.candidates[0].guard_name if result.candidates else 'None'}",
        ),
    ]
    return result, trace


def score_guard(shift: SiteDemand, guard: GuardProfile) -> GuardCandidate:
    score = 50
    rationale = [f"Has required {shift.required_certification} certification."]

    if guard.prior_site_experience == shift.site_id:
        score += 30
        rationale.append("Prior experience at this site.")

    nearby_cities = NEARBY_CITY_POINTS.get(_city_for_site(shift.site_id), set())
    if guard.home_city in nearby_cities:
        score += 20
        rationale.append(f"Home city {guard.home_city} is close enough for this site.")

    fairness_points = max(0, 20 - guard.rotation_score)
    score += fairness_points
    rationale.append(f"Rotation fairness adds {fairness_points} points.")

    return GuardCandidate(
        guard_id=guard.guard_id,
        guard_name=guard.guard_name,
        score=score,
        rationale=rationale,
        hourly_rate=guard.hourly_rate,
    )


def _city_for_site(site_id: str) -> str:
    if site_id == "LANG-LAY":
        return "Langley"
    if site_id == "COQ-YARD":
        return "Coquitlam"
    return "Surrey"
