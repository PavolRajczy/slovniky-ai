import os
import re
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from rdflib import URIRef

from openai import OpenAI

from agents.modelers.modeler import ModelerAgent
from design_project.domain import DesignIteration, DesignProject, DesignTask, DesignTaskCategory
from knowledge_base.domain import KnowledgeDocumentElement
from knowledge_base.service import KnowledgeBaseService
from knowledge_base_index.service import KnowledgeBaseIndexService
from ontology.domain import Ontology, Kind
from collections import defaultdict
from enum import Enum
from ontology.edit_operations import (
    OntologyEditOperation, 
    CreateClassOperation, UpdateClassOperation, DeleteClassOperation,
    CreateAttributeOperation, UpdateAttributeOperation, DeleteAttributeOperation,
    CreateRelationshipOperation, UpdateRelationshipOperation, DeleteRelationshipOperation
)


class SearchQueryDefinitionOutput(BaseModel):
    """
    Pydantic model representing a constructed search query to find relevant knowledge snippets in the knowledge base.
    """
    query: str = Field(
        description="The constructed search query to find relevant knowledge snippets in the knowledge base."
    )
    max_results: int = Field(
        default=10,
        description="The maximum number of search results to return."
    )
    offset: int = Field(
        default=0,
        description="Number of top results to skip (0 means no skipping, >0 means skipping the top results which enables repeating the search to obtain more results when the previous searches yielded insufficient results)."
    )


class SearchQueriesDefinitionOutput(BaseModel):
    """
    Pydantic model representing a list of constructed search queries to find relevant knowledge snippets in the knowledge base.
    """
    queries: List[SearchQueryDefinitionOutput] = Field(
        description="The list of constructed search queries to find relevant knowledge snippets in the knowledge base."
    )

class KnowledgeBaseReference(BaseModel):
    """
    Pydantic model representing a reference to a knowledge base snippet or its fragment.
    """
    snippet_id: str = Field(
        description="The unique ID of the knowledge base snippet."
    )
    fragment_id: str = Field(
        default=None,
        description="An optional ID indicating a specific fragment of the snippet."
    )

class ClassOperationOutput(BaseModel):
    """
    Pydantic model representing a class operation to be performed on the ontology.
    """
    operation_type: str = Field(
        description="The type of operation: 'create', 'update', or 'delete'."
    )
    label: Optional[str] = Field(
        default=None,
        description="The human-readable label for the class (required for create operations)."
    )
    prefixed_name: str = Field(
        description="The prefixed name (i.e. :LocalName) of the class (the last part of the URI) to create, update, or delete."
    )
    definition: Optional[str] = Field(
        default=None,
        description="A formal definition of the class."
    )
    description: Optional[str] = Field(
        default=None,
        description="A human-readable description providing more context about the class semantics."
    )
    generalizations_prefixed_names: Optional[List[str]] = Field(
        default=None,
        description="List of prefixed names (i.e. :LocalName) of classes that are generalizations of this class."
    )
    kind: Kind = Field(
        description="The kind of the class (subject or object)."
    )
    definition_references: List[KnowledgeBaseReference] = Field(
        default_factory=list,
        description="List of references to knowledge base snippets or their fragments (using their IDs) that explicitly define this class."
    )
    specification_references: List[KnowledgeBaseReference] = Field(
        default_factory=list,
        description="List of references to knowledge base snippets or their fragments (using their IDs) that explicitly specify or describe this class."
    )
    references: List[KnowledgeBaseReference] = Field(
        default_factory=list,
        description="List of references to knowledge base snippets or their fragments (using their IDs) that generally reference this class without being explicit in defining, specifying or describing it."
    )


class AttributeOperationOutput(BaseModel):
    """
    Pydantic model representing an attribute operation to be performed on the ontology.
    """
    operation_type: str = Field(
        description="The type of operation: 'create', 'update', or 'delete'."
    )
    label: Optional[str] = Field(
        default=None,
        description="The human-readable label for the attribute (required for create operations)."
    )
    prefixed_name: str = Field(
        description="The prefixed name (i.e. :localName) of the attribute to create, update, or delete."
    )
    definition: Optional[str] = Field(
        default=None,
        description="A formal definition of the attribute."
    )
    description: Optional[str] = Field(
        default=None,
        description="A human-readable description providing more context about the attribute semantics."
    )
    owning_class_prefixed_name: Optional[str] = Field(
        default=None,
        description="The prefixed name (i.e. :localName) of the class that owns this attribute (required for create operations)."
    )
    definition_references: List[KnowledgeBaseReference] = Field(
        default_factory=list,
        description="List of references to knowledge base snippets or their fragments (using their IDs) that explicitly define this attribute."
    )
    specification_references: List[KnowledgeBaseReference] = Field(
        default_factory=list,
        description="List of references to knowledge base snippets or their fragments (using their IDs) that explicitly specify or describe this attribute."
    )
    references: List[KnowledgeBaseReference] = Field(
        default_factory=list,
        description="List of references to knowledge base snippets or their fragments (using their IDs) that generally reference this attribute without being explicit in defining, specifying or describing it."
    )


class RelationshipOperationOutput(BaseModel):
    """
    Pydantic model representing a relationship operation to be performed on the ontology.
    """
    operation_type: str = Field(
        description="The type of operation: 'create', 'update', or 'delete'."
    )
    label: Optional[str] = Field(
        default=None,
        description="The human-readable label for the relationship (required for create operations)."
    )
    prefixed_name: str = Field(
        description="The prefixed name (i.e. :localName) of the relationship to create, update, or delete."
    )
    definition: Optional[str] = Field(
        default=None,
        description="A formal definition of the relationship."
    )
    description: Optional[str] = Field(
        default=None,
        description="A human-readable description providing more context about the relationship semantics."
    )
    source_class_prefixed_name: Optional[str] = Field(
        default=None,
        description="The prefixed name (i.e. :localName) of the source class of this relationship (required for create operations)."
    )
    target_class_prefixed_name: Optional[str] = Field(
        default=None,
        description="The prefixed name (i.e. :localName) of the target class of this relationship (required for create operations)."
    )
    definition_references: List[KnowledgeBaseReference] = Field(
        default_factory=list,
        description="List of references to knowledge base snippets or their fragments (using their IDs) that explicitly define this relationship."
    )
    specification_references: List[KnowledgeBaseReference] = Field(
        default_factory=list,
        description="List of references to knowledge base snippets or their fragments (using their IDs) that explicitly specify or describe this relationship."
    )
    references: List[KnowledgeBaseReference] = Field(
        default_factory=list,
        description="List of references to knowledge base snippets or their fragments (using their IDs) that generally reference this relationship without being explicit in defining, specifying or describing it."
    )


