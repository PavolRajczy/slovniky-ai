# %%
# drive_keys_path = "drive/MyDrive/Colab_Notebooks/keys/"

import time
from langchain_core.prompts import ChatPromptTemplate
from typing import (
    List, Optional
)
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import json
import os
import openai
from collections import defaultdict
from llm_provider import get_llm_instance, resolve_llm_config, get_model_output_dir_name


class ConceptualClass(BaseModel):
    name: str = Field(description="the name of the class in the singular form")
    definition: Optional[str] = Field(
        description="the legally accurate definition of the class")
    explanation: Optional[str] = Field(
        description="the explanation of the class for lay users that is not in contradiction with the definition")
    # legal_kind: str = Field(description="the legal kind of the class with possible values: subject of law, object of law")
    # ontology_kind: str = Field(description="the ontology kind of the class with possible values: kind, category, role, event")


def append_class(conceptual_model, new_class):
    conceptual_model["classes"].append(new_class)


def classMerging(legal_act_number: str, legal_act_year: str, legal_act_valid_from_date: str, legal_act_url: str):
    # f = open(drive_keys_path+"openai.txt", "r")
    # OPENAI_API_KEY=f.readline().strip()
    # f.close()
    # os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
    openai.api_key = os.getenv("OPENAI_API_KEY")

    legal_texts_path = f"{os.getcwd()}\\texts\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\"
    llm_config = resolve_llm_config()
    model_dir = get_model_output_dir_name(llm_config)
    outputs_path = f"{os.getcwd()}/outputs/{legal_act_year}-{legal_act_number}/{legal_act_valid_from_date}/{model_dir}"

    # %%
    sources = {}

    for filename in os.listdir(legal_texts_path):
        filepath = os.path.join(legal_texts_path, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            sources[filename] = file.read()

    # %%

    class_definitions_file = f"{outputs_path}/class_definitions.json"
    with open(class_definitions_file, 'r', encoding="utf-8") as f:
        conceptual_model_input = json.load(f)

    class_sources_file = f"{outputs_path}/class_sources.json"
    with open(class_sources_file, 'r', encoding="utf-8") as f:
        class_sources = json.load(f)

    class_inputs = defaultdict(list)

    for c in conceptual_model_input["classes"]:
        if "defining" in c.get("introduction", "") or "clarifying" in c.get("introduction", ""):
            class_name = c["name"]
            if "defining" in c.get("introduction", ""):
                importance = "high"
            else:
                importance = "low"
            record = {
                "definition": c.get("definition", ""),
                "explanation": c.get("explanation", ""),
                "importance": importance
            }
            class_inputs[class_name].append(record)

    output_parser = JsonOutputParser(pydantic_object=ConceptualClass)
    system_prompt = f"""
    You are an expert on conceptual modeling and ontology engineering for eGovernment.
    You consider ontologies consisting of classes.
    A class represents a named collection of individuals or things, concrete or abstract, that share common characteristics or properties within the domain.
    It has a name, definition and explanation.
    The name is the unambiguous short label of the class. It is spelled out without abbreviations. It is a noun or a noun phrase in the singular form.
    The definition is a legally accurate text. It sets out the precise meaning of the class.
    The explanation is a simplified interpretation of the class definition for lay users enriched with additional notes specifying various contexts in which the class can be used.
    The name, definition and explanation are in the Czech language strictly.

    The user gives you a list of possible definitions and explanations of a class to be modeled in the conceptual model.
    For each possible definition and explanation, you also get their importance which is either 'high' or 'low'.

    Your task is to analyze the given definitions and explanations and merge them into a single definition and single explanation in Czech language.
    The definition and explanation must not be in contradiction.
    The definitions with high importance must be strictly reflected in the merged definition.
    The definitions with low importance do not need to be reflected in the merged definition but must be reflected in the merged explanation.

    {output_parser.get_format_instructions().replace("{", "{{").replace("}", "}}")}
    """

    user_prompt = """
    Class name: {class_name}\n\n
    Class definitions and explanations: {class_model}\n\n
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt),

    ])
    
    # Load LLM using abstraction layer
    llm = get_llm_instance()

    chain = prompt | llm | output_parser
    conceptual_model = {"classes": []}

    for class_name, class_model in class_inputs.items():

        result = chain.invoke(
            {"class_name": class_name, "class_model": class_model})
        print(f"Processed class: {class_name}")
        print(result)

        new_class = {
            "name": result["name"],
            "definition": result.get("definition", ""),
            "explanation": result.get("explanation", "")
        }
        append_class(conceptual_model, new_class)

        for c in conceptual_model["classes"]:
            c["sources"] = []
            c["references"] = []
            for class_input in conceptual_model_input["classes"]:
                if c["name"] == class_input["name"]:
                    if "defining" in class_input.get("introduction", "") or "clarifying" in class_input.get("introduction", "") or "property detailing" in class_input.get("introduction", ""):
                        c["sources"].append(class_input["source"])
                    else:
                        c["references"].append(class_input["source"])
        class_definitions_file = f"{outputs_path}/class_definitions_merged.json"
        with open(class_definitions_file, 'w', encoding="utf-8") as f:
            json.dump(conceptual_model, f, ensure_ascii=False, indent=2)
