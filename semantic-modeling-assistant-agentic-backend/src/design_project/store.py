import os
import json

from typing import Any, Dict, List, Optional
from rdflib import URIRef

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from ontology.domain import Ontology, OntologyAttribute, OntologyClass, OntologyRelationship, Kind
from ontology.service import OntologyService
from ontology.edit_operations import (
    OntologyEditOperation, OperationType,
    CreateClassOperation, UpdateClassOperation, DeleteClassOperation,
    CreateAttributeOperation, UpdateAttributeOperation, DeleteAttributeOperation,
    CreateRelationshipOperation, UpdateRelationshipOperation, DeleteRelationshipOperation
)
from .domain import DesignIteration, DesignProject, DesignTask, DesignTaskPattern, KnowledgeDomain, KnowledgeDomainArea
from .design_task_patterns_factory import DesignTaskPatternsFactoryRegistry

class DesignProjectStore:
    def store_project(self, project: DesignProject) -> None:
        """Persist the complete state of the design project to the store."""
        ...

    def load_project(self, project_id: str) -> DesignProject:
        """Load the complete state of the design project from the store by its id and assign an ontology to the design project."""
        ...

    def list_all_projects(self) -> List[DesignProject]:
        """List all available design projects with basic metadata."""
        ...

    def set_project_knowledge(self, project: DesignProject, legal_knowledge_base: List[KnowledgeDocument], expert_knowledge_base: List[KnowledgeDocument]) -> None:
        """Set the complete knowledge documents for a design project that was previously loaded with placeholder documents."""
        ...


