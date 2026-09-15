# %%
import json
from langchain_core.prompts import ChatPromptTemplate
from typing import (
    List, Optional
)
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import openai
import os
from llm_provider import get_llm_instance, resolve_llm_config, get_model_output_dir_name


def merge_classes(conceptual_model, result):
    """Merges new classes from 'result' into 'conceptual_model',
    replacing existing classes with the same name and appending new ones.

    Args:
    conceptual_model (dict): The dictionary containing the existing conceptual model.
    result (dict): The dictionary containing new classes from the language model output.
    """
    for new_class in result["classes"]:
        found = False
        for i, existing_class in enumerate(conceptual_model["classes"]):
            if existing_class["name"] == new_class["name"]:
                # Replace existing class
                conceptual_model["classes"][i] = new_class
                found = True
                break
        if not found:
            # Append new class
            conceptual_model["classes"].append(new_class)


def append_classes(conceptual_model, result):
    for new_class in result["classes"]:
        conceptual_model["classes"].append(new_class)


def classExtraction(legal_act_number: str, legal_act_year: str, legal_act_valid_from_date: str, legal_act_url: str):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    os.environ['LANGCHAIN_TRACING_V2'] = 'true'
    os.environ['LANGCHAIN_PROJECT'] = 'my-experiments'
    legal_texts_path = f"{os.getcwd()}\\texts\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\"

    class ConceptualClass(BaseModel):
        name: str = Field(
            description="the name of the class in the singular form")
        definition: Optional[str] = Field(
            description="the legally accurate definition of the class")
        explanation: Optional[str] = Field(
            description="the explanation of the class for lay users that is not in contradiction with the definition")
        introduction: List[str] = Field(
            description="the way the class is introduced in the text as a list consisting of 'defining', 'clarifying', 'property detailing', or 'referring'")

    class Model(BaseModel):
        classes: List[ConceptualClass] = Field(
            description="list of identified classes")

    output_parser = JsonOutputParser(pydantic_object=Model)

    # %%

    system_prompt = f"""
    You are an expert on conceptual modeling and ontology engineering for eGovernment.
    You work with legal texts, such as parts of legal acts, in the Czech language.
    You specialize in creating domain ontologies based on a legal text given by the user.

    Your task is to analyse the legal text and identify classes that are specified or referred to in the text.
    As a candidate for a class, consider each term or phrase (typically noun) in the text that refers to a collection of individuals or things, concrete or abstract, that share common characteristics or properties within the domain.

    You must determine how an identified class is introduced in the text.
    You distinguish the following four ways of introducing the class in the text, more are possible.
    defining: The text defines the class, typically in the form similar to "Pro účely tohoto zákona se pod pojmem ... rozumí ..."
    clarifying: The text describes the class but in a less explicit style.
    property detailing: The text mentions the class without defining or describing it, but describing its properties.
    referring: The text only references the class by the name but does not describe it or its properties in detail.

    For an identified class you must output the class name.
    If the way of introducing the class is defining or clarifying, then you must also determine the class definition and explanation.
    The name, definition and explanation must be in the Czech language strictly.
    The name is the unambiguous short label of the class. It is spelled out without abbreviations. It must be strictly a noun or a noun phrase in the singular form.
    The definition is a legally accurate text that is directly based on the legal text. It sets out the precise meaning of the class.
    The explanation is a simplified interpretation of the class definition for lay users enriched with additional notes specifying various contexts in which the class can be used. It should be based on the legal text but does not have to come up straightforwardly from it.
    Definition and explanation must not be in a contradiction.


    Example 1
    Legal text: "§ 5 Zřízení veřejné vysoké školy (1) Veřejná vysoká škola se zřizuje a zrušuje zákonem. Zákon též stanoví její název a sídlo."
    Identified classes: [{{{{
        "name": "Veřejná vysoká škola",
        "introduction": ["clarifying", "property detailing"]
    }}}}]

    Example 2
    Legal text: "§ 61
    (1) Uchazeč se stává studentem dnem zápisu do studia; osoba, které bylo studium přerušeno, se stává studentem dnem opětovného zápisu do studia.
    (2) Osoba přestává být studentem dnem ukončení studia podle § 55 odst. 1 a § 56 odst. 1 a 2 nebo přerušení studia podle § 54."
    Identified classes: [{{{{
        "name": "Student",
        "definition": "Student je osoba, která byla jako uchazeč zapsána nebo opětovně zapsána do studia",
        "explanation": "Osoba se stane studentem dnem zápisu do studia jako uchazeč nebo dnem opětovného zápisu jako osoba s přerušeným studiem.",
        "introduction": ["defining"]
    }}}},{{{{
        "name": "Uchazeč",
        "introduction": ["referring"]
    }}}},{{{{
        "name": "Osoba s přerušeným studiem",
        "definition": "Osoba s přerušeným studiem je osoba, které bylo přerušeno studium.",
        "explanation": "Osobě může být přerušeno studium podle § 54.",
        "introduction": ["clarifying", "property detailing"]
    }}}},{{{{
        "name": "Zápis do studia",
        "introduction": ["referring"]
    }}}},{{{{
        "name": "Přerušení studia",
        "definition": "Akt, kterým je osobě přerušeno studium",
        "explanation": "Přerušení studia musí proběhnout podle § 54.",
        "introduction": ["clarifying"]
    }}}},{{{{
        "name": "Ukončení studia",
        "definition": "Akt, kterým osoba přestává být studentem",
        "explanation": "Přerušení studia musí proběhnout podle § 55 odst. 1 a § 56 odst. 1 a 2.",
        "introduction": ["clarifying"]
    }}}}]

    {output_parser.get_format_instructions().replace("{", "{{").replace("}", "}}")}
    """

    '''
    Example 4
    Legal text: "§ 54 Přerušení studia (1) Studium ve studijním programu může být za podmínek stanovených studijním a zkušebním řádem i opakovaně přerušeno. Studijní a zkušební řád stanoví nejdelší celkovou dobu přerušení studia. (2) Student má právo na přerušení studia vždy v souvislosti s těhotenstvím, porodem či rodičovstvím, a to po celou uznanou dobu rodičovství. Právo na přerušení studia je studentovi po tuto dobu přiznáno i v souvislosti s převzetím dítěte do péče nahrazující péči rodičů na základě rozhodnutí příslušného orgánu podle občanského zákoníku nebo právních předpisů upravujících státní sociální podporu."
    Known classes: [{{{{
        "name": "Student",
        "kind": "subject of law",
        "definition": "Student je osoba, která byla jako uchazeč zapsána nebo opětovně zapsána do studia",
        "explanation": "Osoba se stane studentem dnem zápisu do studia jako uchazeč nebo dnem opětovného zápisu jako osoba s přerušeným studiem."
    }}}},{{{{
        "name": "Uchazeč",
        "kind": "subject of law",
        "definition": "Uchazeč je osoba, která se může stát studentem dnem zápisu do studia.",
        "explanation": "Uchazeč ještě není studentem. Nejprve se musí zapsat do studia."
    }}}},{{{{
        "name": "Osoba s přerušeným studiem",
        "kind": "subject of law",
        "definition": "Osoba s přerušeným studiem je osoba, které bylo přerušeno studium.",
        "explanation": "Osobě může být přerušeno studium podle § 54."
    }}}},{{{{
        "name": "Zápis do studia",
        "kind": "object of law",
        "definition": "Akt, kterým se osoba stává studentem",
        "explanation": "Zapsáním do studia se z uchazeče stane student."
    }}}},{{{{
        "name": "Přerušení studia",
        "kind": "object of law",
        "definition": "Akt, kterým je osobě přerušeno studium",
        "explanation": "Přerušení studia musí proběhnout podle § 54."
    }}}},{{{{
        "name": "Ukončení studia",
        "kind": "object of law",
        "definition": "Akt, kterým osoba přestává být studentem",
        "explanation": "Přerušení studia musí proběhnout podle § 55 odst. 1 a § 56 odst. 1 a 2."
    }}}}]
    Identified classes: [{{{{
        "name": "Student",
        "kind": "subject of law",
        "definition": "Student je osoba, která byla jako uchazeč zapsána nebo opětovně zapsána do studia",
        "explanation": "Osoba se stane studentem dnem zápisu do studia jako uchazeč nebo dnem opětovného zápisu jako osoba s přerušeným studiem."
    }}}},{{{{
        "name": "Uchazeč",
        "kind": "subject of law",
        "definition": "Uchazeč je osoba, která se může stát studentem dnem zápisu do studia.",
        "explanation": "Uchazeč ještě není studentem. Nejprve se musí zapsat do studia."
    }}}},{{{{
        "name": "Přerušení studia",
        "kind": "object of law",
        "definition": "Akt, kterým je osobě přerušeno studium za podmínek stanoveným studijním a zkušebním řádem.",
        "explanation": "Přerušení studia musí vždy proběhnout za podmínek stanoveným studijním a zkušebním řádem a nesmí překročit stanovenou nejdelší celkovou dobu přerušení studia. Studium může být přerušeno opakovaně, ale součet trvání nesmí překročit stanovenou nejdelší dobu. Mezi legitimní důvody přerušení studia patří těhotenství, porod, rodičovství či péče o dítě nahrazjící rodičoství. Student má pak právo na přerušení studia po celou dobu trvání těchto skutečností."
    }}}}]

    Example 5
    Legal text: "§ 72 Habilitační řízení (1) V habilitačním řízení se ověřuje vědecká nebo umělecká kvalifikace uchazeče, a to zejména na základě habilitační práce a její obhajoby a dalších vědeckých, odborných nebo uměleckých prací, a jeho pedagogická způsobilost na základě hodnocení habilitační přednášky a předcházející pedagogické praxe."
    Known classes: []
    Identified classes:[{{{{
        "name": "Habilitační řízení",
        "kind": "object of law",
        "definition": "Řízení, ve kterém se ověřuje vědecká nebo umělecká kvalifikace uchazeče a jeho pedagogická způsobilost.",
        "explanation": "Ověření kvalifikace probíhá zejména na základě habilitační práce a její obhajoby a dalších vědeckých, odborných nebo uměleckých prací uchazeče. Ověření pedagogické způsobilosti probíhá zejména na základě hodnocení habilitační přednášky a předcházející pedagogické praxe."
    }}}},{{{{
        "name": "Habilitační práce",
        "kind": "object of law",
        "definition": "Práce, která slouží k ověření kvalifikace uchazeče habilitačního řízení.",
        "explanation": "Habilitační práce popisuje vědecké, odborné nebo umělecké práce uchazeče."
    }}}}]
    '''

    # A candidate concept that cannot have instances, or it does not make sense to consider its instances, is not a class.
    # A concrete person (such as a concrete government agency) or concrete thing (such as a concrete information system) is not a class.
    # A list or registry of persons or things is not a class.
    # A generic legal concept such as legal act (in Czech: Zákon) or legal right (in Czech: Právo) is not a class.

    user_prompt = """
    Legal text: {legal_text}\n\n
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", user_prompt),

    ])
    
    # Load LLM using abstraction layer
    llm_config = resolve_llm_config()
    llm = get_llm_instance()

    chain = prompt | llm | output_parser

    # %%

    conceptual_model = {"classes": []}
    conceptual_model_sources = {}

    input_filenames = os.listdir(legal_texts_path)
    # input_filenames = ["p2.txt","p3.txt"]

    for filename in input_filenames:
        filepath = os.path.join(legal_texts_path, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            legal_text_from_file = file.read()
        # result = chain.invoke({"legal_text": legal_text_from_file, "known_classes": conceptual_model})
        result = chain.invoke({"legal_text": legal_text_from_file})

        print(f"Processed file: {filename}")
        conceptual_model_extension = result["classes"]
        new_classes_list = []
        for identified_class in conceptual_model_extension:
            identified_class["source"] = filename
            new_classes_list.append(identified_class["name"])
        conceptual_model_sources[filename] = new_classes_list
        print(f"New classes in {filename}: {new_classes_list}")

        # merge_classes(conceptual_model, result)
        append_classes(conceptual_model, result)

        # time.sleep(30)

    # %%
    reversed_conceptual_model_sources = {}
    for filename, classes in conceptual_model_sources.items():
        for c in classes:
            reversed_conceptual_model_sources.setdefault(
                c, []).append(filename)

    print(reversed_conceptual_model_sources)

    # %%
    # Use model name from config for output directory
    model_name_for_path = get_model_output_dir_name(llm_config)
    outputs_path = f"{os.getcwd()}/outputs/{legal_act_year}-{legal_act_number}/{legal_act_valid_from_date}/{model_name_for_path}/"
    os.makedirs(outputs_path, exist_ok=True)

    class_definitions_file = f"{outputs_path}/class_definitions.json"
    with open(class_definitions_file, 'w', encoding="utf-8") as f:
        json.dump(conceptual_model, f, ensure_ascii=False, indent=2)

    class_sources_file = f"{outputs_path}/class_sources.json"
    with open(class_sources_file, 'w', encoding="utf-8") as f:
        json.dump(reversed_conceptual_model_sources,
                  f, ensure_ascii=False, indent=2)

    # %%
    for c in conceptual_model["classes"]:
        c_name = c["name"]
        print(f"Class: {c_name}")
        c_definition = c.get("definition", "")
        print(f" - definice: {c_definition}")
        c_explanation = c.get("explanation", "")
        print(f" - vysvětlení: {c_explanation}")
        # c_sources = reversed_conceptual_model_sources.get(c_name, [])
        c_source = c.get("source")
        print(f" - zdroj: {c_source}")
