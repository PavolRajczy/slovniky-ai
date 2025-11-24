import os
import json
from pathlib import Path
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base.store import KnowledgeDocumentSummarizer
from knowledge_base.utils.cache_manager import CacheManager
import re

load_dotenv()

summarization_system_prompt = """<ROLE>You are a helpful assistant that summarizes documents with a detailed domain knowledge specification.</ROLE>
<TASK>Your task is to generate a concise summary of the text which is a part of a document.</TASK>
<INSTRUCTIONS>
The summary must be concise, up to 200 words.
The summary must capture the key real-world semantic entities and relationships defined, described or constrained by the text.
The summary must use words and phrases that go directly to the point of real-world entities and relationships to make it as informative as possible.
The summary must first briefly mention core semantic entities and relationships, then provide a their more detailed explanation, if there is some space left.
If the text explicitly defines a relationship or relationship, the summary must include a summary of this definition.
For a relationship, the summary must describe what concepts it connects, and how.
The summary must directly summarize the text. It is prohibited to:
    - refer to the original text as "the/this/... text/document/paragraph/...",
    - start with "Summary of" or similar phrases,
    - include text such as "Short summary of", "Detailed explanation of", etc.
    - include legal jargon, citations, or references,
    - use vague phrases like "the text/document/paragraph/... discusses/explains/...",
    - use meta-model phrases like "The entities/relationships defined in the text/document/paragraph/... are ...".
The summary must be stricly in the same language as the given text.
</INSTRUCTIONS>"""

class SimpleOpenAIKnowledgeDocumentSummarizer(KnowledgeDocumentSummarizer):
    """
    A summarizer for knowledge documents using OpenAI API.
    
    Computes summaries bottom-up: leaf summaries are from their content, non-leaf summaries combine their content and child summaries.
    """
    def __init__(self, model: str = "gpt-4.1"):
        self.model = model
        self.open_api_key = os.getenv("OPENAI_API_KEY")
        if not self.open_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=self.open_api_key)

    def summarize_document(self, document: KnowledgeDocument) -> None:
        """
        Computes summaries for all elements in the document hierarchy, storing them in contentSummary.
        Modifies the document in place and saves the updated document to its cache file.
        """
        self._summarize_element(document)
        
        # Save the updated document with summaries back to the cache file
        # Only update content part to preserve metadata
        if document.cacheFilePath:
            CacheManager.update_split_cache(document, update_content=True, update_metadata=False)

    def _summarize_element(self, element: KnowledgeDocumentElement) -> str:
        if element.contentSummary:
            return element.contentSummary  # Already summarized
        
        child_summaries = []
        for child in element.childElements:
            child_summary = self._summarize_element(child)
            if (child_summary is not None):
                child_summaries.append(child_summary)

        if element.content and not child_summaries:
            text_to_summarize = self._prepare_text(element.content)
        elif element.content and child_summaries:
            text_to_summarize = self._prepare_text(element.content) + "\n" + "\n".join(child_summaries)
        elif child_summaries:
            text_to_summarize = "\n".join(child_summaries)
        else:
            text_to_summarize = element.title or ""
        
        print(f"Summarizing element ID {element.id}.")
        summary = self._summarize_text(text_to_summarize)
        print(f"Summarized element ID {element.id}.")
        element.contentSummary = summary
        return summary
    
    def _prepare_text(self, text:str) -> str:
        text = text.strip()
        text = re.sub(r'<[^>]+>', '', text)
        return text

    def _summarize_text(self, text: str) -> str:
        if not text or not text.strip():
            return ""
        messages = [
            {"role": "system", "content": summarization_system_prompt},
            {"role": "user", "content": f"Summarize the following text:\n{text}"}
        ]
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=600,
            temperature=0.3
        )
        if response.choices:
            return response.choices[0].message.content.strip()
        return ""
