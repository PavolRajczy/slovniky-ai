#!/usr/bin/env python3
"""
Command line utility for loading legal acts into a knowledge base.

This utility uses KnowledgeBaseService with ESELKnowledgeDocumentLoader to load
legal acts from the ESEL SPARQL endpoint into the knowledge base.

Usage:
    python cli/load_legal_act.py <legal_act_id>

Example:
    python cli/load_legal_act.py 2001-56-2025-07-01
"""

import sys
import os
import argparse
from pathlib import Path

# Add the src directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base.service import KnowledgeBaseService
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer

# Constants
ESEL_IRI_PREFIX = "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/"


def build_full_legal_act_id(local_part: str) -> str:
    """
    Build the full IRI for a legal act from its local part.
    
    Args:
        local_part: The local part of the legal act ID (e.g., "2001/56/2025-07-01")
        
    Returns:
        The full IRI (e.g., "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01")
    """
    return ESEL_IRI_PREFIX + local_part


def main():
    """Main function to handle command line arguments and load legal acts."""
    parser = argparse.ArgumentParser(
        description="Load legal acts into a knowledge base using ESEL loader",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Load a legal act by local ID:
    python cli/load_legal_act.py 2001/56/2025-07-01
  
  Load with custom SPARQL endpoint:
    python cli/load_legal_act.py 2001/56/2025-07-01 --endpoint https://custom.sparql.endpoint.com/sparql
        """
    )
    
    parser.add_argument(
        'legal_act_local_id', 
        help='The local part of the legal act ID (e.g., "2001/56/2025-07-01"). Will be prefixed with "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/"'
    )
    
    parser.add_argument(
        '--endpoint',
        default='https://opendata.eselpoint.cz/sparql',
        help='SPARQL endpoint URL (default: https://opendata.eselpoint.cz/sparql)'
    )
    
    parser.add_argument(
        '--base-dir',
        default='data/knowledge_base/esel',
        help='Base directory for storing cached documents (default: data/knowledge_base/esel)'
    )
    
    parser.add_argument(
        '--no-summarize',
        action='store_true',
        help='Skip document summarization (faster but no summaries will be generated)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Build the full legal act ID from the local part
    legal_act_id = build_full_legal_act_id(args.legal_act_local_id)
    
    if args.verbose:
        print(f"Local legal act ID: {args.legal_act_local_id}")
        print(f"Full legal act ID: {legal_act_id}")
        print(f"SPARQL endpoint: {args.endpoint}")
        print(f"Base directory: {args.base_dir}")
        print(f"Summarization: {'disabled' if args.no_summarize else 'enabled'}")
        print()
    
    try:
        # Initialize the ESEL document loader
        if args.verbose:
            print("Initializing ESEL knowledge document loader...")
        
        loader = ESELKnowledgeDocumentLoader(
            sparql_endpoint=args.endpoint,
            base_dir=args.base_dir
        )
        
        # Initialize the document summarizer (only if not skipped)
        if args.no_summarize:
            if args.verbose:
                print("Skipping summarization as requested...")
            summarizer = None
        else:
            if args.verbose:
                print("Initializing OpenAI document summarizer...")
            try:
                summarizer = SimpleOpenAIKnowledgeDocumentSummarizer()
            except ValueError as e:
                print(f"Warning: Could not initialize summarizer: {e}")
                print("Proceeding without summarization...")
                summarizer = None
        
        # Create the knowledge base service
        if args.verbose:
            print("Creating knowledge base service...")
        
        service = KnowledgeBaseService(
            document_loader=loader,
            document_summarizer=summarizer
        )
        
        # Load the legal act
        print(f"Loading legal act '{args.legal_act_local_id}' (full ID: {legal_act_id})...")

        documents = service.load_knowledge_documents([legal_act_id], [])

        if not documents:
            print(f"Error: No document found for ID '{legal_act_id}'")
            sys.exit(1)
        
        document = documents[0]
        print(f"✓ Successfully loaded legal act: {document.title}")
        
        if args.verbose:
            print(f"Document ID: {document.id}")
            print(f"Element type: {document.elementType}")
            print(f"Number of child elements: {len(document.childElements)}")
            
            if document.contentSummary:
                print(f"Summary: {document.contentSummary}")
            else:
                print("No summary available")
        
        # Generate and display document outline if verbose
        if args.verbose and document:
            print("\nDocument outline:")
            outline = service.get_knowledge_document_outline_from_summaries(document)
            print(outline)
            
    except Exception as e:
        print(f"Error loading legal act: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
