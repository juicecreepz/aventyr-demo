from aventyr_ops.config import DATA_DIR
from aventyr_ops.crews.incident_intake import (
    build_incident_intake_crew,
    classify_incident,
)
from aventyr_ops.services.data_loader import load_incident_samples


def test_incident_classifier_assigns_expected_severities():
    samples = load_incident_samples(DATA_DIR / "incident_samples.json")

    results = {sample.sample_id: classify_incident(sample)[0] for sample in samples}

    assert results["INC-SAMPLE-1"].severity == 3
    assert results["INC-SAMPLE-1"].incident_type == "trespass"
    assert results["INC-SAMPLE-2"].severity == 2
    assert results["INC-SAMPLE-3"].severity == 5
    assert "timestamp" in results["INC-SAMPLE-3"].audit_fields
    assert "retention policy depends" in results["INC-SAMPLE-3"].retention_note


def test_incident_intake_crew_objects_are_available():
    crew = build_incident_intake_crew()

    assert len(crew.agents) == 3
    assert crew.agents[0].role == "Intake Agent"

