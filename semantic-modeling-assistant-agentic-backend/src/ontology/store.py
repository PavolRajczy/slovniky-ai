import os
import json
import re
import hashlib

from typing import Any, Dict, List
from rdflib import URIRef

from .domain import Ontology, OntologyClass, OntologyAttribute, OntologyRelationship, Kind

class OntologyStore:
    def store_ontology(self, ontology: Ontology) -> None:
        """Persist the complete state of the ontology to the store."""
        ...

    def load_ontology(self, ontology_id: str) -> Ontology:
        """Load the complete state of the ontology from the store by its id."""
        ...

    def exists(self, ontology_uri: str) -> bool:
        """Return True if an ontology with the given URI already exists in the store."""
        ...

    def list_all(self) -> List[Ontology]:
        """Return a list of all ontologies stored in the store."""
        ...

class FilesystemOntologyStore(OntologyStore):
    def __init__(self, base_dir: str = "data/ontologies"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.ontologies = {}

    def _uri_to_safe_dirname(self, uri: str) -> str:
        """
        Convert a URI to a filesystem-safe directory name.
        
        Args:
            uri (str): The URI to convert
            
        Returns:
            str: A filesystem-safe directory name
        """
        if not uri:
            return "unnamed"
            
        # Remove protocol and convert to lowercase
        safe_name = uri.lower()
        
        # Remove common protocols
        safe_name = re.sub(r'^https?://', '', safe_name)
        safe_name = re.sub(r'^ftp://', '', safe_name)
        safe_name = re.sub(r'^file://', '', safe_name)
        
        # Replace invalid filesystem characters with underscores
        # Windows invalid chars: < > : " | ? * \ /
        # Also replace spaces and other problematic chars
        safe_name = re.sub(r'[<>:"|?*\\/\s#%&{}\\^~\[\]`=]', '_', safe_name)
        
        # Replace multiple underscores with single underscore
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # Remove leading/trailing underscores and dots
        safe_name = safe_name.strip('_.')
        
        # Ensure it's not empty and not too long
        if not safe_name:
            safe_name = "unnamed"
        
        # Limit length and add hash if too long to ensure uniqueness
        if len(safe_name) > 100:
            # Take first 80 chars and add hash of full URI for uniqueness
            hash_suffix = hashlib.md5(uri.encode('utf-8')).hexdigest()[:16]
            safe_name = safe_name[:80] + "_" + hash_suffix
            
        return safe_name

    def exists(self, ontology_uri: str) -> bool:
        """Check if ontology.json exists for the given ontology URI without creating it."""
        if not ontology_uri:
            return False
        safe_dirname = self._uri_to_safe_dirname(ontology_uri)
        ontology_dir = os.path.join(self.base_dir, safe_dirname)
        ontology_file = os.path.join(ontology_dir, "ontology.json")
        return os.path.exists(ontology_file)

    def list_all(self) -> List[Ontology]:
        """List all ontologies by scanning the base directory for ontology.json files.

        Returns:
            List[Ontology]: A list of ontologies reconstructed from their stored JSON.

        Notes:
            - This method reads existing ontology.json files only and will not create new ones.
            - Invalid or unreadable files are skipped with best-effort logging.
        """
        ontologies: List[Ontology] = []
        if not os.path.isdir(self.base_dir):
            return ontologies

        try:
            for name in os.listdir(self.base_dir):
                ontology_dir = os.path.join(self.base_dir, name)
                if not os.path.isdir(ontology_dir):
                    continue
                ontology_file = os.path.join(ontology_dir, "ontology.json")
                if not os.path.exists(ontology_file):
                    continue
                try:
                    with open(ontology_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    ontology = self._ontology_from_dict(data)
                    # Cache it internally as load_ontology would do
                    if ontology and ontology.uri is not None:
                        self.ontologies[ontology.uri] = ontology
                    if ontology is not None:
                        ontologies.append(ontology)
                except Exception:
                    # Skip invalid files
                    continue
        except FileNotFoundError:
            # Base dir does not exist
            return ontologies

        return ontologies

    def store_ontology(self, ontology: Ontology) -> None:
        """
        Store the previously loaded ontology in its own subdirectory named by ontology id.
        It is always necessary to call load an ontology before it can be stored.

        Args:
            ontology (Ontology): The ontology to store.

        Raises:
            ValueError: If the ontology is not found in the store.
        """
        if ontology.uri not in self.ontologies:
            raise ValueError(f"Ontology not found in the store: {ontology.uri}")

        safe_dirname = self._uri_to_safe_dirname(str(ontology.uri))
        ontology_dir = os.path.join(self.base_dir, safe_dirname)
        os.makedirs(ontology_dir, exist_ok=True)
        ontology_file = os.path.join(ontology_dir, "ontology.json")
        with open(ontology_file, "w", encoding="utf-8") as f:
            json.dump(self._ontology_to_dict(ontology), f, ensure_ascii=False, indent=2)

    def load_ontology(self, ontology_uri: str) -> Ontology:
        """
        Load the ontology from its subdirectory by id.
        When the loaded ontology is changed later, it is necessary to call store_ontology() for it to be persisted.

        Args:
            ontology_id (str): The ID of the ontology to load.

        Returns:
            Ontology: The loaded ontology.
        """
        safe_dirname = self._uri_to_safe_dirname(ontology_uri)
        ontology_dir = os.path.join(self.base_dir, safe_dirname)
        ontology_file = os.path.join(ontology_dir, "ontology.json")
        if not os.path.exists(ontology_file):
            # Create an empty ontology and persist it
            empty_ontology = Ontology(
                uri=URIRef(ontology_uri),
                label="",
                description=None
            )
            os.makedirs(ontology_dir, exist_ok=True)
            with open(ontology_file, "w", encoding="utf-8") as f:
                json.dump(self._ontology_to_dict(empty_ontology), f, ensure_ascii=False, indent=2)
        with open(ontology_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        ontology = self._ontology_from_dict(data)

        self.ontologies[ontology.uri] = ontology
        return ontology


    def _ontology_to_dict(self, ontology: Ontology) -> Dict[str, Any]:
        """Convert the full ontology into a JSON-serializable dict.

        Notes:
        - Class references (generalizations/specializations) are stored as class IDs (URIs as strings).
        - Attribute owningClass is stored as a class ID.
        - Relationship sourceClass/targetClass are stored as class IDs.
        - Within classes, attributes/outgoingRelationships/incomingRelationships are stored as IDs.
        """
        if ontology is None:
            return None

        classes_dict: Dict[str, Any] = {}
        for uri, cls in ontology.classes.items():
            classes_dict[str(uri)] = self._ontology_class_to_dict(cls)

        attributes_dict: Dict[str, Any] = {}
        for uri, attr in ontology.attributes.items():
            attributes_dict[str(uri)] = self._ontology_attribute_to_dict(attr)

        relationships_dict: Dict[str, Any] = {}
        for uri, rel in ontology.relationships.items():
            relationships_dict[str(uri)] = self._ontology_relationship_to_dict(rel)

        return {
            "uri": str(ontology.uri) if ontology.uri is not None else None,
            "label": ontology.label,
            "description": ontology.description,
            "classes": classes_dict,
            "attributes": attributes_dict,
            "relationships": relationships_dict,
        }

    def _ontology_class_to_dict(self, cls: OntologyClass) -> Dict[str, Any]:
        # Handle kind which can be either a Kind enum or already a string
        if cls.kind is not None:
            if hasattr(cls.kind, 'value'):
                kind_value = cls.kind.value
            elif isinstance(cls.kind, str):
                kind_value = cls.kind
            else:
                # Fallback: convert to string
                kind_value = str(cls.kind)
        else:
            kind_value = None
            
        return {
            "uri": str(cls.uri) if cls.uri is not None else None,
            "label": cls.label,
            "definition": cls.definition,
            "description": cls.description,
            "kind": kind_value,
            "generalizations": [str(c.uri) for c in (cls.generalizations or []) if getattr(c, "uri", None) is not None],
            "specializations": [str(c.uri) for c in (cls.specializations or []) if getattr(c, "uri", None) is not None],
            # Reference attributes/relationships by their IDs to avoid duplication and cycles
            "attributes": [str(a.uri) for a in (cls.attributes or []) if getattr(a, "uri", None) is not None],
            "outgoingRelationships": [str(r.uri) for r in (cls.outgoingRelationships or []) if getattr(r, "uri", None) is not None],
            "incomingRelationships": [str(r.uri) for r in (cls.incomingRelationships or []) if getattr(r, "uri", None) is not None],
            "definition_references": list(cls.definition_references) if hasattr(cls, 'definition_references') else [],
            "specification_references": list(cls.specification_references) if hasattr(cls, 'specification_references') else [],
            "references": list(cls.references) if hasattr(cls, 'references') else [],
        }

    def _ontology_attribute_to_dict(self, attr: OntologyAttribute) -> Dict[str, Any]:
        return {
            "uri": str(attr.uri) if attr.uri is not None else None,
            "label": attr.label,
            "definition": attr.definition,
            "description": attr.description,
            "owningClass": str(attr.owningClass.uri) if getattr(attr, "owningClass", None) is not None and getattr(attr.owningClass, "uri", None) is not None else None,
            "definition_references": attr.definition_references if hasattr(attr, 'definition_references') else [],
            "specification_references": attr.specification_references if hasattr(attr, 'specification_references') else [],
            "references": attr.references if hasattr(attr, 'references') else [],
        }

    def _ontology_relationship_to_dict(self, rel: OntologyRelationship) -> Dict[str, Any]:
        return {
            "uri": str(rel.uri) if rel.uri is not None else None,
            "label": rel.label,
            "definition": rel.definition,
            "description": rel.description,
            "sourceClass": str(rel.sourceClass.uri) if getattr(rel, "sourceClass", None) is not None and getattr(rel.sourceClass, "uri", None) is not None else None,
            "targetClass": str(rel.targetClass.uri) if getattr(rel, "targetClass", None) is not None and getattr(rel.targetClass, "uri", None) is not None else None,
            "definition_references": rel.definition_references if hasattr(rel, 'definition_references') else [],
            "specification_references": rel.specification_references if hasattr(rel, 'specification_references') else [],
            "references": rel.references if hasattr(rel, 'references') else [],
        }

    def _ontology_from_dict(self, data: Dict[str, Any]) -> Ontology:
        """Reconstruct the Ontology object from its dict representation.

        This mirrors _ontology_to_dict:
        - Build all classes first (without links) so references can resolve.
        - Build attributes and relationships and attach them to classes.
        - Link class generalizations/specializations by class IDs.
        """
        if data is None:
            return None

        # First pass: instantiate classes
        classes_by_id: Dict[str, OntologyClass] = {}
        classes_input: Dict[str, Any] = data.get("classes", {}) or {}
        for cls_id, cls_data in classes_input.items():
            kind_value = cls_data.get("kind")
            kind = Kind(kind_value) if kind_value is not None else Kind.SUBJECT  # Default to SUBJECT for backwards compatibility
            cls_obj = OntologyClass(
                uri=URIRef(cls_id) if cls_id is not None else None,
                label=cls_data.get("label", ""),
                definition=cls_data.get("definition"),
                description=cls_data.get("description"),
                kind=kind,
                definition_references=cls_data.get("definition_references", []),
                specification_references=cls_data.get("specification_references", []),
                references=cls_data.get("references", [])
            )
            classes_by_id[cls_id] = cls_obj

        # Helper to get or create a placeholder class if a reference points to a missing class ID
        def ensure_class(class_id: str) -> OntologyClass:
            if class_id in classes_by_id:
                return classes_by_id[class_id]
            # Create minimal placeholder
            placeholder = OntologyClass(
                uri=URIRef(class_id) if class_id is not None else None,
                label="",
                definition=None,
                description=None,
                kind=Kind.SUBJECT,  # Default kind for placeholder classes
                definition_references=[],
                specification_references=[],
                references=[]
            )
            classes_by_id[class_id] = placeholder
            return placeholder

        # Second pass: instantiate attributes and attach to owning classes
        attributes_by_id: Dict[str, OntologyAttribute] = {}
        attrs_input: Dict[str, Any] = data.get("attributes", {}) or {}
        for attr_id, attr_data in attrs_input.items():
            owning_id = attr_data.get("owningClass")
            owning_class = ensure_class(owning_id) if owning_id else None
            attr_obj = OntologyAttribute(
                uri=URIRef(attr_id) if attr_id is not None else None,
                label=attr_data.get("label", ""),
                definition=attr_data.get("definition"),
                description=attr_data.get("description"),
                owningClass=owning_class,
                definition_references=attr_data.get("definition_references", []),
                specification_references=attr_data.get("specification_references", []),
                references=attr_data.get("references", [])
            )
            attributes_by_id[attr_id] = attr_obj
            if owning_class is not None:
                owning_class.attributes.append(attr_obj)

        # Third pass: instantiate relationships and attach to source/target classes
        relationships_by_id: Dict[str, OntologyRelationship] = {}
        rels_input: Dict[str, Any] = data.get("relationships", {}) or {}
        for rel_id, rel_data in rels_input.items():
            src_id = rel_data.get("sourceClass")
            tgt_id = rel_data.get("targetClass")
            source_class = ensure_class(src_id) if src_id else None
            target_class = ensure_class(tgt_id) if tgt_id else None
            rel_obj = OntologyRelationship(
                uri=URIRef(rel_id) if rel_id is not None else None,
                label=rel_data.get("label", ""),
                definition=rel_data.get("definition"),
                description=rel_data.get("description"),
                sourceClass=source_class,
                targetClass=target_class,
                definition_references=rel_data.get("definition_references", []),
                specification_references=rel_data.get("specification_references", []),
                references=rel_data.get("references", [])
            )
            relationships_by_id[rel_id] = rel_obj
            if source_class is not None:
                source_class.outgoingRelationships.append(rel_obj)
            if target_class is not None:
                target_class.incomingRelationships.append(rel_obj)

        # Fourth pass: link class generalizations and specializations
        for cls_id, cls_data in classes_input.items():
            cls_obj = classes_by_id[cls_id]
            for gen_id in cls_data.get("generalizations", []) or []:
                gen_cls = ensure_class(gen_id)
                if gen_cls not in cls_obj.generalizations:
                    cls_obj.generalizations.append(gen_cls)
                if cls_obj not in gen_cls.specializations:
                    gen_cls.specializations.append(cls_obj)
            for spec_id in cls_data.get("specializations", []) or []:
                spec_cls = ensure_class(spec_id)
                if spec_cls not in cls_obj.specializations:
                    cls_obj.specializations.append(spec_cls)
                if cls_obj not in spec_cls.generalizations:
                    spec_cls.generalizations.append(cls_obj)

        # Build the Ontology object
        ontology = Ontology(
            uri=URIRef(data.get("uri")) if data.get("uri") is not None else None,
            label=data.get("label", ""),
            description=data.get("description"),
            classes={URIRef(cid): cobj for cid, cobj in classes_by_id.items()},
            attributes={URIRef(aid): aobj for aid, aobj in attributes_by_id.items()},
            relationships={URIRef(rid): robj for rid, robj in relationships_by_id.items()},
        )
        return ontology

