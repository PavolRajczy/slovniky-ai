"""
Cache management utilities for knowledge base components.

This module provides common functionality for loading and saving KnowledgeDocument
objects to and from JSON cache files.
"""

import json
from pathlib import Path
from typing import Optional, Callable
from knowledge_base.domain import KnowledgeDocument
from .document_serialization import (
    knowledge_document_to_dict, dict_to_knowledge_document,
    knowledge_document_content_to_dict, knowledge_document_metadata_to_dict,
    dict_to_knowledge_document_content, apply_metadata_to_knowledge_document,
    merge_content_and_metadata
)


class CacheManager:
    """
    Manages JSON cache operations for KnowledgeDocument objects.
    """
    
    @staticmethod
    def get_split_cache_paths(cache_path: Path) -> tuple[Path, Path]:
        """
        Generate content and metadata cache file paths from base cache path.
        
        Args:
            cache_path: Base cache file path (e.g., document.json)
            
        Returns:
            Tuple of (content_path, metadata_path)
        """
        base_path = cache_path.with_suffix('')
        content_path = base_path.with_suffix('.content.json')
        metadata_path = base_path.with_suffix('.metadata.json')
        return content_path, metadata_path

    @staticmethod
    def load_from_split_cache(cache_path: Path) -> Optional[KnowledgeDocument]:
        """
        Load document from split JSON cache files (content + metadata) if they exist.
        
        Args:
            cache_path: Base path to the cache files (without .content/.metadata suffix)
            
        Returns:
            KnowledgeDocument if successfully loaded, None otherwise
        """
        try:
            content_path, metadata_path = CacheManager.get_split_cache_paths(cache_path)
            
            # Load content (required)
            if not content_path.exists():
                return None
                
            with open(content_path, 'r', encoding='utf-8') as f:
                content_data = json.load(f)
            
            # Load metadata (optional)
            metadata_data = None
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata_data = json.load(f)
            
            # Create document
            if metadata_data:
                doc = merge_content_and_metadata(content_data, metadata_data)
            else:
                doc = dict_to_knowledge_document_content(content_data)
            
            # Set the cache file path to the base path
            doc.cacheFilePath = str(cache_path)
            return doc
            
        except Exception as e:
            print(f"Failed to load from split cache {cache_path}: {e}")
            return None

    @staticmethod
    def save_to_split_cache(knowledge_doc: KnowledgeDocument, cache_path: Path) -> None:
        """
        Save document to split JSON cache files (content + metadata).
        
        Args:
            knowledge_doc: The document to save
            cache_path: Base path where to save the cache files
        """
        try:
            content_path, metadata_path = CacheManager.get_split_cache_paths(cache_path)
            
            # Ensure the directory exists
            content_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Set the cache file path on the knowledge document
            knowledge_doc.cacheFilePath = str(cache_path)
            
            # Save content
            content_data = knowledge_document_content_to_dict(knowledge_doc)
            with open(content_path, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, ensure_ascii=False, indent=2)
            
            # Save metadata
            metadata_data = knowledge_document_metadata_to_dict(knowledge_doc)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Failed to save to split cache {cache_path}: {e}")

    @staticmethod
    def save_content_to_split_cache(knowledge_doc: KnowledgeDocument, cache_path: Path) -> None:
        """
        Save only the content part of document to split cache, preserving existing metadata.
        
        Args:
            knowledge_doc: The document to save
            cache_path: Base path where to save the cache files
        """
        try:
            content_path, metadata_path = CacheManager.get_split_cache_paths(cache_path)
            
            # Ensure the directory exists
            content_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Set the cache file path on the knowledge document
            knowledge_doc.cacheFilePath = str(cache_path)
            
            # Save only content (don't touch metadata file)
            content_data = knowledge_document_content_to_dict(knowledge_doc)
            with open(content_path, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Failed to save content to split cache {cache_path}: {e}")

    @staticmethod
    def save_metadata_to_split_cache(knowledge_doc: KnowledgeDocument, cache_path: Path) -> None:
        """
        Save only the metadata part of document to split cache, preserving existing content.
        
        Args:
            knowledge_doc: The document to save
            cache_path: Base path where to save the cache files
        """
        try:
            content_path, metadata_path = CacheManager.get_split_cache_paths(cache_path)
            
            # Ensure the directory exists
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save only metadata (don't touch content file)
            metadata_data = knowledge_document_metadata_to_dict(knowledge_doc)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Failed to save metadata to split cache {cache_path}: {e}")

    @staticmethod
    def update_split_cache(document: KnowledgeDocument, update_content: bool = True, update_metadata: bool = True) -> None:
        """
        Update existing split cache files with the current document state.
        
        Args:
            document: The document to update in cache
            update_content: Whether to update the content file
            update_metadata: Whether to update the metadata file
        """
        try:
            if document.cacheFilePath:
                cache_path = Path(document.cacheFilePath)
                
                if update_content and update_metadata:
                    CacheManager.save_to_split_cache(document, cache_path)
                    print(f"Updated split cache files: {cache_path.name}")
                elif update_content:
                    CacheManager.save_content_to_split_cache(document, cache_path)
                    print(f"Updated content cache file: {cache_path.name}")
                elif update_metadata:
                    CacheManager.save_metadata_to_split_cache(document, cache_path)
                    print(f"Updated metadata cache file: {cache_path.name}")
            else:
                print("Warning: Document has no cache file path set")
        except Exception as e:
            print(f"Failed to update split cache file {document.cacheFilePath}: {e}")
