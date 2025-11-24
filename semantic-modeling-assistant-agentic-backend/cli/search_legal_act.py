#!/usr/bin/env python3
"""
Interactive command line utility for searching in legal acts using dual knowledge base indexing.

This utility uses KnowledgeBaseIndexService with both FAISSFullTextOpenAIKnowledgeDocumentIndexer
and FAISSSummaryOpenAIKnowledgeDocumentIndexer to search for information within legal acts 
that have been previously loaded and indexed. It provides comparative results from both indexers
and combines them using Reciprocal Rank Fusion (RRF) for improved ranking.

Usage:
    python cli/search_legal_act.py <legal_act_id>

Example:
    python cli/search_legal_act.py 2001-56-2025-07-01

After loading the legal act, you can interactively search by entering queries.
The system will search using both full-text and summary indexers and display
comparative results ranked using RRF. Type 'quit' or 'exit' to stop.
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
from knowledge_base.store import KnowledgeDocumentSummarizer
from knowledge_base_index.service import KnowledgeBaseIndexService
from knowledge_base_index.indexers.faiss_fulltext_openai_indexer import FAISSFullTextOpenAIKnowledgeDocumentIndexer
from knowledge_base_index.indexers.faiss_summary_openai_indexer import FAISSSummaryOpenAIKnowledgeDocumentIndexer

# Constants
ESEL_IRI_PREFIX = "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/"


class NoOpSummarizer(KnowledgeDocumentSummarizer):
    """
    A no-operation summarizer that does nothing.
    Used when we don't need document summarization for search operations.
    """
    def summarize_document(self, document) -> None:
        # Do nothing - we don't need summarization for search
        pass


def build_full_legal_act_id(local_part: str) -> str:
    """
    Build the full IRI for a legal act from its local part.
    
    Args:
        local_part: The local part of the legal act ID (e.g., "2001/56/2025-07-01")
        
    Returns:
        The full IRI (e.g., "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01")
    """
    return ESEL_IRI_PREFIX + local_part


def truncate_element_id(element_id, legal_act_local_id):
    """
    Truncate element ID by removing the common prefix and showing only the unique part.
    
    Args:
        element_id: Full element ID
        legal_act_local_id: Local part of the legal act ID (e.g., "2001/56/2025-07-01")
        
    Returns:
        Truncated element ID showing only the unique part
    """
    # Build the expected prefix
    prefix = f"https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/{legal_act_local_id}/dokument/norma/"
    
    if element_id.startswith(prefix):
        return element_id[len(prefix):]
    else:
        # Fallback: just show the last part after the last slash
        return element_id.split('/')[-1] if '/' in element_id else element_id


def wait_for_user_input(message="Press any key to continue..."):
    """Wait for user to press any key before continuing."""
    try:
        input(f"\n{message}")
    except KeyboardInterrupt:
        print("\n\nExiting...")
        raise
    except EOFError:
        print("\n\nExiting...")
        raise


def ask_user_for_details():
    """Ask user if they want to see detailed results. Returns True if yes, False if no."""
    while True:
        try:
            response = input("\nDo you want to see detailed results? (Y/N): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter Y (yes) or N (no).")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            raise
        except EOFError:
            print("\n\nExiting...")
            raise


def calculate_rrf_scores(fulltext_results, summary_results, k=60):
    """
    Calculate Reciprocal Rank Fusion (RRF) scores for combining results from multiple rankings.
    
    RRF formula: RRF(d) = sum over all rankings r of (1 / (k + rank_r(d)))
    where k is typically 60, and rank_r(d) is the rank of document d in ranking r.
    
    Args:
        fulltext_results: List of results from full-text indexer (in ranked order)
        summary_results: List of results from summary indexer (in ranked order)
        k: RRF parameter (default: 60)
        
    Returns:
        Dictionary mapping element_id to RRF score
    """
    rrf_scores = {}
    
    # Process full-text results
    if fulltext_results:
        for rank, result in enumerate(fulltext_results, 1):  # rank starts from 1
            element_id = result.element_id
            rrf_scores[element_id] = rrf_scores.get(element_id, 0.0) + (1.0 / (k + rank))
    
    # Process summary results
    if summary_results:
        for rank, result in enumerate(summary_results, 1):  # rank starts from 1
            element_id = result.element_id
            rrf_scores[element_id] = rrf_scores.get(element_id, 0.0) + (1.0 / (k + rank))
    
    return rrf_scores


def display_results_summary_table(fulltext_results, summary_results, query, legal_act_local_id, rrf_k=60):
    """Display a summary comparison table of results from both indexers ordered by RRF scores."""
    print(f"\n=== SEARCH RESULTS SUMMARY FOR: '{query}' ===")
    print("Comparison of Full-Text vs Summary Indexer Results (Ordered by Reciprocal Rank Fusion)")
    print("=" * 110)
    
    # Create a unified list of all unique element IDs from both result sets
    all_element_ids = set()
    if fulltext_results:
        all_element_ids.update(result.element_id for result in fulltext_results)
    if summary_results:
        all_element_ids.update(result.element_id for result in summary_results)
    
    if not all_element_ids:
        print("No results found in either indexer.")
        return
    
    # Calculate RRF scores
    rrf_scores = calculate_rrf_scores(fulltext_results, summary_results, k=rrf_k)
    
    # Create dictionaries for quick lookup
    fulltext_dict = {result.element_id: result for result in (fulltext_results or [])}
    summary_dict = {result.element_id: result for result in (summary_results or [])}
    
    # Calculate column widths for better formatting
    truncated_ids = [truncate_element_id(eid, legal_act_local_id) for eid in all_element_ids]
    max_id_length = max(len(tid) for tid in truncated_ids) if truncated_ids else 15
    max_id_length = max(max_id_length, 15)  # Minimum width for readability
    
    id_width = max_id_length + 2
    score_width = 12
    diff_width = 10
    rrf_width = 12
    
    # Print table header with proper column alignment
    header_line = f"{'Element ID':<{id_width}} {'RRF Score':<{rrf_width}} {'Full-Text':<{score_width}} {'Summary':<{score_width}} {'FT-Sum Diff':<{diff_width}}"
    print(header_line)
    print("=" * len(header_line))
    
    # Sort by RRF scores (descending order)
    sorted_elements = sorted(all_element_ids, 
                           key=lambda eid: rrf_scores.get(eid, 0.0), 
                           reverse=True)
    
    for element_id in sorted_elements:
        ft_result = fulltext_dict.get(element_id)
        sm_result = summary_dict.get(element_id)
        
        ft_score = ft_result.overall_relevance_score if ft_result else 0.0
        sm_score = sm_result.overall_relevance_score if sm_result else 0.0
        diff = ft_score - sm_score
        rrf_score = rrf_scores.get(element_id, 0.0)
        
        # Truncate the element ID for display
        truncated_id = truncate_element_id(element_id, legal_act_local_id)
        
        rrf_score_str = f"{rrf_score:.4f}"
        ft_score_str = f"{ft_score:.4f}" if ft_result else "---"
        sm_score_str = f"{sm_score:.4f}" if sm_result else "---"
        diff_str = f"{diff:+.4f}" if ft_result and sm_result else "---"
        
        print(f"{truncated_id:<{id_width}} {rrf_score_str:<{rrf_width}} {ft_score_str:<{score_width}} {sm_score_str:<{score_width}} {diff_str:<{diff_width}}")
    
    print("=" * len(header_line))
    print(f"📊 Total Full-Text Results: {len(fulltext_results) if fulltext_results else 0}")
    print(f"📊 Total Summary Results: {len(summary_results) if summary_results else 0}")
    print(f"📊 Unique Elements Found: {len(all_element_ids)}")
    print(f"🔄 Ordering: Reciprocal Rank Fusion (RRF) with k={rrf_k}")


def display_detailed_results(fulltext_results, summary_results, query, legal_act_local_id, rrf_k=60):
    """Display detailed results from both indexers ordered by RRF ranking."""
    print(f"\n=== DETAILED RESULTS (Ordered by Reciprocal Rank Fusion) ===")
    
    # Calculate RRF scores to determine the unified order
    rrf_scores = calculate_rrf_scores(fulltext_results, summary_results, k=rrf_k)
    
    # Get all unique element IDs and sort by RRF score
    all_element_ids = set()
    if fulltext_results:
        all_element_ids.update(result.element_id for result in fulltext_results)
    if summary_results:
        all_element_ids.update(result.element_id for result in summary_results)
    
    if not all_element_ids:
        print("No detailed results to display.")
        return
    
    # Sort elements by RRF score (descending)
    sorted_element_ids = sorted(all_element_ids, 
                               key=lambda eid: rrf_scores.get(eid, 0.0), 
                               reverse=True)
    
    # Create lookup dictionaries
    fulltext_dict = {result.element_id: result for result in (fulltext_results or [])}
    summary_dict = {result.element_id: result for result in (summary_results or [])}
    
    # Display results in RRF order
    for i, element_id in enumerate(sorted_element_ids, 1):
        ft_result = fulltext_dict.get(element_id)
        sm_result = summary_dict.get(element_id)
        rrf_score = rrf_scores.get(element_id, 0.0)
        
        truncated_id = truncate_element_id(element_id, legal_act_local_id)
        
        print(f"\n🔄 RRF Rank #{i} (Score: {rrf_score:.4f}) - Element: {truncated_id}")
        print("=" * 80)
        
        # Show full-text result if available
        if ft_result:
            print(f"🔍 FULL-TEXT RESULT (Score: {ft_result.overall_relevance_score:.4f})")
            print("-" * 40)
            display_single_result(ft_result, legal_act_local_id, "Full-Text", show_header=False)
        else:
            print("🔍 FULL-TEXT RESULT: Not found in full-text results")
        
        print()  # Add spacing
        
        # Show summary result if available
        if sm_result:
            print(f"📋 SUMMARY RESULT (Score: {sm_result.overall_relevance_score:.4f})")
            print("-" * 40)
            display_single_result(sm_result, legal_act_local_id, "Summary", show_header=False)
        else:
            print("📋 SUMMARY RESULT: Not found in summary results")
        
        # Wait after each unified result (except the last one)
        if i < len(sorted_element_ids):
            wait_for_user_input("Press any key for next RRF-ranked result...")
        
        print("=" * 80)


def display_single_result(result, legal_act_local_id, indexer_type="", show_header=True):
    """Display a single search result in a formatted way."""
    # Truncate element ID for display
    truncated_id = truncate_element_id(result.element_id, legal_act_local_id)
    
    prefix = f"[{indexer_type}] " if indexer_type else ""
    
    if show_header:
        print(f"\n{prefix}Result:")
    print(f"Overall Relevance Score: {result.overall_relevance_score:.4f}")
    print(f"Element ID: {truncated_id}")
    
    if result.matching_chunks:
        print(f"Number of matching chunks: {len(result.matching_chunks)}")
        
        for j, chunk in enumerate(result.matching_chunks, 1):
            print(f"\n  Chunk {j}:")
            print(f"  Chunk ID: {chunk.chunk_id}")
            print(f"  Relevance Score: {chunk.relevance_score:.4f}")
            
            if chunk.fragment_id:
                print(f"  Fragment ID: {chunk.fragment_id}")
            
            if chunk.text:
                print(f"  Text:")
                print("  " + "-" * 38)
                # Indent the chunk text
                chunk_lines = chunk.text.strip().split('\n')
                for line in chunk_lines:
                    print(f"  {line}")
                print("  " + "-" * 38)


def display_search_results(results, query, legal_act_local_id, indexer_type=""):
    """Display search results in a formatted way."""
    if not results:
        print("No results found.")
        return
    
    for i, result in enumerate(results, 1):
        print(f"\nResult {i}:")
        display_single_result(result, legal_act_local_id, indexer_type, show_header=False)
        
        # Wait after each result (except the last one)
        if i < len(results):
            wait_for_user_input("Press any key for next result...")
        
        print("-" * 80)


def interactive_search(fulltext_index_service, summary_index_service, legal_act_local_id, max_results, include_summaries, show_details=True, rrf_k=60):
    """Handle interactive search queries using both indexers."""
    print(f"\nInteractive dual search mode for legal act '{legal_act_local_id}'")
    print("Searches will be performed using both Full-Text and Summary indexers")
    print(f"Results will be ranked using Reciprocal Rank Fusion (RRF) with k={rrf_k}")
    if not show_details:
        print("(Showing summary table only - detailed results disabled)")
    print("Enter your search queries (type 'quit' or 'exit' to stop):")
    print("-" * 60)
    
    while True:
        try:
            query = input("\nSearch query: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
                
            print(f"\nSearching for '{query}' using both indexers...")
            
            # Search using full-text indexer
            print("🔍 Searching with Full-Text indexer...")
            fulltext_results = fulltext_index_service.search(
                query_text=query,
                max_results=max_results,
                include_summaries=include_summaries
            )
            
            # Search using summary indexer  
            print("📋 Searching with Summary indexer...")
            summary_results = summary_index_service.search(
                query_text=query,
                max_results=max_results,
                include_summaries=include_summaries
            )
            
            # Display results
            try:
                display_results_summary_table(fulltext_results, summary_results, query, legal_act_local_id, rrf_k)
                
                if show_details:
                    # Ask user if they want to see detailed results
                    show_detailed = ask_user_for_details()
                    if show_detailed:
                        display_detailed_results(fulltext_results, summary_results, query, legal_act_local_id, rrf_k)
                else:
                    print("\n(Detailed results hidden - use --show-details to see them)")
            except (KeyboardInterrupt, EOFError):
                print("\nReturning to search prompt...")
                continue
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break


def main():
    """Main function to handle command line arguments and search legal acts interactively."""
    parser = argparse.ArgumentParser(
        description="Interactive dual search in legal acts using both full-text and summary FAISS indexers with Reciprocal Rank Fusion (RRF) ranking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Start interactive dual search for a legal act:
    python cli/search_legal_act.py 2001/56/2025-07-01
  
  Start search with custom options (summary table only):
    python cli/search_legal_act.py 2001/56/2025-07-01 --max-results 20 --no-details
    
  Full verbose search with summaries and custom RRF parameter:
    python cli/search_legal_act.py 2001/56/2025-07-01 --include-summaries --verbose --rrf-k 30

The tool will use both Full-Text and Summary indexers for each query and display:
1. A summary table comparing results from both indexers (ordered by RRF scores)
2. Detailed results from each indexer in RRF order (unless --no-details is used)

Reciprocal Rank Fusion (RRF) combines rankings from both indexers by giving each result
a score of 1/(k + rank), where k is configurable (default: 60). Lower k values give
more weight to top-ranked results.

Interactive controls:
- Press any key to advance through results
- Press Ctrl+C during result display to return to search prompt
- Type 'quit' or 'exit' to exit the program
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
        '--max-results',
        type=int,
        default=10,
        help='Maximum number of search results to return (default: 10)'
    )
    
    parser.add_argument(
        '--include-summaries',
        action='store_true',
        help='Include content summaries in search results'
    )
    
    parser.add_argument(
        '--show-details',
        action='store_true',
        default=True,
        help='Show detailed results after summary table (default: True)'
    )
    
    parser.add_argument(
        '--no-details',
        dest='show_details',
        action='store_false',
        help='Only show summary table, skip detailed results'
    )
    
    parser.add_argument(
        '--rrf-k',
        type=int,
        default=60,
        help='RRF parameter k for Reciprocal Rank Fusion (default: 60). Lower values give more weight to top-ranked results.'
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
        print(f"Max results: {args.max_results}")
        print(f"Include summaries: {args.include_summaries}")
        print(f"Show detailed results: {args.show_details}")
        print(f"RRF parameter k: {args.rrf_k}")
        print()
    
    try:
        # Initialize the ESEL document loader
        if args.verbose:
            print("Initializing ESEL knowledge document loader...")
        
        loader = ESELKnowledgeDocumentLoader(
            sparql_endpoint=args.endpoint,
            base_dir=args.base_dir
        )
        
        # Create the knowledge base service
        if args.verbose:
            print("Creating knowledge base service...")
        
        kb_service = KnowledgeBaseService(
            document_loader=loader,
            document_summarizer=NoOpSummarizer()  # Use no-op summarizer for search
        )
        
        # Load the legal act
        if args.verbose:
            print(f"Loading legal act '{args.legal_act_local_id}' (full ID: {legal_act_id})...")
        
        documents = kb_service.load_knowledge_documents([legal_act_id], [])
        
        if not documents:
            print(f"Error: No document found for ID '{legal_act_id}'")
            print("Make sure the legal act has been loaded first using load_legal_act.py")
            sys.exit(1)
        
        document = documents[0]
        if args.verbose:
            print(f"✓ Successfully loaded legal act: {document.title}")
        
        # Initialize both knowledge base index services
        if args.verbose:
            print("Initializing knowledge base index services with both FAISS indexers...")
        
        # Full-text indexer
        fulltext_indexer = FAISSFullTextOpenAIKnowledgeDocumentIndexer()
        fulltext_index_service = KnowledgeBaseIndexService(indexer=fulltext_indexer)
        
        # Summary indexer  
        summary_indexer = FAISSSummaryOpenAIKnowledgeDocumentIndexer()
        summary_index_service = KnowledgeBaseIndexService(indexer=summary_indexer)
        
        # Add document to both indexes
        if args.verbose:
            print("Adding legal act to both indexes...")
        
        print("🔍 Building full-text index...")
        fulltext_index_service.add_document(document)
        
        print("📋 Building summary index...")
        summary_index_service.add_document(document)
        
        if args.verbose:
            print("✓ Document added to both indexes successfully")
        
        # Start interactive search with both services
        interactive_search(
            fulltext_index_service=fulltext_index_service,
            summary_index_service=summary_index_service,
            legal_act_local_id=args.legal_act_local_id,
            max_results=args.max_results,
            include_summaries=args.include_summaries,
            show_details=args.show_details,
            rrf_k=args.rrf_k
        )
                
    except Exception as e:
        print(f"Error searching legal act: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
