from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
from enum import Enum

from ontology.domain import Ontology, OntologyAttribute, OntologyClass, OntologyRelationship
from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement

if TYPE_CHECKING:
    from ontology.edit_operations import OntologyEditOperation

class DesignTaskCategory(str, Enum):
    # The category of the design task pattern.
    CLASS = "class"
    ATTRIBUTE = "attribute"
    RELATIONSHIP = "relationship"
    INHERITANCE = "inheritance"

class DesignIterationStatus(str, Enum):
    # The status of the design iteration.
    # Status represents the detailed work stage within the iteration's workflow position.
    # 
    # When in plannedIterations:
    PLANNED = "planned"                             # Initial state: iteration created, no tasks yet
    TASKS_PLANNED = "tasks_planned"                 # Tasks have been initialized/planned
    
    # When in currentIteration (being actively worked on):
    GENERATING_OPERATIONS = "generating_operations" # Currently generating operations from tasks
    OPERATIONS_GENERATED = "operations_generated"   # Operations generated and ready to apply
    APPLYING_OPERATIONS = "applying_operations"     # Currently applying operations to ontology
    
    # When in finishedIterations:
    COMPLETED = "completed"                         # Successfully completed and applied

class DesignTaskStatus(str, Enum):
    # The status of the design task.
    # Status represents the detailed work stage within the task's workflow position.
    #
    # When in plannedTasks:
    PLANNED = "planned"                             # Initial state: task created and planned
    
    # When in currentTask (being actively worked on):
    GENERATING_OPERATIONS = "generating_operations" # Currently generating operations for this task
    OPERATIONS_GENERATED = "operations_generated"   # Operations generated for this task
    
    # When in finishedTasks:
    COMPLETED = "completed"                         # Task successfully completed

class ProjectGuidanceItemType(str, Enum):
    """Type of a human-in-the-loop guidance item for a project."""
    INSTRUCTION = "instruction"
    CORRECTION = "correction"
    PREFERENCE = "preference"
    CONSTRAINT = "constraint"

class ProjectGuidanceItemSource(str, Enum):
    """Source of a guidance item."""
    MANUAL = "manual"
    CORRECTION = "correction"
    SAVED_FROM_REQUEST = "saved_from_request"

@dataclass
class ProjectGuidanceItem:
    """
    A single human-in-the-loop guidance item bound to a design project.
    Stored in data/projects/{project_id}/guidance.json and injected into agent prompts.
    """
    id: str
    project_id: str
    type: ProjectGuidanceItemType
    content: str
    created_at: Optional[str] = None
    source: Optional[ProjectGuidanceItemSource] = None

@dataclass
class IdentifiedOperation:
    """
    Wrapper for OntologyEditOperation that adds identity for CRUD operations.
    
    This wrapper allows operations to be managed as entities during the prepare-review-apply
    workflow while keeping the underlying OntologyEditOperation immutable.
    """
    id: str                                         # Unique identifier for this operation instance
    operation: 'OntologyEditOperation'              # The actual operation (immutable value object)
    created_from_task_id: Optional[str]             # ID of the task that generated this operation (for traceability)

@dataclass
class DesignProject:
    # A design project represents the whole project of designing a domain ontology.
    id: str                                                 # A globally unique identifier of the design project.
    name: Optional[str]                                     # The human-readable name of the design project.
    finishedIterations: List[DesignIteration]               # The list of finished design iterations.
    currentIteration: Optional[DesignIteration]             # The design iteration we are currently working on within the design project.
    plannedIterations: List[DesignIteration]                # The list of planned design iterations.
    patterns: List[DesignTaskPattern]                       # The list of design task patterns used in the project. Tasks reference these by ID via followedPattern.
    patternsFactoryId: str                                  # The identifier of the design task patterns factory used in the project. Used for persistence - patterns are loaded dynamically using this factory.
    legalKnowledgeBase: List[KnowledgeDocument]             # The list of legal act knowledge documents used in the design project.
    expertKnowledgeBase: List[KnowledgeDocument]            # The list of expert knowledge documents used in the design project.
    keyKnowledgeDocument: Optional[KnowledgeDocument]       # The key knowledge document that structures the knowledge domain and its areas.
    modeledKnowledgeDomain: Optional[KnowledgeDomain]       # The knowledge domain for which we design an ontology in the design project.
    designedOntology: Ontology                              # The ontology that is being designed.

