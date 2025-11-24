import os
import re
import json
from pathlib import Path
from typing import Optional, List, Tuple
from docling.document_converter import DocumentConverter
from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base.store import KnowledgeDocumentLoader
from knowledge_base.utils.cache_manager import CacheManager


class LocalKnowledgeDocumentLoader(KnowledgeDocumentLoader):
    """
    A knowledge document loader for local documents stored in the PROJECT/data/local directory.
    It loads various document formats (PDF, DOCX, etc.) as knowledge documents using the docling library.
    A loaded knowledge document has elementType="Document".
    The content of a loaded knowledge document is converted to JSON format using docling.
    """

    def __init__(self, base_dir: str = "data/knowledge_base/local"):
        """
        Initialize the Local knowledge document loader.
        """
        self.base_local_data_dir = Path(base_dir)
        self.base_local_data_dir.mkdir(parents=True, exist_ok=True)
        self.converter = DocumentConverter()

    def _get_document_data_dir(self, document_id: str) -> Path:
        """
        Get the data directory for a specific document.
        
        Args:
            document_id: The document ID in format "https://localhost/[file-name].[file-type]"
            
        Returns:
            Path to the document's data directory
        """
        # Extract filename and create directory based on filename stem
        filename = self._extract_filename_from_document_id(document_id)
        file_stem = Path(filename).stem
        document_data_dir = self.base_local_data_dir / file_stem
        document_data_dir.mkdir(parents=True, exist_ok=True)
        return document_data_dir

    def load_document(self, document_id: str) -> KnowledgeDocument | None:
        """
        Load a knowledge document by its ID.

        Args:
            document_id: The ID of the knowledge document to load in format "https://localhost/[file-name].[file-type]"

        Returns:
            The loaded knowledge document, or None if not found.
            
        Raises:
            ValueError: If document_id format is invalid
            FileNotFoundError: If the requested file doesn't exist in the local directory
            Exception: If document conversion fails
        """
        # First, try to load from split cache
        cached_doc = self._load_from_cache(document_id)
        if cached_doc is not None:
            filename = self._extract_filename_from_document_id(document_id)
            print(f"Loaded document {filename} from split cache")
            return cached_doc
        
        try:
            # Extract filename from document_id
            filename = self._extract_filename_from_document_id(document_id)
            
            # Get document-specific data directory
            document_data_dir = self._get_document_data_dir(document_id)
            
            # Check if file exists in document's directory
            file_path = document_data_dir / filename
            if not file_path.exists():
                raise FileNotFoundError(f"File '{filename}' not found in document directory: {document_data_dir}")
            
            # Create markdown cache file path
            file_stem = file_path.stem  # filename without extension
            md_cache_path = document_data_dir / f"{file_stem}.md"
            
            # Check if markdown cache exists
            if md_cache_path.exists():
                print(f"Loading document {filename} from markdown cache: {md_cache_path.name}")
                # Parse the cached markdown file into hierarchical structure
                knowledge_doc = self._parse_markdown_to_hierarchy(md_cache_path, document_id, file_stem)
            else:
                print(f"Loading document {filename} from original file and creating markdown cache")
                
                # Convert document using docling
                try:
                    result = self.converter.convert(str(file_path))
                    doc = result.document
                    
                    # Export to MD format
                    content = doc.export_to_markdown()
                    
                    # Save content to markdown cache file (for archival purposes)
                    try:
                        md_cache_path.write_text(content, encoding='utf-8')
                        print(f"Created markdown cache: {md_cache_path.name}")
                    except Exception as e:
                        print(f"Warning: Failed to create markdown cache {md_cache_path.name}: {e}")
                    
                    # Extract title from filename (without extension) or use document title if available
                    title = filename
                    if hasattr(doc, 'title') and doc.title:
                        title = doc.title
                    else:
                        # Use filename without extension as title
                        title = file_stem
                    
                    # Parse the markdown content into hierarchical structure
                    knowledge_doc = self._parse_markdown_to_hierarchy(md_cache_path, document_id, title)

                except Exception as e:
                    raise Exception(f"Failed to convert document '{filename}' using docling: {e}")
            
            # Save to JSON cache for future use
            self._save_to_cache(document_id, knowledge_doc)
            
            return knowledge_doc
            
        except (ValueError, FileNotFoundError) as e:
            print(f"Error loading document {document_id}: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error loading document {document_id}: {e}")
            raise

    def _get_cache_filename_from_document_id(self, document_id: str) -> str:
        """
        Get JSON cache filename from document ID.
        """
        filename = self._extract_filename_from_document_id(document_id)
        file_stem = Path(filename).stem
        return f"{file_stem}.json"

    def _load_from_cache(self, document_id: str) -> KnowledgeDocument | None:
        """
        Load document from split JSON cache if it exists.
        This preserves both content and metadata.
        """
        try:
            document_data_dir = self._get_document_data_dir(document_id)
            cache_filename = self._get_cache_filename_from_document_id(document_id)
            # Remove .json extension to get base name for split cache
            cache_path = document_data_dir / Path(cache_filename).stem
            return CacheManager.load_from_split_cache(cache_path)
        except Exception as e:
            print(f"Failed to load from split cache for {document_id}: {e}")
            return None

    def _save_to_cache(self, document_id: str, knowledge_doc: KnowledgeDocument) -> None:
        """
        Save document content to split cache.
        """
        try:
            document_data_dir = self._get_document_data_dir(document_id)
            cache_filename = self._get_cache_filename_from_document_id(document_id)
            # Remove .json extension to get base name for split cache
            cache_path = document_data_dir / Path(cache_filename).stem
            CacheManager.save_to_split_cache(knowledge_doc, cache_path)
        except Exception as e:
            print(f"Failed to save content to split cache for {document_id}: {e}")

    def _extract_filename_from_document_id(self, document_id: str) -> str:
        """
        Extract filename from document ID URL.
        
        Args:
            document_id: URL in format https://localhost/[file-name].[file-type]
            
        Returns:
            Filename in format [file-name].[file-type]
            
        Raises:
            ValueError: If the document_id format is invalid
        """
        # Expected format: https://localhost/[file-name].[file-type]
        pattern = r"^https://localhost/(.+\..+)$"
        match = re.match(pattern, document_id)
        
        if not match:
            raise ValueError(f"Invalid document_id format: {document_id}. Expected format: https://localhost/[file-name].[file-type]")
        
        filename = match.group(1)
        return filename

    def _parse_markdown_to_hierarchy(self, markdown_path: Path, document_id: str, title: str) -> KnowledgeDocument:
        """
        Parse a markdown file and convert it to a hierarchical KnowledgeDocument structure.
        
        Args:
            markdown_path: Path to the markdown file
            document_id: The document ID for the KnowledgeDocument
            title: The title for the KnowledgeDocument
            
        Returns:
            A KnowledgeDocument with hierarchical structure based on markdown headers
        """
        try:
            content = markdown_path.read_text(encoding='utf-8')
        except Exception as e:
            raise Exception(f"Failed to read markdown file {markdown_path}: {e}")
        
        # Split content into lines for processing
        lines = content.split('\n')
        
        # Parse the markdown structure and extract document intro content
        sections, document_intro_content = self._extract_markdown_sections(lines)
        
        # Build hierarchical structure
        child_elements = self._build_hierarchy_from_sections(sections, document_id, lines)
        
        # Create the main knowledge document with only the introductory content
        knowledge_doc = KnowledgeDocument(
            id=document_id,
            title=title,
            content=document_intro_content,  # Only content before first header
            contentSummary=None,
            childElements=child_elements,
            parentElement=None,
            elementType="Document"
        )
        
        # Set parent references for child elements
        for child in child_elements:
            child.parentElement = knowledge_doc
            self._set_parent_references_recursive(child)
        
        return knowledge_doc
    
    def _extract_markdown_sections(self, lines: List[str]) -> Tuple[List[Tuple[int, str, str, int]], str]:
        """
        Extract sections from markdown lines based on headers.
        
        Args:
            lines: List of markdown lines
            
        Returns:
            Tuple of (sections, document_intro_content) where:
            - sections: List of tuples (header_level, header_text, section_id, line_index)
            - document_intro_content: Content that appears before the first header
        """
        sections = []
        document_intro_lines = []
        first_header_found = False
        
        for i, line in enumerate(lines):
            # Check if line is a header
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            
            if header_match:
                first_header_found = True
                
                # Record section info
                header_level = len(header_match.group(1))
                header_text = header_match.group(2).strip()
                section_id = f"section_{i}_{re.sub(r'[^a-zA-Z0-9]', '_', header_text.lower())}"
                sections.append((header_level, header_text, section_id, i))
            else:
                # Add line to document intro if before first header
                if not first_header_found and line.strip():
                    document_intro_lines.append(line)
        
        # Prepare document intro content
        document_intro_content = '\n'.join(document_intro_lines).strip() if document_intro_lines else ""
        
        return sections, document_intro_content
    
    def _build_hierarchy_from_sections(self, sections: List[Tuple[int, str, str, int]], document_id: str, lines: List[str]) -> List[KnowledgeDocumentElement]:
        """
        Build hierarchical structure from flat list of sections.
        
        Args:
            sections: List of tuples (header_level, header_text, section_id, line_index)
            document_id: The parent document ID
            lines: Original markdown lines
            
        Returns:
            List of top-level KnowledgeDocumentElement instances
        """
        if not sections:
            return []
        
        elements = []
        stack = []  # Stack to keep track of parent elements at different levels
        
        for i, (header_level, header_text, section_id, line_index) in enumerate(sections):
            # Create full section ID including document reference
            full_section_id = f"{document_id}#{section_id}"
            
            # Create element type based on header level
            element_type = self._get_element_type_for_level(header_level)
            
            # Extract content for this section (content before first child)
            section_content = self._extract_section_content(i, sections, lines)
            
            # Create the knowledge element
            element = KnowledgeDocumentElement(
                id=full_section_id,
                title=header_text,
                content=section_content,
                contentSummary=None,
                childElements=[],
                parentElement=None,  # Will be set later
                elementType=element_type
            )
            
            # Find the correct parent based on header hierarchy
            while stack and stack[-1][0] >= header_level:
                stack.pop()
            
            if stack:
                # Add as child to the last element in stack
                parent_element = stack[-1][1]
                parent_element.childElements.append(element)
                element.parentElement = parent_element
            else:
                # This is a top-level element
                elements.append(element)
            
            # Add current element to stack
            stack.append((header_level, element))
        
        return elements
    
    def _extract_section_content(self, section_index: int, sections: List[Tuple[int, str, str, int]], lines: List[str]) -> str:
        """
        Extract content for a section - only the text that appears before its first child.
        
        Args:
            section_index: Index of the current section in sections list
            sections: List of all sections
            lines: Original markdown lines
            
        Returns:
            Content string for the section
        """
        current_level, _, _, current_line_index = sections[section_index]
        
        # Find the range of lines for this section
        start_line = current_line_index + 1  # Start after the header line
        
        # Find the end line (before next header at same or higher level, or before first child)
        end_line = len(lines)  # Default to end of document
        
        # Look for next section that would end this section's content
        for next_section_index in range(section_index + 1, len(sections)):
            next_level, _, _, next_line_index = sections[next_section_index]
            
            # If next section is a child (deeper level), continue looking
            if next_level > current_level:
                continue
            
            # If next section is at same or higher level, it ends this section
            end_line = next_line_index
            break
        
        # Now find the first child section to determine where this section's own content ends
        first_child_line = end_line  # Default: no children, content goes to end of section
        
        for next_section_index in range(section_index + 1, len(sections)):
            next_level, _, _, next_line_index = sections[next_section_index]
            
            if next_level > current_level:
                # This is a child - section's own content ends here
                first_child_line = next_line_index
                break
            elif next_level <= current_level:
                # This is a sibling or parent - no children found
                break
        
        # Extract content lines between header and first child (or end of section)
        content_lines = []
        for line_idx in range(start_line, first_child_line):
            if line_idx < len(lines):
                line = lines[line_idx]
                if line.strip():  # Only add non-empty lines
                    content_lines.append(line)
        
        return '\n'.join(content_lines).strip() if content_lines else ""
    
    def _get_element_type_for_level(self, header_level: int) -> str:
        """
        Get element type based on header level.
        
        Args:
            header_level: The markdown header level (1-6)
            
        Returns:
            String representing the element type
        """
        type_mapping = {
            1: "Chapter",
            2: "Section", 
            3: "Subsection",
            4: "Paragraph",
            5: "Subparagraph",
            6: "Item"
        }
        return type_mapping.get(header_level, "Section")
    
    def _set_parent_references_recursive(self, element: KnowledgeDocumentElement) -> None:
        """
        Recursively set parent references for all child elements.
        
        Args:
            element: The current element to process (its children will get it as parent)
        """
        for child in element.childElements:
            child.parentElement = element
            self._set_parent_references_recursive(child)
