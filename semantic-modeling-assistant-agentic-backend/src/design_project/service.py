from typing import List, Optional
import uuid
import copy

from agents.knowledge_domain_area_analyzers.knowledge_domain_area_analyzer import KnowledgeDomainAreaAnalyzerAgent
from agents.iteration_suggesters.iteration_suggester import IterationSuggesterAgent
from agents.modelers.modeler import ModelerAgent
from agents.task_planners.task_planner import TaskPlannerAgent

from design_project.domain import DesignIteration, DesignProject, DesignTask, DesignTaskPattern, KnowledgeDomain, KnowledgeDomainArea, DesignTaskStatus, DesignIterationStatus
from design_project.design_task_patterns_factory import DesignTaskPatternsFactory_Basic
from design_project.project_guidance_service import ProjectGuidanceService
from design_project.store import DesignProjectStore
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from knowledge_base.service import KnowledgeBaseService

from knowledge_base.store import KnowledgeDocumentLoader
from ontology.domain import Ontology
from ontology.edit_operation_handlers import CreatedElementExistsError, DeletedElementNotExistsError, ReferrencedElementNotExistsError, UpdatedElementNotExistsError
from ontology.edit_operations import OperationType
from ontology.service import OntologyService
from ontology.edit_operations import OntologyEditOperation


