from typing import List
from design_project.domain import DesignIteration, DesignIterationStatus, DesignProject, KnowledgeDomainArea
from ontology.domain import Ontology


class IterationSuggesterAgent:
    """
    An agent that suggests iterations for a design project based on user input and project context.
    """

    def __init__(self, model_name: str):
        ...

    def suggest_iterations(self, design_project: DesignProject, focused_area: KnowledgeDomainArea, k: int, user_instruction: str) -> List[DesignIteration]:
        """
        Suggests new design iterations for the given design project.
        If the user instruction is specified, the agent suggestsions are guided by it.

        Args:
            design_project (DesignProject): The design project to suggest iterations for.
            focused_area (KnowledgeDomainArea): The knowledge domain area to focus the suggestions on.
            k (int): The number of iterations to suggest.
            user_instruction (str): Instructions from the user to guide the suggestions.

        Returns:
            List[DesignIteration]: A list of suggested design iterations.
        """
        # Implementation of the iteration suggestion logic goes here
        ...

class IterationSuggesterAgentFake(IterationSuggesterAgent):
    """
    A primitive implementation of IterationSuggesterAgent that returns k fake iterations.
    """

    def __init__(self, model_name: str = "fake"):
        self.model_name = model_name

    def suggest_iterations(self, design_project: DesignProject, focused_area: KnowledgeDomainArea, k: int, user_instruction: str) -> List[DesignIteration]:
        return [
            DesignIteration(
                id=f"fake-{i+1}",
                name=f"Fake Iteration {i+1}",
                status=DesignIterationStatus.PLANNED,
                specification=f"This is a fake iteration {i+1} in {design_project.name} design project to improve {design_project.designedOntology.label} ontology in a knowledge domain area {focused_area.label} considering the user instruction: {user_instruction}.",
                finishedTasks=[],
                currentTask=None,
                plannedTasks=[],
                focusedArea=focused_area,
                plannedOperations=None,  # No operations yet - will be generated during prepare phase
                designedOntologyChangesSpecification=None
            )
            for i in range(k)
        ]