@dataclass
class DesignIteration:
    # A design iteration represents a specific iteration within a design project with the goal to incrementally extend, refine, detail or improve the domain ontology.
    id: str                                                 # A globally unique identifier of the design iteration. It is unique across the entire space of all design iterations across all design projects.
    name: Optional[str]                                     # The human-readable name of the design iteration.
    status: DesignIterationStatus                           # The current status of the design iteration within its workflow stage.
    specification: Optional[str]                            # A detailed description of the design iteration - its goals/objectives/scope. It must be detailed enough to enable designing the iteration tasks.
    finishedTasks: List[DesignTask]                         # The list of finished design tasks within the design iteration.
    currentTask: Optional[DesignTask]                       # The design task we are currently working on within the design iteration.
    plannedTasks: List[DesignTask]                          # The list of planned design tasks within the design iteration.
    focusedArea: KnowledgeDomainArea                        # The knowledge domain area that the design iteration is focused on.
    plannedOperations: Optional[List[IdentifiedOperation]] # The list of planned ontology edit operations generated during prepare phase. Stored for traceability and review.
                                                            #   Set to None initially, populated by prepare_planned_iteration(), cleared after apply_current_iteration_changes().
                                                            #   Each operation has a unique ID for CRUD management.
    designedOntologyChangesSpecification: Optional[str]     # A structured textual description of the changes made to the designed ontology as a result of performing the design iteration.
                                                            #   It is a compilation of all designed ontology changes made by executed tasks during the design iteration.
                                                            #   It is compiled after the design iteration is completed.

@dataclass
class DesignTask:
    # A design task represents a specific task within a design iteration.
    id: str                                                 # A globally unique identifier of the design task. It is unique across the entire space of all design tasks across all design iterations and all design processes.
    name: Optional[str]                                     # The human-readable name of the design task.
    status: DesignTaskStatus                                # The current status of the design task within its workflow stage.
    followedPattern: DesignTaskPattern                      # The design task pattern that this task follows. It is mandatory that a design task follows exactly one design task pattern.
    specification: Optional[str]                            # A detailed description of the design task that implements the followed pattern into the specific context of the design iteration.
    knowledgeResources: List[KnowledgeDocumentElement]      # The knowledge document elements used when executing the tasks.
                                                            #   It can be planned in advance or discovered during performing the design task.
    designedOntologyChangesSpecification: Optional[str]     # A structured textual description of the changes made to the designed ontology as a result of performing the design task.

@dataclass
class DesignTaskPattern:
    # A design task pattern represents a reusable design step specification.
    id: str                                                 # A globally unique identifier of the design task pattern.
    name: str                                               # The human-readable name of the design task pattern.
    category: DesignTaskCategory                            # The category of the design task pattern.
                                                            #   The category specifies the kind of ontology constructs targeted by this design task pattern.
                                                            #   A design task pattern must target exactly one of the defined categories.
    specification: Optional[str]                            # A detailed description of the design task pattern.
                                                            #   It is a generic description of a single ontology design task, e.g.
                                                            #       "Discover one or more new ontology classes related to a topic and specify their details."
                                                            #       "Specify inheritance/specialization/generalization between existing ontology classes."
                                                            #       "Discover one or more relationships between existing ontology classes and specify their details."
    whenApplicable: Optional[str]                           # A description of the situations when the design task pattern is applicable.
    exampleTasks: List[DesignTask]                          # A list of example design tasks that follow this pattern.

@dataclass
class KnowledgeDomainArea:
    # A class representing an area within its knowledge domain.
    #   We divide a knowledge domain into several areas to make the design of the domain ontology more manageable.
    #   A knowledge area is modeled by one or more ontology elements from the ontology associated with the knowledge area.
    id: str                                                 # A globally unique identifier of the knowledge domain area.
    label: str                                              # A human-readable label for the area.
    description: Optional[str]                              # A human-readable description providing more context about the area semantics.
    parent: KnowledgeDomain                                 # The knowledge domain this area belongs to.
    keyConcepts: List[str]                                  # The list of key concepts that are central in this area.
                                                            #   A key concept is expressed only as a string term. It is not an ontology class.
                                                            #   It can be modeled in the domain ontology as a single ontology class but also as a more complex ontology structure,
                                                            #       e.g. more ontology classes connected with ontology relationships.
    modelingClasses: List[OntologyClass]                    # The list of classes that model this area.
    modelingAttributes: List[OntologyAttribute]             # The list of attributes that model this area.
    modelingRelationships: List[OntologyRelationship]       # The list of relationships that model this area.
    explainingKnowledgeResources: List[KnowledgeDocumentElement]  # The list of knowledge document elements that explain this area.

@dataclass
class KnowledgeDomain:
    # A class representing a knowledge domain modeled by an ontology.
    label: str                                              # A human-readable label for the knowledge domain.
    description: Optional[str]                              # A human-readable description providing the basic summarized characterization of the domain semantics.
    areas: List[KnowledgeDomainArea]                        # The list of areas this domain is structured to.
                                                            #   A domain is typically structured to more areas to make the design of the domain ontology better manageable.