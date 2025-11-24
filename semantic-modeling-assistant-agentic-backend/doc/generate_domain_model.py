#!/usr/bin/env python3
"""
Script to generate a PlantUML class diagram from domain.py files.
"""

import ast
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ClassInfo:
    name: str
    module: str
    base_classes: List[str]
    attributes: List[Tuple[str, str]]  # (name, type_annotation)

@dataclass
class Association:
    source_class: str
    target_class: str
    cardinality: str
    attribute_name: str

def extract_type_from_annotation(annotation_node) -> str:
    """Extract type string from AST annotation node."""
    if isinstance(annotation_node, ast.Name):
        return annotation_node.id
    elif isinstance(annotation_node, ast.Constant):
        return str(annotation_node.value)
    elif isinstance(annotation_node, ast.Subscript):
        # Handle generic types like List[T], Optional[T], Dict[K, V]
        value = extract_type_from_annotation(annotation_node.value)
        if isinstance(annotation_node.slice, ast.Name):
            slice_type = annotation_node.slice.id
        elif isinstance(annotation_node.slice, ast.Tuple):
            # Handle multiple type parameters like Dict[K, V]
            slice_types = [extract_type_from_annotation(elt) for elt in annotation_node.slice.elts]
            slice_type = ", ".join(slice_types)
        else:
            slice_type = extract_type_from_annotation(annotation_node.slice)
        return f"{value}[{slice_type}]"
    elif isinstance(annotation_node, ast.Attribute):
        # Handle qualified names like typing.Optional
        return f"{extract_type_from_annotation(annotation_node.value)}.{annotation_node.attr}"
    else:
        return "Unknown"

def is_primitive_type(type_str: str, enum_types: Set[str] = None) -> bool:
    """Check if a type is primitive (should be PlantUML attribute, not association)."""
    primitive_types = {
        'str', 'int', 'float', 'bool', 'date', 'datetime', 'URIRef'
    }
    if enum_types is None:
        enum_types = set()
    
    # Remove generic wrappers to check the inner type
    inner_type = type_str
    if '[' in type_str:
        if type_str.startswith('Dict['):
            # For Dict[K, V], check the value type V
            dict_content = type_str[5:-1]  # Remove 'Dict[' and ']'
            parts = dict_content.split(',')
            if len(parts) >= 2:
                inner_type = parts[1].strip()
            else:
                inner_type = dict_content.strip()
        else:
            # For other generic types like List[T], Optional[T], check T
            inner_type = type_str.split('[')[1].split(',')[0].split(']')[0].strip()
    
    return inner_type in primitive_types or inner_type in enum_types

def get_cardinality_and_type(type_str: str) -> Tuple[str, str]:
    """Extract cardinality and inner type from a type annotation."""
    if type_str.startswith('Optional['):
        inner_type = type_str[9:-1]  # Remove 'Optional[' and ']'
        return "0..1", inner_type
    elif type_str.startswith('List['):
        inner_type = type_str[5:-1]  # Remove 'List[' and ']'
        return "0..*", inner_type
    elif type_str.startswith('Dict['):
        # For Dict[K, V], we care about V for associations
        dict_content = type_str[5:-1]  # Remove 'Dict[' and ']'
        parts = dict_content.split(',')
        if len(parts) >= 2:
            inner_type = parts[1].strip()
            return "0..*", inner_type
        return "0..*", dict_content
    else:
        return "1..1", type_str