class EditOperationsOutput(BaseModel):
    """
    Pydantic model representing the list of edit operations to be applied to the ontology.
    """
    class_operations: List[ClassOperationOutput] = Field(
        default_factory=list,
        description="The list of class operations to be performed on the ontology. Keep empty if the task does not focus on classes."
    )
    attribute_operations: List[AttributeOperationOutput] = Field(
        default_factory=list,
        description="The list of attribute operations to be performed on the ontology. Keep empty if the task does not focus on attributes."
    )
    relationship_operations: List[RelationshipOperationOutput] = Field(
        default_factory=list,
        description="The list of relationship operations to be performed on the ontology. Keep empty if the task does not focus on relationships."
    )

class ModelerAgent_Simple_OpenAI(ModelerAgent):
    """
    A simple implementation of ModelerAgent using OpenAI.
    """

    def __init__(self, knowledge_base_service: KnowledgeBaseService, knowledge_base_index_service: KnowledgeBaseIndexService, model_name: str = "gpt-5-mini"):
        """
        Initialize the simple modeler agent.

        Args:
            knowledge_base_service (KnowledgeBaseService): The knowledge base service instance for loading and accessing knowledge documents.
            knowledge_base_index_service (KnowledgeBaseIndexService): The knowledge base index service instance for searching in the knowledge base.
            model_name (str): The name of the model (defaults to "gpt-4o").
        """
        self.knowledge_base_service = knowledge_base_service
        self.knowledge_base_index_service = knowledge_base_index_service
        self.model_name = "gpt-5-mini"
        self.language = "Czech"

        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=api_key)


    #TODO - The current implementation pressumes that the ontology edit operations are directly applied to the ontology and that this edited ontology is then used in the next task.

    def get_operations_for_design_task(self, design_project: DesignProject, current_ontology: Ontology, iteration: DesignIteration, task: DesignTask) -> List[OntologyEditOperation]:
        """
        Gets the ontology edit operations for the given design task.

        Args:
            design_project (DesignProject): The design project containing the iteration.
            current_ontology (Ontology): The current ontology being modified. This ontology should reflect all changes made by previously executed tasks in the same iteration. We cannot work with the original ontology from the design_project as this needs to remain unchanged until the final list of operations for all tasks in the iteration is ready and approved.
            iteration (DesignIteration): The iteration in which the task is to be performed.
            task (DesignTask): The design task to be executed.

        Returns:
            List[OntologyEditOperation]: A list of ontology edit operations resulting from the task.
        """

        relevant_knowledge_document_elements = self._find_relevant_knowledge_document_elements(design_project, iteration, task)

        if task.followedPattern.category == DesignTaskCategory.CLASS:
            operations = self._generate_class_operations(design_project, current_ontology, iteration, task, relevant_knowledge_document_elements)
        elif task.followedPattern.category == DesignTaskCategory.ATTRIBUTE:
            operations = self._generate_attribute_operations(design_project, current_ontology, iteration, task, relevant_knowledge_document_elements)
        elif task.followedPattern.category == DesignTaskCategory.RELATIONSHIP:
            operations = self._generate_relationship_operations(design_project, current_ontology, iteration, task, relevant_knowledge_document_elements)
        else:
            raise ValueError(f"Unsupported ontology element category: {task.followedPattern.category}")

        return operations

    def _find_relevant_knowledge_document_elements(self, design_project: DesignProject, iteration: DesignIteration, task: DesignTask) -> List[KnowledgeDocumentElement]:

        query = task.specification.strip()
        
        search_result = self._search_relative(query, relative_difference=0.15)

        return search_result

    def _find_relevant_knowledge_document_elements_smarter(self, design_project: DesignProject, iteration: DesignIteration, task: DesignTask) -> List[KnowledgeDocumentElement]:

        system_prompt_prepare_search = f"""<ROLE>You are an expert in ontology modeling and knowledge domain analysis.</ROLE>

<GOAL>To perform the next ontology design task, you need to gather relevant domain knowledge snippets from a large collection of long documents that provide detailed domain knowledge specification. You must plan search queries to find relevant knowledge snippets.</GOAL>

<GOAL_CONTEXT>
You are working on designing the ontology "{design_project.designedOntology.label}" which models the domain "{design_project.modeledKnowledgeDomain.label}".
The current ontology is provided by the user in their user message.
You are working in iterations, the current iteration is "{iteration.name}" described as "{iteration.specification}".
The domain is separated into multiple areas, and the current iteration focuses on the area "{iteration.focusedArea.label}" described as "{iteration.focusedArea.description}".
The key concepts of the focused area are: {', '.join(iteration.focusedArea.keyConcepts) if iteration.focusedArea.keyConcepts else 'None'}.
The current iteration comprises a sequence of planned ontology design tasks.
The next ontology design task is "{task.name}" which strictly focuses only at "{task.followedPattern.category.value}" elements in the ontology.
This next ontology design step is specified as: "{task.specification}"
</GOAL_CONTEXT>

<KNOWLEDGE_BASE>
As a source of the domain knowledge to plan the search queries, use the summary of the domain knowledge provided by the user in their user message.
</KNOWLEDGE_BASE>

<INSTRUCTIONS>
- Plan one or more search queries to search relevant domain knowledge snippets in the detailed domain knowledge specification that will help you perform the ontology design task.
- You will use the found knowledge snippets later to generate specific ontology edit operations to complete the ontology design task.
- To construct the search queries, you must use the provided knowledge base, the domain language and domain terms from that knowledge base. Use the exact terms and phrases from the knowledge base but also their slight modifications to increase the recall.
- Strictly output the search queries in {self.language} language.
</INSTRUCTIONS>"""
        
        input_prepare_search = [
            {"role": "system", "content": system_prompt_prepare_search},
            {"role": "assistant", "content": "To gather relevant knowledge snippets for performing the design task, I need to plan search queries. First, what is the current ontology?"},
            {"role": "user", "content": self._ontology_to_prompt(design_project.designedOntology)},
            {"role": "assistant", "content": "Thank you. Now, please provide the summary of the domain knowledge that we can use as a source for planning the search queries."},
            {"role": "user", "content": self.knowledge_base_service.get_knowledge_document_outline_from_summaries(design_project.keyKnowledgeDocument)}
        ]

        messages_prepare_search = input_prepare_search[:]
        max_search_iterations = 8
        search_iteration = 0
        
        # Use a set to track unique elements by their ID to avoid duplicates
        seen_element_ids = set()
        all_search_outputs = []

        def _call_model_to_prepare_search(msgs):
            return self.client.responses.parse(
                model=self.model_name,
                input=msgs,
                text={
                    "verbosity": "low"
                },
                reasoning={
                    "effort": "minimal"
                },
                text_format=SearchQueriesDefinitionOutput
            )

        try:
            response = _call_model_to_prepare_search(messages_prepare_search)
            while search_iteration < max_search_iterations:
                search_iteration += 1
                current_iteration_outputs = []

                for item in response.output_parsed.queries:
                    query = item.query if hasattr(item, 'query') else None
                    max_results_val = item.max_results if hasattr(item, 'max_results') else 10
                    offset_val = item.offset if hasattr(item, 'offset') else 0

                    try:
                        max_results = int(max_results_val)
                    except (ValueError, TypeError):
                        max_results = 10
                    try:
                        offset = int(offset_val)
                    except (ValueError, TypeError):
                        offset = 0
                    # Guardrails
                    if max_results <= 0:
                        max_results = 10
                    if offset < 0:
                        offset = 0

                    search_output = self._search(query, max_results, offset)

                    if search_output:
                        snippets_xml = "\n".join([f"<snippet>{elem.content}</snippet>" for elem in search_output])

                        input_prepare_search.append({
                            "role": "assistant",
                            "content": "We searched the knowledge base with the query:\n" + query + " for max_results=" + str(max_results) + " and offset=" + str(offset) + " and found the following knowledge snippets:\n" + snippets_xml
                        })
                        
                        # Add unique elements to all_search_outputs
                        for element in search_output:
                            if element.id not in seen_element_ids:
                                seen_element_ids.add(element.id)
                                all_search_outputs.append(element)
                
                    # Add to current iteration for loop control
                    current_iteration_outputs.append(search_output)

                if current_iteration_outputs:
                    input_prepare_search.append({
                        "role": "user",
                        "content": "Based on the performed search queries, do you need to perform other search queries to obtain more relevant knowledge snippets to perform the ontology design task? If yes, plan one or more additional search queries to find more relevant knowledge snippets. If no, respond with an empty list."
                    })
                    response = _call_model_to_prepare_search(input_prepare_search)
                    continue
                break

        except Exception as e:
            raise RuntimeError(f"OpenAI API call with tool loop failed: {str(e)}")
        
        return all_search_outputs


