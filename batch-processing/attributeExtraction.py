# %%

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
from llm_provider import get_llm_instance, resolve_llm_config, get_model_output_dir_name


def attributeExtraction(legal_act_number: str, legal_act_year: str, legal_act_valid_from_date: str, legal_act_url: str):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    legal_texts_path = f"{os.getcwd()}\\texts\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\"
    llm_config = resolve_llm_config()
    model_dir = get_model_output_dir_name(llm_config)
    outputs_path = f"{os.getcwd()}\\outputs\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\{model_dir}\\"

    # %%
    sources = {}

    for filename in os.listdir(legal_texts_path):
        filepath = os.path.join(legal_texts_path, filename)
        with open(filepath, 'r', encoding='utf-8') as file:
            sources[filename] = file.read()

    # %%

    class_definitions_file = f"{outputs_path}/class_definitions_merged.json"
    with open(class_definitions_file, 'r', encoding="utf-8") as f:
        conceptual_model = json.load(f)

    # %%

    class Attribute(BaseModel):
        name: str = Field(description="name of the attribute")
        definition: str = Field(
            description="legally accurate definition of the attribute")
        explanation: str = Field(
            description="explanation of the attribute for lay users that is not in contradiction with the definition")
        primitive_type: str = Field(
            description="primitive type of possible attribute values")

    class ConceptAttributes(BaseModel):
        attributes: List[Attribute] = Field(
            description="list of identified attributes of the class")

    output_parser_attributes = JsonOutputParser(
        pydantic_object=ConceptAttributes)

    # %%

    system_prompt_attributes = f"""
    You are an expert on conceptual modeling and ontology engineering for eGovernment.
    You work with legal texts, such as parts of legal acts, in the Czech language.
    You specialize in creating ontologies that describe information artifacts representing real-world entities from the domain of interest described in and specified by the legal texts.
    You work on an ontology consisting of classes with attributes.
    A class represents a named collection of individuals or things, concrete or abstract, that share common characteristics or properties within the domain.
    An attribute of the class is a property that for a given instance of the class holds zero or more primitive data values of a primitive type string, date, integer, or boolean.
    You consider strictly only attributes that can hold data values for class instances.

    The user gives you a legal text and the list of classes in the ontology.
    For each class, you get its name, definition and explanation for each class.
    The user also selects one of the classes by referring to its name.

    Your task is to analyze the given legal text and identify properties of the class pointed by the user that can be modeled as attributes with primitive values.
    If a candidate property's values are instances of another known class in the ontology then you must ignore it.
    If a candidate property's values are not primitive data values but more complex values then you must ignore it.

    For each identified attribute, you must determine its name, definition, explanation, and primitive type.
    The name, definition and explanation must be in the Czech language strictly.
    The attribute name is the unambiguous short label of the attribute. It is a nominal phrase with nouns and adjectives in the singular form. It must be spelled out without abbreviations.
    The attribute definition is a legally accurate text that is directly based on the legal text. It sets out the precise meaning of the attribute.
    The attribute explanation is a simplified interpretation of the attribute definition for lay users enriched with additional notes spefifying various contexts in which the attribute can be used. It should be based on the legal text but does not have to come up straightforwardly from it.

    Example 1
    Legal text: "§ 46 Magisterský studijní program (1) Magisterský studijní program je zaměřen na získání teoretických i praktických poznatků založených na soudobém stavu vědeckého poznání, výzkumu a vývoje, na zvládnutí jejich aplikace a na rozvinutí schopností k tvůrčí činnosti; v oblasti umění je zaměřen na náročnou uměleckou přípravu a rozvíjení talentu. (2) Nestanoví-li tento zákon jinak, magisterský studijní program navazuje na bakalářský studijní program; standardní doba tohoto studia je nejméně jeden a nejvýše tři roky. V případech, kdy to vyžaduje charakter studijního programu, nenavazuje magisterský studijní program na bakalářský studijní program; v tomto případě je standardní doba studia nejméně čtyři a nejvýše šest roků. (3) Studium se řádně ukončuje státní závěrečnou zkouškou, jejíž součástí je obhajoba diplomové práce. V oblasti všeobecného lékařství a zubního lékařství a veterinárního lékařství a veterinární hygieny se studium řádně ukončuje státní rigorózní zkouškou. (4) Absolventům studia v magisterských studijních programech se udělují akademické tituly."
    Known classes: [{{{{
        "name": "Magisterský studijní program",
        "definition": "Magisterský studijní program je studijní program na vysoké škole zaměření na získání teoretických i praktických poznatků založených na soudobém stavu vědeckého poznání, výzkumu a vývoje nebo na náročnou uměleckou přípravu a rozvíjení talentu",
        "explanation": "Magisterský studijní program se také zaměřuje na zvládnutí aplikace získaných schopností v praxi. Typicky navazuje na jiný bakalářský studijní program."
    }}}},{{{{
        "name": "Bakalářský studijní program",
        "definition": "Bakalářský studijní program je zaměřen na přípravu k výkonu povolání a ke studiu v magisterském studijním programu.",
        "explanation": "Bakalářský studijní program je obvykle prakticky zaměřen."
    }}}},{{{{
        "name": "Státní závěrečná zkouška",
        "definition": "Státní závěřečná zkouška je zkouška, kterou se řádně ukončuje studium v magisterském studijním programu.",
        "explanation": "Součástí státní závěrečné zkoušky je také obhajoba diplomové práce."
    }}}},{{{{
        "name": "Studium v magisterském studijním programu",
        "definition": "Studium daného studenta v magisterském studijním programu, do kterého se student zapsal.",
        "explanation": "Magisterské studium každého studenta probíhá v rámci magisterského studijního programu, do kterého se zapsal na začátku svého studia. Standardní doba studia je nejméně jeden a nejvýše tři roky. V případech, kdy magisterský studijní program, ve kterém studium probíhá, nenavazuje na bakalářský studijní program je standardní doba studia nejméně čtyři a nejvýše šest roků."
    }}}},{{{{
        "name": "Diplomová práce",
        "definition": "Diplomová práce je závěrečná práce, jejíž obhajoba je součástí státní závěrečné zkoušky v magisterském studijním programu.",
        "explanation": "Diplomová práce musí být po obhajobě zveřejněna."
    }}}}]
    Selected class: Magisterský studijní program
    Identified attributes: {{{{
    "attributes": [{{{{
        "name": "oblast magisterského studijního programu",
        "definition": "Oblast magisterského studijního programu určuje zaměření studia v daném programu.",
        "explanation": "Oblastí může být oblast vědy, výzkumu a vývoje, např. všeobecné lékařství, zubního lékařství, veterinární lékařství nebo veterinární hygiena. Oblast také může být umělecká.",
        "primitive_type": "string"
    }}}},{{{{
        "name": "standardní doba studia v magisterském studijním programu",
        "definition": "Doba studia v magisterském studijním programu při jeho standardním průběhu.",
        "explanation": "Standardní doba studia je uváděna v letech. V případě magisterského studijního programu navazujícího na bakalářský studijní program je hodnotou nejméně 1 a nejvýše 3 roky. V případě, že magisterský studijní program nenavazuje na bakalářský studijní program je hodnotou nejméně 4 a nejvýše 6 roků.",
        "primitive_type": "integer"
    }}}},{{{{
        "name": "akademický titul udělovaný v magisterském studijním programu",
        "definition": "Akademický titul, který je udělován absolventům studia v magisterském studijním programu.",
        "explanation": "Určuje, jaký titul nebo tituly jsou udělovány absolventům studia v magisterském studijním programu.",
        "primitive_type": "string"
    }}}}]

    Example 2
    Legal text: "§ 46 Magisterský studijní program (1) Magisterský studijní program je zaměřen na získání teoretických i praktických poznatků založených na soudobém stavu vědeckého poznání, výzkumu a vývoje, na zvládnutí jejich aplikace a na rozvinutí schopností k tvůrčí činnosti; v oblasti umění je zaměřen na náročnou uměleckou přípravu a rozvíjení talentu. (2) Nestanoví-li tento zákon jinak, magisterský studijní program navazuje na bakalářský studijní program; standardní doba tohoto studia je nejméně jeden a nejvýše tři roky. V případech, kdy to vyžaduje charakter studijního programu, nenavazuje magisterský studijní program na bakalářský studijní program; v tomto případě je standardní doba studia nejméně čtyři a nejvýše šest roků. (3) Studium se řádně ukončuje státní závěrečnou zkouškou, jejíž součástí je obhajoba diplomové práce. V oblasti všeobecného lékařství a zubního lékařství a veterinárního lékařství a veterinární hygieny se studium řádně ukončuje státní rigorózní zkouškou. (4) Absolventům studia v magisterských studijních programech se udělují tyto akademické tituly: a) v oblasti ekonomie, technických věd a technologií, zemědělství, lesnictví a vojenství „inženýr“ (ve zkratce „Ing.“ uváděné před jménem), b) v oblasti architektury „inženýr architekt“ (ve zkratce „Ing. arch.“ uváděné před jménem), c) v oblasti všeobecného lékařství „doktor medicíny“ (ve zkratce „MUDr.“ uváděné před jménem), d) v ostatních oblastech „magistr“ (ve zkratce „Mgr.“ uváděné před jménem)."
    Known classes: [{{{{
        "name": "Magisterský studijní program",
        "definition": "Magisterský studijní program je studijní program na vysoké škole zaměření na získání teoretických i praktických poznatků založených na soudobém stavu vědeckého poznání, výzkumu a vývoje nebo na náročnou uměleckou přípravu a rozvíjení talentu",
        "explanation": "Magisterský studijní program se také zaměřuje na zvládnutí aplikace získaných schopností v praxi. Typicky navazuje na jiný bakalářský studijní program."
    }}}},{{{{
        "name": "Bakalářský studijní program",
        "definition": "Bakalářský studijní program je zaměřen na přípravu k výkonu povolání a ke studiu v magisterském studijním programu.",
        "explanation": "Bakalářský studijní program je obvykle prakticky zaměřen."
    }}}},{{{{
        "name": "Státní závěrečná zkouška",
        "definition": "Státní závěřečná zkouška je zkouška, kterou se řádně ukončuje studium v magisterském studijním programu.",
        "explanation": "Součástí státní závěrečné zkoušky je také obhajoba diplomové práce."
    }}}},{{{{
        "name": "Studium v magisterském studijním programu",
        "definition": "Studium daného studenta v magisterském studijním programu, do kterého se student zapsal.",
        "explanation": "Magisterské studium každého studenta probíhá v rámci magisterského studijního programu, do kterého se zapsal na začátku svého studia. Standardní doba studia je nejméně jeden a nejvýše tři roky. V případech, kdy magisterský studijní program, ve kterém studium probíhá, nenavazuje na bakalářský studijní program je standardní doba studia nejméně čtyři a nejvýše šest roků."
    }}}},{{{{
        "name": "Diplomová práce",
        "definition": "Diplomová práce je závěrečná práce, jejíž obhajoba je součástí státní závěrečné zkoušky v magisterském studijním programu.",
        "explanation": "Diplomová práce musí být po obhajobě zveřejněna."
    }}}},{{{{
        "name": "Akademický titul",
        "definition": "Akademický titul je udělován absolventům studia v magisterských studijních programech.",
        "explanation": "Odlišujeme různé akademické tituly podle oblastí magisterských studijních programů, např. v oblasti ekonomie, technických věd a technologií, zemědělství, lesnictví a vojenství „inženýr“ (ve zkratce „Ing.“ uváděné před jménem), v oblasti architektury „inženýr architekt“ (ve zkratce „Ing. arch.“ uváděné před jménem), v oblasti všeobecného lékařství „doktor medicíny“ (ve zkratce „MUDr.“ uváděné před jménem), v ostatních oblastech „magistr“ (ve zkratce „Mgr.“ uváděné před jménem)."
    }}}}]
    Selected class: Magisterský studijní program
    Identified attributes: {{{{
    "attributes": [{{{{
        "name": "oblast magisterského studijního programu",
        "definition": "Oblast magisterského studijního programu určuje zaměření studia v daném programu.",
        "explanation": "Oblastí může být oblast vědy, výzkumu a vývoje, např. všeobecné lékařství, zubního lékařství, veterinární lékařství nebo veterinární hygiena. Oblast také může být umělecká.",
        "primitive_type": "string"
    }}}},{{{{
        "name": "standardní doba studia v magisterském studijním programu",
        "definition": "Doba studia v magisterském studijním programu při jeho standardním průběhu.",
        "explanation": "Standardní doba studia je uváděna v letech. V případě magisterského studijního programu navazujícího na bakalářský studijní program je hodnotou nejméně 1 a nejvýše 3 roky. V případě, že magisterský studijní program nenavazuje na bakalářský studijní program je hodnotou nejméně 4 a nejvýše 6 roků.",
        "primitive_type": "integer"
    }}}}]

    {output_parser_attributes.get_format_instructions().replace("{", "{{").replace("}", "}}")}
    """

    user_prompt_attributes = """
    Legal text (in Czech): {legal_text}\n\n
    Known classes: {known_classes}\n
    Selected class: {class_name}
    """

    prompt_attributes = ChatPromptTemplate.from_messages([
        ("system", system_prompt_attributes),
        ("user", user_prompt_attributes),

    ])
    
    # Load LLM using abstraction layer
    llm = get_llm_instance()

    chain_attributes = prompt_attributes | llm | output_parser_attributes

    # %%

    class_attributes = {}

    for c in conceptual_model["classes"]:
        class_name = c["name"]

        sources_of_class = list(set(c.get("sources", [])))
        legal_text = ""
        for class_source in sources_of_class:
            legal_text += sources[class_source]

        relevant_conceptual_model = {
            "classes": []
        }
        for potentially_relevant_class in conceptual_model["classes"]:
            potentially_relevant_class_name = potentially_relevant_class["name"]
            potentially_relevant_class_sources = potentially_relevant_class.get(
                "sources", [])
            potentially_relevant_legal_texts = set(
                potentially_relevant_class_sources).intersection(set(sources_of_class))
            if (len(potentially_relevant_legal_texts) > 0):
                relevant_class = {}
                relevant_class["name"] = potentially_relevant_class_name
                relevant_class["definition"] = potentially_relevant_class.get(
                    "definition", [])
                relevant_class["explanation"] = potentially_relevant_class.get(
                    "explanation", [])
                relevant_conceptual_model["classes"].append(relevant_class)

        if (not relevant_conceptual_model["classes"]):
            continue

        result = chain_attributes.invoke({"legal_text": legal_text, "known_classes": json.dumps(
            relevant_conceptual_model), "class_name": class_name})
        class_attributes[class_name] = result["attributes"]

        attributes_list = []
        for prop in result["attributes"]:
            if ("name" in prop and prop["name"]):
                attributes_list.append(prop["name"])
        print(f"Attributes of {class_name}: {attributes_list}")

        # time.sleep(30)

    # %%
    class_attributes_definitions_file = f"{outputs_path}/class_attributes_definitions.json"
    with open(class_attributes_definitions_file, 'w', encoding="utf-8") as f:
        json.dump(class_attributes, f, ensure_ascii=False, indent=2)

    # %%
    for c in conceptual_model["classes"]:
        class_name = c["name"]
        print(f"{class_name}")
        print(f" - atributy:")
        if (class_name not in class_attributes):
            continue
        for class_attribute in class_attributes[class_name]:
            class_attribute_name = class_attribute["name"]
            print(f"    {class_attribute_name}")
            class_attribute_definition = class_attribute.get("definition", "")
            print(f"     - definice: {class_attribute_definition}")
            class_attribute_explanation = class_attribute.get(
                "explanation", "")
            print(f"     - vysvětlení: {class_attribute_explanation}")
            class_attribute_primitive_type = class_attribute.get(
                "primitive_type", "")
            if (class_attribute_primitive_type != ""):
                print(
                    f"     - primitivní typ: {class_attribute_primitive_type}")

    # %%
