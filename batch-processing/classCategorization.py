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
from llm_provider import LLMFactory, LLMConfig, LLMProvider, load_llm_config_from_file, load_llm_config_from_env


def classCategorization(legal_act_number: str, legal_act_year: str, legal_act_valid_from_date: str, legal_act_url: str):
    # f = open(drive_keys_path+"openai.txt", "r")
    # OPENAI_API_KEY=f.readline().strip()
    # f.close()
    # os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # f = open(drive_keys_path+"langchain.txt", "r")
    # LANGCHAIN_API_KEY=f.readline().strip()
    # f.close()
    # os.environ['LANGCHAIN_API_KEY'] = LANGCHAIN_API_KEY

    # os.environ['LANGCHAIN_TRACING_V2'] = 'false'
    # os.environ['LANGCHAIN_PROJECT'] = 'my-experiments'

    legal_texts_path = f"{os.getcwd()}\\texts\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\"
    outputs_path = f"{os.getcwd()}\\outputs\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\gpt-4o\\"

    # %%

    class_definitions_file = f"{outputs_path}/class_definitions_merged.json"
    with open(class_definitions_file, 'r', encoding="utf-8") as f:
        conceptual_model = json.load(f)

    # %%

    class ConceptualClass(BaseModel):
        name: str = Field(
            description="the name of the class in the singular form")
        kind: str = Field(
            description="the kind of the class, one of 'subject of law', 'object of law', 'event'")

    output_parser = JsonOutputParser(pydantic_object=ConceptualClass)

    # %%

    system_prompt_attributes = f"""
    You are an expert on conceptual modeling and ontology engineering for eGovernment.
    You consider ontologies consisting of classes.
    A class represents a named collection of individuals or things, concrete or abstract, that share common characteristics or properties within the domain.
    It has a name, definition and description.
    The name is the unambiguous short label of the class. It is spelled out without abbreviations. It is a noun or a noun phrase in the singular form.
    The definition is a legally accurate text. It sets out the precise meaning of the class.
    The explanation is a simplified interpretation of the class definition for lay users enriched with additional notes specifying various contexts in which the class can be used.
    The name, definition and explanation are in the Czech language strictly.

    The user gives you a class with its name, definition and explanation.
    Your task is to analyze the given class and determine the kind of the class.
    You must distinguish four kinds of classes: subject of law, object of law, event.
    A subject of law is a class whose instances are persons who participate in legal relations and who can be bearers of rights and obligations. These persons act on other persons or things - they do and exercise their will. Examples are classes of people, organizations, legal persons, companies, unions, authorities, public orgnaizations, courts, government agencies, or roles of those.
    An object of law is a class whose instances are things that do not have their own will, cannot exercise it, and that cannot act as agents. They cause subject of law instances' entry into a legal relationship. Examples are classes of assets and tangible objects, places, documents, licences, offences, decisions, prohibitions, permits, agreements, contracts, actions, processes, events.
    An event is a class whose instances represent events that happened or happen in time and after they happen, they do not change. They happen based on the will on some instances of one or more subjects of law. When they happen they may change or impact instances of other subjects or objects of law.

    Example 1
    Class: {{{{
        "name": "Magisterský studijní program",
        "definition": "Magisterský studijní program je studijní program na vysoké škole zaměření na získání teoretických i praktických poznatků založených na soudobém stavu vědeckého poznání, výzkumu a vývoje nebo na náročnou uměleckou přípravu a rozvíjení talentu",
        "explanation": "Magisterský studijní program se také zaměřuje na zvládnutí aplikace získaných schopností v praxi. Typicky navazuje na jiný bakalářský studijní program."
    }}}}
    Output:
    {{{{
        "name": "Magisterský studijní program",
        "kind": "object of law"
    }}}}

    Example 2
    Class: {{{{
        "name": "Student",
        "definition": "Student je fyzická osoba, která je zapsána do studijního programu univerzity.",
        "explanation": "Studentem se stává uchazeč o studium poté, co je přijat ke studiu na univerzitě a zapíše se do některého z nabízených studijních programů."
    }}}}
    Output:
    {{{{
        "name": "Student",
        "kind": "subject of law"
    }}}}

    Example 3
    Class: {{{{
        "name": "Zápis studenta do předmětu",
        "definition": "Zápis studenta je akt, kterým se student zapíše do předmětu.",
        "explanation": "Zapsáním do předmětu se student přihlašuje k navštěvování výuky v předmětu a ke složení zkoušky z předmětu."
    }}}}
    Output:
    {{{{
        "name": "Zápis studenta do předmětu",
        "kind": "event"
    }}}}

    {output_parser.get_format_instructions().replace("{", "{{").replace("}", "}}")}
    """

    user_prompt = """
    Class: {known_class}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_attributes),
        ("user", user_prompt),

    ])
    
    # Load LLM using abstraction layer
    from llm_provider import get_llm_instance
    llm = get_llm_instance()

    chain = prompt | llm | output_parser

    # %%

    conceptual_model_categorized = {
        "classes": []
    }

    for c in conceptual_model["classes"]:
        class_name = c["name"]

        known_class = {
            "name": class_name,
            "definition": c["definition"],
            "explanation": c["explanation"]
        }

        result = chain.invoke(
            {"known_class": json.dumps(known_class, ensure_ascii=False)})

        known_class_categorized = {
            "name": class_name,
            "definition": c["definition"],
            "explanation": c["explanation"],
            "kind": result["kind"]
        }

        conceptual_model_categorized["classes"].append(known_class_categorized)

        print(f"Kind of {class_name}: {known_class_categorized['kind']}")

    #   time.sleep(10)

    # %%
    class_definitions_categorized_file = f"{outputs_path}/class_definitions_categorized.json"
    with open(class_definitions_categorized_file, 'w', encoding="utf-8") as f:
        json.dump(conceptual_model_categorized,
                  f, ensure_ascii=False, indent=2)

    # %%
    for c in conceptual_model_categorized["classes"]:
        class_name = c["name"]
        print(f"{class_name}")
        class_kind = c["kind"]
        print(f" - druh: {class_kind}")
