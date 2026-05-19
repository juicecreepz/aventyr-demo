from __future__ import annotations

from crewai import Agent, Crew, Process, Task

from aventyr_ops.models import CrewTraceStep, IncidentClassification, IncidentSample


def build_incident_intake_crew() -> Crew:
    intake_agent = Agent(
        role="Intake Agent",
        goal="Capture guard reports from SMS or voice inputs and preserve the original site context.",
        backstory="A monitoring intake assistant built for fast field reports and complete audit trails.",
        llm=None,
    )
    classification_agent = Agent(
        role="Classification Agent",
        goal="Classify incident severity and type without over-escalating nuisance events.",
        backstory="A practical incident reviewer that separates nuisance signals from urgent security events.",
        llm=None,
    )
    routing_agent = Agent(
        role="Routing Agent",
        goal="Route incidents to the right review tier and create audit-ready fields.",
        backstory="A compliance-aware workflow assistant that keeps human dispatch decisions visible.",
        llm=None,
    )
    return Crew(
        agents=[intake_agent, classification_agent, routing_agent],
        tasks=[
            Task(
                description="Receive the site report and preserve source text.",
                expected_output="Normalized incident input.",
                agent=intake_agent,
            ),
            Task(
                description="Classify severity, incident type, and action required.",
                expected_output="Severity tier and incident class.",
                agent=classification_agent,
            ),
            Task(
                description="Route the incident and create audit fields.",
                expected_output="Audit-ready incident record.",
                agent=routing_agent,
            ),
        ],
        process=Process.sequential,
        verbose=False,
    )


def classify_incident(sample: IncidentSample) -> tuple[IncidentClassification, list[CrewTraceStep]]:
    message = sample.message.lower()
    if any(term in message for term in ["active break-in", "weapon", "fire", "medical", "call police"]):
        severity = 5
        incident_type = "emergency_security"
        route = "Immediate escalation"
        action_required = "Call police/site manager and open emergency dispatch protocol."
    elif any(term in message for term in ["individuals", "trespass", "north fence", "after hours"]):
        severity = 3
        incident_type = "trespass"
        route = "Monitoring supervisor review"
        action_required = "Notify site contact, log event, and monitor for repeat activity."
    elif any(term in message for term in ["wind", "animal", "shadow", "tarp"]):
        severity = 2
        incident_type = "nuisance_or_environmental"
        route = "Log only"
        action_required = "Log event and include in weekly nuisance digest."
    else:
        severity = 1
        incident_type = "general_observation"
        route = "Log only"
        action_required = "Log event for operator review."

    classification = IncidentClassification(
        sample_id=sample.sample_id,
        site_id=sample.site_id,
        site_name=sample.site_name,
        severity=severity,
        incident_type=incident_type,
        route=route,
        action_required=action_required,
        audit_fields={
            "timestamp": sample.reported_at.isoformat(),
            "signal_type": incident_type,
            "operator_action": action_required,
            "response_tier": str(severity),
            "dispatch_outcome": route,
        },
        retention_note=(
            "Demo record includes fields expected in an audit trail for alarm handling; "
            "final retention policy depends on Aventyr's compliance binder."
        ),
    )
    trace = [
        CrewTraceStep(
            step="1",
            agent_name="Intake Agent",
            action="Received synthetic guard report.",
            result=f"{sample.sample_id} from {sample.site_name}",
        ),
        CrewTraceStep(
            step="2",
            agent_name="Classification Agent",
            action="Classified severity and incident type.",
            result=f"Severity {severity}: {incident_type}",
        ),
        CrewTraceStep(
            step="3",
            agent_name="Routing Agent",
            action="Prepared route and audit fields.",
            result=route,
        ),
    ]
    return classification, trace
