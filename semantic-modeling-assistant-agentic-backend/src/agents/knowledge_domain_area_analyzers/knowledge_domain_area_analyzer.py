from typing import List
from design_project.domain import DesignProject, KnowledgeDomain, KnowledgeDomainArea
from knowledge_base.domain import KnowledgeDocument


class KnowledgeDomainAreaAnalyzerAgent:
    """
    An agent that analyzes knowledge domains and identifies knowledge domain areas 
    for a given design project based on the knowledge bases in the project.
    """

    def __init__(self, model_name: str):
        """
        Initialize the domain area analyzer agent.

        Args:
            model_name (str): The name of the model to use for analysis.
        """
        self.model_name = model_name

    def identify_domain_areas(self, knowledge_domain: KnowledgeDomain, knowledge_document: KnowledgeDocument, consider_existing_areas: bool = False, user_instruction: str = "") -> List[KnowledgeDomainArea]:
        """
        Identifies knowledge domain areas in the given knowledge domain using the knowledge from the given knowledge document.
        If the user instruction is specified, the agent analysis is guided by it.

        Args:
            knowledge_domain (KnowledgeDomain): The knowledge domain to analyze.
            knowledge_document (KnowledgeDocument): The knowledge document to identify domain areas from.
            consider_existing_areas (bool): Whether to consider existing domain areas in the analysis.
            user_instruction (str): Instructions from the user to guide the analysis.

        Returns:
            List[KnowledgeDomainArea]: A list of identified knowledge domain areas.
        """
        ...