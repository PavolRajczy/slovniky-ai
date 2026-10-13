"""
Prompt blocks that carry the user's goal and subarea to every agent working on an iteration.
"""
from typing import List, Optional

from design_project.domain import DesignIteration
from ontology.domain import Ontology


def render_iteration_scope(ontology: Optional[Ontology], iteration: DesignIteration) -> str:
    """Goal and subarea blocks for an iteration, or an empty string when the iteration has neither."""
    return render_scope(ontology, iteration.goal, iteration.subareaClassUris)


def render_scope(ontology: Optional[Ontology], goal: Optional[str], subarea_class_uris: Optional[List[str]]) -> str:
    """Goal and subarea blocks for an agent prompt, or an empty string when neither is set."""
    blocks = []
    if goal and goal.strip():
        blocks.append(_render_goal(goal.strip()))
    if subarea_class_uris:
        blocks.append(_render_subarea(ontology, subarea_class_uris))
    return "\n".join(blocks)


def _render_goal(goal: str) -> str:
    return f"""<GOAL_OF_USER>
The user stated this objective for the work: {goal}
Plan and model only what serves this objective.
</GOAL_OF_USER>"""


def _render_subarea(ontology: Optional[Ontology], class_uris: List[str]) -> str:
    lines = [
        "<SUBAREA>",
        "The user restricted the work to the classes below and their immediate neighbourhood "
        "(their attributes and the relationships that start or end in them).",
        "Do not plan, propose, change or delete any other ontology element. "
        "A new class may be introduced only when it is directly related to a subarea class.",
        "Classes:",
    ]
    selected = set(class_uris)
    classes = ontology.classes if ontology else {}
    for uri in class_uris:
        cls = next((c for key, c in classes.items() if str(key) == uri), None)
        if cls is None:
            lines.append(f"- <{uri}> (no longer in the ontology)")
            continue
        lines.append(f'- <{uri}> "{cls.label}"')
        attributes = [
            attribute for attribute in (ontology.attributes.values() if ontology else [])
            if attribute.owningClass is not None and str(attribute.owningClass.uri) == uri
        ]
        for attribute in attributes:
            lines.append(f'    attribute <{attribute.uri}> "{attribute.label}"')

    relationships = [
        relationship for relationship in (ontology.relationships.values() if ontology else [])
        if _class_uri(relationship.sourceClass) in selected or _class_uri(relationship.targetClass) in selected
    ]
    if relationships:
        lines.append("Relationships touching the subarea:")
        for relationship in relationships:
            source = relationship.sourceClass.label if relationship.sourceClass else "?"
            target = relationship.targetClass.label if relationship.targetClass else "?"
            lines.append(f'- <{relationship.uri}> "{relationship.label}": "{source}" -> "{target}"')
    lines.append("</SUBAREA>")
    return "\n".join(lines)


def _class_uri(cls) -> Optional[str]:
    return str(cls.uri) if cls is not None else None