#TODO!!!! Vrátil update operaci pro http://.../ZvlastniVozidlo, ale přitom správně mělo být https!!!

    def _get_goal_context(self, design_project: DesignProject, iteration: DesignIteration, task: DesignTask) -> str:
        return f"""<GOAL_CONTEXT>
- You are working on designing the ontology "{design_project.designedOntology.label}" which models the domain "{design_project.modeledKnowledgeDomain.label}".
- The current ontology is provided by the user in their user message.
- The domain is separated into multiple areas, now you focus on the area "{iteration.focusedArea.label}" described as "{iteration.focusedArea.description}".
- You work in iterations, the current iteration is "{iteration.name}" described as "{iteration.specification}".
- There is a planned sequence of ontology design tasks in the current iteration comprising finished, current, and planned tasks specified below. You must accomplish the solely current task in the context of the finished and planned tasks.
</GOAL_CONTEXT>"""
    
    def _get_tasks_context(self, iteration: DesignIteration, task: DesignTask) -> str:
        finished_tasks_str = (
            "".join(f"- {dt.name}: {dt.specification}\n" for dt in iteration.finishedTasks)
            if iteration.finishedTasks else "- None"
        )
        planned_tasks_str = (
            "".join(f"- {dt.name}: {dt.specification}\n" for dt in iteration.plannedTasks)
            if iteration.plannedTasks else "- None"
        )
        return f"""<FINISHED_DESIGN_TASKS>
{finished_tasks_str}
</FINISHED_DESIGN_TASKS>

<CURRENT_DESIGN_TASK>
- {task.name}: {task.specification}
</CURRENT_DESIGN_TASK>

<PLANNED_DESIGN_TASKS>
{planned_tasks_str}
</PLANNED_DESIGN_TASKS>"""
    
    def _get_domain_knowledge_context(self) -> str:
        return f"""<DOMAIN_KNOWLEDGE_BASE>
As a source of the domain knowledge to guide your decisions, use the domain knowledge provided by the user as a list of relevant domain knowledge snippets selected from the detailed domain knowledge specification.
</DOMAIN_KNOWLEDGE_BASE>"""
    
    def _get_context(self, design_project: DesignProject, iteration: DesignIteration, task: DesignTask) -> str:
        return f"""{self._get_goal_context(design_project, iteration, task)}

{self._get_tasks_context(iteration, task)}

{self._get_domain_knowledge_context()}"""
    
    def _get_generic_instructions(self) -> str:
        return f"""<INSTRUCTIONS>
- The user speaks {self.language} language, you must respond in {self.language} language.
- Generate ontology edit operations that are needed to accomplish the ontology design task.
- Focus solely on ontology elements as specified by the ontology design task.
- Consider the ontology metamodel described below.
- Work in the context of the finished as well as planned ontology design tasks in the current iteration - do not generate operations that would overtake to the scope of other design tasks.
- If the task or its part is already fulfilled satisfactorily by the current ontology, do not generate operations that would re-design respective ontology elements. Even an empty list of operations is acceptable in this case. However, you can generate operations that improve the respective ontology elements, based on the domain knowledge
- If the ontology design task requires designing a concrete new ontology element with a concrete label, you must change it if the provided domain knowledge requires a different label.
- Strictly output the labels, definitions, and descriptions in {self.language} language.
- Strictly double-check that IDs of references to knowledge base snippets that you provide actually exist in the provided relevant knowledge snippets.
- Strictly double-check that other ontology elements you reference in the operations (e.g. generalizations of a class, owning class of an attribute, source and target class of a relationship) actually exist in the current ontology.
- For the ontology edit operations, return definition, specification or generic references to the original knowledge base snippets (using snippet ID) to support your modeling decisions. If the content of the snippets is further structured into fragments represented as <f> XML elements with IDs, refer to the most specific fragments (using the snippet ID and fragment ID).
</INSTRUCTIONS>"""
    
    def _get_ontology_metamodel_description(self) -> str:
        return """<ONTOLOGY_METAMODEL>
- Ontology consists of the following elements: Classes, Attributes, Relationships.
- Class represents a primary entity in the domain that exists independently. It is the main subject or object of interest.
    - Subject: An entity with legal agency, capable of rights and obligations (e.g., a person, a company, a role).
    - Object: An entity that is the target of an action but has no legal agency (e.g., a document, a physical asset, a legal right).
    - A class X can generalize another class Y in the ontological (IS-A hierarchy) sense. X generalizes Y if and only if every instance of Y is also an instance of X, i.e. for any instance y of Y, we can also say that 'y is an X'.
- Attribute is a simple, literal property of a single Class (e.g., a name, a date, a number)
    - It represents an intrinsic property of the class, inseparable from that class.
    - It represents a single fact, like a simple field in a form.
    - Its values are simple and primitive (e.g., string, number, date).
- Relationship is a binary directed semantic link that describes how one Class is related to another.
    - It is a property of the first class (the domain) that points to the second class (the range).
    - It cannot exist without the two classes it connects.
    - It represents a property whose value is a complex object (another class).
- No cardinalities.
- No primary keys.
- No primitive datatypes.
</ONTOLOGY_METAMODEL>"""

    def _generate_class_operations(self, design_project: DesignProject, current_ontology: Ontology, iteration: DesignIteration, task: DesignTask, relevant_knowledge_document_elements: List[KnowledgeDocumentElement], ) -> List[OntologyEditOperation]:
        system_prompt_generate_operations = f""""<ROLE>You are an expert ontology modeler specializing in modeling ontology classes.</ROLE>

<GOAL>Based on the provided domain knowledge and current ontology state, determine what classes need to be created, updated, or deleted to accomplish the current ontology design task.</GOAL>

{self._get_context(design_project, iteration, task)}

{self._get_generic_instructions()}

<CLASS_SPECIFIC_INSTRUCTIONS>
- For each new or updated class, ensure that you specify the following details based on the domain knowledge:
    - label: Unique, human readable (diacritics, space separated words), concrete, short label, noun/noun phrase, first letter upper-case (e.g. "Kosmická loď"). Mandatory.
    - prefixed_name: Unique URI in the prefixed form, valid, based on the label, no diacritics, e.g. ":KosmickaLod". Mandatory.
    - definition: Concise, non-circular, exact, self-contained, domain-oriented; preferably one or two sentences; preferably quotes definition from the domain knowledge with only minor linguistic modifications; no references to the knowledge base. E.g. 'Kosmická loď je dopravní prostředek určený k přepravě osob, zvířat nebo věcí ve vesmíru.'. Mandatory for create operations, optional for update operations if the existing definition can be improved.
    - description: Explains the class meaning, expanding on semantics without introducing extraneous context; self-contained, domain-oriented; no technical-ontology-expert jargon; do not explain the class but the semantic concept behind it; must summarize all important and relevant domain aspects throughout the domain knowledge; preferably a paragraph. E.g. 'Kosmická loď zahrnuje obecně všechny prostředky pro přepravu do a ve vesmíru. Zahrnuje jak lodě schopné startovat ze zemského povrchu, tak z povrchu jiných planet, tak i prostředky schopné startovat pouze z oběžné dráhy vesmírného objektu.'. Mandatory for create operations, optional for update operations if the existing description can be improved.
    - generalization_prefixed_names: List of prefixed names of classes that are direct, named superclasses of this class in the IS-A (specialization) hierarchy. Mandatory only when the task explicitly requests to model the generalization (either in the generalization or specialization direction). If present, ensure that the specified generalizations actually exist in the current ontology.
    - kind: The kind of the class - either subject or object. Mandatory.
    - definition_references: One or more references to knowledge base snippets or their <f> fragments (using their IDs) that explicitly define this class - use when the content of the snippet includes a definitory phrase that introduces the class.
    - specification_references: One or more references to knowledge base snippets or their <f> fragments (using their IDs) that explicitly specify or describe this class - use when the content of the snippet includes a specification of the class semantics, meaning, context, usage, etc. but is not definitory.
    - references: One or more generic references to knowledge base snippets or their <f> fragments (using their IDs) that generally reference this class without being explicit in defining, specifying or describing it.
</CLASS_SPECIFIC_INSTRUCTIONS>

{self._get_ontology_metamodel_description()}
"""
        return self._generate_operations(design_project, current_ontology, iteration, task, relevant_knowledge_document_elements, system_prompt_generate_operations)
    
    def _generate_attribute_operations(self, design_project: DesignProject, current_ontology: Ontology, iteration: DesignIteration, task: DesignTask, relevant_knowledge_document_elements: List[KnowledgeDocumentElement], ) -> List[OntologyEditOperation]:
        system_prompt_generate_operations = f""""<ROLE>You are an expert ontology modeler specializing in modeling ontology attributes (datatype properties).</ROLE>

<GOAL>Based on the provided domain knowledge and current ontology state, determine what attributes need to be created, updated, or deleted to accomplish the given design task.</GOAL>

{self._get_context(design_project, iteration, task)}

{self._get_generic_instructions()}

<ATTRIBUTE_SPECIFIC_INSTRUCTIONS>
- For each attribute, ensure that you specify the following details based on the domain knowledge:
    - label: Unique, human readable (diacritics, space separated words), concrete, short label, noun/noun phrase, lower case. Includes the ontology owning class's label linguistically incorporated (e.g. "barva kosmické lodi" instead of "barva"). Mandatory.
    - prefixed_name: Unique URI in the prefixed form, valid, based on the label, no diacritics, e.g. ":barvaKosmickeLodi". Mandatory.
    - definition: Concise, non-circular, exact, self-contained, domain-oriented; preferably one or two sentences; preferably quotes legal definition from the legal knowledge with only minor linguistic modifications. Mandatory for create operations, optional for update operations if the existing definition can be improved.
    - description: Explains the attribute meaning, expanding on semantics without introducing extraneous context; self-contained, domain-oriented; no technical-ontology-expert jargon; do not explain the attribute but the semantic concept behind it; must summarize all important and relevant domain aspects throughout the domain knowledge. Mandatory for create operations, optional for update operations if the existing description can be improved.
    - owning_class_prefixed_name: The prefixed name of the class that owns this attribute. It must be a class that already exists in the ontology. Mandatory.
    - definition_references: One or more references to knowledge base snippets or their <f> fragments (using their IDs) that explicitly define this attribute - use when the content of the snippet includes a definitory phrase that introduces the attribute.
    - specification_references: One or more references to knowledge base snippets or their <f> fragments (using their IDs) that explicitly specify or describe this attribute - use when the content of the snippet includes a specification of the attribute semantics, meaning, context, usage, etc. but is not definitory.
    - references: One or more generic references to knowledge base snippets or their <f> fragments (using their IDs) that generally reference this attribute without being explicit in defining, specifying or describing it.
</ATTRIBUTE_SPECIFIC_INSTRUCTIONS>

{self._get_ontology_metamodel_description()}
"""
        
        return self._generate_operations(design_project, current_ontology, iteration, task, relevant_knowledge_document_elements, system_prompt_generate_operations)
    
    def _generate_relationship_operations(self, design_project: DesignProject, current_ontology: Ontology, iteration: DesignIteration, task: DesignTask, relevant_knowledge_document_elements: List[KnowledgeDocumentElement], ) -> List[OntologyEditOperation]:
        system_prompt_generate_operations = f""""<ROLE>You are an expert ontology modeler specializing in modeling ontology relationships (object properties).</ROLE>

<GOAL>Based on the provided domain knowledge and current ontology state, determine what relationships need to be created, updated, or deleted to accomplish the given design task.</GOAL>

{self._get_context(design_project, iteration, task)}

{self._get_generic_instructions()}

<RELATIONSHIP_SPECIFIC_INSTRUCTIONS>
- For each relationship, ensure that you specify the following details based on the domain knowledge:
    - label: Unique, human readable (diacritics, space separated words), concrete, short label, verb/verb phrase, lower case. Includes the ontology source class's label linguistically incorporated (e.g. "je kapitánem kosmické lodi" instead of "je kapitánem" or "je"). Mandatory.
    - prefixed_name: Unique URI in the prefixed form, valid, based on the label, no diacritics, e.g. ":jeKapitanemKosmickeLodi". Mandatory.
    - definition: Concise, non-circular, exact, self-contained, domain-oriented; preferably one or two sentences; preferably quotes legal definition from the legal knowledge with only minor linguistic modifications. Mandatory for create operations, optional for update operations if the existing definition can be improved.
    - description: Explains the relationship meaning, expanding on semantics without introducing extraneous context; self-contained, domain-oriented; no technical-ontology-expert jargon; do not explain the relationship but the semantic concept behind it; must summarize all important and relevant domain aspects throughout the domain knowledge. Mandatory for create operations, optional for update operations if the existing description can be improved.
    - source_class_prefixed_name: The prefixed name of the class that this relationship starts at (i.e., the domain class). It must be a class that already exists in the ontology. Mandatory.
    - target_class_prefixed_name: The prefixed name of the class that this relationship ends at (i.e., the range class). It must be a class that already exists in the ontology. Mandatory.
    - definition_references: One or more references to knowledge base snippets or their <f> fragments (using their IDs) that explicitly define this relationship - use when the content of the snippet includes a definitory phrase that introduces the relationship.
    - specification_references: One or more references to knowledge base snippets or their <f> fragments (using their IDs) that explicitly specify or describe this relationship - use when the content of the snippet includes a specification of the relationship semantics, meaning, context, usage, etc. but is not definitory.
    - references: One or more generic references to knowledge base snippets or their <f> fragments (using their IDs) that generally reference this relationship without being explicit in defining, specifying or describing it.
</RELATIONSHIP_SPECIFIC_INSTRUCTIONS>

{self._get_ontology_metamodel_description()}
"""
        
        return self._generate_operations(design_project, current_ontology, iteration, task, relevant_knowledge_document_elements, system_prompt_generate_operations)
        
    def _local_name_to_full_uri(self, prefixed_name: str, ontology_uri: str) -> Optional[URIRef]:
        """
        Convert a local name (e.g., ":LocalName") to a full URI using the ontology base URI.
        
        Args:
            prefixed_name: The prefixed name in the format ":LocalName"
            ontology_uri: The base URI of the ontology
            
        Returns:
            Optional[URIRef]: The full URI as a URIRef object, or None if the prefixed_name is invalid/empty
        """
        if not prefixed_name or not prefixed_name.startswith(':'):
            return None
        
        local_name = prefixed_name[1:]  # Remove the ':' prefix
        # If LLM returned e.g. ":turistické-cíle#SilnicniVozidlo", use only the fragment after last '#'
        if '#' in local_name:
            local_name = local_name.split('#')[-1]
        
        # If local name is empty after removing ':', return None
        if not local_name.strip():
            return None
        
        # Ensure ontology URI ends with # or / for proper concatenation
        if not ontology_uri.endswith(('#', '/')):
            ontology_uri += '#'
        
        full_uri = ontology_uri + local_name
        return URIRef(full_uri)

    def _local_names_to_full_uris(self, prefixed_names: List[str], ontology_uri: str) -> Optional[List[URIRef]]:
        """
        Convert a list of local names (e.g., [":LocalName1", ":LocalName2"]) to full URIs using the ontology base URI.
        Filters out invalid/empty prefixed names.
        
        Args:
            prefixed_names: List of prefixed names in the format [":LocalName1", ":LocalName2"]
            ontology_uri: The base URI of the ontology
            
        Returns:
            Optional[List[URIRef]]: List of full URIs as URIRef objects, or None if no valid URIs were found
        """
        if not prefixed_names:
            return None
            
        valid_uris = [
            uri for uri in 
            [self._local_name_to_full_uri(prefixed_name, ontology_uri) for prefixed_name in prefixed_names]
            if uri is not None
        ]
        
        return valid_uris if valid_uris else None

    def _convert_kb_references_to_strings(self, references: List[KnowledgeBaseReference]) -> List[str]:
        """
        Convert a list of KnowledgeBaseReference objects to string references.
        
        Args:
            references: List of KnowledgeBaseReference objects
            
        Returns:
            List[str]: List of string references
            
        Rules:
            - If only snippet_id: return snippet_id
            - If both snippet_id and fragment_id: return snippet_id + fragment_id (concatenated)
            - If only fragment_id:
                - If starts with "http://": return fragment_id
                - Otherwise: raise exception
        """
        if not references:
            return []
        
        result = []
        for ref in references:
            if ref.snippet_id and ref.fragment_id:
                # Both present: concatenate without separator
                result.append(ref.snippet_id + ref.fragment_id)
            elif ref.snippet_id:
                # Only snippet_id
                result.append(ref.snippet_id)
            elif ref.fragment_id:
                # Only fragment_id
                if ref.fragment_id.startswith("http://"):
                    result.append(ref.fragment_id)
                else:
                    raise ValueError(f"Fragment ID '{ref.fragment_id}' without snippet_id must be an absolute IRI starting with 'http://'")
            else:
                # Neither present - skip this reference
                continue
        
        return result

    def _generate_operations(self, design_project: DesignProject, current_ontology: Ontology, iteration: DesignIteration, task: DesignTask, relevant_knowledge_document_elements: List[KnowledgeDocumentElement], system_prompt_generate_operations: str) -> List[OntologyEditOperation]:

        # Group knowledge document elements by their root document using document id

        def get_root_document_info(elem):
            current = elem
            while getattr(current, 'parentElement', None) is not None:
                current = current.parentElement
            doc_id = getattr(current, 'id', 'unknown_id')
            doc_title = getattr(current, 'title', 'Unknown Document')
            return doc_id, doc_title

        # Build mapping: document_id -> (document_title, list of snippets)
        doc_snippets = defaultdict(lambda: {"title": "", "snippets": []})
        for elem in relevant_knowledge_document_elements:
            doc_id, doc_title = get_root_document_info(elem)
            doc_snippets[doc_id]["title"] = doc_title
            # Trim the id attribute in <f> tags to keep only the local part after elem.id
            def trim_f_tag_ids(content, base_id):
                # Replace id attribute values that start with base_id, keeping only the local part
                pattern = r'(<f\s+[^>]*id=")[^"]*' + re.escape(base_id) + r'([^"]*"[^>]*>)'
                return re.sub(pattern, r'\1\2', content)
            
            cleaned_content = trim_f_tag_ids(elem.content, elem.id)
            doc_snippets[doc_id]["snippets"].append(f"<snippet id=\"{elem.id}\">{cleaned_content}</snippet>")

        # Build XML output grouped by <knowledge-document>
        snippets_xml = "\n".join(
            f"<knowledge-document title=\"{doc_info['title']}\">\n{''.join(doc_info['snippets'])}\n</knowledge-document>"
            for doc_info in doc_snippets.values()
        )

        input_generate_operations = [
            {"role": "system", "content": system_prompt_generate_operations},
            {"role": "assistant", "content": "To determine the necessary operations for performing the design task, I need to analyze the current ontology and relevant domain knowledge. First, what is the current ontology?"},
            {"role": "user", "content": self._ontology_to_prompt(current_ontology)},
            #{"role": "assistant", "content": "Thank you. Now, please provide the summary of the domain knowledge that we can use as a domain knowledge context for performing the design task."},
            #{"role": "user", "content": self.knowledge_base_service.get_knowledge_document_outline_from_summaries(design_project.keyKnowledgeDocument)},
            {"role": "assistant", "content": "Great. Now, please provide the relevant knowledge snippets from the detailed domain knowledge specification that you found useful for performing the ontology design task."},
            {"role": "user", "content": snippets_xml},
        ]

        operations_output = None

        # Generate edit operations
        try:
            response = self.client.responses.parse(
                model=self.model_name,
                input=input_generate_operations,
                text={
                    "verbosity": "low"
                },
                reasoning={
                    "effort": "minimal"
                },
                text_format=EditOperationsOutput
            )
            
            operations_output = response.output_parsed
        except Exception as e:
            print(f"Error generating edit operations: {e}")
            return []

        # Step 4: Convert Pydantic models to actual edit operation objects
        edit_operations = []
        
        # Process class operations
        for class_op in operations_output.class_operations:
            try:
                uri = self._local_name_to_full_uri(class_op.prefixed_name, design_project.designedOntology.uri)
                if uri is None:
                    print(f"Skipping class operation with invalid prefixed_name: {class_op.prefixed_name}")
                    continue
                    
                generalization_uris = None
                if class_op.generalizations_prefixed_names:
                    generalization_uris = self._local_names_to_full_uris(class_op.generalizations_prefixed_names, design_project.designedOntology.uri)
                
                if class_op.operation_type == "create":
                    edit_operations.append(CreateClassOperation(
                        uri=uri,
                        label=class_op.label,
                        definition=class_op.definition,
                        description=class_op.description,
                        generalization_uris=generalization_uris,
                        kind=class_op.kind,
                        definition_references=self._convert_kb_references_to_strings(class_op.definition_references),
                        specification_references=self._convert_kb_references_to_strings(class_op.specification_references),
                        references=self._convert_kb_references_to_strings(class_op.references)
                    ))
                elif class_op.operation_type == "update":
                    edit_operations.append(UpdateClassOperation(
                        uri=uri,
                        label=class_op.label,
                        definition=class_op.definition,
                        description=class_op.description,
                        generalization_uris=generalization_uris,
                        kind=class_op.kind,
                        definition_references=self._convert_kb_references_to_strings(class_op.definition_references),
                        specification_references=self._convert_kb_references_to_strings(class_op.specification_references),
                        references=self._convert_kb_references_to_strings(class_op.references)
                    ))
                elif class_op.operation_type == "delete":
                    edit_operations.append(DeleteClassOperation(uri=uri))
            except Exception as e:
                print(f"Error processing class operation {class_op}: {e}")
                continue
        
        # Process attribute operations
        for attr_op in operations_output.attribute_operations:
            try:
                uri = self._local_name_to_full_uri(attr_op.prefixed_name, design_project.designedOntology.uri)
                if uri is None:
                    print(f"Skipping attribute operation with invalid prefixed_name: {attr_op.prefixed_name}")
                    continue
                    
                owning_class_uri = None
                if attr_op.owning_class_prefixed_name:
                    owning_class_uri = self._local_name_to_full_uri(attr_op.owning_class_prefixed_name, design_project.designedOntology.uri)
                    if owning_class_uri is None:
                        print(f"Skipping attribute operation with invalid owning_class_prefixed_name: {attr_op.owning_class_prefixed_name}")
                        continue
                
                if attr_op.operation_type == "create":
                    edit_operations.append(CreateAttributeOperation(
                        uri=uri,
                        label=attr_op.label,
                        owning_class_uri=owning_class_uri,
                        definition=attr_op.definition,
                        description=attr_op.description,
                        definition_references=self._convert_kb_references_to_strings(attr_op.definition_references),
                        specification_references=self._convert_kb_references_to_strings(attr_op.specification_references),
                        references=self._convert_kb_references_to_strings(attr_op.references)
                    ))
                elif attr_op.operation_type == "update":
                    edit_operations.append(UpdateAttributeOperation(
                        uri=uri,
                        label=attr_op.label,
                        owning_class_uri=owning_class_uri,
                        definition=attr_op.definition,
                        description=attr_op.description,
                        definition_references=self._convert_kb_references_to_strings(attr_op.definition_references),
                        specification_references=self._convert_kb_references_to_strings(attr_op.specification_references),
                        references=self._convert_kb_references_to_strings(attr_op.references)
                    ))
                elif attr_op.operation_type == "delete":
                    edit_operations.append(DeleteAttributeOperation(uri=uri))
            except Exception as e:
                print(f"Error processing attribute operation {attr_op}: {e}")
                continue
        
        # Process relationship operations
        for rel_op in operations_output.relationship_operations:
            try:
                uri = self._local_name_to_full_uri(rel_op.prefixed_name, design_project.designedOntology.uri)
                if uri is None:
                    print(f"Skipping relationship operation with invalid prefixed_name: {rel_op.prefixed_name}")
                    continue
                    
                source_class_uri = None
                target_class_uri = None
                if rel_op.source_class_prefixed_name:
                    source_class_uri = self._local_name_to_full_uri(rel_op.source_class_prefixed_name, design_project.designedOntology.uri)
                    if source_class_uri is None:
                        print(f"Skipping relationship operation with invalid source_class_prefixed_name: {rel_op.source_class_prefixed_name}")
                        continue
                if rel_op.target_class_prefixed_name:
                    target_class_uri = self._local_name_to_full_uri(rel_op.target_class_prefixed_name, design_project.designedOntology.uri)
                    if target_class_uri is None:
                        print(f"Skipping relationship operation with invalid target_class_prefixed_name: {rel_op.target_class_prefixed_name}")
                        continue
                
                if rel_op.operation_type == "create":
                    edit_operations.append(CreateRelationshipOperation(
                        uri=uri,
                        label=rel_op.label,
                        source_class_uri=source_class_uri,
                        target_class_uri=target_class_uri,
                        definition=rel_op.definition,
                        description=rel_op.description,
                        definition_references=self._convert_kb_references_to_strings(rel_op.definition_references),
                        specification_references=self._convert_kb_references_to_strings(rel_op.specification_references),
                        references=self._convert_kb_references_to_strings(rel_op.references)
                    ))
                elif rel_op.operation_type == "update":
                    edit_operations.append(UpdateRelationshipOperation(
                        uri=uri,
                        label=rel_op.label,
                        source_class_uri=source_class_uri,
                        target_class_uri=target_class_uri,
                        definition=rel_op.definition,
                        description=rel_op.description,
                        definition_references=self._convert_kb_references_to_strings(rel_op.definition_references),
                        specification_references=self._convert_kb_references_to_strings(rel_op.specification_references),
                        references=self._convert_kb_references_to_strings(rel_op.references)
                    ))
                elif rel_op.operation_type == "delete":
                    edit_operations.append(DeleteRelationshipOperation(uri=uri))
            except Exception as e:
                print(f"Error processing relationship operation {rel_op}: {e}")
                continue

        return edit_operations
    
    def _search(self, query: str, max_results=10, offset=0) -> List[KnowledgeDocumentElement]:
        """
        Search the knowledge base for relevant knowledge document elements.

        Args:
            query (str): The search query.
            max_results (int): Maximum number of results to return. Defaults to 10.
            offset (int): Number of top results to skip (0 means no skipping). Defaults to 0.

        Returns:
            str: The relevant knowledge snippets as a list of XML elements <knowledge_snippet />.
        """
        search_results = self.knowledge_base_index_service.search(query, max_results, offset)

        return search_results

    def _search_relative(self, query: str, relative_difference: float = 0.25) -> List[KnowledgeDocumentElement]:
        """
        Search the knowledge base for relevant knowledge document elements.

        Args:
            query (str): The search query.
            relative_difference (float): The relative difference threshold for filtering results. Defaults to 0.25.

        Returns:
            str: The relevant knowledge snippets as a list of XML elements <knowledge_snippet />.
        """
        search_results = self.knowledge_base_index_service.search_relative(query, relative_difference)

        return search_results

    def prefix_uri(self, element_uri, ontology_uri) -> str:
        """
        Convert a full URI to a prefixed URI relative to the ontology URI.
        
        Args:
            element_uri: The full URI of the ontology element
            ontology_uri: The base URI of the ontology
            
        Returns:
            str: The prefixed URI (without the : prefix)
        """
        if not element_uri or not ontology_uri:
            return str(element_uri) if element_uri else ""
        
        element_str = str(element_uri)
        ontology_str = str(ontology_uri)
        
        # Extract the namespace from the ontology URI
        # This handles cases where elements share the same namespace as the ontology
        ontology_namespace = ontology_str.rstrip('#/') + '#'
        if not ontology_str.endswith(('#', '/')):
            # If ontology URI doesn't end with # or /, try extracting the base
            if '/' in ontology_str:
                ontology_namespace = ontology_str.rsplit('/', 1)[0] + '/'
        
        # Check if element is in the same namespace
        if element_str.startswith(ontology_namespace):
            # Remove the namespace part
            relative_part = element_str[len(ontology_namespace):]
            return relative_part
        elif element_str.startswith(ontology_str.rstrip('#/')):
            # Check if it starts with the ontology base without separator
            base_uri = ontology_str.rstrip('#/')
            if element_str.startswith(base_uri + '/'):
                relative_part = element_str[len(base_uri + '/'):]
                return relative_part
            elif element_str.startswith(base_uri + '#'):
                relative_part = element_str[len(base_uri + '#'):]
                return relative_part
        
        # If not under the ontology namespace, return the full URI
        return f"<{element_str}>"

    def _ontology_to_prompt(self, ontology: Ontology) -> str:
        """
        Convert an ontology to a compact string representation suitable for Modeler.
        Shows complete semantic information including definitions - optimized for generating edit operations.
        
        Args:
            ontology: The ontology object to serialize
            
        Returns:
            str: Compact full semantic view representation
        """
        if ontology is None:
            return "ONTOLOGY: Empty"
        
        if not ontology.uri:
            raise ValueError("Ontology must have a valid URI to be serialized.")
        
        lines = []
        
        # Ontology header
        ontology_prefix = self.prefix_uri(ontology.uri, ontology.uri)
        if not ontology_prefix:
            ontology_prefix = ":"
        elif not ontology_prefix.startswith(":"):
            ontology_prefix = f":{ontology_prefix}"
        
        lines.append(f'ONTOLOGY: {ontology_prefix} "{ontology.label}"')
        lines.append("")
        
        # Classes section
        lines.append(f"CLASSES ({len(ontology.classes)}):")
        
        if ontology.classes:
            # Sort classes by label for consistent output
            sorted_classes = sorted(
                ontology.classes.items(),
                key=lambda x: x[1].label if x[1].label else ""
            )
            
            for class_uri, ontology_class in sorted_classes:
                prefixed_class = self.prefix_uri(class_uri, ontology.uri)
                if not prefixed_class.startswith(":"):
                    prefixed_class = f":{prefixed_class}"
                
                kind_str = f"[{ontology_class.kind.value.upper()}]"
                lines.append(f'  {prefixed_class} "{ontology_class.label}" {kind_str}')
                
                # Definition
                definition = ontology_class.definition or ontology_class.description
                if definition:
                    lines.append(f"    DEF: {definition}")
                
                # Superclasses (references only - URI only)
                if ontology_class.generalizations:
                    super_refs = []
                    for parent in ontology_class.generalizations:
                        if parent.uri:
                            prefixed_parent = self.prefix_uri(parent.uri, ontology.uri)
                            if not prefixed_parent.startswith(":"):
                                prefixed_parent = f":{prefixed_parent}"
                            super_refs.append(prefixed_parent)
                    lines.append(f"    SUPER: {', '.join(super_refs)}")
                else:
                    lines.append("    SUPER: (none)")
                
                # Attributes (introductions with definitions)
                if ontology_class.attributes:
                    lines.append("    ATTRS:")
                    for attr in sorted(ontology_class.attributes, key=lambda x: x.label if x.label else ""):
                        prefixed_attr = self.prefix_uri(attr.uri, ontology.uri)
                        if not prefixed_attr.startswith(":"):
                            prefixed_attr = f":{prefixed_attr}"
                        lines.append(f'      - {prefixed_attr} "{attr.label}"')
                        
                        attr_definition = attr.definition or attr.description
                        if attr_definition:
                            lines.append(f"        DEF: {attr_definition}")
                else:
                    lines.append("    ATTRS: (none)")
                
                lines.append("")  # Empty line between classes
        else:
            lines.append("  (none)")
            lines.append("")
        
        # Relationships section
        lines.append(f"RELATIONSHIPS ({len(ontology.relationships)}):")
        
        if ontology.relationships:
            # Sort relationships by label for consistent output
            sorted_relationships = sorted(
                ontology.relationships.items(),
                key=lambda x: x[1].label if x[1].label else ""
            )
            
            for rel_uri, relationship in sorted_relationships:
                prefixed_rel = self.prefix_uri(rel_uri, ontology.uri)
                if not prefixed_rel.startswith(":"):
                    prefixed_rel = f":{prefixed_rel}"
                
                lines.append(f'  {prefixed_rel} "{relationship.label}"')
                
                # Definition
                rel_definition = relationship.definition or relationship.description
                if rel_definition:
                    lines.append(f"    DEF: {rel_definition}")
                
                # Source and target (references only - URI only)
                source_ref = "(none)"
                if relationship.sourceClass and relationship.sourceClass.uri:
                    source_ref = self.prefix_uri(relationship.sourceClass.uri, ontology.uri)
                    if not source_ref.startswith(":"):
                        source_ref = f":{source_ref}"
                
                target_ref = "(none)"
                if relationship.targetClass and relationship.targetClass.uri:
                    target_ref = self.prefix_uri(relationship.targetClass.uri, ontology.uri)
                    if not target_ref.startswith(":"):
                        target_ref = f":{target_ref}"
                
                lines.append(f"    FROM: {source_ref}  TO: {target_ref}")
                lines.append("")  # Empty line between relationships
        else:
            lines.append("  (none)")
        
        return '\n'.join(lines)