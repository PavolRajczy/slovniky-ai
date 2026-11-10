"""
Tests for the goal and subarea that scope a design iteration.

Covers validation and stamping in DesignProjectService.suggest_iterations, persistence of both
fields through the project store, and the prompt blocks that carry them to the agents.
"""
import pytest
from rdflib import URIRef

from agents.iteration_scope_prompt import render_iteration_scope, render_scope
from design_project.domain import DesignIteration, DesignIterationStatus, KnowledgeDomainArea
from ontology.domain import Ontology, OntologyAttribute, OntologyClass, OntologyRelationship

from fakes import create_fake_design_project_service

ONTOLOGY_URI = "http://example.org/vehicles#"
VEHICLE_URI = "http://example.org/vehicles#Vehicle"
PERSON_URI = "http://example.org/vehicles#Person"
ROAD_URI = "http://example.org/vehicles#Road"


def create_vehicle_ontology() -> Ontology:
    person = OntologyClass(uri=URIRef(PERSON_URI), label="Person", definition=None, description=None)
    vehicle = OntologyClass(uri=URIRef(VEHICLE_URI), label="Vehicle", definition=None, description=None)
    road = OntologyClass(uri=URIRef(ROAD_URI), label="Road", definition=None, description=None)
    vin = OntologyAttribute(uri=URIRef(f"{ONTOLOGY_URI}vin"), label="VIN", definition=None, description=None, owningClass=vehicle)
    road_name = OntologyAttribute(uri=URIRef(f"{ONTOLOGY_URI}roadName"), label="Road name", definition=None, description=None, owningClass=road)
    owns = OntologyRelationship(uri=URIRef(f"{ONTOLOGY_URI}owns"), label="owns", definition=None, description=None, sourceClass=person, targetClass=vehicle)
    return Ontology(
        uri=URIRef(ONTOLOGY_URI),
        label="Vehicles",
        description=None,
        classes={c.uri: c for c in (person, vehicle, road)},
        attributes={a.uri: a for a in (vin, road_name)},
        relationships={owns.uri: owns},
    )


def create_project_with_area(service):
    service.ontology_service.store_ontology(create_vehicle_ontology())
    project = service.initialize_new_project(project_name="Vehicles", working_ontology_uri=ONTOLOGY_URI)
    area = KnowledgeDomainArea(
        id="area-registration",
        label="Vehicle registration",
        description=None,
        parent=project.modeledKnowledgeDomain,
        keyConcepts=[],
        modelingClasses=[],
        modelingAttributes=[],
        modelingRelationships=[],
        explainingKnowledgeResources=[],
    )
    project.modeledKnowledgeDomain.areas.append(area)
    service.store.store_project(project)
    return project, area


def create_iteration(goal=None, subarea_class_uris=None) -> DesignIteration:
    return DesignIteration(
        id="it-1",
        name="Registration",
        status=DesignIterationStatus.PLANNED,
        specification="Model vehicle registration.",
        finishedTasks=[],
        currentTask=None,
        plannedTasks=[],
        focusedArea=None,
        plannedOperations=None,
        designedOntologyChangesSpecification=None,
        goal=goal,
        subareaClassUris=subarea_class_uris or [],
    )


def test_suggest_iterations_stamps_goal_and_subarea_on_every_iteration(tmp_path):
    service = create_fake_design_project_service(str(tmp_path))
    project, area = create_project_with_area(service)

    iterations = service.suggest_iterations(
        project.id, area.id, 2, "",
        goal="  Model who may register a vehicle  ",
        subarea_class_uris=[f" {VEHICLE_URI} ", PERSON_URI, VEHICLE_URI],
    )

    assert len(iterations) == 2
    for iteration in iterations:
        assert iteration.goal == "Model who may register a vehicle"
        assert iteration.subareaClassUris == [VEHICLE_URI, PERSON_URI]


def test_goal_and_subarea_survive_a_store_round_trip(tmp_path):
    service = create_fake_design_project_service(str(tmp_path))
    project, area = create_project_with_area(service)
    service.suggest_iterations(project.id, area.id, 1, "", goal="Model registration", subarea_class_uris=[VEHICLE_URI])

    reloaded = create_fake_design_project_service(str(tmp_path)).load_project(project.id)

    [iteration] = reloaded.plannedIterations
    assert iteration.goal == "Model registration"
    assert iteration.subareaClassUris == [VEHICLE_URI]


def test_suggest_iterations_without_scope_leaves_iterations_unrestricted(tmp_path):
    service = create_fake_design_project_service(str(tmp_path))
    project, area = create_project_with_area(service)

    [iteration] = service.suggest_iterations(project.id, area.id, 1, "", goal="   ", subarea_class_uris=None)

    assert iteration.goal is None
    assert iteration.subareaClassUris == []


def test_suggest_iterations_rejects_class_outside_the_ontology(tmp_path):
    service = create_fake_design_project_service(str(tmp_path))
    project, area = create_project_with_area(service)
    unknown_uri = "http://example.org/vehicles#Spaceship"

    with pytest.raises(ValueError, match="Spaceship"):
        service.suggest_iterations(project.id, area.id, 1, "", subarea_class_uris=[VEHICLE_URI, unknown_uri])

    assert service.load_project(project.id).plannedIterations == []


def test_render_scope_is_empty_without_goal_and_subarea():
    assert render_scope(create_vehicle_ontology(), None, []) == ""
    assert render_scope(create_vehicle_ontology(), "   ", None) == ""


def test_render_scope_states_the_goal():
    rendered = render_scope(None, "  Model who may register a vehicle ", None)

    assert "<GOAL_OF_USER>" in rendered
    assert "The user stated this objective for the work: Model who may register a vehicle" in rendered
    assert "<SUBAREA>" not in rendered


def test_render_iteration_scope_lists_subarea_classes_with_their_neighbourhood():
    iteration = create_iteration(goal="Model registration", subarea_class_uris=[VEHICLE_URI])

    rendered = render_iteration_scope(create_vehicle_ontology(), iteration)

    assert "<GOAL_OF_USER>" in rendered
    assert f'- <{VEHICLE_URI}> "Vehicle"' in rendered
    assert f'attribute <{ONTOLOGY_URI}vin> "VIN"' in rendered
    assert f'- <{ONTOLOGY_URI}owns> "owns": "Person" -> "Vehicle"' in rendered
    assert "Road" not in rendered


def test_render_scope_marks_subarea_classes_removed_from_the_ontology():
    removed_uri = "http://example.org/vehicles#Trailer"

    rendered = render_scope(create_vehicle_ontology(), None, [removed_uri])

    assert f"- <{removed_uri}> (no longer in the ontology)" in rendered
