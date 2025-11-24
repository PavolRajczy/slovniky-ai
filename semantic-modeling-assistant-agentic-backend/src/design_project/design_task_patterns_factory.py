from abc import ABC, abstractmethod
from typing import List
import uuid

from design_project.domain import DesignTaskPattern, DesignTaskCategory


class DesignTaskPatternsFactory(ABC):
    """
    Abstract factory class for creating design task patterns.
    Serves as an interface for different implementations.
    """
    
    @staticmethod
    @abstractmethod
    def get_factory_id() -> str:
        """
        Returns the unique identifier of this factory implementation.
        
        Returns:
            str: The unique identifier of the factory.
        """
        pass
    
    @staticmethod
    @abstractmethod
    def get_design_task_patterns() -> List[DesignTaskPattern]:
        """
        Returns a list of design task patterns.
        
        Returns:
            List[DesignTaskPattern]: A list of available design task patterns.
        """
        pass


class DesignTaskPatternsFactory_Basic(DesignTaskPatternsFactory):
    """
    DesignTaskPatternsFactory that returns predefined basic patterns.
    """
    
    @staticmethod
    def get_factory_id() -> str:
        """
        Returns the unique identifier of this factory implementation.
        
        Returns:
            str: The unique identifier 'basic' for the basic factory.
        """
        return "basic"
    
    @staticmethod
    def get_design_task_patterns() -> List[DesignTaskPattern]:
        """
        Returns a list of basic design task patterns for testing purposes.

        Returns:
            List[DesignTaskPattern]: A list of basic design task patterns.
        """
        patterns = [
            DesignTaskPattern(
                id="DP_CLASS_01",
                name="Discover Domain Classes - Core Concepts",
                category=DesignTaskCategory.CLASS,
                specification="Analyze the domain knowledge to identify new ontology classes that represent the following key concepts in the domain: [list of names of core concepts that can be potentially represented as classes or groups of semantically related classes]. Output solely new classes, not other ontology constructs.",
                whenApplicable="When there is a need to expand the ontology with new core concepts that are central to the domain but not yet represented in the ontology. Usually applicable among the first design tasks in a design iteration. Should not be used to discover detailed specialized classes that specialize a more general concept. Should be used rather for more general concepts if possible based on the domain knowledge.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_CLASS_02",
                name="Discover Classes - Core Events",
                category=DesignTaskCategory.CLASS,
                specification="Analyze the domain knowledge to identify new ontology classes that represent the following key events in the domain: [list of names of core events that can be potentially represented as classes or groups of semantically related classes]. Output solely new classes, not other ontology constructs.",
                whenApplicable="When there is a need to expand the ontology with new core events that are central to the domain but not yet represented in the ontology. Usually applicable among the first design tasks in a design iteration. Should not be used to discover detailed specialized classes that specialize a more general concept. Should be used rather for more general concepts if possible based on the domain knowledge.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_CLASS_03",
                name="Discover Classes - Semantic Neighbors",
                category=DesignTaskCategory.CLASS,
                specification="Analyze the domain knowledge to identify new ontology classes that are semantically close (semantic neighbours) of the existing class [class name]. Output solely new classes, not other ontology constructs.",
                whenApplicable="When there is a need to expand the ontology with new classes that are semantically related to existing classes. Usually applicable after some core classes are already established in the ontology. Should not be used to discover detailed specialized classes that specialize a more general concept. Should be used rather for more general concepts if possible based on the domain knowledge.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_CLASS_04",
                name="Generalize Classes",
                category=DesignTaskCategory.CLASS,
                specification="Analyze the domain knowledge to identify a new ontology class that generalizes, in the IS-A/inheritance relationship, two or more existing classes [list of class names]. Output solely a new class as a generalization of the existing classes, not other ontology constructs.",
                whenApplicable="When there is a need to introduce a more general class that captures commonalities among several existing classes. Usually applicable after some core classes are already established in the ontology and the domain knowledge indicates the presence of a more general concept.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_CLASS_05",
                name="Specialize Class",
                category=DesignTaskCategory.CLASS,
                specification="Analyze the domain knowledge to identify new ontology classes that specialize, in the IS-A/inheritance relationship, an existing class [class name]. Output solely new classes as specializations of the existing class, not other ontology constructs.",
                whenApplicable="When there is a need to introduce more specific classes that capture distinctions within an existing class. Usually applicable after some core classes are already established in the ontology and the domain knowledge indicates the presence of more specific concepts.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_CLASS_06",
                name="Establish Inheritance between Classes",
                category=DesignTaskCategory.CLASS,
                specification="Analyze the domain knowledge to identify inheritance links between the existing ontology class [class name] with other existing ontology classes.",
                whenApplicable="When there is a need to define or refine the inheritance structure between classes in the ontology.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_CLASS_07",
                name="Convert Attribute to Class",
                category=DesignTaskCategory.CLASS,
                specification="Analyze the domain knowledge to check if the existing ontology attribute [attribute name] of the class [class name] represents a complex concept that should be modeled as a class instead of an attribute. If yes, identify the new ontology class that replaces the attribute. Output solely the new class that replaces the attribute, not other ontology constructs.",
                whenApplicable="When there is a need to refactor the ontology by converting an attribute into a class to better capture its complexity or relationships. Applicable usually later in the whole ontology design process when the basic skeleton of the ontology is established. After this task, there should be a sequence of tasks to remove the old attribute and link the new class appropriately to the existing class with a new relationship based on the old attribute.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_CLASS_08",
                name="Convert Relationship to Class",
                category=DesignTaskCategory.CLASS,
                specification="Analyze the domain knowledge to check if the existing ontology relationship [relationship name] connecting the classes [domain (source) class name] and [range (target) class name] represents a complex concept that should be modeled as a class connected to the classes with relationships instead of a simple relationship. If yes, identify the new ontology class that replaces the relationship. Output solely the new class that replaces the relationship, not other ontology constructs.",
                whenApplicable="When there is a need to refactor the ontology by converting a relationship into a class to better capture its complexity or relationships. Applicable usually later in the whole ontology design process when the basic skeleton of the ontology is established. After this task, there should be a sequence of tasks to remove the old relationship and link the new class appropriately to the existing classes with new relationships based on the old relationship.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_CLASS_09",
                name="Improve Class Specification",
                category=DesignTaskCategory.CLASS,
                specification="Analyze the domain knowledge to improve the existing definition and/or description of the existing ontology class [class name].",
                whenApplicable="When there is a need to refine the understanding and representation of an existing class based on deeper insights from the domain knowledge. Applicable at any stage of the design iteration when the domain knowledge indicates that the current specification of the class can be enhanced.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_CLASS_10",
                name="Delete Class",
                category=DesignTaskCategory.CLASS,
                specification="Remove the existing ontology class [class name].",
                whenApplicable="When the existing ontology class is redundant or not relevant based on the previous tasks in the design iteration where we refactored the ontology or re-modeled the given domain concept with another ontology structure making this class unnecessary.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_ATTRIBUTE_01",
                name="Define Class Attributes",
                category=DesignTaskCategory.ATTRIBUTE,
                specification="Analyze the domain knowledge to identify new ontology attributes of the existing ontology class [class name] that describe the characteristics, features, intrinsic moments, or data fields of the classes. Output solely new attributes, not other ontology constructs.",
                whenApplicable="When there is a need to enrich an existing class with attributes that capture its properties or characteristics based on the domain knowledge. Applicable usually later in the design iteration after the core classes are established.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_ATTRIBUTE_02",
                name="Improve Attribute Specification",
                category=DesignTaskCategory.ATTRIBUTE,
                specification="Analyze the domain knowledge to improve the existing definition and/or description of the existing ontology attribute [attribute name] of the class [class name].",
                whenApplicable="When there is a need to refine the understanding and representation of an existing attribute based on deeper insights from the domain knowledge. Applicable at any stage of the design iteration when the domain knowledge indicates that the current specification of the attribute can be enhanced.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_ATTRIBUTE_03",
                name="Delete Attribute",
                category=DesignTaskCategory.ATTRIBUTE,
                specification="Remove the existing ontology attribute [attribute name] of the class [class name].",
                whenApplicable="When the existing ontology attribute is redundant or not relevant based on the previous tasks in the design iteration where we refactored the ontology or re-modeled the given domain concept with another ontology structure making this attribute unnecessary.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_ATTRIBUTE_04",
                name="Split Attribute",
                category=DesignTaskCategory.ATTRIBUTE,
                specification="Analyze the domain knowledge to identify the need for splitting the existing ontology attribute [attribute name] of the class [class name] into multiple attributes.",
                whenApplicable="When the existing ontology attribute is found to be too broad or encompassing multiple distinct properties, necessitating a split into more specific attributes.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_ATTRIBUTE_05",
                name="Reconnect Attribute to Another Class",
                category=DesignTaskCategory.ATTRIBUTE,
                specification="Analyze the domain knowledge to identify the need for reconnecting the existing ontology attribute [attribute name] of the class [class name] to another class.",
                whenApplicable="When the existing ontology attribute is found to be more relevant to another class based on the refined understanding of the domain.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_RELATIONSHIP_01",
                name="Establish Class Relationships (no inheritance)",
                category=DesignTaskCategory.RELATIONSHIP,
                specification="Analyze the domain knowledge to identify new ontology relationships (not inheritance) connecting the existing ontology class [class name] with other existing ontology classes. Output solely new relationships, not other ontology constructs.",
                whenApplicable="When there is a need to define or refine the relationships between classes in the ontology. Applicable usually later in the design iteration after some core classes are already established in the ontology.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_RELATIONSHIP_02",
                name="Establish Relationships Between Concrete Classes (no inheritance)",
                category=DesignTaskCategory.RELATIONSHIP,
                specification="Analyze the domain knowledge to identify new ontology relationships (not inheritance) connecting existing ontology classes [list of names of existing classes]. Output solely new relationships, not other ontology constructs.",
                whenApplicable="When there is a need to define or refine the relationships between concrete classes in the ontology. Applicable usually later in the design iteration after some core classes are already established in the ontology.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_RELATIONSHIP_03",
                name="Improve Relationship Specification",
                category=DesignTaskCategory.RELATIONSHIP,
                specification="Analyze the domain knowledge to improve the existing definition and/or description of the existing ontology relationship [relationship name] connecting the classes [domain (source) class name] and [range (target) class name].",
                whenApplicable="When there is a need to refine the understanding and representation of an existing relationship based on deeper insights from the domain knowledge. Applicable at any stage of the design iteration when the domain knowledge indicates that the current specification of the relationship can be enhanced.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_RELATIONSHIP_04",
                name="Delete Relationship",
                category=DesignTaskCategory.RELATIONSHIP,
                specification="Remove the existing ontology relationship [relationship name] connecting the classes [domain (source) class name] and [range (target) class name].",
                whenApplicable="When the existing ontology relationship is redundant or not relevant based on the previous tasks in the design iteration where we refactored the ontology or re-modeled the given domain concept with another ontology structure making this relationship unnecessary.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_RELATIONSHIP_05",
                name="Reconnect Relationship to Another Class",
                category=DesignTaskCategory.RELATIONSHIP,
                specification="Analyze the domain knowledge to identify the need for reconnecting the existing ontology relationship [relationship name] connecting the classes [domain (source) class name] and [range (target) class name] to another domain or range.",
                whenApplicable="When the existing ontology relationship is found to be more relevant to another class based on the refined understanding of the domain.",
                exampleTasks=[]
            ),
            DesignTaskPattern(
                id="DP_RELATIONSHIP_06",
                name="Split Relationship",
                category=DesignTaskCategory.RELATIONSHIP,
                specification="Analyze the domain knowledge to identify the need for splitting the existing ontology relationship [relationship name] connecting the classes [domain (source) class name] and [range (target) class name] into multiple relationships with the same domain and range.",
                whenApplicable="When the existing ontology relationship is found to be too broad or encompassing multiple distinct relationships, necessitating a split into more specific relationships.",
                exampleTasks=[]
            )

        ]
        
        return patterns


