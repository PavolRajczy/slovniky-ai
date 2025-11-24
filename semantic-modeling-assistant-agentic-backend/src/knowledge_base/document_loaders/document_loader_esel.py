import re
import json
import os
from pathlib import Path
from typing import Optional, List
from rdflib import Graph
from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base.store import KnowledgeDocumentLoader
from knowledge_base.utils.cache_manager import CacheManager

# Legacy data structures for compatibility with the existing logic
class LegacyLegalElement:
    """Base class for legacy legal elements."""
    def __init__(self, id: str, officialIdentifier: str, title: str, elements: List, textContent: Optional[str]):
        self.id = id
        self.officialIdentifier = officialIdentifier
        self.title = title
        self.elements = elements
        self.textContent = textContent

class LegacyLegalAct(LegacyLegalElement):
    """Legacy legal act structure."""
    pass

class LegalStructuralElement(LegacyLegalElement):
    """Legacy structural element."""
    pass

class LegalPart(LegalStructuralElement):
    """Legacy legal part structure."""
    pass

class LegalChapter(LegalStructuralElement):
    """Legacy legal chapter structure."""
    pass

class LegalDivision(LegalStructuralElement):
    """Legacy legal division structure."""
    pass

class LegalSection(LegalStructuralElement):
    """Legacy legal section structure."""
    pass

class LegalAppendix(LegalStructuralElement):
    """Legacy legal appendix structure."""
    pass

# Type alias for compatibility
LegalAct = LegacyLegalAct

