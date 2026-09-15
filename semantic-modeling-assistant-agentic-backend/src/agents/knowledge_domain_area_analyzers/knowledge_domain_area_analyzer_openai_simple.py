import os
from typing import List, Optional
from pydantic import BaseModel, Field

from openai import OpenAI

from agents.knowledge_domain_area_analyzers.knowledge_domain_area_analyzer import KnowledgeDomainAreaAnalyzerAgent
from agents.model_config import get_mini_model
from design_project.domain import DesignProject, KnowledgeDomain, KnowledgeDomainArea
from knowledge_base.domain import KnowledgeDocument
from knowledge_base.service import KnowledgeBaseService

class KnowledgeDomainAreaOutput(BaseModel):
    """
    Pydantic model representing a knowledge domain area for LLM output.
    """
    label: str = Field(
        description="A human-readable label for the area that clearly identifies its scope and purpose"
    )
    description: Optional[str] = Field(
        default=None,
        description="A human-readable description providing more context about the area semantics and what it encompasses"
    )
    keyConcepts: List[str] = Field(
        description="The list of key concepts that are central in this area. Each key concept is expressed as a string term and represents important domain concepts that should be modeled in the ontology"
    )

class KnowledgeDomainOutput(BaseModel):
    """
    Pydantic model representing a knowledge domain for LLM output.
    """
    #label: str = Field(
        #description="A human-readable label for the knowledge domain that clearly identifies what domain it represents"
    #)
    #description: Optional[str] = Field(
        #default=None,
        #description="A human-readable description providing the basic summarized characterization of the domain semantics and its scope"
    #)
    areas: List[KnowledgeDomainAreaOutput] = Field(
        description="The list of areas this domain is structured into. A domain is typically structured into multiple areas to make the design of the domain ontology more manageable and organized"
    )

class KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI(KnowledgeDomainAreaAnalyzerAgent):
    """
    A simple implementation of KnowledgeDomainAreaAnalyzerAgent.
    """

    def __init__(self, knowledge_base_service: KnowledgeBaseService, model_name: Optional[str] = None):
        """
        Initialize the simple domain area analyzer agent.

        Args:
            knowledge_base_service (KnowledgeBaseService): The knowledge base service to work with knowledge documents.
            model_name (str, optional): Overrides the model; defaults to the OPENAI_MODEL_MINI environment variable.
        """
        self.knowledge_base_service = knowledge_base_service
        self.model_name = model_name or get_mini_model()
        self.language = "Czech"

        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key must be provided as OPENAI_API_KEY environment variable")

        self.openai_client = OpenAI(api_key=api_key)

    def identify_domain_areas(self, knowledge_domain: KnowledgeDomain, knowledge_document: KnowledgeDocument, consider_existing_areas: bool = False, user_instruction: str = "") -> List[KnowledgeDomainArea]:
        """
        Identifies knowledge domain areas in the given knowledge domain using the knowledge from the given knowledge document.
        If the user instruction is specified, the agent analysis is guided by it.

        This implementation:
         - uses OpenAI's GPT model to perform the analysis,
         - uses the outline of the knowledge_document built from the summaries of its elements

        Args:
            knowledge_domain (KnowledgeDomain): The knowledge domain to analyze.
            knowledge_document (KnowledgeDocument): The knowledge document to identify domain areas from.
            consider_existing_areas (bool): Whether to consider existing domain areas in the analysis.
            user_instruction (str): Instructions from the user to guide the analysis.

        Returns:
            List[KnowledgeDomainArea]: A list of identified knowledge domain areas.
        """
        areas = []

        system_prompt = f"""<ROLE>You are an expert in knowledge domain analysis and ontology design.</ROLE>

<TASK>Your task is to analyze the provided document with the specification of the user's domain knowledge and identify distinct domain areas within it.</TASK>

<INSTRUCTIONS>
- The user speaks {self.language} language, you must respond in {self.language} language.
- Each area must correspond to some central domain concept and some key concepts around it representing real-world entities (persons, things, events, etc.).
- You should aim at a small number of areas, typically between 5 and 15, that cover the main aspects of the knowledge domain. You are allowed to have more areas if justified by the complexity and heterogeneity of the domain.
- Each area should be clearly defined with a label, a description, and a list of key concepts that are central to that area.
- Distinguish areas that focus more on the descriptive aspects of the domain concepts from those that focus more on processes, activities, or functions involving those concepts.
- Output the areas focused on the descriptiive aspects of the domain concepts first, followed by the areas focused on processes, activities, or functions.
- If the user provides a customization instruction, you must follow it in your analysis.
- Strictly output the label, description, and key concepts of each area in {self.language} language.
</INSTRUCTIONS>"""

        document_outline = self.knowledge_base_service.get_knowledge_document_outline_from_summaries(knowledge_document)

        user_prompt = f"""This is the document with the specification of my knowledge domain:
<document>{document_outline}</document>
"""
        
        if consider_existing_areas and knowledge_domain and knowledge_domain.areas:
            existing_areas_str = "\n".join([f"- {area.label}: {area.description}" for area in knowledge_domain.areas])
            user_prompt += f"\nThese are the existing domain areas in the knowledge domain that you should consider in your analysis but you are required to refine them:\n{existing_areas_str}\n"

        if user_instruction:
            user_prompt += f"\nCustomize your analysis with this instruction that is very important for me: {user_instruction}\n"

        input = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.openai_client.responses.parse(
            model=self.model_name,
            input=input,
            text={
                "verbosity": "medium"
            },
            reasoning={
                "effort": "medium"
            },
            text_format=KnowledgeDomainOutput
        )

        knowledge_domain_output: KnowledgeDomainOutput = response.output_parsed

        areas = []
        for area_output in knowledge_domain_output.areas:
            # Generate a unique ID for the area
            import uuid
            area_id = str(uuid.uuid4())
            
            area = KnowledgeDomainArea(
                id=area_id,
                label=area_output.label,
                description=area_output.description,
                parent=knowledge_domain,
                keyConcepts=area_output.keyConcepts,
                modelingClasses=[],
                modelingAttributes=[],
                modelingRelationships=[],
                explainingKnowledgeResources=[]
            )
            areas.append(area)

        

        return areas