class DesignProjectService:
    """
    A service for managing design projects.
    """
    def __init__(self, store: DesignProjectStore, knowledge_base_service: KnowledgeBaseService, ontology_service: OntologyService, knowledge_domain_area_analyzer_agent: KnowledgeDomainAreaAnalyzerAgent, iteration_suggester_agent: IterationSuggesterAgent, task_planner_agent: TaskPlannerAgent, modeler_agent: ModelerAgent, guidance_service: Optional[ProjectGuidanceService] = None):
        """
        Initializes a service for managing design projects.

        Args:
            store (DesignProjectStore): The store for persisting design projects.
            knowledge_base_service (KnowledgeBaseService): The service for managing knowledge base.
            ontology_service (OntologyService): The service for managing ontologies.
            knowledge_domain_area_analyzer_agent (KnowledgeDomainAreaAnalyzerAgent): The agent for analyzing knowledge domain areas.
            iteration_suggester_agent (IterationSuggesterAgent): The agent for suggesting design iterations.
            task_planner_agent (TaskPlannerAgent): The agent for planning design tasks.
            modeler_agent (ModelerAgent): The agent for modeling ontology elements.
            guidance_service (ProjectGuidanceService, optional): Service for project-scoped human-in-the-loop guidance. If set, guidance items are injected into agent prompts.
        """
        self.store = store
        self.knowledge_base_service = knowledge_base_service
        self.ontology_service = ontology_service
        self.guidance_service = guidance_service

        self.iteration_suggester_agent = iteration_suggester_agent
        self.knowledge_domain_area_analyzer_agent = knowledge_domain_area_analyzer_agent
        self.task_planner_agent = task_planner_agent
        self.modeler_agent = modeler_agent

        # Initialize the design task patterns factory to be used to get design task patterns.
        self.design_task_patterns_factory = DesignTaskPatternsFactory_Basic()

    def _effective_user_instruction(self, project_id: str, user_instruction: str) -> str:
        """Combine project guidance (if any) with the per-request user_instruction for agent prompts."""
        if self.guidance_service is None:
            return user_instruction or ""
        guidance = self.guidance_service.get_guidance_text_for_prompt(project_id)
        if not guidance:
            return user_instruction or ""
        if not (user_instruction or "").strip():
            return guidance
        return guidance + "\n\n" + (user_instruction or "").strip()

    def _rollback_iteration(self, project: DesignProject, iteration: DesignIteration, ontology_backup) -> None:
        """
        Rollback the iteration and ontology to their state before the iteration started.
        This method restores the ontology from backup and resets all task states.

        Args:
            project (DesignProject): The project containing the iteration.
            iteration (DesignIteration): The iteration to rollback.
            ontology_backup: The deep copy backup of the ontology before iteration started.
        """
        print(f"Rolling back iteration {iteration.id}...")

        # Restore the ontology from backup by clearing current state and copying from backup
        project.designedOntology.classes.clear()
        project.designedOntology.attributes.clear()
        project.designedOntology.relationships.clear()
        
        project.designedOntology.classes.update(ontology_backup.classes)
        project.designedOntology.attributes.update(ontology_backup.attributes)
        project.designedOntology.relationships.update(ontology_backup.relationships)
        
        # Also restore the basic ontology metadata in case it was modified
        project.designedOntology.uri = ontology_backup.uri
        project.designedOntology.label = ontology_backup.label
        project.designedOntology.description = ontology_backup.description

        # Reset all performed tasks back to planned state in correct order
        # Collect all tasks that need to be restored to planned state in original order
        tasks_to_restore = []
        
        # Add finished tasks in their original order (first task finished was first in original plan)
        tasks_to_restore.extend(iteration.finishedTasks)
        
        # Add current task if it exists (it comes after finished tasks in original order)
        if iteration.currentTask:
            tasks_to_restore.append(iteration.currentTask)
            iteration.currentTask = None

        # Reset all task statuses to planned
        for task in tasks_to_restore:
            task.status = DesignTaskStatus.PLANNED

        # Restore tasks to planned list by prepending them in reverse order
        # This ensures original order: if we had [T1,T2,T3] to restore and [T4,T5] remaining,
        # we prepend T3, then T2, then T1 to get [T1,T2,T3,T4,T5]
        for task in reversed(tasks_to_restore):
            iteration.plannedTasks.insert(0, task)
        
        iteration.finishedTasks.clear()

        # Clear any stored operations
        iteration.plannedOperations = None

        # Status transition: Any status -> PLANNED (if no tasks) or TASKS_PLANNED (if tasks exist)
        # Location transition: currentIteration -> plannedIterations
        if iteration.plannedTasks:
            iteration.status = DesignIterationStatus.TASKS_PLANNED
        else:
            iteration.status = DesignIterationStatus.PLANNED

        # Move iteration back to planned iterations
        project.currentIteration = None
        project.plannedIterations.insert(0, iteration)

        print(f"... iteration {iteration.id} rolled back successfully")

    def _process_ontology_element_references(self, project: DesignProject, operation: OntologyEditOperation, ontology_element) -> None:
        """
        Process the references in an ontology edit operation by retrieving knowledge document elements
        and updating their respective ontology element lists.

        Args:
            project (DesignProject): The project containing the knowledge base.
            operation (OntologyEditOperation): The operation containing the references.
            ontology_element: The ontology element that was created or updated.
        """
        # Process definition_references
        if hasattr(operation, 'definition_references') and operation.definition_references:
            for ref_id in operation.definition_references:
                try:
                    knowledge_element = self.knowledge_base_service.get_knowledge_document_element(ref_id)
                    if ontology_element not in knowledge_element.definedOntologyElements:
                        knowledge_element.definedOntologyElements.append(ontology_element)
                except ValueError as e:
                    print(f"Warning: Could not find knowledge document element for definition reference {ref_id}: {e}")

        # Process specification_references  
        if hasattr(operation, 'specification_references') and operation.specification_references:
            for ref_id in operation.specification_references:
                try:
                    knowledge_element = self.knowledge_base_service.get_knowledge_document_element(ref_id)
                    if ontology_element not in knowledge_element.specifiedOntologyElements:
                        knowledge_element.specifiedOntologyElements.append(ontology_element)
                except ValueError as e:
                    print(f"Warning: Could not find knowledge document element for specification reference {ref_id}: {e}")

        # Process references
        if hasattr(operation, 'references') and operation.references:
            for ref_id in operation.references:
                try:
                    knowledge_element = self.knowledge_base_service.get_knowledge_document_element(ref_id)
                    if ontology_element not in knowledge_element.referencedOntologyElements:
                        knowledge_element.referencedOntologyElements.append(ontology_element)
                except ValueError as e:
                    print(f"Warning: Could not find knowledge document element for reference {ref_id}: {e}")

    def _print_edit_operation_result(self, operation: OntologyEditOperation, element) -> None:
        """
        Prints information about the element returned by an edit operation,
        distinguishing the type of the created element and operation type.

        Args:
            operation (OntologyEditOperation): The applied operation.
            element: The ontology element that was returned by the operation.
        """
        operation_type_str = operation.operation_type.value if hasattr(operation, 'operation_type') else "unknown"
        element_type = type(element).__name__ if element else "None"
        
        if element:
            element_uri = getattr(element, 'uri', 'N/A')
            element_label = getattr(element, 'label', 'N/A')
            kind_str = f" ({getattr(element, 'kind')})" if hasattr(element, 'kind') and getattr(element, 'kind') else ""
            print(f"  → {operation_type_str.upper()} operation completed: {element_type}{kind_str}  '{element_label}' ({element_uri})")
            if element_type == "OntologyClass":
                if hasattr(element, 'generalizations') and element.generalizations:
                    gen_labels = [f"'{gen.label}' ({gen.uri})" for gen in element.generalizations]
                    print(f"     - Generalizations: {', '.join(gen_labels)}")
                if hasattr(element, 'specializations') and element.specializations:
                    spec_labels = [f"'{spec.label}' ({spec.uri})" for spec in element.specializations]
                    print(f"     - Specializations: {', '.join(spec_labels)}")
            if element_type == "OntologyAttribute":
                owning_class = getattr(element, 'owningClass', None)
                if owning_class:
                    print(f"     - Owning class: '{owning_class.label}' ({owning_class.uri})")
                else:
                    print(f"     - Owning class: N/A")
            if element_type == "OntologyRelationship":
                source_class = getattr(element, 'sourceClass', None)
                target_class = getattr(element, 'targetClass', None)
                if source_class:
                    print(f"     - Source class: '{source_class.label}' ({source_class.uri})")
                else:
                    print(f"     - Source class: N/A")
                if target_class:
                    print(f"     - Target class: '{target_class.label}' ({target_class.uri})")
                else:
                    print(f"     - Target class: N/A")
            
        else:
            print(f"  → {operation_type_str.upper()} operation completed: No element returned")

    def generate_operations_from_instruction(self, project_id: str, user_instruction: str) -> List[OntologyEditOperation]:
        """
        Generates ontology edit operations from a free-form user instruction (human in the loop).
        Loads the project, gets the current designed ontology, and asks the modeler to produce operations.

        Args:
            project_id (str): The ID of the project.
            user_instruction (str): The user's instruction describing the desired ontology changes.

        Returns:
            List[OntologyEditOperation]: The list of proposed edit operations.
        """
        project = self.load_project(project_id)
        effective = self._effective_user_instruction(project_id, user_instruction)
        return self.modeler_agent.get_operations_from_instruction(
            design_project=project,
            current_ontology=project.designedOntology,
            user_instruction=effective,
        )

    def apply_operations_to_project_ontology(self, project_id: str, operations: List[OntologyEditOperation]) -> Ontology:
        """
        Applies the given ontology edit operations directly to the project's designed ontology,
        saves the project, and persists the ontology. Does not use iteration state.

        Args:
            project_id (str): The ID of the project.
            operations (List[OntologyEditOperation]): The operations to apply.

        Returns:
            Ontology: The updated ontology.
        """
        project = self.load_project(project_id)
        self._apply_operations_to_ontology(project.designedOntology, operations, project)
        self.store.store_project(project)
        self.ontology_service.store_ontology(project.designedOntology)
        return project.designedOntology

    def load_project(self, project_id: str) -> DesignProject:
        """
        Loads an existing design project by its ID.

        Args:
            project_id (str): The ID of the project to load.

        Returns:
            DesignProject: The loaded design project.
        """
        project = self.store.load_project(project_id)
        legal_knowledge_base =  self.knowledge_base_service.load_legal_knowledge_documents([doc.id for doc in project.legalKnowledgeBase])
        expert_knowledge_base = self.knowledge_base_service.load_expert_knowledge_documents([doc.id for doc in project.expertKnowledgeBase])
        self.store.set_project_knowledge(project, legal_knowledge_base, expert_knowledge_base)
        return project

    def list_all_projects(self) -> List[DesignProject]:
        """
        Lists all available design projects with their basic metadata.
        
        Note: This method loads projects without fully loading their knowledge bases,
        so the knowledge documents will be placeholder objects with only IDs.
        Use load_project() to get a fully loaded project.

        Returns:
            List[DesignProject]: List of all design projects.
        """
        return self.store.list_all_projects()

    def initialize_new_project(self, project_name: str, working_ontology_uri: str, knowledge_domain_name: str = "", knowledge_domain_description: str = "") -> DesignProject:
        """
        Initializes a new design project with empty knowledge base.

        Args:
            project_name (str): The name of the new project.
            working_ontology_uri (str): The URI of the ontology to be managed in the project.
            knowledge_domain_name (str, optional): The name of the knowledge domain the project will focus on.
            knowledge_domain_description (str, optional): A description of the knowledge domain the project will focus on.

        Returns:
            DesignProject: The initialized design project with empty knowledge base and no domain areas.
        """

        if not knowledge_domain_name:
            knowledge_domain_name = f"Domain of {project_name}"

        knowledge_domain = KnowledgeDomain(
            label=knowledge_domain_name,
            description=knowledge_domain_description,
            areas=[]  # Empty - will be generated later
        )

        working_ontology = self.ontology_service.load_ontology(working_ontology_uri)

        factory_id = self.design_task_patterns_factory.get_factory_id()
        
        project = DesignProject(
            id=str(uuid.uuid4()),
            name=project_name,
            finishedIterations=[],
            currentIteration=None,
            plannedIterations=[],
            patterns=self.design_task_patterns_factory.get_design_task_patterns(),
            patternsFactoryId=factory_id,
            legalKnowledgeBase=[],  # Empty - will be added later
            expertKnowledgeBase=[],  # Empty - will be added later
            keyKnowledgeDocument=None,  # Will be set later
            modeledKnowledgeDomain=knowledge_domain,
            designedOntology=working_ontology
        )

        self.store.store_project(project)
        return project

    def set_key_knowledge_document(self, project_id: str, document_id: str) -> DesignProject:
        """
        Sets the key knowledge document for domain area generation.
        Validates that the document exists in the project's knowledge base.

        Args:
            project_id (str): The ID of the project.
            document_id (str): The ID of the document to set as key document.

        Returns:
            DesignProject: The updated design project.

        Raises:
            ValueError: If document not found in project's knowledge base.
        """
        project = self.load_project(project_id)
        
        # Find document in combined knowledge base
        key_doc = None
        for doc in project.legalKnowledgeBase + project.expertKnowledgeBase:
            if doc.id == document_id:
                key_doc = doc
                break
        
        if key_doc is None:
            raise ValueError(f"Document '{document_id}' not found in project knowledge base. Please add the document to the knowledge base first.")
        
        project.keyKnowledgeDocument = key_doc
        self.store.store_project(project)
        
        print(f"Set key knowledge document: {key_doc.title}")
        
        return project

    def get_design_task_patterns(self, project_id: str) -> List[DesignTaskPattern]:
        """
        Gets the list of design task patterns for a project.

        Args:
            project_id (str): The ID of the project.

        Returns:
            List[DesignTaskPattern]: The list of design task patterns used in the project.
        """
        project = self.load_project(project_id)
        return project.patterns

    def generate_domain_areas(self, project_id: str, user_instruction: str = "") -> List[KnowledgeDomainArea]:
        """
        Generates domain areas using AI based on the key knowledge document.
        Requires that keyKnowledgeDocument is already set.

        Args:
            project_id (str): The ID of the project.
            user_instruction (str, optional): Optional user guidance for area generation.

        Returns:
            List[KnowledgeDomainArea]: The generated domain areas.

        Raises:
            ValueError: If key knowledge document not set or knowledge domain not initialized.
        """
        project = self.load_project(project_id)
        
        if project.keyKnowledgeDocument is None:
            raise ValueError("Cannot generate domain areas: key knowledge document not set. Please set a key document first using the set_key_knowledge_document operation.")
        
        if project.modeledKnowledgeDomain is None:
            raise ValueError("Cannot generate domain areas: knowledge domain not initialized.")
        
        print(f"Asking the agent to identify knowledge domain areas in the knowledge domain '{project.modeledKnowledgeDomain.label}' using the key knowledge document '{project.keyKnowledgeDocument.title}' ...")
        
        effective = self._effective_user_instruction(project_id, user_instruction)
        # Call AI agent to identify domain areas
        areas = self.knowledge_domain_area_analyzer_agent.identify_domain_areas(
            knowledge_domain=project.modeledKnowledgeDomain,
            knowledge_document=project.keyKnowledgeDocument,
            user_instruction=effective,
        )
        
        project.modeledKnowledgeDomain.areas = areas
        self.store.store_project(project)
        
        print(f"... identified {len(areas)} knowledge domain areas.")
        
        return areas

    def reidentify_domain_areas(self, project_id: str, user_instruction: str = "") -> List[KnowledgeDomainArea]:
        """
        Re-identifies domain areas using AI based on the key knowledge document and existing areas.
        The AI considers the existing areas and applies the user's instruction to modify them.
        Requires that keyKnowledgeDocument is already set.

        Args:
            project_id (str): The ID of the project.
            user_instruction (str): User guidance for area reidentification.

        Returns:
            List[KnowledgeDomainArea]: The reidentified domain areas.

        Raises:
            ValueError: If key knowledge document not set or knowledge domain not initialized.
        """
        project = self.load_project(project_id)
        
        if project.keyKnowledgeDocument is None:
            raise ValueError("Cannot reidentify domain areas: key knowledge document not set. Please set a key document first using the set_key_knowledge_document operation.")
        
        if project.modeledKnowledgeDomain is None:
            raise ValueError("Cannot reidentify domain areas: knowledge domain not initialized.")
        
        print(f"Asking the agent to reidentify knowledge domain areas in the knowledge domain '{project.modeledKnowledgeDomain.label}' using the key knowledge document '{project.keyKnowledgeDocument.title}' and considering existing areas ...")
        
        effective = self._effective_user_instruction(project_id, user_instruction)
        # Call AI agent to reidentify domain areas, considering existing areas
        areas = self.knowledge_domain_area_analyzer_agent.identify_domain_areas(
            knowledge_domain=project.modeledKnowledgeDomain,
            knowledge_document=project.keyKnowledgeDocument,
            consider_existing_areas=True,
            user_instruction=effective,
        )
        
        project.modeledKnowledgeDomain.areas = areas
        self.store.store_project(project)
        
        print(f"... reidentified {len(areas)} knowledge domain areas.")
        
        return areas

    def suggest_iterations(self, project_id: str, focused_area_id: str, k: int, user_instruction: str) -> List[DesignIteration]:
        """
        Suggests new design iterations for the given project focusing on the given knowledge domain area.
        If the user instruction is specified, the suggestions are guided by it.

        Args:
            project_id (str): The ID of the project to suggest iterations for.
            focused_area_id (str): The ID of the knowledge domain area to focus the suggestions on.
            k (int): The number of suggestions to return.
            user_instruction (str): Instructions from the user to guide the suggestions.

        Returns:
            List[DesignIteration]: A list of k suggested design iterations.
        """
        project = self.store.load_project(project_id)
        focused_area = next((area for area in project.modeledKnowledgeDomain.areas if area.id == focused_area_id), None)
        if not focused_area:
            raise ValueError(f"Focused area not found: {focused_area_id}")

        print(f"Suggesting {k} iterations for project {project.name} and knowledge domain area {focused_area.label} ...")

        effective = self._effective_user_instruction(project_id, user_instruction)
        iterations = self.iteration_suggester_agent.suggest_iterations(project, focused_area, k, effective)
        project.plannedIterations.extend(iterations)
        self.store.store_project(project)
        print(f"... suggested {len(iterations)} iterations.")

        return iterations
    
    def initialize_iteration_tasks(self, project_id: str, iteration_id: str, user_instruction: str) -> List[DesignTask]:
        """
        Initializes the planned tasks for a design iteration that has no planned, current or finished tasks.
        If the user instruction is specified, the task planning is guided by it.

        If the iteration already has planned, current or finished tasks, use update_iteration_tasks.

        Args:
            project_id (str): The ID of the project containing the iteration.
            iteration_id (str): The ID of the iteration to initialize tasks for.
            user_instruction (str): Instructions from the user to guide the planning.

        Returns:
            List[DesignTask]: A list of planned design tasks for the iteration.
        """
        project = self.store.load_project(project_id)

        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if not iteration:
            raise ValueError(f"Iteration not found in planned iterations: {iteration_id}")

        print(f"Initializing tasks for iteration {iteration.id}...")

        effective = self._effective_user_instruction(project_id, user_instruction)
        iteration.plannedTasks = self.task_planner_agent.build_iteration_plan(project, iteration, effective)

        # Status transition: PLANNED -> TASKS_PLANNED
        # Location: remains in plannedIterations
        iteration.status = DesignIterationStatus.TASKS_PLANNED

        self.store.store_project(project)

        print(f"Initialized {len(iteration.plannedTasks)} tasks for iteration {iteration.id}")

        return iteration.plannedTasks
    
    def update_iteration_tasks(self, project_id: str, iteration_id: str, user_instruction: str) -> List[DesignTask]:
        """
        Updates the planned tasks for a design iteration that already has planned tasks.
        If the user instruction is specified, the task planning update is guided by it.

        If the iteration has no planned tasks, use initialize_iteration_tasks.

        Args:
            project_id (str): The ID of the project containing the iteration.
            iteration_id (str): The ID of the iteration to update tasks for.
            user_instruction (str): Instructions from the user to guide the planning update.

        Returns:
            List[DesignTask]: An updated list of planned design tasks for the iteration.
        """
        project = self.store.load_project(project_id)

        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if not iteration:
            raise ValueError(f"Iteration not found: {iteration_id}")

        effective = self._effective_user_instruction(project_id, user_instruction)
        iteration.plannedTasks = self.task_planner_agent.update_iteration_plan(project, iteration, effective)

        self.store.store_project(project)

        print(f"Updated to {len(iteration.plannedTasks)} tasks for iteration {iteration.id}")

        return iteration.plannedTasks

    def prepare_planned_iteration(self, project_id: str, iteration_id: str):
        """
        Prepares a planned design iteration by generating operations for all tasks.
        The iteration must have at least one planned task.
        The iteration can have finished tasks. These tasks will not be repeated nor changed.
        
        This method generates operations and stores them in the iteration for review and traceability.
        The operations are returned for the client to review and potentially modify before applying.

        Args:
            project_id (str): The ID of the project to iterate on.
            iteration_id (str): The ID of the iteration to prepare.
            
        Returns:
            List[IdentifiedOperation]: The list of identified operations to be applied.
        """
        project = self.store.load_project(project_id)
        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if not iteration:
            raise ValueError(f"Iteration not found in planned iterations: {iteration_id}")
        if iteration.status not in [DesignIterationStatus.PLANNED, DesignIterationStatus.TASKS_PLANNED]:
            raise ValueError(f"Iteration must be in PLANNED or TASKS_PLANNED status, but is: {iteration.status}")
        
        if not iteration.plannedTasks or len(iteration.plannedTasks) == 0:
            raise ValueError(f"Iteration has no planned tasks: {iteration_id}")

        # Status transition: PLANNED/TASKS_PLANNED -> GENERATING_OPERATIONS
        # Location transition: plannedIterations -> currentIteration
        project.plannedIterations.remove(iteration)
        project.currentIteration = iteration
        iteration.status = DesignIterationStatus.GENERATING_OPERATIONS

        print(f"Preparing iteration {iteration.id}...")
        
        # Create a deep copy of the ontology for fake updates during task processing
        print(f"Creating ontology copy for fake updates during task processing...")
        current_ontology = copy.deepcopy(project.designedOntology)
        print(f"... ontology copy created")
        
        all_operations = []
        
        try:
            import uuid
            from design_project.domain import IdentifiedOperation
            
            plannedTasksToProcess = list(iteration.plannedTasks)  # Copy of the original planned tasks to process
            iteration.plannedTasks.clear()
            project_guidance = self.guidance_service.get_guidance_text_for_prompt(project_id) if self.guidance_service else None
            while plannedTasksToProcess and len(plannedTasksToProcess) > 0:
                task = plannedTasksToProcess.pop(0)
                iteration.currentTask = task

                print(f" Getting operations for task {task.id} \"{task.specification}\" ...")

                # Status transition for task: PLANNED -> GENERATING_OPERATIONS
                task.status = DesignTaskStatus.GENERATING_OPERATIONS

                try:
                    # Provide the current ontology state (with fake updates from previous tasks)
                    edit_operations = self.modeler_agent.get_operations_for_design_task(project, current_ontology, iteration, task, project_guidance_text=project_guidance)
                    
                    # Wrap each operation with identity
                    for operation in edit_operations:
                        identified_op = IdentifiedOperation(
                            id=str(uuid.uuid4()),
                            operation=operation,
                            created_from_task_id=task.id
                        )
                        all_operations.append(identified_op)
                    
                    print(f"  Generated {len(edit_operations)} operations for task")
                    
                    # Apply operations to the fake ontology copy (without processing references)
                    if edit_operations:
                        self._apply_operations_to_ontology(current_ontology, edit_operations)
                        print(f"  ... applied {len(edit_operations)} operations to fake ontology")
                        
                except Exception as e:
                    print(f"  Error while generating operations for task {task.id}: {e}")
                    # Rollback the iteration state
                    self._rollback_iteration_state(project, iteration)
                    self.store.store_project(project)
                    raise e

                # Status transition for task: GENERATING_OPERATIONS -> OPERATIONS_GENERATED
                task.status = DesignTaskStatus.OPERATIONS_GENERATED
                iteration.plannedTasks.append(task)
                iteration.currentTask = None

                print(f" ... generated operations for task {task.id}")

            # Status transition: GENERATING_OPERATIONS -> OPERATIONS_GENERATED
            # Location: remains in currentIteration
            iteration.status = DesignIterationStatus.OPERATIONS_GENERATED
            
            # Store the operations in the iteration for traceability and review
            iteration.plannedOperations = all_operations
            
            self.store.store_project(project)
            
            print(f"... prepared iteration {iteration.id} with {len(all_operations)} total operations")
            return all_operations

        except Exception as e:
            # If any unexpected exception occurs at the iteration level, rollback
            print(f"Unexpected error during iteration preparation {iteration.id}: {e}")
            self._rollback_iteration_state(project, iteration)
            self.store.store_project(project)
            raise e

    def _rollback_iteration_state(self, project: DesignProject, iteration: DesignIteration) -> None:
        """
        Rollback the iteration state without touching the ontology.
        This method resets task states and moves the iteration back to planned.

        Args:
            project (DesignProject): The project containing the iteration.
            iteration (DesignIteration): The iteration to rollback.
        """
        print(f"Rolling back iteration state {iteration.id}...")

        # Reset all performed tasks back to planned state in correct order
        # Collect all tasks that need to be restored to planned state in original order
        tasks_to_restore = []
        
        # Add finished tasks in their original order (first task finished was first in original plan)
        tasks_to_restore.extend(iteration.finishedTasks)
        
        # Add current task if it exists (it comes after finished tasks in original order)
        if iteration.currentTask:
            tasks_to_restore.append(iteration.currentTask)
            iteration.currentTask = None

        # Reset all task statuses to planned
        for task in tasks_to_restore:
            task.status = DesignTaskStatus.PLANNED

        for task in iteration.plannedTasks:
            task.status = DesignTaskStatus.PLANNED

        # Restore tasks to planned list by prepending them in reverse order
        # This ensures original order: if we had [T1,T2,T3] to restore and [T4,T5] remaining,
        # we prepend T3, then T2, then T1 to get [T1,T2,T3,T4,T5]
        for task in reversed(tasks_to_restore):
            iteration.plannedTasks.insert(0, task)
        
        iteration.finishedTasks.clear()

        # Clear any stored operations
        iteration.plannedOperations = None

        # Status transition: Any status -> PLANNED (if no tasks) or TASKS_PLANNED (if tasks exist)
        # Location transition: currentIteration -> plannedIterations
        if iteration.plannedTasks:
            iteration.status = DesignIterationStatus.TASKS_PLANNED
        else:
            iteration.status = DesignIterationStatus.PLANNED

        # Move iteration back to planned iterations
        project.currentIteration = None
        project.plannedIterations.insert(0, iteration)

        print(f"... iteration state {iteration.id} rolled back successfully")

    def _apply_operations_to_ontology(self, ontology: Ontology, operations: List[OntologyEditOperation], project: DesignProject = None):
        """
        Applies a list of ontology edit operations to the given ontology.

        Args:
            ontology (Ontology): The ontology to apply operations to.
            operations (List[OntologyEditOperation]): The operations to apply.
            project (DesignProject, optional): The project for processing references. If None, references are not processed.

        """
        for i, op in enumerate(operations):
            print(f"  Applying operation {i+1}/{len(operations)}: {type(op).__name__} ...")
            try:
                element = self.ontology_service.apply_edit_operation(ontology, op)
                self._print_edit_operation_result(op, element)
                
                if project and (op.operation_type == OperationType.CREATE or op.operation_type == OperationType.UPDATE):
                    self._process_ontology_element_references(project, op, element)
                
            except CreatedElementExistsError as e:
                print(f"  Warning: {e}. Skipping operation.")
            except UpdatedElementNotExistsError as e:
                print(f"  Warning: {e}. Skipping operation.")
            except DeletedElementNotExistsError as e:
                print(f"  Warning: {e}. Skipping operation.")
            except ReferrencedElementNotExistsError as e:
                print(f"  Warning: {e}. Skipping operation.")
            print(f"  ... processed operation {i+1}")

    def apply_current_iteration_changes(self, project_id: str, operations=None):
        """
        Applies the provided ontology edit operations to the current iteration.
        The current iteration must be in OPERATIONS_GENERATED status.
        Moves the current iteration to finished iterations.

        Args:
            project_id (str): The ID of the project to apply changes to.
            operations: Optional list of IdentifiedOperations. If None, uses persisted operations.
        
        Returns:
            Ontology: The updated ontology.
        """
        project = self.store.load_project(project_id)
        iteration = project.currentIteration
        if not iteration:
            raise ValueError("No current iteration to apply changes from.")
        if iteration.status != DesignIterationStatus.OPERATIONS_GENERATED:
            raise ValueError(f"Current iteration must be in OPERATIONS_GENERATED status, but is: {iteration.status}")

        # Get operations to apply
        if operations is not None:
            ops_to_apply = operations
        else:
            if iteration.plannedOperations is None:
                raise ValueError("No operations available to apply")
            ops_to_apply = iteration.plannedOperations
        
        # Extract the actual operations from the wrappers
        actual_operations = [identified_op.operation for identified_op in ops_to_apply]

        # Status transition: OPERATIONS_GENERATED -> APPLYING_OPERATIONS
        # Location: remains in currentIteration
        iteration.status = DesignIterationStatus.APPLYING_OPERATIONS

        print(f"Applying {len(actual_operations)} operations from iteration {iteration.id} to the project's designed ontology...")

        # Create a deep copy backup of the ontology before applying operations
        print(f"Creating ontology backup before applying operations...")
        ontology_backup = copy.deepcopy(project.designedOntology)
        print(f"... ontology backup created")

        try:
            self._apply_operations_to_ontology(project.designedOntology, actual_operations, project)
            print(f"Successfully applied {len(actual_operations)} operations")

            # Mark all tasks as completed
            for task in iteration.plannedTasks:
                task.status = DesignTaskStatus.COMPLETED
                iteration.finishedTasks.append(task)
            iteration.plannedTasks.clear()

            # Status transition: APPLYING_OPERATIONS -> COMPLETED
            # Location transition: currentIteration -> finishedIterations
            iteration.status = DesignIterationStatus.COMPLETED
            project.finishedIterations.append(iteration)
            project.currentIteration = None

            # Clear the stored operations as they've been applied
            iteration.plannedOperations = None

            self.store.store_project(project)
            self.ontology_service.store_ontology(project.designedOntology)

            print(f"... completed iteration {iteration.id}")

        except Exception as e:
            print(f"Critical error while applying operations: {e}")
            # Restore the ontology from backup
            print(f"Restoring ontology from backup...")
            project.designedOntology.classes.clear()
            project.designedOntology.attributes.clear()
            project.designedOntology.relationships.clear()
            
            project.designedOntology.classes.update(ontology_backup.classes)
            project.designedOntology.attributes.update(ontology_backup.attributes)
            project.designedOntology.relationships.update(ontology_backup.relationships)
            
            project.designedOntology.uri = ontology_backup.uri
            project.designedOntology.label = ontology_backup.label
            project.designedOntology.description = ontology_backup.description

            print(f"Rolling back iteration state...")
            self._rollback_iteration_state(project, iteration)

            self.store.store_project(project)
            self.ontology_service.store_ontology(project.designedOntology)
            print(f"... ontology restored from backup")
            raise e
        
        return project.designedOntology

    def save_project(self, project: DesignProject) -> None:
        """
        Saves the current state of a design project.

        Args:
            project (DesignProject): The project to save.
        """
        self.store.store_project(project)

    def remove_iteration(self, project_id: str, iteration_id: str) -> None:
        """
        Removes a design iteration from the given project.
        Can remove planned iterations or the current iteration (regardless of its status).
        Cannot remove finished iterations.

        Args:
            project_id (str): The ID of the project to remove the iteration from.
            iteration_id (str): The ID of the iteration to remove.
            
        Raises:
            ValueError: If iteration is not found or is already finished.
        """
        project = self.store.load_project(project_id)
        
        # Check if it's the current iteration
        if project.currentIteration and project.currentIteration.id == iteration_id:
            print(f"Removing current iteration {iteration_id}...")
            project.currentIteration = None
            self.store.store_project(project)
            print(f"... removed current iteration {iteration_id}")
            return
        
        # Check if it's in planned iterations
        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if iteration:
            print(f"Removing planned iteration {iteration.id}...")
            project.plannedIterations.remove(iteration)
            self.store.store_project(project)
            print(f"... removed planned iteration {iteration.id}")
            return
        
        # Check if it's in finished iterations (not allowed)
        if any(it.id == iteration_id for it in project.finishedIterations):
            raise ValueError(f"Cannot remove finished iteration: {iteration_id}")
        
        raise ValueError(f"Iteration not found: {iteration_id}")

    def remove_planned_iteration(self, project_id: str, iteration_id: str) -> None:
        """
        Removes a planned design iteration from the given project.
        
        DEPRECATED: Use remove_iteration() instead for more flexibility.

        Args:
            project_id (str): The ID of the project to remove the iteration from.
            iteration_id (str): The ID of the iteration to remove.
        """
        project = self.store.load_project(project_id)
        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if not iteration:
            raise ValueError(f"Iteration not found: {iteration_id}")

        print(f"Rejecting iteration {iteration.id}...")
        project.plannedIterations.remove(iteration)
        self.store.store_project(project)
        print(f"... rejected iteration {iteration.id}")

    def reorder_iteration_operations(self, project_id: str, iteration_id: str, operation_ids: List[str]) -> None:
        """
        Reorder operations within the current iteration.
        
        Args:
            project_id: The project ID
            iteration_id: The iteration ID (must be current iteration)
            operation_ids: List of operation IDs in desired order
            
        Raises:
            ValueError: If iteration is not current or not in correct state
            ValueError: If any operation ID is invalid
        """
        project = self.load_project(project_id)
        
        if not project.currentIteration or project.currentIteration.id != iteration_id:
            raise ValueError(f"Iteration {iteration_id} is not the current iteration")
        
        if project.currentIteration.status != DesignIterationStatus.OPERATIONS_GENERATED:
            raise ValueError(f"Cannot reorder operations in status: {project.currentIteration.status}")
        
        if project.currentIteration.plannedOperations is None:
            raise ValueError("No operations to reorder")
        
        # Validate all IDs exist
        existing_ids = {op.id for op in project.currentIteration.plannedOperations}
        for op_id in operation_ids:
            if op_id not in existing_ids:
                raise ValueError(f"Operation with ID '{op_id}' not found")
        
        # Validate all operations are included (no additions/removals)
        if set(operation_ids) != existing_ids:
            raise ValueError("Operation IDs must match existing operations exactly")
        
        # Reorder
        id_to_operation = {op.id: op for op in project.currentIteration.plannedOperations}
        project.currentIteration.plannedOperations = [id_to_operation[op_id] for op_id in operation_ids]
        
        self.save_project(project)

    def update_iteration_operation(self, project_id: str, iteration_id: str, operation_id: str, updated_operation):
        """
        Update a specific operation within the current iteration.
        
        Args:
            project_id: The project ID
            iteration_id: The iteration ID (must be current iteration)
            operation_id: The ID of the operation to update
            updated_operation: The new operation data (OntologyEditOperation)
            
        Returns:
            The updated IdentifiedOperation
            
        Raises:
            ValueError: If iteration is not current or not in correct state
            ValueError: If operation ID is not found
        """
        from design_project.domain import IdentifiedOperation
        
        project = self.load_project(project_id)
        
        if not project.currentIteration or project.currentIteration.id != iteration_id:
            raise ValueError(f"Iteration {iteration_id} is not the current iteration")
        
        if project.currentIteration.status != DesignIterationStatus.OPERATIONS_GENERATED:
            raise ValueError(f"Cannot update operations in status: {project.currentIteration.status}")
        
        if project.currentIteration.plannedOperations is None:
            raise ValueError("No operations to update")
        
        # Find and update the operation
        for i, identified_op in enumerate(project.currentIteration.plannedOperations):
            if identified_op.id == operation_id:
                # Create new IdentifiedOperation with updated operation but same ID
                updated_identified_op = IdentifiedOperation(
                    id=identified_op.id,
                    operation=updated_operation,
                    created_from_task_id=identified_op.created_from_task_id
                )
                project.currentIteration.plannedOperations[i] = updated_identified_op
                self.save_project(project)
                return updated_identified_op
        
        raise ValueError(f"Operation with ID '{operation_id}' not found")

    def delete_iteration_operation(self, project_id: str, iteration_id: str, operation_id: str) -> None:
        """
        Delete a specific operation from the current iteration.
        
        Args:
            project_id: The project ID
            iteration_id: The iteration ID (must be current iteration)
            operation_id: The ID of the operation to delete
            
        Raises:
            ValueError: If iteration is not current or not in correct state
            ValueError: If operation ID is not found
        """
        project = self.load_project(project_id)
        
        if not project.currentIteration or project.currentIteration.id != iteration_id:
            raise ValueError(f"Iteration {iteration_id} is not the current iteration")
        
        if project.currentIteration.status != DesignIterationStatus.OPERATIONS_GENERATED:
            raise ValueError(f"Cannot delete operations in status: {project.currentIteration.status}")
        
        if project.currentIteration.plannedOperations is None:
            raise ValueError("No operations to delete")
        
        # Find and remove the operation
        original_count = len(project.currentIteration.plannedOperations)
        project.currentIteration.plannedOperations = [
            op for op in project.currentIteration.plannedOperations if op.id != operation_id
        ]
        
        if len(project.currentIteration.plannedOperations) == original_count:
            raise ValueError(f"Operation with ID '{operation_id}' not found")
        
        self.save_project(project)