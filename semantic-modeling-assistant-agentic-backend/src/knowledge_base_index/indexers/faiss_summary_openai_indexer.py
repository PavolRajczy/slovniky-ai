import os
import uuid
import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import faiss
from openai import OpenAI

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base_index.indexer import KnowledgeDocumentIndexer
from ..domain import IndexDocument, TextChunk, SearchQuery, SearchResult, ChunkMatch
from ..chunkers.semchunk_chunker import SemchunkIndexDocumentChunker


class FAISSSummaryOpenAIKnowledgeDocumentIndexer(KnowledgeDocumentIndexer):
    """
    FAISS-based implementation of KnowledgeDocumentIndexer using OpenAI embeddings.
    
    This indexer creates an in-memory FAISS vector store for semantic search
    over knowledge document content summaries using OpenAI's text-embedding-3-large model.
    Unlike the full-text indexer, this indexes contentSummary instead of content.
    Only leaf nodes (elements with no children) in the knowledge document hierarchy are indexed.
    """
    
    def __init__(self,
                 target_model: str = "gpt-4.1",
                 chunk_size: int = 250,
                 embedding_model: str = "text-embedding-3-large",
                 embedding_dimension: int = 3072
                 ):
        """
        Initialize the FAISS-based knowledge document indexer for summaries.
        
        Args:
            target_model: Target LLM model the chunks are optimized for.
            chunk_size: Size of text chunks to create.
            embedding_model: OpenAI embedding model to use.
            embedding_dimension: Dimension of the embedding vectors.

        """
        self.embedding_model = embedding_model
        self.embedding_dimension = embedding_dimension

        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key must be provided as OPENAI_API_KEY environment variable")

        self.openai_client = OpenAI(api_key=api_key)
        
        # Initialize chunker
        self.chunker = SemchunkIndexDocumentChunker(chunk_size=chunk_size, chunk_overlap=0.15, target_model=target_model)
        
        # FAISS index and metadata storage
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dimension)  # Inner product for cosine similarity
        self.chunk_metadata: List[TextChunk] = []  # Store chunk metadata by index
        self.index_documents: Dict[str, IndexDocument] = {}  # Store index documents by ID
    
    def build_index(self, knowledge_document: KnowledgeDocument) -> None:
        """
        Build an index for the given knowledge document.
        
        This method:
        1. Creates IndexDocument objects from the knowledge document structure
        2. Chunks each IndexDocument using the configured chunker
        3. Generates embeddings for each text chunk
        4. Stores embeddings in FAISS index for fast similarity search
        
        Args:
            knowledge_document: The knowledge document to index
        """
        print(f"Building summary index for knowledge document: {knowledge_document.id}")
        
        # Create index documents
        index_documents = self._create_index_documents(knowledge_document)
        print(f"Created {len(index_documents)} index documents")
        
        # Store index documents
        for index_doc in index_documents:
            self.index_documents[index_doc.id] = index_doc
        
        # Chunk all index documents and collect text chunks
        all_chunks = []
        for index_doc in index_documents:
            chunks = self.chunker.get_text_chunks(index_doc)
            all_chunks.extend(chunks)
        
        print(f"Created {len(all_chunks)} text chunks")
        
        if not all_chunks:
            print("No text chunks created, skipping embedding generation")
            return
        
        # Extract text for embedding
        chunk_texts = [chunk.text for chunk in all_chunks]
        
        # Generate embeddings in batches to handle API limits
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(chunk_texts), batch_size):
            batch_texts = chunk_texts[i:i + batch_size]
            print(f"Generating embeddings for batch {i//batch_size + 1}/{(len(chunk_texts) + batch_size - 1)//batch_size}")
            
            batch_embeddings = self._get_embeddings(batch_texts)
            all_embeddings.append(batch_embeddings)
        
        # Combine all embeddings
        embeddings = np.vstack(all_embeddings) if all_embeddings else np.array([]).reshape(0, self.embedding_dimension)
        
        if len(embeddings) == 0:
            print("No embeddings to add to index")
            return
        
        # Convert to float32 for FAISS compatibility
        embeddings = embeddings.astype(np.float32)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Store embeddings in chunks
        for chunk, embedding in zip(all_chunks, embeddings):
            chunk.embedding = embedding
        
        # Add embeddings to FAISS index
        self.faiss_index.add(embeddings)
        
        # Store chunk metadata
        self.chunk_metadata.extend(all_chunks)
        
        print(f"Successfully built summary index with {len(self.chunk_metadata)} chunks")
    
    def build_or_load_index(self, knowledge_document: KnowledgeDocument) -> None:
        """
        Build an index for the given knowledge document, or load from cache if available.
        
        This is a convenience method that first tries to load a cached index,
        and if that fails, builds a new index and stores it for future use.
        
        Args:
            knowledge_document: The knowledge document to index
        """
        # Try to load existing index first
        if self.load_index(knowledge_document):
            print("Loaded existing summary index from cache")
            return
        
        # If loading failed, build new index
        print("Building new summary index...")
        self.build_index(knowledge_document)
        
        # Store the newly built index
        try:
            self.store_index(knowledge_document)
        except Exception as e:
            print(f"Warning: Failed to store summary index: {e}")
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search the index for the given query.
        
        Returns aggregated results where each knowledge document element appears
        only once, with all matching chunks and their fragment IDs included.
        
        Args:
            query: The search query to execute
            
        Returns:
            A list of search results matching the query, sorted by overall relevance
        """
        if self.faiss_index.ntotal == 0:
            return []
        
        # Generate embedding for the query
        query_embedding = self._get_embeddings([query.query_text])
        query_embedding = query_embedding.astype(np.float32)
        faiss.normalize_L2(query_embedding)
        
        # Search FAISS index - get more results initially since we'll aggregate
        # Use a larger k to ensure we don't miss relevant chunks after aggregation
        k = min(query.max_results * 3, self.faiss_index.ntotal)
        scores, indices = self.faiss_index.search(query_embedding, k)
        
        # Group chunks by element_id (document_id)
        element_chunks = {}
        
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for invalid indices
                continue
                
            chunk = self.chunk_metadata[idx]
            
            # Get the actual knowledge document element ID from the index document
            index_doc = self.index_documents.get(chunk.document_id)
            if not index_doc:
                continue  # Skip if index document not found
            
            element_id = index_doc.element_id
            
            # Create ChunkMatch object
            chunk_match = ChunkMatch(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                relevance_score=float(score),
                fragment_id=chunk.fragment_id,
                start_offset=chunk.start_offset,
                end_offset=chunk.end_offset
            )
            
            # Group by element_id
            if element_id not in element_chunks:
                element_chunks[element_id] = []
            element_chunks[element_id].append(chunk_match)
        
        # Create SearchResult objects with aggregated information
        results = []
        for element_id, chunks in element_chunks.items():
            # Sort chunks by relevance score (descending)
            chunks.sort(key=lambda c: c.relevance_score, reverse=True)
            
            # Overall score is the maximum score (best match)
            overall_score = max(chunk.relevance_score for chunk in chunks)
            
            result = SearchResult(
                element_id=element_id,
                overall_relevance_score=overall_score,
                matching_chunks=chunks
            )
            
            results.append(result)
        
        # Sort results by overall relevance score (descending)
        results.sort(key=lambda r: r.overall_relevance_score, reverse=True)
        
        # Return only the requested number of results
        return results[:query.max_results]
    
    def store_index(self, knowledge_document: KnowledgeDocument) -> None:
        """
        Store the index for the given knowledge document to persistent storage.
        
        This method saves:
        1. FAISS index to a binary file
        2. Chunk metadata to a pickle file
        3. Index documents to a JSON file
        4. Index configuration to a JSON file
        
        Args:
            knowledge_document: The knowledge document whose index should be stored
        """
        if not knowledge_document.cacheFilePath:
            raise ValueError("Knowledge document must have a cacheFilePath to store the index")
        
        # Create the index storage directory
        cache_path = Path(knowledge_document.cacheFilePath)
        index_dir = cache_path.parent / "indexes" / "faiss_summary_openai"
        index_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Storing summary index to: {index_dir}")
        
        # Store FAISS index
        faiss_file = index_dir / "faiss.index"
        faiss.write_index(self.faiss_index, str(faiss_file))
        
        # Store chunk metadata (using pickle for numpy arrays)
        metadata_file = index_dir / "chunks.pkl"
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.chunk_metadata, f)
        
        # Store index documents (convert to JSON-serializable format)
        index_docs_file = index_dir / "index_documents.json"
        serializable_docs = {}
        for doc_id, doc in self.index_documents.items():
            serializable_docs[doc_id] = {
                'id': doc.id,
                'element_id': doc.element_id,
                'content': doc.content,
                'element_type': doc.element_type
            }
        
        with open(index_docs_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_docs, f, ensure_ascii=False, indent=2)
        
        # Store index configuration
        config_file = index_dir / "config.json"
        config = {
            'embedding_model': self.embedding_model,
            'embedding_dimension': self.embedding_dimension,
            'chunk_size': getattr(self.chunker, 'chunk_size', None),
            'target_model': getattr(self.chunker, 'target_model', None),
            'total_chunks': len(self.chunk_metadata),
            'indexer_type': 'summary'  # Mark as summary indexer
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully stored summary index with {len(self.chunk_metadata)} chunks")
    
    def load_index(self, knowledge_document: KnowledgeDocument) -> bool:
        """
        Load a previously stored index for the given knowledge document.
        
        This method restores:
        1. FAISS index from a binary file
        2. Chunk metadata from a pickle file
        3. Index documents from a JSON file
        4. Validates configuration compatibility
        
        Args:
            knowledge_document: The knowledge document whose index should be loaded
            
        Returns:
            True if the index was successfully loaded, False if no stored index exists
            or loading failed
        """
        if not knowledge_document.cacheFilePath:
            print("Knowledge document has no cacheFilePath, cannot load summary index")
            return False
        
        # Check if index storage directory exists
        cache_path = Path(knowledge_document.cacheFilePath)
        index_dir = cache_path.parent / "indexes" / "faiss_summary_openai"
        
        if not index_dir.exists():
            print(f"Summary index directory does not exist: {index_dir}")
            return False
        
        # Check if all required files exist
        faiss_file = index_dir / "faiss.index"
        metadata_file = index_dir / "chunks.pkl"
        index_docs_file = index_dir / "index_documents.json"
        config_file = index_dir / "config.json"
        
        required_files = [faiss_file, metadata_file, index_docs_file, config_file]
        for file_path in required_files:
            if not file_path.exists():
                print(f"Required summary index file missing: {file_path}")
                return False
        
        try:
            print(f"Loading summary index from: {index_dir}")
            
            # Load and validate configuration
            with open(config_file, 'r', encoding='utf-8') as f:
                stored_config = json.load(f)
            
            # Check configuration compatibility
            if stored_config.get('embedding_model') != self.embedding_model:
                print(f"Embedding model mismatch: stored={stored_config.get('embedding_model')}, current={self.embedding_model}")
                return False
            
            if stored_config.get('embedding_dimension') != self.embedding_dimension:
                print(f"Embedding dimension mismatch: stored={stored_config.get('embedding_dimension')}, current={self.embedding_dimension}")
                return False
                
            # Check if this is a summary indexer
            if stored_config.get('indexer_type') != 'summary':
                print(f"Indexer type mismatch: expected=summary, stored={stored_config.get('indexer_type')}")
                return False
            
            # Load FAISS index
            self.faiss_index = faiss.read_index(str(faiss_file))
            
            # Load chunk metadata
            with open(metadata_file, 'rb') as f:
                self.chunk_metadata = pickle.load(f)
            
            # Load index documents
            with open(index_docs_file, 'r', encoding='utf-8') as f:
                serializable_docs = json.load(f)
            
            self.index_documents = {}
            for doc_id, doc_data in serializable_docs.items():
                # Reconstruct IndexDocument objects
                index_doc = IndexDocument(
                    id=doc_data['id'],
                    element_id=doc_data['element_id'],
                    content=doc_data['content'],
                    element_type=doc_data['element_type']
                )
                self.index_documents[doc_id] = index_doc
            
            # Verify data consistency
            expected_chunks = stored_config.get('total_chunks', 0)
            if len(self.chunk_metadata) != expected_chunks:
                print(f"Chunk count mismatch: expected={expected_chunks}, loaded={len(self.chunk_metadata)}")
                return False
            
            if self.faiss_index.ntotal != len(self.chunk_metadata):
                print(f"FAISS index size mismatch: faiss={self.faiss_index.ntotal}, metadata={len(self.chunk_metadata)}")
                return False
            
            print(f"Successfully loaded summary index with {len(self.chunk_metadata)} chunks")
            return True
            
        except Exception as e:
            print(f"Error loading summary index: {e}")
            return False
    
    def _create_index_documents(self, knowledge_document: KnowledgeDocument) -> List[IndexDocument]:
        """
        Create IndexDocument objects from a KnowledgeDocument and its elements.
        It creates an IndexDocument only for leaf nodes (elements with no children) that have a contentSummary.
        This approach focuses indexing on the most specific, detailed content while avoiding redundancy
        from intermediate hierarchy levels. This is the key difference from the full-text indexer.

        Args:
            knowledge_document: The knowledge document to process
            
        Returns:
            List of IndexDocument objects for leaf nodes only
        """
        index_documents = []
        
        def process_element(element: KnowledgeDocumentElement, parent_content: str = ""):
            """
            Recursively process knowledge document elements.
            
            Args:
                element: The current knowledge document element
                parent_content: Accumulated content from parent elements (not used in the current implementation, but could in the future be for the context)
                
            """
            
            # Check if this element is a leaf node (has no children)
            is_leaf_node = len(element.childElements) == 0
            
            # Use contentSummary instead of content for indexing
            stripped_element_content = element.contentSummary.strip() if element.contentSummary else ""

            # Create index document only for leaf nodes that have a contentSummary
            if is_leaf_node and stripped_element_content:
                index_doc = IndexDocument(
                    id=str(uuid.uuid4()),
                    element_id=element.id,
                    content=stripped_element_content,  # Store contentSummary in the content field
                    element_type=element.elementType
                )
                index_documents.append(index_doc)
            
            # Continue processing child elements regardless
            for child in element.childElements:
                process_element(child, "")
        
        # Process the root document and all its elements
        process_element(knowledge_document)
        
        return index_documents
    
    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Get embeddings for a list of texts using OpenAI API.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            NumPy array of embeddings
        """
        response = self.openai_client.embeddings.create(
            model=self.embedding_model,
            input=texts
        )
        
        embeddings = np.array([item.embedding for item in response.data])
        return embeddings