class FileSystemDesignProjectStore(DesignProjectStore):
    def __init__(self, ontology_service: OntologyService, base_dir: str = "data/projects"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.cached_design_projects = {}
        self.ontology_service = ontology_service

    def store_project(self, project: DesignProject) -> None:
        """
        Store the previously loaded design project in its own subdirectory named by project id.

        Args:
            project (DesignProject): The project to store.

        Raises:
            ValueError: If the project is not found in the store.
        """
        if project.id not in self.cached_design_projects:
            self.cached_design_projects[project.id] = project

        project_dir = os.path.join(self.base_dir, project.id)
        os.makedirs(project_dir, exist_ok=True)
        project_file = os.path.join(project_dir, "project.json")
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(self._design_project_to_dict(project), f, ensure_ascii=False, indent=2)

    def load_project(self, project_id: str) -> DesignProject:
        """
        Load the design project from its subdirectory by id.

        When the loaded design project is changed later, it is not persisted automatically.
        It is necessary to call store_project() for it to be persisted.

        The loaded project is not complete:
        - For each knowledge base document in legalKnowledgeBase and expertKnowledgeBase it contains a temporary knowledge document with id but with other fields empty.
        - For each knowledge base document element in knowledgeResources of each design task, it contains a temporary knowledge document element with id but with other fields empty.

        These items from the knowledge base must be completed with the actual knowledge documents and their elements by the caller.

        Args:
            project_id (str): The ID of the project to load.

        Returns:
            DesignProject: The loaded design project. 
        """
        if project_id in self.cached_design_projects:
            return self.cached_design_projects[project_id]

        project_dir = os.path.join(self.base_dir, project_id)
        project_file = os.path.join(project_dir, "project.json")
        if not os.path.exists(project_file):
            raise FileNotFoundError(f"Project file not found: {project_file}")
        with open(project_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        project = self._design_project_from_dict(data)

        self.cached_design_projects[project.id] = project
        return project

    def list_all_projects(self) -> List[DesignProject]:
        """
        List all available design projects by scanning the project directories.

        Returns:
            List[DesignProject]: List of all design projects with basic metadata loaded.
        """
        projects = []
        
        # Check if base directory exists
        if not os.path.exists(self.base_dir):
            return projects
        
        # Scan all subdirectories
        for project_id in os.listdir(self.base_dir):
            project_dir = os.path.join(self.base_dir, project_id)
            
            # Skip if not a directory
            if not os.path.isdir(project_dir):
                continue
            
            project_file = os.path.join(project_dir, "project.json")
            
            # Skip if project.json doesn't exist
            if not os.path.exists(project_file):
                continue
            
            try:
                # Load the project
                project = self.load_project(project_id)
                projects.append(project)
            except Exception as e:
                # Log error but continue with other projects
                print(f"Warning: Failed to load project {project_id}: {e}")
                continue
        
        return projects

    def set_project_knowledge(self, project: DesignProject, legal_knowledge_base: List[KnowledgeDocument], expert_knowledge_base: List[KnowledgeDocument]) -> None:
        """
        Set the complete knowledge documents for a project that was previously loaded with placeholder documents.
        
        This method resolves the incomplete knowledge documents loaded by load_project() by replacing
        the placeholder documents (with only IDs) with complete documents containing all fields.
        It also updates knowledge document elements in design tasks' knowledgeResources.
        
        Args:
            project_id (str): The ID of the project to update.
            legal_knowledge_base (List[KnowledgeDocument]): Complete legal knowledge documents.
            expert_knowledge_base (List[KnowledgeDocument]): Complete expert knowledge documents.
            
        Raises:
            ValueError: If the project is not found in the store.
        """
        if project.id not in self.cached_design_projects:
            raise ValueError(f"Project not found in the store: {project.id}")

        project.legalKnowledgeBase = legal_knowledge_base
        project.expertKnowledgeBase = expert_knowledge_base

        # Create lookup dictionaries for efficient document and element retrieval
        all_docs = legal_knowledge_base + expert_knowledge_base
        docs_by_id = {doc.id: doc for doc in all_docs}
        
        # Collect all document elements for lookup
        elements_by_id = {}
        for doc in all_docs:
            if hasattr(doc, 'elements') and doc.elements:
                for element in doc.elements:
                    elements_by_id[element.id] = element
        
        # Replace placeholder legal knowledge base documents
        project.legalKnowledgeBase = [
            docs_by_id.get(doc.id, doc) for doc in project.legalKnowledgeBase
        ]
        
        # Replace placeholder expert knowledge base documents
        project.expertKnowledgeBase = [
            docs_by_id.get(doc.id, doc) for doc in project.expertKnowledgeBase
        ]
        
        # Replace placeholder key knowledge document if present
        if project.keyKnowledgeDocument:
            project.keyKnowledgeDocument = docs_by_id.get(project.keyKnowledgeDocument.id, project.keyKnowledgeDocument)

        # Update knowledge document elements in all design tasks
        def update_knowledge_resources(tasks: List[DesignTask]) -> None:
            for task in tasks:
                task.knowledgeResources = [
                    elements_by_id.get(element.id, element) for element in task.knowledgeResources
                ]
        
        # Update knowledge resources in all iterations and tasks
        if project.currentIteration:
            update_knowledge_resources(project.currentIteration.finishedTasks)
            if project.currentIteration.currentTask:
                update_knowledge_resources([project.currentIteration.currentTask])
            update_knowledge_resources(project.currentIteration.plannedTasks)
            
        for iteration in project.finishedIterations + project.plannedIterations:
            update_knowledge_resources(iteration.finishedTasks)
            if iteration.currentTask:
                update_knowledge_resources([iteration.currentTask])
            update_knowledge_resources(iteration.plannedTasks)
            
        # Update explaining knowledge resources in modeled knowledge domain areas
        if project.modeledKnowledgeDomain:
            for area in project.modeledKnowledgeDomain.areas:
                if hasattr(area, 'explainingKnowledgeResources'):
                    area.explainingKnowledgeResources = [
                        elements_by_id.get(element.id, element) for element in area.explainingKnowledgeResources
                    ]

    def _design_project_to_dict(self, project: DesignProject) -> Dict[str, Any]:
        return {
            "id": project.id,
            "name": project.name,
            "finishedIterations": [self._design_iteration_to_dict(it) for it in project.finishedIterations],
            "currentIteration": self._design_iteration_to_dict(project.currentIteration) if project.currentIteration else None,
            "plannedIterations": [self._design_iteration_to_dict(it) for it in project.plannedIterations],
            # Persist only the factory ID, patterns are loaded dynamically
            "patternsFactoryId": project.patternsFactoryId,
            "legalKnowledgeBase": [doc.id for doc in project.legalKnowledgeBase],
            "expertKnowledgeBase": [doc.id for doc in project.expertKnowledgeBase],
            "keyKnowledgeDocument": project.keyKnowledgeDocument.id if project.keyKnowledgeDocument else None,
            "modeledKnowledgeDomain": self._knowledge_domain_to_dict(project.modeledKnowledgeDomain) if project.modeledKnowledgeDomain else None,
            "designedOntology": project.designedOntology.uri if project.designedOntology else None
        }

    def _design_project_from_dict(self, data: Dict[str, Any]) -> DesignProject:
        # Load ontology first so we can resolve domain references to it
        stored_ontology_uri = data["designedOntology"]
        designed_ontology = self.ontology_service.load_ontology(stored_ontology_uri) if stored_ontology_uri else None
        if designed_ontology is None:
            raise ValueError(f"Designed ontology not found or could not be loaded: {stored_ontology_uri}")

        modeled_knowledge_domain = self._knowledge_domain_from_dict(data["modeledKnowledgeDomain"], designed_ontology) if data["modeledKnowledgeDomain"] else None

        # Load patterns from factory using the factory ID
        patterns_factory_id = data.get("patternsFactoryId")
        if patterns_factory_id:
            factory = DesignTaskPatternsFactoryRegistry.get_factory(patterns_factory_id)
            patterns = factory.get_design_task_patterns()
        else:
            # Fallback: try to load from serialized patterns (backward compatibility)
            patterns_input = data.get("patterns", []) or []
            patterns_by_id: Dict[str, DesignTaskPattern] = {}
            # First pass: create patterns without example tasks
            for p in patterns_input:
                pat = DesignTaskPattern(
                    id=p["id"],
                    name=p.get("name"),
                    category=p.get("category"),
                    specification=p.get("specification"),
                    whenApplicable=p.get("whenApplicable"),
                    exampleTasks=[],
                )
                patterns_by_id[pat.id] = pat
            # Second pass: populate example tasks (resolve followedPattern by id)
            for p in patterns_input:
                pat = patterns_by_id[p["id"]]
                ex_tasks = [self._design_task_from_dict(t, patterns_by_id) for t in p.get("exampleTasks", []) or []]
                pat.exampleTasks = ex_tasks
            patterns = list(patterns_by_id.values())

        # Build patterns mapping for resolving task references
        patterns_by_id = {p.id: p for p in patterns}

        project = DesignProject(
            id=data["id"],
            name=data["name"],
            finishedIterations=[self._design_iteration_from_dict(it, modeled_knowledge_domain, patterns_by_id) for it in data["finishedIterations"]],
            currentIteration=self._design_iteration_from_dict(data["currentIteration"], modeled_knowledge_domain, patterns_by_id) if data["currentIteration"] else None,
            plannedIterations=[self._design_iteration_from_dict(it, modeled_knowledge_domain, patterns_by_id) for it in data["plannedIterations"]],
            patterns=patterns,
            patternsFactoryId=patterns_factory_id or "basic",  # Default to basic if not specified
            # Create placeholder documents with only ID, other fields empty
            legalKnowledgeBase=[KnowledgeDocument(id=doc_id, title=None, content=None, contentSummary=None) for doc_id in data["legalKnowledgeBase"]],
            expertKnowledgeBase=[KnowledgeDocument(id=doc_id, title=None, content=None, contentSummary=None) for doc_id in data["expertKnowledgeBase"]],
            keyKnowledgeDocument=KnowledgeDocument(id=data["keyKnowledgeDocument"], title=None, content=None, contentSummary=None) if data.get("keyKnowledgeDocument") else None,
            modeledKnowledgeDomain=modeled_knowledge_domain,
            designedOntology=designed_ontology
        )
        return project

    def _design_iteration_to_dict(self, iteration: DesignIteration) -> Dict[str, Any]:
        return {
            "id": iteration.id,
            "name": iteration.name,
            "status": iteration.status,
            "specification": iteration.specification,
            "finishedTasks": [self._design_task_to_dict(task) for task in iteration.finishedTasks],
            "currentTask": self._design_task_to_dict(iteration.currentTask) if iteration.currentTask else None,
            "plannedTasks": [self._design_task_to_dict(task) for task in iteration.plannedTasks],
            "focusedArea": iteration.focusedArea.id if iteration.focusedArea else None,
            "plannedOperations": [self._identified_operation_to_dict(op) for op in iteration.plannedOperations] if iteration.plannedOperations else None,
            "designedOntologyChangesSpecification": iteration.designedOntologyChangesSpecification,
        }

    def _design_iteration_from_dict(self, data: Dict[str, Any], modeled_knowledge_domain: KnowledgeDomain, patterns_by_id: Dict[str, DesignTaskPattern]) -> DesignIteration:
        focused_area_id = data["focusedArea"]
        focused_area = None
        for area in modeled_knowledge_domain.areas:
            if area.id == focused_area_id:
                focused_area = area
                break
        if not focused_area:
            raise ValueError(f"Focused area '{focused_area_id}' not found in modeled knowledge domain.")


        # Handle plannedOperations with backward compatibility
        planned_operations = None
        if data.get("plannedOperations"):
            operations_data = data["plannedOperations"]
            if operations_data and isinstance(operations_data[0], dict):
                # Check if this is new format (with id and operation) or old format (direct operation)
                if 'id' in operations_data[0] and 'operation' in operations_data[0]:
                    # New format - deserialize as IdentifiedOperation
                    planned_operations = [self._identified_operation_from_dict(op_dict) for op_dict in operations_data]
                else:
                    # Old format - wrap with generated IDs for backward compatibility
                    import uuid
                    from design_project.domain import IdentifiedOperation
                    planned_operations = [
                        IdentifiedOperation(
                            id=str(uuid.uuid4()),
                            operation=self._operation_from_dict(op_dict),
                            created_from_task_id=None
                        )
                        for op_dict in operations_data
                    ]

        return DesignIteration(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            specification=data["specification"],
            finishedTasks=[self._design_task_from_dict(task, patterns_by_id) for task in data["finishedTasks"]],
            currentTask=self._design_task_from_dict(data["currentTask"], patterns_by_id) if data["currentTask"] else None,
            plannedTasks=[self._design_task_from_dict(task, patterns_by_id) for task in data["plannedTasks"]],
            focusedArea=focused_area,
            plannedOperations=planned_operations,
            designedOntologyChangesSpecification=data["designedOntologyChangesSpecification"],
        )

    def _design_task_to_dict(self, task: DesignTask) -> Dict[str, Any]:
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status,
            # Persist only pattern ID; patterns are stored centrally on project
            "followedPattern": task.followedPattern.id if task.followedPattern else None,
            "specification": task.specification,
            "knowledgeResources": [el.id for el in task.knowledgeResources],
            "designedOntologyChangesSpecification": task.designedOntologyChangesSpecification,
        }

    def _design_task_from_dict(self, data: Dict[str, Any], patterns_by_id: Dict[str, DesignTaskPattern]) -> DesignTask:
        pat_id = data.get("followedPattern")
        pattern = patterns_by_id.get(pat_id) if pat_id else None
        return DesignTask(
            id=data["id"],
            name=data["name"],
            status=data["status"],
            followedPattern=pattern,
            specification=data["specification"],
            # Create placeholder elements with required fields empty
            knowledgeResources=[KnowledgeDocumentElement(id=el_id, title=None, content=None, contentSummary=None) for el_id in data["knowledgeResources"]],
            designedOntologyChangesSpecification=data["designedOntologyChangesSpecification"],
        )

    def _design_task_pattern_to_dict(self, pattern: DesignTaskPattern) -> Dict[str, Any]:
        return {
            "id": pattern.id,
            "name": pattern.name,
            "category": pattern.category,
            "specification": pattern.specification,
        # Example tasks will reference this pattern by ID as well
        "exampleTasks": [self._design_task_to_dict(task) for task in pattern.exampleTasks],
        }

    # Note: _design_task_pattern_from_dict is no longer used for full reconstruction to
    # avoid needing patterns mapping before creation. See two-pass logic in _design_project_from_dict.

    def _knowledge_domain_to_dict(self, domain: KnowledgeDomain) -> Dict[str, Any]:
        return {
            "label": domain.label,
            "description": domain.description,
            "areas": [self._knowledge_domain_area_to_dict(area) for area in domain.areas],
        }

    def _knowledge_domain_from_dict(self, data: Dict[str, Any], ontology: Ontology) -> KnowledgeDomain:
        domain = KnowledgeDomain(
            label=data["label"],
            description=data["description"],
            areas=[]
        )
        # Create areas with proper parent reference
        domain.areas = [self._knowledge_domain_area_from_dict(area_data, domain, ontology) for area_data in data["areas"]]
        return domain

    def _knowledge_domain_area_to_dict(self, area: KnowledgeDomainArea) -> Dict[str, Any]:
        return {
            "id": area.id,
            "label": area.label,
            "description": area.description,
            "keyConcepts": area.keyConcepts,
            "modelingClasses": [str(cls.uri) for cls in area.modelingClasses],
            "modelingAttributes": [str(attr.uri) for attr in area.modelingAttributes],
            "modelingRelationships": [str(rel.uri) for rel in area.modelingRelationships],
            # Store only IDs of knowledge document elements to avoid duplicating KB content
            "explainingKnowledgeResources": [el.id for el in getattr(area, "explainingKnowledgeResources", [])],
        }

    def _knowledge_domain_area_from_dict(self, data: Dict[str, Any], parent: KnowledgeDomain, ontology: Ontology) -> KnowledgeDomainArea:
        # Resolve references to ontology elements by their IDs (URIs)
        def get_class(uri: str) -> OntologyClass:
            cls = ontology.classes.get(URIRef(uri)) if ontology and ontology.classes else None
            if cls is None:
                raise ValueError(f"Ontology class not found for URI '{uri}' when loading KnowledgeDomainArea '{data.get('label')}'.")
            return cls

        def get_attribute(uri: str) -> OntologyAttribute:
            attr = ontology.attributes.get(URIRef(uri)) if ontology and ontology.attributes else None
            if attr is None:
                raise ValueError(f"Ontology attribute not found for URI '{uri}' when loading KnowledgeDomainArea '{data.get('label')}'.")
            return attr

        def get_relationship(uri: str) -> OntologyRelationship:
            rel = ontology.relationships.get(URIRef(uri)) if ontology and ontology.relationships else None
            if rel is None:
                raise ValueError(f"Ontology relationship not found for URI '{uri}' when loading KnowledgeDomainArea '{data.get('label')}'.")
            return rel

        return KnowledgeDomainArea(
            id=data["id"],
            label=data["label"],
            description=data["description"],
            parent=parent,
            keyConcepts=data["keyConcepts"],
            modelingClasses=[get_class(uri) for uri in data.get("modelingClasses", [])],
            modelingAttributes=[get_attribute(uri) for uri in data.get("modelingAttributes", [])],
            modelingRelationships=[get_relationship(uri) for uri in data.get("modelingRelationships", [])],
            # Create placeholder knowledge document elements with only IDs
            explainingKnowledgeResources=[
                KnowledgeDocumentElement(id=el_id, title=None, content=None, contentSummary=None)
                for el_id in data.get("explainingKnowledgeResources", [])
            ],
        )

    def _operation_to_dict(self, operation: OntologyEditOperation) -> Dict[str, Any]:
        """Convert an OntologyEditOperation to a dictionary for JSON serialization."""
        # Get the operation class name to identify the operation type
        op_class = operation.__class__.__name__
        
        # Build the base dictionary with all fields
        result = {
            "__operation_class__": op_class,
            "operation_type": operation.operation_type.value if hasattr(operation, 'operation_type') else None,
        }
        
        # Add all fields from the dataclass
        for field_name, field_value in operation.__dict__.items():
            if field_name == 'operation_type':
                continue  # Already handled
            
            if isinstance(field_value, URIRef):
                result[field_name] = str(field_value)
            elif isinstance(field_value, Kind):
                result[field_name] = field_value.value
            elif isinstance(field_value, list):
                # Handle lists (e.g., generalization_uris, references)
                result[field_name] = [str(item) if isinstance(item, URIRef) else item for item in field_value] if field_value else None
            else:
                result[field_name] = field_value
        
        return result

    def _operation_from_dict(self, data: Dict[str, Any]) -> OntologyEditOperation:
        """Convert a dictionary to an OntologyEditOperation."""
        op_class_name = data.get("__operation_class__")
        if not op_class_name:
            raise ValueError("Operation dictionary missing __operation_class__ field")
        
        # Map of class names to classes
        operation_classes = {
            "CreateClassOperation": CreateClassOperation,
            "UpdateClassOperation": UpdateClassOperation,
            "DeleteClassOperation": DeleteClassOperation,
            "CreateAttributeOperation": CreateAttributeOperation,
            "UpdateAttributeOperation": UpdateAttributeOperation,
            "DeleteAttributeOperation": DeleteAttributeOperation,
            "CreateRelationshipOperation": CreateRelationshipOperation,
            "UpdateRelationshipOperation": UpdateRelationshipOperation,
            "DeleteRelationshipOperation": DeleteRelationshipOperation,
        }
        
        op_class = operation_classes.get(op_class_name)
        if not op_class:
            raise ValueError(f"Unknown operation class: {op_class_name}")
        
        # Prepare kwargs for the operation constructor
        kwargs = {}
        for key, value in data.items():
            if key in ["__operation_class__", "operation_type"]:
                continue
            
            # Convert URIRef strings back to URIRef objects
            if key == "uri" or key == "owning_class_uri" or key == "source_class_uri" or key == "target_class_uri":
                kwargs[key] = URIRef(value) if value else None
            elif key == "generalization_uris":
                kwargs[key] = [URIRef(uri) for uri in value] if value else None
            elif key == "kind":
                kwargs[key] = Kind(value) if value else None
            else:
                kwargs[key] = value
        
        # Add operation_type
        op_type_str = data.get("operation_type")
        if op_type_str:
            kwargs["operation_type"] = OperationType(op_type_str)
        
        return op_class(**kwargs)

    def _identified_operation_to_dict(self, identified_op) -> Dict[str, Any]:
        """Convert an IdentifiedOperation to a dictionary for JSON serialization."""
        return {
            "id": identified_op.id,
            "operation": self._operation_to_dict(identified_op.operation),
            "created_from_task_id": identified_op.created_from_task_id
        }

    def _identified_operation_from_dict(self, data: Dict[str, Any]):
        """Convert a dictionary to an IdentifiedOperation."""
        from design_project.domain import IdentifiedOperation
        
        return IdentifiedOperation(
            id=data["id"],
            operation=self._operation_from_dict(data["operation"]),
            created_from_task_id=data.get("created_from_task_id")
        )