def parse_domain_file(file_path: Path) -> Tuple[List[ClassInfo], str, Set[str]]:
    """Parse a domain.py file and extract class information."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    classes = []
    enum_types = set()
    module_name = file_path.parent.name
    
    # First pass: collect enum types
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if this is an Enum class
            is_enum = any(isinstance(base, ast.Name) and base.id == 'Enum' for base in node.bases)
            if is_enum:
                enum_types.add(node.name)
    
    # Second pass: collect regular classes (skip enums)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Skip Enum classes - we don't want them as separate UML classes
            is_enum = any(isinstance(base, ast.Name) and base.id == 'Enum' for base in node.bases)
            if is_enum:
                continue
                
            class_name = node.name
            base_classes = []
            
            # Extract base classes
            for base in node.bases:
                if isinstance(base, ast.Name):
                    base_classes.append(base.id)
                elif isinstance(base, ast.Attribute):
                    # Handle qualified base classes
                    base_classes.append(f"{extract_type_from_annotation(base.value)}.{base.attr}")
            
            # Extract attributes from dataclass fields
            attributes = []
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    attr_name = item.target.id
                    if item.annotation:
                        type_str = extract_type_from_annotation(item.annotation)
                        attributes.append((attr_name, type_str))
            
            classes.append(ClassInfo(class_name, module_name, base_classes, attributes))
    
    return classes, module_name, enum_types

def generate_plantuml(classes_by_module: Dict[str, List[ClassInfo]], enum_types_by_module: Dict[str, Set[str]]) -> str:
    """Generate PlantUML class diagram from parsed classes."""
    lines = []
    lines.append("@startuml")
    lines.append("' Generated PlantUML domain model")
    lines.append("' Assumptions:")
    lines.append("'   - Primitive types (str, int, float, bool, date, datetime, URIRef) are shown as attributes")
    lines.append("'   - Enum types are shown as attributes with their Enum type name")
    lines.append("'   - Complex types are shown as associations")
    lines.append("'   - Optional[T] indicates 0..1 cardinality")
    lines.append("'   - List[T] indicates 0..* cardinality")
    lines.append("'   - Dict[K,V] indicates 0..* cardinality to V")
    lines.append("'   - Simple types indicate 1..1 cardinality")
    lines.append("")
    
    all_classes = {}
    all_enum_types = set()
    associations = []
    
    # Collect all enum types
    for module_enum_types in enum_types_by_module.values():
        all_enum_types.update(module_enum_types)
    
    # Collect all classes and process them
    for module_name, classes in classes_by_module.items():
        if classes:  # Only create package if there are classes
            lines.append(f"package {module_name} {{")
            
            for class_info in classes:
                all_classes[class_info.name] = class_info
                
                # Generate class definition
                lines.append(f"  class {class_info.name} {{")
                
                # Add primitive attributes (including enum types)
                for attr_name, type_str in class_info.attributes:
                    cardinality, inner_type = get_cardinality_and_type(type_str)
                    
                    if is_primitive_type(type_str, all_enum_types):
                        if cardinality == "0..1":
                            lines.append(f"    {attr_name}: {inner_type} [0..1]")
                        elif cardinality == "0..*":
                            lines.append(f"    {attr_name}: {inner_type} [0..*]")
                        else:
                            lines.append(f"    {attr_name}: {inner_type}")
                    else:
                        # This will be an association
                        associations.append(Association(
                            class_info.name, 
                            inner_type, 
                            cardinality, 
                            attr_name
                        ))
                
                lines.append("  }")
                lines.append("")
            
            lines.append("}")
            lines.append("")
    
    # Add inheritance relationships
    for class_info in all_classes.values():
        for base_class in class_info.base_classes:
            if base_class in all_classes:
                lines.append(f"{base_class} <|-- {class_info.name}")
    
    if any(class_info.base_classes for class_info in all_classes.values()):
        lines.append("")
    
    # Add associations
    for assoc in associations:
        if assoc.target_class in all_classes:
            if assoc.cardinality == "1..1":
                lines.append(f"{assoc.source_class} --> {assoc.target_class} : {assoc.attribute_name}")
            else:
                lines.append(f"{assoc.source_class} --> \"{assoc.cardinality}\" {assoc.target_class} : {assoc.attribute_name}")
    
    lines.append("")
    lines.append("@enduml")
    
    return "\n".join(lines)

def main():
    """Main function to generate the PlantUML diagram."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    
    # Find all domain.py files
    domain_files = list(src_dir.glob("**/domain.py"))
    print(f"Found {len(domain_files)} domain.py files:")
    for file in domain_files:
        print(f"  {file}")
    
    # Parse all domain files
    classes_by_module = {}
    enum_types_by_module = {}
    for domain_file in domain_files:
        try:
            classes, module_name, enum_types = parse_domain_file(domain_file)
            if classes:
                classes_by_module[module_name] = classes
                enum_types_by_module[module_name] = enum_types
                print(f"Parsed {len(classes)} classes and {len(enum_types)} enum types from {module_name}")
                if enum_types:
                    print(f"  Enum types: {', '.join(sorted(enum_types))}")
        except Exception as e:
            print(f"Error parsing {domain_file}: {e}")
    
    # Generate PlantUML
    plantuml_content = generate_plantuml(classes_by_module, enum_types_by_module)
    
    # Create doc directory if it doesn't exist
    doc_dir = project_root / "doc"
    doc_dir.mkdir(exist_ok=True)
    
    # Write PlantUML file
    output_file = doc_dir / "domain-model.puml"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(plantuml_content)
    
    print(f"Generated PlantUML diagram: {output_file}")
    print(f"Classes found: {sum(len(classes) for classes in classes_by_module.values())}")
    print(f"Modules: {list(classes_by_module.keys())}")

if __name__ == "__main__":
    main()