class ESELKnowledgeDocumentLoader(KnowledgeDocumentLoader):
    """
    A knowledge document loader for the Czech Code of Laws.
    It loads legal acts as knowledge documents.
    A loaded knowledge document has elementType="LegalAct".
    Its knowledge document elements have elementType="Part"|"Chapter"|"Division"|"Section".
    The content of a loaded knowledge document is an XML string with a hierarchical structure denoted by elements <f id="f_id"> where f_id is the unique identifier of the fragment.
    """

    def __init__(self, sparql_endpoint: str, base_dir: str = "data/knowledge_base/esel"):
        """
        Initialize the ESEL knowledge document loader.
        
        Args:
            sparql_endpoint: The SPARQL endpoint URL for querying ESEL data.
        """
        self.sparql_endpoint = sparql_endpoint
        self.base_cache_dir = Path(base_dir)
        self.base_cache_dir.mkdir(parents=True, exist_ok=True)

    def load_document(self, document_id: str) -> KnowledgeDocument | None:
        """
        Load a knowledge document by its ID.

        Args:
            document_id: The ID of the knowledge document to load.

        Returns:
            The loaded knowledge document, or None if not found.
        """
        # First, try to load from cache
        cached_doc = self._load_from_cache(document_id)
        if cached_doc is not None:
            print(f"Loaded document {document_id} from cache")
            return cached_doc
        
        try:
            print(f"Loading document {document_id} from SPARQL endpoint")
            
            # Create a temporary legacy legal act structure to use the existing logic
            legacy_legal_act = LegacyLegalAct(
                id=document_id,
                officialIdentifier="",
                title="",
                elements=[],
                textContent=None
            )
            
            # Load the content using the legacy method
            loaded_legacy_act = self._load_legal_act_content_from_esel(legacy_legal_act)
            
            # Convert to our domain model
            knowledge_doc = self._convert_legacy_to_knowledge_document(loaded_legacy_act)
            
            # Save to cache for future use
            self._save_to_cache(document_id, knowledge_doc)
            
            return knowledge_doc
            
        except Exception as e:
            print(f"Failed to load document {document_id}: {e}")
            return None

    def _get_document_cache_dir(self, document_id: str) -> Path:
        """
        Get the cache directory for a specific document.
        
        Args:
            document_id: The document ID
            
        Returns:
            Path to the document's cache directory
        """
        # Create a safe directory name from document ID
        safe_dir_name = self._extract_cache_filename(document_id).replace('.json', '')
        document_cache_dir = self.base_cache_dir / safe_dir_name
        document_cache_dir.mkdir(parents=True, exist_ok=True)
        return document_cache_dir

    def _extract_cache_filename(self, document_id: str) -> str:
        """
        Extract cache filename from document ID URL.
        
        Args:
            document_id: URL in format https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/YEAR/NUMBER/DATE
            
        Returns:
            Filename in format year-number-date.json
        """
        # Extract the last three parts (year, number, date) from the URL
        parts = document_id.rstrip('/').split('/')
        if len(parts) >= 3:
            year, number, date = parts[-3], parts[-2], parts[-1]
            return f"{year}-{number}-{date}.json"
        else:
            # Fallback to a safe filename if URL format is unexpected
            safe_name = document_id.replace('/', '_').replace(':', '_').replace('?', '_').replace('#', '_')
            # Handle empty string case
            if not safe_name:
                safe_name = "_"
            return f"{safe_name}.json"

    def _load_from_cache(self, document_id: str) -> KnowledgeDocument | None:
        """
        Load document from split cache if it exists.
        This preserves both content and metadata.
        """
        try:
            document_cache_dir = self._get_document_cache_dir(document_id)
            cache_filename = self._extract_cache_filename(document_id)
            # Remove .json extension to get base name for split cache
            cache_path = document_cache_dir / Path(cache_filename).stem
            return CacheManager.load_from_split_cache(cache_path)
        except Exception as e:
            print(f"Failed to load from split cache for {document_id}: {e}")
            return None

    def _save_to_cache(self, document_id: str, knowledge_doc: KnowledgeDocument) -> None:
        """
        Save document to split cache.
        """
        try:
            document_cache_dir = self._get_document_cache_dir(document_id)
            cache_filename = self._extract_cache_filename(document_id)
            # Remove .json extension to get base name for split cache
            cache_path = document_cache_dir / Path(cache_filename).stem
            CacheManager.save_to_split_cache(knowledge_doc, cache_path)
        except Exception as e:
            print(f"Failed to save content to split cache for {document_id}: {e}")

    def _convert_legacy_to_knowledge_document(self, legacy_act: LegacyLegalAct) -> KnowledgeDocument:
        """
        Convert a legacy legal act structure to a KnowledgeDocument.
        
        Args:
            legacy_act: The legacy legal act to convert.
            
        Returns:
            A KnowledgeDocument representing the legal act.
        """
        # Convert child elements
        child_elements = []
        for legacy_element in legacy_act.elements:
            child_element = self._convert_legacy_element_to_knowledge_element(legacy_element)
            child_elements.append(child_element)
        
        # Create the main knowledge document
        knowledge_doc = KnowledgeDocument(
            id=legacy_act.id,
            title=legacy_act.title if legacy_act.title else legacy_act.officialIdentifier,
            content=legacy_act.textContent,
            contentSummary=None,
            childElements=child_elements,
            parentElement=None,
            elementType="LegalAct"
        )
        
        # Set parent references for child elements
        for child in child_elements:
            child.parentElement = knowledge_doc
        
        return knowledge_doc
    
    def _convert_legacy_element_to_knowledge_element(self, legacy_element: LegacyLegalElement) -> KnowledgeDocumentElement:
        """
        Convert a legacy legal element to a KnowledgeDocumentElement.
        
        Args:
            legacy_element: The legacy element to convert.
            
        Returns:
            A KnowledgeDocumentElement representing the legacy element.
        """
        # Convert child elements recursively
        child_elements = []
        for child_legacy_element in legacy_element.elements:
            child_element = self._convert_legacy_element_to_knowledge_element(child_legacy_element)
            child_elements.append(child_element)
        
        # Determine element type based on class
        element_type = legacy_element.__class__.__name__.replace('Legal', '').replace('Legacy', '')
        
        # Create the knowledge element
        knowledge_element = KnowledgeDocumentElement(
            id=legacy_element.id,
            title=legacy_element.title if legacy_element.title else legacy_element.officialIdentifier,
            content=legacy_element.textContent,
            contentSummary=None,
            childElements=child_elements,
            parentElement=None,  # Will be set by parent
            elementType=element_type
        )
        
        # Set parent references for child elements
        for child in child_elements:
            child.parentElement = knowledge_element
        
        return knowledge_element

    def _load_legal_act_content_from_esel(self, legal_act: LegalAct) -> LegalAct:
        """
        Loads the content of a legal act from the SPARQL endpoint using the provided query.

        :param legal_act_id: The ID of the legal act to fetch
        :return: An instance of LegalAct containing the fetched data
        """
        g = Graph()
        sparql_str = f"""
            PREFIX esel: <https://slovník.gov.cz/datový/sbírka/pojem/>

            SELECT ?fragment_id ?citace ?hierarchie ?poradi ?obsah
            WHERE {{
                SERVICE <{self.sparql_endpoint}> {{
                    <{legal_act.id}> esel:má-fragment-znění ?fragment_id .

                    {{
                        ?fragment_id esel:citace-označení-fragmentu-znění-právního-aktu ?citace ;
                            esel:hierarchie-fragmentu-znění-právního-aktu ?hierarchie ;
                            esel:pořadí-fragmentu-znění-právního-aktu ?poradi ;
                            esel:obsahuje-fragment/esel:text-fragmentu ?obsah .
                    }} UNION {{
                        ?fragment_id 
                            esel:hierarchie-fragmentu-znění-právního-aktu ?hierarchie ;
                            esel:pořadí-fragmentu-znění-právního-aktu ?poradi ;
                            esel:obsahuje-fragment ?fragment_s_textem .
                        ?fragment_s_textem esel:text-fragmentu ?obsah ;
                            esel:má-typ-fragmentu <https://opendata.eselpoint.cz/esel-esb/cis-esb-typ-fragmentu/položka/Nadpis_pod>
                        BIND("Nadpis" AS ?citace)
                    }} UNION {{
                        ?fragment_id 
                            esel:hierarchie-fragmentu-znění-právního-aktu ?hierarchie ;
                            esel:pořadí-fragmentu-znění-právního-aktu ?poradi ;
                            esel:obsahuje-fragment ?fragment_s_textem .
                        FILTER NOT EXISTS {{?fragment_id esel:citace-označení-fragmentu-znění-právního-aktu []}}
                        ?fragment_s_textem esel:text-fragmentu ?obsah ;
                            esel:má-typ-fragmentu <https://opendata.eselpoint.cz/esel-esb/cis-esb-typ-fragmentu/položka/Odstavec_Dc>
                        BIND("Text" AS ?citace)
                    }}
                }}
            }}
            ORDER BY ?poradi
        """

        try:
            results = g.query(sparql_str)

            current_parent = legal_act
            last_element = None
            legal_elements = {}

            sections_data = {}

            appendices_data = {}

            last_hierarchy_prefix = None
            
            for row in results: # !!!!!!!!! par 7g u 56/2001 nezpracujeme správně - není jako fragment, ale jako text přímo
                citace = str(row.citace)
                fragment_id = str(row.fragment_id)
                hierarchie = str(row.hierarchie)
                obsah = str(row.obsah)
                                
                # Check if the citation is a part of the legal act
                part_match = re.match(r"^Část\s+(\d+[a-z]*)$", citace)
                if part_match:
                    part_number = part_match.group(1)
                    
                    new_legal_part = LegalPart(
                        id=fragment_id,
                        officialIdentifier=citace,
                        title=citace,
                        elements=[],
                        textContent=None,
                    )

                    # A part is a top-level element, so we reset to legal_act
                    current_parent = legal_act
                    current_parent.elements.append(new_legal_part)
                    current_parent = new_legal_part
                    legal_elements[f"Část {part_number}"] = new_legal_part
                    last_element = new_legal_part
                    continue
                
                # Check if the citation is a chapter of the legal act
                chapter_match = re.match(r"^Část\s+(\d+[a-z]*)\s+Hlava\s+(\d+[a-z]*)$", citace)
                if chapter_match:
                    part_number = chapter_match.group(1)
                    chapter_number = chapter_match.group(2)
                    
                    new_legal_chapter = LegalChapter(
                        id=fragment_id,
                        officialIdentifier=citace,
                        title=citace,
                        elements=[],
                        textContent=None,
                    )

                    # A chapter is a sub-element of a part, so we need to find the part
                    current_parent = legal_elements.get(f"Část {part_number}", legal_act)
                    current_parent.elements.append(new_legal_chapter)
                    current_parent = new_legal_chapter
                    legal_elements[f"Část {part_number} Hlava {chapter_number}"] = new_legal_chapter
                    last_element = new_legal_chapter
                    continue
                
                # Check if the citation is a division of the legal act
                division_match = re.match(r"^Část\s+(\d+[a-z]*)\s+Hlava\s+(\d+[a-z]*)\s+Díl\s+(\d+[a-z]*)$", citace)
                if division_match:
                    part_number = division_match.group(1)
                    chapter_number = division_match.group(2)
                    division_number = division_match.group(3)
                    
                    new_legal_division = LegalDivision(
                        id=fragment_id,
                        officialIdentifier=citace,
                        title=citace,
                        elements=[],
                        textContent=None,
                    )

                    # A division is a sub-element of a chapter, so we need to find the chapter
                    current_parent = legal_elements.get(f"Část {part_number} Hlava {chapter_number}", legal_act)
                    current_parent.elements.append(new_legal_division)
                    current_parent = new_legal_division
                    legal_elements[f"Část {part_number} Hlava {chapter_number} Díl {division_number}"] = new_legal_division
                    last_element = new_legal_division
                    continue
                
                # Handle section fragments (§)
                section_match = re.match(r"^§\s*(\d+[a-z]*).*", citace)
                if section_match:
                    section_number = section_match.group(1)
                    
                    # Initialize section data if not exists
                    if section_number not in sections_data:
                        sections_data[section_number] = {
                            'fragments': [],
                            'title': None,
                            'parent': current_parent,
                            'section_id': fragment_id,
                        }
                        last_element = sections_data[section_number]
                        last_hierarchy_prefix = hierarchie

                    # Cut the last_hierarchy_prefix from hierarchie if present
                    if last_hierarchy_prefix and hierarchie.startswith(last_hierarchy_prefix):
                        hierarchie = hierarchie[len(last_hierarchy_prefix):]
                        if hierarchie.startswith('/'):
                            hierarchie = hierarchie[1:]

                    hierarchie = "1/" + hierarchie.strip('/')
                    
                    # Store fragment data for later processing
                    sections_data[section_number]['fragments'].append({
                        'hierarchie': hierarchie, # We need to cut the prefix that is common for all fragments in the same section. It is the value of 'hierarchie' property of the first fragment in the section.
                        'obsah': obsah,
                        'citace': citace,
                        'fragment_id': fragment_id
                    })
                    continue

                appendix_match = re.match(r"^Příloha\s+č\.\s+(\d+).*", citace)
                if appendix_match:
                    appendix_number = appendix_match.group(1)
                    
                    if appendix_number not in appendices_data:
                        appendices_data[appendix_number] = {
                            'fragments': [],
                            'title': None,
                            'parent': legal_act,
                            'appendix_id': fragment_id,
                        }
                        last_element = appendices_data[appendix_number]
                        last_hierarchy_prefix = hierarchie

                    # Cut the last_hierarchy_prefix from hierarchie if present
                    if last_hierarchy_prefix and hierarchie.startswith(last_hierarchy_prefix):
                        hierarchie = hierarchie[len(last_hierarchy_prefix):]
                        if hierarchie.startswith('/'):
                            hierarchie = hierarchie[1:]

                    hierarchie = "1/" + hierarchie.strip('/')

                    appendices_data[appendix_number]['fragments'].append({
                        'hierarchie': hierarchie,
                        'obsah': obsah,
                        'citace': citace,
                        'fragment_id': fragment_id
                    })

                text_match = re.match(r"^Text$", citace)
                if text_match:
                    if last_element:
                        # Cut the section_hierarchy_prefix from hierarchie if present
                        if last_hierarchy_prefix and hierarchie.startswith(last_hierarchy_prefix):
                            hierarchie = hierarchie[len(last_hierarchy_prefix):]
                            if hierarchie.startswith('/'):
                                hierarchie = hierarchie[1:]

                        hierarchie = "1/" + hierarchie.strip('/')
                        
                        last_element['fragments'].append({
                            'hierarchie': hierarchie,
                            'obsah': obsah,
                            'citace': None,
                            'fragment_id': fragment_id
                        })
                    continue

                title_match = re.match(r"^Nadpis$", citace)
                if title_match:
                    # If the fragment is a title, we set it as the title of the current element
                    if last_element:
                        if isinstance(last_element, LegalStructuralElement):
                            last_element.title = obsah.strip()
                        else:
                            last_element['title'] = obsah.strip()
                    continue
            
            # Process collected sections and add them to their respective parents
            for section_number, section_data in sections_data.items():
                fragments = section_data['fragments']
                title = section_data['title']
                parent_element = section_data['parent']
                section_id = section_data['section_id']
                
                # Build hierarchical XML structure for section content
                xml_content = self._build_hierarchical_xml(fragments)
                
                new_section = LegalSection(
                    id=section_id,
                    officialIdentifier=f"§ {section_number}",
                    title=title if title else f"§ {section_number}",
                    textContent=xml_content,
                    elements=[],
                )
                
                parent_element.elements.append(new_section)

            # Process collected appendices and add them to their respective parents
            for appendix_number, appendix_data in appendices_data.items():
                fragments = appendix_data['fragments']
                title = appendix_data['title']
                parent_element = appendix_data['parent']
                appendix_id = appendix_data['appendix_id']
                
                # Build hierarchical XML structure for appendix content
                xml_content = self._build_hierarchical_xml(fragments)
                
                new_appendix = LegalAppendix(
                    id=appendix_id,
                    officialIdentifier=f"§ {appendix_number}",
                    title=title if title else f"Příloha č. {appendix_number}",
                    textContent=xml_content,
                    elements=[],
                )
                
                parent_element.elements.append(new_appendix)
            
            return legal_act
        except Exception as e:
            raise RuntimeError(f"Failed to load legal act: {e}")
    
    def _build_hierarchical_xml(self, fragments):
        """
        Build hierarchical XML structure from fragments based on their hierarchy.
        """
        
        # Build hierarchy tree
        hierarchy_tree = {}
        
        for fragment in fragments:
            hierarchie = fragment['hierarchie']
            hierarchy_parts = hierarchie.strip('/').split('/')
            
            # Navigate to the correct position in the tree
            current_level = hierarchy_tree
            for part in hierarchy_parts[:-1]:
                if part not in current_level:
                    current_level[part] = {'children': {}, 'content': '', 'id': ''}
                current_level = current_level[part]['children']
            
            # Add the fragment at the final level
            final_part = hierarchy_parts[-1]
            if final_part not in current_level:
                current_level[final_part] = {'children': {}, 'content': '', 'id': ''}
            
            # Clean HTML from content
            clean_content = re.sub(r"<[^>]*>", "", fragment['obsah'])
            current_level[final_part]['content'] = clean_content
            current_level[final_part]['id'] = fragment['fragment_id']

        return self._tree_to_xml(hierarchy_tree)
    
    def _tree_to_xml(self, tree, level=0):
        """
        Convert hierarchy tree to XML string.
        """
        xml_parts = []
        
        for key in tree.keys():
            node = tree[key]
            indent = "  " * level
            
            if node['content'] or node['children']:
                xml_parts.append(f"{indent}<f id=\"{node['id']}\">")
                
                if node['content']:
                    # Add content with proper indentation
                    content_lines = node['content'].strip().split('\n')
                    for line in content_lines:
                        if line.strip():
                            xml_parts.append(f"{indent}  {line.strip()}")
                
                if node['children']:
                    xml_parts.append(self._tree_to_xml(node['children'], level + 1))
                
                xml_parts.append(f"{indent}</f>")
        
        return '\n'.join(xml_parts)