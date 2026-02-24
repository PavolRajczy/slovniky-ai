from typing import List
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

    def get_operations_for_design_task(self, design_project: DesignProject, current_ontology: Ontology, iteration: DesignIteration, task: DesignTask) -> List[OntologyEditOperation]:
        """
        Performs the given ontology design task.

        Args:
            design_project (DesignProject): The design project containing the iteration.
            current_ontology (Ontology): The current ontology being modified. This ontology should reflect all changes made by previously executed tasks in the same iteration. We cannot work with the original ontology from the design_project as this needs to remain unchanged until the final list of operations for all tasks in the iteration is ready and approved.
            iteration (DesignIteration): The iteration in which the task is to be performed.
            task (DesignTask): The design task to be executed.

        Returns:
            List[OntologyEditOperation]: A list of ontology edit operations resulting from the task.
        """
        ...
        return []  # Placeholder for actual implementation