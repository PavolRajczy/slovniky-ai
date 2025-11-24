from collections import defaultdict
import os
import json
import re
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

from openai import OpenAI

from agents.iteration_suggesters.iteration_suggester import IterationSuggesterAgent
from agents.task_planners.task_planner import TaskPlannerAgent
from design_project.design_task_patterns_factory import DesignTaskPatternsFactory_Basic
from design_project.domain import DesignIteration, DesignIterationStatus, DesignProject, DesignTask, DesignTaskStatus, KnowledgeDomainArea
from knowledge_base.domain import KnowledgeDocumentElement
from knowledge_base.service import KnowledgeBaseService
from knowledge_base_index.service import KnowledgeBaseIndexService
from ontology.domain import Ontology
import uuid

class DesignTaskOutput(BaseModel):
    """
    Pydantic model representing a single suggested design task for the given design iteration.
    """
    name: str = Field(
        description="A human-readable name for the design task that clearly identifies its purpose."
    )
    followedPatternName: str = Field(
        description="The name of the design task pattern that this task follows. It is mandatory that a design task follows exactly one design task pattern. The pattern must be chosen from the list of supported design patterns."
    )
    specification: str = Field(
        description="A detailed description of the design task that implements the followed pattern into the specific context of the design iteration."
    )

class DesignTasksOutput(BaseModel):
    """
    Pydantic model representing the ordered list of suggested design tasks to completely execute the iteration.
    """
    tasks: List[DesignTaskOutput] = Field(
        description="The list of suggested tasks to be performed to completely execute the iteration. The design tasks must be listed in the order in which they should be executed."
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

class TaskPlannerAgent_Simple_OpenAI(TaskPlannerAgent):
    """
    A simple implementation of TaskPlannerAgent using OpenAI.
    """

    def __init__(self, knowledge_base_service: KnowledgeBaseService, knowledge_base_index_service: KnowledgeBaseIndexService, model_name: str = "gpt-5"):
        """
        Initialize the simple task planner agent.

        Args:
            knowledge_base_service (KnowledgeBaseService): The knowledge base service instance for loading and accessing knowledge documents.
            knowledge_base_index_service (KnowledgeBaseIndexService): The knowledge base index service instance for searching in the knowledge base.
            model_name (str): The name of the model (defaults to "gpt-4.1").
        """
        self.knowledge_base_service = knowledge_base_service
        self.knowledge_base_index_service = knowledge_base_index_service
        self.model_name = "gpt-5"
        self.language = "Czech"

        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        self.client = OpenAI(api_key=api_key)

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

        relevant_knowledge_document_elements = self._find_relevant_knowledge_document_elements(design_project, iteration, user_instruction)

        planned_tasks = self._generate_ontology_design_tasks(design_project, iteration, user_instruction, relevant_knowledge_document_elements)

        return planned_tasks

    def _find_relevant_knowledge_document_elements(self, design_project: DesignProject, iteration: DesignIteration, user_instruction: str) -> List[KnowledgeDocumentElement]:
        query = iteration.specification.strip()

        if user_instruction:
            query += " " + user_instruction.strip()
        
        search_result = self._search_relative(query, relative_difference=0.15)

        return search_result

    def _find_relevant_knowledge_document_elements_smarter(self, design_project: DesignProject, iteration: DesignIteration, user_instruction: str) -> List[KnowledgeDocumentElement]:

        system_prompt_prepare_search = f"""<ROLE>You are an expert in knowledge domain analysis and iterative ontology design.</ROLE>

<GOAL>To plan the next iteration of the ontology design process in the form of a detailed plan of individual ontology design tasks, you need to gather relevant domain knowledge snippets from a large collection of long documents that provide detailed domain knowledge specification. You must plan search queries to find relevant knowledge snippets.</GOAL>

<GOAL_CONTEXT>
You are working on designing the ontology "{design_project.designedOntology.label}" which models the domain "{design_project.modeledKnowledgeDomain.label}".
The current ontology is provided by the user in their user message.
You are working in iterations, the next planned iteration is "{iteration.name}" described as "{iteration.specification}".
The domain is separated into multiple areas, and the next iteration focuses on the area "{iteration.focusedArea.label}" described as "{iteration.focusedArea.description}".
The key concepts of the focused area are: {', '.join(iteration.focusedArea.keyConcepts) if iteration.focusedArea.keyConcepts else 'None'}.
</GOAL_CONTEXT>

<KNOWLEDGE_BASE>
As a source of the domain knowledge to plan the search queries, use the summary of the domain knowledge provided by the user in their user message.
</KNOWLEDGE_BASE>

<INSTRUCTIONS>
- Plan one or more search queries to search relevant domain knowledge snippets in the detailed domain knowledge specification that will help you plan the ontology design tasks for the next iteration.
- You will use the found knowledge snippets later to plan the design tasks for the next iteration in detail.
- Consider, that the planned ontology design tasks must completely achieve the goal of the iteration.
- Consider, that the planned ontology design tasks must each follow exactly one design task pattern from the catalogue of design tasks patterns listed below.
- To construct the search queries, you must use the provided knowledge base, the domain language and domain terms from that knowledge base. Use the exact terms and phrases from the knowledge base but also their slight modifications to increase the recall.
- If the user customization instruction is specified, the planned ontology design tasks must be guided by it.
- Strictly output the search queries in {self.language} language.
</INSTRUCTIONS>

<DESIGN_TASK_PATTERNS_CATALOGUE>
{self._get_patterns_catalogue_xml(design_project.patterns)}
</DESIGN_TASK_PATTERNS_CATALOGUE>"""

        document_outline = self.knowledge_base_service.get_knowledge_document_outline_from_summaries(design_project.keyKnowledgeDocument)

        user_prompt_prepare_search = f"""<CURRENT_ONTOLOGY>
{self._ontology_to_prompt(design_project.designedOntology) if design_project.designedOntology else 'None'}
</CURRENT_ONTOLOGY>
<OVERVIEW_DOCUMENT>
{document_outline}
</OVERVIEW_DOCUMENT>"""

        input_prepare_search = [
            {"role": "system", "content": system_prompt_prepare_search},
            {"role": "user", "content": user_prompt_prepare_search}
        ]

        input_prepare_search = [
            {"role": "system", "content": system_prompt_prepare_search},
            {"role": "assistant", "content": "To gather relevant knowledge snippets for planning the ontology design tasks, I need to plan search queries. First, what is the current ontology?"},
            {"role": "user", "content": self._ontology_to_prompt(design_project.designedOntology)},
            {"role": "assistant", "content": "Thank you. Now, please provide the summary of the domain knowledge that we can use as a source for planning the search queries."},
            {"role": "user", "content": self.knowledge_base_service.get_knowledge_document_outline_from_summaries(design_project.keyKnowledgeDocument)}
        ]

        if user_instruction:
            input_prepare_search.append({
                "role": "assistant",
                "content": "Do you want to customize how the the ontology design tasks are planned?"
            })
            input_prepare_search.append({
                "role": "user",
                "content": f"Customize your analysis with this instruction that is very important for me: {user_instruction}"
            })

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
                text_format=SearchQueriesDefinitionOutput,
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
                        "content": "Based on the performed search queries, do you need to perform other search queries to obtain more relevant knowledge snippets to plan the ontology design task? If yes, plan one or more additional search queries to find more relevant knowledge snippets. If no, respond with an empty list."
                    })
                    response = _call_model_to_prepare_search(input_prepare_search)
                    continue
                break

        except Exception as e:
            raise RuntimeError(f"OpenAI API call with tool loop failed: {str(e)}")
        
        return all_search_outputs


    def _generate_ontology_design_tasks(self, design_project: DesignProject, iteration: DesignIteration, user_instruction: str, relevant_knowledge_document_elements: List[KnowledgeDocumentElement]) -> List[DesignTask]:
        system_prompt_generate_tasks = f"""<ROLE>You are an expert in knowledge domain analysis and iterative ontology design.</ROLE>

<GOAL>Based on the provided domain knowledge and current ontology state, build a detailed plan with concrete ontology design tasks to completely execute the next planned ontology design iteration.</GOAL>

<GOAL_CONTEXT>
You are working on designing the ontology "{design_project.designedOntology.label}" which models the domain "{design_project.modeledKnowledgeDomain.label}".
The current ontology is provided by the user in their user message.
The next planned ontology design iteration is "{iteration.name}" described as "{iteration.specification}".
The domain is separated into multiple areas, and the next iteration focuses on the area "{iteration.focusedArea.label}" described as "{iteration.focusedArea.description}".
The key concepts of the focused area are: {', '.join(iteration.focusedArea.keyConcepts) if iteration.focusedArea.keyConcepts else 'None'}.
</GOAL_CONTEXT>

<DOMAIN_KNOWLEDGE_BASE>
As a source of the domain knowledge to guide your decisions, use the domain knowledge provided by the user:
- the summary of the domain knowledge
- the relevant domain knowledge snippets from the detailed domain knowledge specification
- other planned iterations that will be executed after the current iteration
</DOMAIN_KNOWLEDGE_BASE>

<INSTRUCTIONS>
- The user speaks {self.language} language, you must respond in {self.language} language.
- You must propose an ordered sequence of ontology design tasks that, when executed in order, will completely achieve the goals of the iteration.
- You must work with the given domain knowledge base to plan ontology design tasks correctly from the domain point of view.
- If the iteration is already partly fulfilled by the current ontology, do not propose tasks to design the respective ontology parts. You can propose design tasks that improve the respective ontology parts.
- Do not plan design tasks that would belong to other planned iterations that will be executed after the current iteration.
- Each ontology design task must follow exactly one ontology design task pattern from the catalogue of ontology design tasks patterns listed below and implement its specification into the specific context of the iteration.
- Each ontology design task must focus on designing ontology elements of solely one category, i.e. it can focus on either classes, relationships, or attributes, but not their combination.
- When specifying an ontology design task, ensure that it follows the ontology metamodel described below.
- Keep the proposed ontology design tasks as granular as possible.
- If the user customization instruction is specified, the planned ontology design tasks must be guided by it.
- Never aim at data types, cardinalities, or other kinds of constraints and rules in ontology design tasks.
- Never refer to specific parts of the provided domain knowledge base in the ontology design tasks. Insteads, specify the design task so that its specification can be used to semantically search the domain knowledge base for relevant knowledge resources.
- Strictly output the name and specification of each ontology design task in {self.language} language.
</INSTRUCTIONS>

<ONTOLOGY_METAMODEL>
- Ontology consists of the following elements: Classes, Attributes, Relationships.
- Class represents a primary entity in the domain, it is the main subject or object of interest.
    - Subject: An entity with legal agency, capable of rights and obligations (e.g., a person, a company, a role).
    - Object: An entity that is the target of an action but has no legal agency (e.g., a document, a physical asset, a legal right).
    - A class can specialize another class in the ontological (IS-A hierarchy) sense.
- Attribute is a simple, literal property of a single Class (e.g., a name, a date, a number)
    - It represents an intrinsic property of the class.
    - It represents a single fact about the class, like a simple field in a form.
    - It represents a property whose value is a simple, primitive value (e.g., string, number, date).
- Relationship is a binary directed semantic link that describes how one Class is related to another.
    - It is a property of the first class (the domain) that points to the second class (the range).
    - It represents a property whose value is a complex object (another class).
- No cardinalities.
- No primary keys.
- No primitive datatypes.
</ONTOLOGY_METAMODEL>

<DESIGN_TASK_PATTERNS_CATALOGUE>
{self._get_patterns_catalogue_xml(design_project.patterns)}
</DESIGN_TASK_PATTERNS_CATALOGUE>"""
        
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
            # Remove only <f> start and end tags, but keep their text content
            cleaned_content = re.sub(r'</?f[^>]*>', '', elem.content)
            doc_snippets[doc_id]["snippets"].append(f"<snippet id=\"{elem.id}\">{cleaned_content}</snippet>")

        # Build XML output grouped by <knowledge-document>
        snippets_xml = "\n".join(
            f"<knowledge-document title=\"{doc_info['title']}\">\n{''.join(doc_info['snippets'])}\n</knowledge-document>"
            for doc_info in doc_snippets.values()
        )

        input_generate_tasks = [
            {"role": "system", "content": system_prompt_generate_tasks},
            {"role": "assistant", "content": "To build the detailed plan of individual ontology design tasks to completely execute the next planned ontology design iteration, I need to analyze the current ontology and relevant domain knowledge. First, what is the current ontology?"},
            {"role": "user", "content": self._ontology_to_prompt(design_project.designedOntology)},
            {"role": "assistant", "content": "Thank you. Now, please provide the summary of the domain knowledge that we can use as a domain knowledge context for performing the design task."},
            {"role": "user", "content": self.knowledge_base_service.get_knowledge_document_outline_from_summaries(design_project.keyKnowledgeDocument)},
            {"role": "assistant", "content": "Great. Now, please provide the relevant knowledge snippets from the detailed domain knowledge specification that you found useful for building the detailed plan."},
            {"role": "user", "content": snippets_xml},
            {"role": "assistant", "content": "Thank you. Now, please provide information about other planned iterations that will be executed after the current iteration."},
            {"role": "user", "content": "\n".join([f"- {it.name}: {it.specification}" for it in design_project.plannedIterations if it.id != iteration.id]) if design_project.plannedIterations else "None"},
        ]
                
        if user_instruction:
            input_generate_tasks.append({
                "role": "assistant",
                "content": "Do you want to customize how the the ontology design tasks are planned?"
            })
            input_generate_tasks.append({
                "role": "user",
                "content": f"Customize your analysis with this instruction that is very important for me: {user_instruction}"
            })

        try:
            response = self.client.responses.parse(
                model=self.model_name,
                input=input_generate_tasks,
                text={
                    "verbosity": "low"
                },
                reasoning={
                    "effort": "low"
                },
                text_format=DesignTasksOutput,
            )

            design_tasks_output = response.output_parsed

        except Exception as e:
            raise RuntimeError(f"OpenAI API call with tool loop failed: {str(e)}")

        planned_tasks: List[DesignTask] = []
        for design_task_output in design_tasks_output.tasks:
            pattern_obj = next((p for p in design_project.patterns if p.name == design_task_output.followedPatternName), None)
            task = DesignTask(
                id=str(uuid.uuid4()),
                name=design_task_output.name,
                status=DesignTaskStatus.PLANNED,
                followedPattern=pattern_obj,
                specification=design_task_output.specification,
                knowledgeResources=[],
                designedOntologyChangesSpecification=None
            )
            planned_tasks.append(task)

        return planned_tasks

    def _get_patterns_catalogue_xml(self, patterns: List[Any]) -> str:
        # Get the design task patterns
        patterns_xml = ""
        for pattern in patterns:
            patterns_xml += f"<PATTERN><NAME>{pattern.name}</NAME><SPECIFICATION>{pattern.specification}</SPECIFICATION><WHEN_APPLICABLE>{pattern.whenApplicable}</WHEN_APPLICABLE></PATTERN>\n"
        return patterns_xml

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


    def prefix_uri(self, element_uri, ontology_uri) -> str:
        """
        Convert a full URI to a prefixed URI relative to the ontology URI.
        
        Args:
            element_uri: The full URI of the ontology element
            ontology_uri: The base URI of the ontology
            
        Returns:
            str: The prefixed URI (without the onto: prefix)
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
        Convert an ontology to a compact string representation suitable for TaskPlanner.
        Shows classes with their attributes and relationships with structure - optimized for planning design tasks.
        
        Args:
            ontology: The ontology object to serialize
            
        Returns:
            str: Compact structural overview representation
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
                
                # Attributes (introductions - URI + label)
                if ontology_class.attributes:
                    attr_strs = []
                    for attr in sorted(ontology_class.attributes, key=lambda x: x.label if x.label else ""):
                        prefixed_attr = self.prefix_uri(attr.uri, ontology.uri)
                        if not prefixed_attr.startswith(":"):
                            prefixed_attr = f":{prefixed_attr}"
                        attr_strs.append(f'{prefixed_attr} "{attr.label}"')
                    lines.append(f"    ATTRS: {', '.join(attr_strs)}")
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