class DesignTaskPatternsFactoryRegistry:
    """
    Registry for resolving DesignTaskPatternsFactory implementations by their identifiers.
    """
    
    _factories = {
        "basic": DesignTaskPatternsFactory_Basic
    }
    
    @classmethod
    def get_factory(cls, factory_id: str) -> DesignTaskPatternsFactory:
        """
        Get a factory instance by its identifier.
        
        Args:
            factory_id (str): The identifier of the factory to retrieve.
            
        Returns:
            DesignTaskPatternsFactory: The factory implementation.
            
        Raises:
            ValueError: If the factory_id is not registered.
        """
        if factory_id not in cls._factories:
            raise ValueError(f"Unknown factory ID: {factory_id}. Available factories: {list(cls._factories.keys())}")
        
        return cls._factories[factory_id]
    
    @classmethod
    def register_factory(cls, factory_class: type[DesignTaskPatternsFactory]) -> None:
        """
        Register a new factory implementation.
        
        Args:
            factory_class: The factory class to register.
        """
        factory_id = factory_class.get_factory_id()
        cls._factories[factory_id] = factory_class
    
    @classmethod
    def get_available_factory_ids(cls) -> List[str]:
        """
        Get a list of all available factory identifiers.
        
        Returns:
            List[str]: List of available factory identifiers.
        """
        return list(cls._factories.keys())