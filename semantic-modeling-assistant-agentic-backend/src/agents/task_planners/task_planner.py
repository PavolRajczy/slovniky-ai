from typing import List
from design_project.domain import DesignIteration, DesignProject, DesignTask, DesignTaskPattern, DesignTaskCategory, DesignTaskStatus
from knowledge_base.domain import KnowledgeDocumentElement


class TaskPlannerAgent:
    """
    An agent that plans tasks for design iterations based on project context and iteration specifications.
    """

    def __init__(self, model_name: str):
        ...

    def build_iteration_plan(self, design_project: DesignProject, iteration: DesignIteration, user_instruction: str = "") -> List[DesignTask]:
        """
        Creates an initial plan for a design iteration by generating planned tasks.
        This method works with iterations that have no or empty finishedTasks, currentTask, and plannedTasks.
        If the user instruction is specified, the agent planning is guided by it.

        Args:
            design_project (DesignProject): The design project containing the iteration.
            iteration (DesignIteration): The iteration to create a plan for.
            user_instruction (str): Instructions from the user to guide the planning.

        Returns:
            List[DesignTask]: A list of planned design tasks for the iteration.
        """
        # Implementation of the initial iteration planning logic goes here
        ...

    def update_iteration_plan(self, design_project: DesignProject, iteration: DesignIteration, user_instruction: str = "") -> List[DesignTask]:
        """
        Updates the plan for a design iteration based on current project context.
        This method works with iterations that have non-empty plannedTasks, may have finishedTasks,
        and may have a currentTask.
        If the user instruction is specified, the agent planning update is guided by it.

        Args:
            design_project (DesignProject): The design project containing the iteration.
            iteration (DesignIteration): The iteration to update the plan for.
            user_instruction (str): Instructions from the user to guide the planning update.

        Returns:
            List[DesignTask]: An updated list of planned design tasks for the iteration.
        """
        # Implementation of the iteration plan update logic goes here
        ...