import os
import uuid
from typing import List, Optional
from pydantic import BaseModel, Field

from openai import OpenAI

from agents.iteration_suggesters.iteration_suggester import IterationSuggesterAgent
from agents.model_config import get_model
from design_project.domain import DesignIteration, DesignIterationStatus, DesignProject, KnowledgeDomainArea
from knowledge_base.service import KnowledgeBaseService
from knowledge_base_index.service import KnowledgeBaseIndexService
from ontology.domain import Ontology

class IterationOutput(BaseModel):
    """
    Pydantic model representing a single suggested iteration for LLM output.
    """
    name: str = Field(
        description="A human-readable name for the iteration that clearly identifies its purpose"
    )
    specification: str = Field(
        description="A detailed description of the design iteration - its goals/objectives/scope. It must be detailed enough to enable further designing the detailed iteration tasks later."
    )

class IterationsOutput(BaseModel):
    """
    Pydantic model representing the output of suggested iterations for LLM output.
    """
    iterations: List[IterationOutput] = Field(
        description="The list of suggested design iterations. Each iteration is expressed as a string specification that clearly describes what changes to make to the designed ontology in the context of the focused area."
    )

class IterationSuggesterAgent_Simple_OpenAI(IterationSuggesterAgent):
    """
    A simple implementation of IterationSuggesterAgent using OpenAI.
    """

    def __init__(self, knowledge_base_service: KnowledgeBaseService, knowledge_base_index_service: KnowledgeBaseIndexService, model_name: Optional[str] = None):
        """
        Initialize the simple iteration suggester agent.

        Args:
            knowledge_base_service (KnowledgeBaseService): The knowledge base service instance.
            model_name (str, optional): Overrides the model; defaults to the OPENAI_MODEL environment variable.
        """
        self.knowledge_base_service = knowledge_base_service
        self.knowledge_base_index_service = knowledge_base_index_service
        self.model_name = model_name or get_model()
        self.language = "Czech"

        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        self.client = OpenAI(api_key=api_key)

    def suggest_iterations(self, design_project: DesignProject, focused_area: KnowledgeDomainArea, k: int, user_instruction: str) -> List[DesignIteration]:
        """
        Suggests new design iterations for the given design project using OpenAI.

        Args:
            design_project (DesignProject): The design project to suggest iterations for.
            focused_area (KnowledgeDomainArea): The knowledge domain area to focus the suggestions on.
            k (int): The number of iterations to suggest.
            user_instruction (str): Instructions from the user to guide the suggestions.

        Returns:
            List[DesignIteration]: A list of suggested design iterations.
        """
        # Implementation of the iteration suggestion logic using OpenAI goes here

        if design_project.keyKnowledgeDocument is None:
            raise ValueError("Design project must have a key knowledge document to suggest iterations.")        

        iterations = []

        system_prompt = f"""<ROLE>You are an expert in knowledge domain analysis and iterative ontology design.</ROLE>

<TASK>Plan next {k} new ontology design iterations to incrementally improve the given ontology, focusing specifically on the area "{focused_area.label}". Each iteration should be small, precise, and targeted to a single key concept and its neighborhood or a small number of strongly related concepts. .</TASK>

<KNOWLEDGE_CONTEXT>
The ontology models the domain {design_project.modeledKnowledgeDomain.label} which is separated into multiple areas including the focused area "{focused_area.label}" described as "{focused_area.description}".
The key domain concepts in this focused area are {', '.join([kc for kc in focused_area.keyConcepts]) if focused_area.keyConcepts else 'not specified'}.
Plan the iterations solely based on the following knowledge context provided to you by the user in their user message:
- The previously finished iterations (if any, we are in the middle of the ontology design process to cover the focused area).
- Other planned iterations (if any, the user wants you to plan more iterations following the planned ones).
- The current state of the ontology you work on listed below.
- The document with an overview of the main aspects of the knowledge domain.
</KNOWLEDGE_CONTEXT>

<INSTRUCTIONS>
- The user speaks {self.language} language, you must respond in {self.language} language.
- Keep the planned iterations small and focused on particular aspects of the focused area "{focused_area.label}".
- Prefer iterations that introduce the key domain concepts into the ontology, if they are not yet modeled or planned in previous or planned iterations. In other words, prioritize "breath-first" exploration of the focused area, before going into deep refinement of the focused area. Only if all key domain concepts are already modeled or planned, you can plan iterations that go deeep into the focused area, i.e. refine the already modeled key concepts.
- The newly planned iterations do not need to cover the whole focused area. Prefer keeping the iterations small and focused. You will be asked to propose more iterations later if needed.
- A newly planned iteration should build on the finished and already planned iterations.
- An iteration should not specify concrete ontology design tasks or steps, but only the goal aiming at constructing, editing or deleting specific ontology elements corresponding to the ontology metamodel specified below.
- For each iteration, output:
    -- name: A human-readable name in {self.language} for the iteration that clearly identifies its purpose.
    -- specification: The specification of the goals and scope of the iteration in {self.language};  focused on the domain, using solely the domain language, no ontology expert jargon, no details of concrete ontology elements except the names of concepts to be modeled and their short explanation supporting their discovery or enhancement.
- Strictly output the name and specification of each iteration in {self.language} language.
- If the user specifies their customization instruction, you must follow it in your analysis.
</INSTRUCTIONS>

<ONTOLOGY_METAMODEL>
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

<EXAMPLES>
1. Name: Model spacecrafts and their basic properties.
Specification: Focus on modeling the spacecrafts used in space missions. Model spacecrafts and their subtypes covering different categories of spacecrafts such as military, commercial, and scientific. For each, define key properties such as name, type, launch date, and mission duration. Also, establish relationships between spacecrafts and their captains and operators.
2. Name: Detail spacecraft systems and components.
Specification: Focus on modeling the various systems and components of spacecrafts, such as propulsion systems, power systems, and communication systems. Model their properties, as well as relationships between different systems and components within a spacecraft.
3. Name: Model spacecraft missions and their objectives.
Specification: Focus on spacecrafts and their space missions and refine in detail their relationships to express planned, ongoing, and completed missions. Define different types of missions such as exploration, research, and commercial missions. For missions, define their key properties such as mission name, objectives, launch date, and duration.
</EXAMPLES>"""

        document_outline = self.knowledge_base_service.get_knowledge_document_outline_from_summaries(design_project.keyKnowledgeDocument)

        finished_iterations_str = (
            "".join(f"\t<ITERATION><NAME>{it.name}</NAME><SPECIFICATION>{it.specification}</SPECIFICATION></ITERATION>\n" for it in design_project.finishedIterations)
            if design_project.finishedIterations else "None"
        )
        planned_iterations_str = (
            "".join(f"\t<ITERATION><NAME>{it.name}</NAME><SPECIFICATION>{it.specification}</SPECIFICATION></ITERATION>\n" for it in design_project.plannedIterations)
            if design_project.plannedIterations else "None"
        )

        user_prompt = f"""<PREVIOUS_ITERATIONS>
{finished_iterations_str}
</PREVIOUS_ITERATIONS>
<PLANNED_ITERATIONS>
{planned_iterations_str}
</PLANNED_ITERATIONS>
<CURRENT_ONTOLOGY>
{self._ontology_to_prompt(design_project.designedOntology) if design_project.designedOntology else 'None'}
</CURRENT_ONTOLOGY>
<OVERVIEW_DOCUMENT>
{document_outline}
</OVERVIEW_DOCUMENT>"""
        
        if user_instruction:
            user_prompt += f"\n<USER_CUSTOMIZATION>Customize your analysis with this instruction that is very important for me: {user_instruction}</USER_CUSTOMIZATION>\n"

        input = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self.client.responses.parse(
                model=self.model_name,
                input=input,
                text={
                    "verbosity": "medium"
                },
                reasoning={
                    "effort": "low"
                },
                text_format=IterationsOutput,
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")

        iterations_output: IterationsOutput = response.output_parsed

        iterations: List[DesignIteration] = []
        if iterations_output and iterations_output.iterations:
            for iteration_output in iterations_output.iterations:
                iteration = DesignIteration(
                    id=str(uuid.uuid4()),  # Generate unique UUID for each iteration
                    name=iteration_output.name,
                    status=DesignIterationStatus.PLANNED,
                    specification=iteration_output.specification,
                    finishedTasks=[],
                    currentTask=None,
                    plannedTasks=[],
                    focusedArea=focused_area,
                    plannedOperations=None,  # No operations yet - will be generated during prepare phase
                    designedOntologyChangesSpecification=None
                )
                iterations.append(iteration)

        return iterations

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
        Convert an ontology to a compact string representation suitable for IterationSuggester.
        Shows only class hierarchy with kinds - optimized for planning new iterations.
        
        Args:
            ontology: The ontology object to serialize
            
        Returns:
            str: Compact class hierarchy representation
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
        lines.append(f"CLASSES ({len(ontology.classes)}):")
        
        if not ontology.classes:
            lines.append("  (none)")
            return '\n'.join(lines)
        
        # Build class hierarchy - find root classes (those with no generalizations)
        root_classes = []
        for class_uri, ontology_class in ontology.classes.items():
            if not ontology_class.generalizations:
                root_classes.append((class_uri, ontology_class))
        
        # Sort root classes by label for consistent output
        root_classes.sort(key=lambda x: x[1].label if x[1].label else "")
        
        # Helper function to recursively print class hierarchy
        def print_class_hierarchy(class_uri, ontology_class, indent=1):
            prefixed_class = self.prefix_uri(class_uri, ontology.uri)
            if not prefixed_class.startswith(":"):
                prefixed_class = f":{prefixed_class}"
            
            indent_str = "  " * indent
            kind_str = f"[{ontology_class.kind.value.upper()}]"
            lines.append(f'{indent_str}{prefixed_class} "{ontology_class.label}" {kind_str}')
            
            # Find and print specializations (subclasses)
            specializations = sorted(
                ontology_class.specializations,
                key=lambda x: x.label if x.label else ""
            )
            for subclass in specializations:
                if subclass.uri in ontology.classes:
                    print_class_hierarchy(subclass.uri, subclass, indent + 1)
        
        # Print hierarchy starting from root classes
        for class_uri, ontology_class in root_classes:
            print_class_hierarchy(class_uri, ontology_class)
        
        return '\n'.join(lines)
