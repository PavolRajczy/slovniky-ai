from typing import List, Optional
from design_project.domain import DesignIteration, DesignProject, DesignTask
from ontology.domain import Ontology
from ontology.edit_operations import OntologyEditOperation

class ModelerAgent:
    """
    An agent that accepts a given modeling task to model ontology elements of a specified type (e.g., classes, attributes, relationships).
    It outputs a sequence of one or more ontology edit operations that can be applied to the designed ontology in the design project.
    """

    def __init__(self, model_name: str):
        ...

    def get_operations_for_design_task(self, design_project: DesignProject, current_ontology: Ontology, iteration: DesignIteration, task: DesignTask, project_guidance_text: Optional[str] = None) -> List[OntologyEditOperation]:
        """
        Performs the given ontology design task.

        Args:
            design_project (DesignProject): The design project containing the iteration.
            current_ontology (Ontology): The finalized designed ontology. This must not include unreviewed proposals from other tasks; those stay pending until the user finalizes.
            iteration (DesignIteration): The iteration in which the task is to be performed.
            task (DesignTask): The design task to be executed.
            project_guidance_text (str, optional): Project-scoped human-in-the-loop guidance to inject into the prompt.

        Returns:
            List[OntologyEditOperation]: A list of ontology edit operations resulting from the task.
        """
        ...
        return []  # Placeholder for actual implementation

    def get_operations_from_instruction(self, design_project: DesignProject, current_ontology: Ontology, user_instruction: str) -> List[OntologyEditOperation]:
        """
        Generates ontology edit operations from a free-form user instruction (human in the loop).
        The user describes desired changes (e.g. rename a class, change a relationship); the model outputs the minimal set of create/update/delete operations.

        Args:
            design_project (DesignProject): The design project (for ontology base URI and context).
            current_ontology (Ontology): The current ontology to modify.
            user_instruction (str): The user's instruction describing the desired changes.

        Returns:
            List[OntologyEditOperation]: A list of ontology edit operations that fulfill the instruction.
        """
        ...
        return []  # Placeholder for actual implementation