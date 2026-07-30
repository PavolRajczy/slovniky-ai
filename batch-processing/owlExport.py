# %%
import os
import json

from llm_provider import resolve_llm_config, get_model_output_dir_name


def modelToOntology(legal_act_year: str, legal_act_number: str, legal_act_valid_from_date: str):
    """

    Args:
      legal_act_year:
      legal_act_number:
      legal_act_valid_from_date:
    """
    legal_texts_path = f"{os.getcwd()}\\texts\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\"
    llm_config = resolve_llm_config()
    model_dir = get_model_output_dir_name(llm_config)
    outputs_path = f"{os.getcwd()}\\outputs\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\{model_dir}\\"
    classes_definitions_file = f"{outputs_path}class_definitions_categorized.json"
    with open(classes_definitions_file, 'r', encoding="utf-8") as f:
        classes = json.load(f)

    classes_relationships_definitions_file = f"{outputs_path}/class_relationships_definitions.json"
    with open(classes_relationships_definitions_file, 'r', encoding="utf-8") as f:
        classes_relationships = json.load(f)

    classes_attributes_definitions_file = f"{outputs_path}/class_attributes_definitions.json"
    with open(classes_attributes_definitions_file, 'r', encoding="utf-8") as f:
        classes_attributes = json.load(f)

    with open(f"{outputs_path}/{legal_act_year}-{legal_act_number}-{legal_act_valid_from_date}-ontology.owl", 'w', newline='', encoding='utf-8') as f:

        f.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
        f.write("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n")
        f.write("@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n")
        f.write("@prefix dcterms: <http://purl.org/dc/terms/> .\n")
        f.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n")
        f.write(
            f"@prefix : <https://slovník.gov.cz/vocabulary/legal/{legal_act_year}/{legal_act_number}/{legal_act_valid_from_date}/> .\n\n")

        for model_class in classes["classes"]:
            model_class_name = model_class["name"]
            model_class_relative_iri = model_class["name"].replace(" ", "-")
            model_class_kind = model_class["kind"]
            model_class_definition = model_class.get("definition", "")
            model_class_explanation = model_class.get("explanation", "")

            f.write(f":{model_class_relative_iri} a owl:Class ;\n")
            if model_class_kind == "subject of law":
                f.write(
                    f"  a <https://slovník.gov.cz/veřejný-sektor/pojem/typ-subjektu-práva> ;\n")
            if model_class_kind == "object of law":
                f.write(
                    f"  a <https://slovník.gov.cz/veřejný-sektor/pojem/typ-objektu-práva> ;\n")
            if model_class_kind == "event":
                f.write(
                    f"  a <https://slovník.gov.cz/veřejný-sektor/pojem/typ-události> ;\n")
            f.write(f"  rdfs:label \"{model_class_name}\"@cs ;\n")
            f.write(f"  skos:prefLabel \"{model_class_name}\"@cs ;\n")
            f.write(f"  skos:definition \"{model_class_definition}\"@cs ;\n")
            f.write(
                f"  dcterms:description \"{model_class_explanation}\"@cs .\n\n")

        for model_class_name, relationships in classes_relationships.items():
            domain_class_relative_iri = model_class_name.replace(" ", "-")
            for relationship in relationships:
                relationship_name = relationship["name"]
                relationship_relative_iri = relationship_name.replace(" ", "-")
                relationship_definition = relationship.get("definition", "")
                relationship_explanation = relationship.get("explanation", "")
                target_model_class_name = relationship["target"]
                target_class_relative_iri = target_model_class_name.replace(
                    " ", "-")

                f.write(
                    f":{relationship_relative_iri} a owl:ObjectProperty ;\n")
                f.write(f"  rdfs:label \"{relationship_name}\"@cs ;\n")
                f.write(f"  skos:prefLabel \"{relationship_name}\"@cs ;\n")
                f.write(
                    f"  skos:definition \"{relationship_definition}\"@cs ;\n")
                f.write(
                    f"  dcterms:description \"{relationship_explanation}\"@cs ;\n")
                f.write(f"  rdfs:domain :{domain_class_relative_iri} ;\n")
                f.write(f"  rdfs:range :{target_class_relative_iri} .\n\n")

        for model_class_name, attributes in classes_attributes.items():
            class_relative_iri = model_class_name.replace(" ", "-")
            for attribute in attributes:
                attribute_name = attribute["name"]
                attribute_relative_iri = attribute_name.replace(" ", "-")
                attribute_definition = attribute.get("definition", "")
                attribute_explanation = attribute.get("explanation", "")
                attribute_type = attribute["primitive_type"]

                f.write(f":{attribute_relative_iri} a owl:DatatypeProperty ;\n")
                f.write(f"  rdfs:label \"{attribute_name}\"@cs ;\n")
                f.write(f"  skos:prefLabel \"{attribute_name}\"@cs ;\n")
                f.write(f"  skos:definition \"{attribute_definition}\"@cs ;\n")
                f.write(
                    f"  dcterms:description \"{attribute_explanation}\"@cs ;\n")
                f.write(f"  rdfs:domain :{class_relative_iri} ;\n")
                f.write(f"  rdfs:range xsd:{attribute_type} .\n\n")


# %%
modelToOntology("2001", "449", "2024-01-01")
# modelToOntology("2001", "56", "2024-01-01")
# modelToOntology("2011", "372", "2024-11-01")
# modelToOntology("2000", "365", "2024-01-20")

# modelToOntology("1998", "111", "2025-02-19-test")
