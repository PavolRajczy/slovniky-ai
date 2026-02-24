
# %%

import time
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import (
    List, Optional
)
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import json
import os
import openai


def relationshipExtraction(legal_act_number: str, legal_act_year: str, legal_act_valid_from_date: str, legal_act_url: str):
    openai.api_key = os.getenv("OPENAI_API_KEY")

    legal_texts_path = f"{os.getcwd()}\\texts\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\"
    outputs_path = f"{os.getcwd()}\\outputs\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\gpt-4o\\"

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

    class Relationship(BaseModel):
        name: str = Field(description="name of the relationship")
        definition: str = Field(
            description="legally accurate definition of the relationship")
        explanation: str = Field(
            description="explanation of the relationship for lay users that is not in contradiction with the definition")
        source: str = Field(
            description="name of the source class of the relationship")
        target: str = Field(
            description="name of the target class of the relationship")

    class ConceptRelationships(BaseModel):
        relationships: List[Relationship] = Field(
            description="list of identified relationships of the concept")

    output_parser_relationships = JsonOutputParser(
        pydantic_object=ConceptRelationships)

    # %%

    system_prompt_relationships = f"""
    You are an expert on conceptual modeling and ontology engineering for eGovernment.
    You work with legal texts, such as parts of legal acts, in the Czech language.
    You specialize in creating ontologies that describe information artifacts representing real-world entities from the domain of interest described in and specified by the legal texts.
    You work on an ontology consisting of classes and relationships between the classes.
    A class represents a named collection of individuals or things, concrete or abstract, that share common characteristics or properties within the domain.
    A relationship connects a source class with a target class and specifies that an instance of the source class is related to zero or more instances of the target class.

    The user gives you a legal text and the list of classes in the ontology.
    For each class, you get its name, definition and explanation for each class.
    The user also selects one of the classes by referring to its name.

    Your task is to analyze the given legal text and identify relationships between the class pointed by the user and another class from the given list of classes.
    You consider strictly only relationships that can exist between instances of the connected concepts.
    If a candidate relationship is just a generic and abstract intrinsic characteristic of the class, you do not consider it as a relationship.

    For each identified relationship, you must determine its name, definition, explanation, and its source and target class.
    The class pointed to by the user can be a source or a target of the relationship.
    The name, definition and explanation must be in the Czech language strictly.
    The relationship name is the unambiguous short label of the relationship. It should be a verb or verb phrase in the singular form that also contains the noun or noun phrase referring to the target class. It is spelled out without abbreviations. It must make sense to read it from the source class to the target class.
    The relationship definition is a legally accurate text that is directly based on the legal text. It sets out the precise meaning of the relationship.
    The relationship explanation is a simplified interpretation of the relationship definition for lay users enriched with additional notes spefifying various contexts in which the relationship can be used. It should be based on the legal text but does not have to come up straightforwardly from it. Examples - "Jedná se o popis skutečnosti, že daný člověk (fyzická osoba) ovládá pohyb vozidla na veřejné komunikaci. Je to důležitý vztah v situacích, kdy probíhá silniční kontrola nebo měření, např. rychlosti.", "Z definice vyplývá, že řidiči, kteří jsou evidovaní v registru řidičů, jsou držiteli řidičského průkazu.", "Vlastník ale nemusí nutně vozidlo řídit a ani jej nemusí provozovat. Může jej svěřit do provozování jinou osobou, může vozidlo zapůjčit nebo pronajmout."

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
    Identified relationships: {{{{
    "relationships": [{{{{
        "name": "navazuje na bakalářský studijní program",
        "definition": "Určuje bakalářský studijní program, na který magisterský studijní program navazuje.",
        "explanation": "Magisterský studijní program navazuje na bakalářský studijní program. Pokud ale zákon stanoví jinak nebo to charakter magisterského studijního programu nevyžaduje, nemusí na žádný bakalářský studijní program navazovat. Pokud ale magisterský studijní program nenavazuje na bakalářský studijní program, je jeho standardní doba delší - nejméně čtyři a nejvýše šest roků, oproti navazujícímu, kde je standardní doba studia nejméně jeden a nejvýše tři roky.",
        "source": "Magisterský studijní program",
        "target": "Bakalářský studijní program"
    }}}},{{{{
        "name": "je studiem v magisterském studijním programu",
        "definition": "Určuje magisterský studijní program, ve kterém studium probíhá.",
        "explanation": "Magisterské studium daného studenta vždy probíhá v rámci magisterského studijního programu, do kterého se student na začátku svého studia zapsal.",
        "source": "Studium v magisterském studijním programu",
        "target": "Magisterský studijní program"
    }}}}]

    Example 2
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
    Selected class: Studium v magisterském studijním programu
    Identified relationships: {{{{
    "relationships": [{{{{
        "name": "je studiem v magisterském studijním programu",
        "definition": "Určuje magisterský studijní program, ve kterém studium probíhá.",
        "explanation": "Magisterské studium daného studenta vždy probíhá v rámci magisterského studijního programu, do kterého se student na začátku svého studia zapsal.",
        "source": "Studium v magisterském studijním programu",
        "target": "Magisterský studijní program"
    }}}},{{{{
        "name": "je řádně ukončeno státní závěrečnou zkouškou",
        "definition": "Určuje státní závěrečnou zkoušku, kterou bylo studium daného studenta řádně ukončeno.",
        "explanation": "Magisterské studium daného studenta je ukončeno státní závěrečnou zkouškou, jejíž součástí je také obhajoba diplomové práce.",
        "source": "Studium v magisterském studijním programu",
        "target": "Státní závěrečná zkouška"
    }}}}]

    Example 3
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
    Identified relationships: {{{{
    "relationships": [{{{{
        "name": "navazuje na bakalářský studijní program",
        "definition": "Určuje bakalářský studijní program, na který magisterský studijní program navazuje.",
        "explanation": "Magisterský studijní program navazuje na bakalářský studijní program. Pokud ale zákon stanoví jinak nebo to charakter magisterského studijního programu nevyžaduje, nemusí na žádný bakalářský studijní program navazovat. Pokud ale magisterský studijní program nenavazuje na bakalářský studijní program, je jeho standardní doba delší - nejméně čtyři a nejvýše šest roků, oproti navazujícímu, kde je standardní doba studia nejméně jeden a nejvýše tři roky.",
        "source": "Magisterský studijní program",
        "target": "Bakalářský studijní program"
    }}}},{{{{
        "name": "je studiem v magisterském studijním programu",
        "definition": "Určuje magisterský studijní program, ve kterém studium probíhá.",
        "explanation": "Magisterské studium daného studenta vždy probíhá v rámci magisterského studijního programu, do kterého se student na začátku svého studia zapsal.",
        "source": "Studium v magisterském studijním programu",
        "target": "Magisterský studijní program"
    }}}},{{{{
        "name": "má dělovaný akademický titul",
        "definition": "Určuje akademický titul, který je udělován absolventům studia v magisterském studijním programu.",
        "explanation": "Absolventům studia v magisterském studijním programu mohou být udělovány různé tituly v závislosti na oblasti daného magisterského studijního programu.",
        "source": "Magisterský studijní program",
        "target": "Akademický titul"
    }}}}]

    {output_parser_relationships.get_format_instructions().replace("{", "{{").replace("}", "}}")}
    """

    user_prompt_relationships = """
    Legal text (in Czech): {legal_text}\n\n
    Known classes: {known_classes}\n
    Selected class: {class_name}
    """

    prompt_relationships = ChatPromptTemplate.from_messages([
        ("system", system_prompt_relationships),
        ("user", user_prompt_relationships),

    ])
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    chain_relationships = prompt_relationships | llm | output_parser_relationships

    # %%

    class_relationships = {}

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

        result = chain_relationships.invoke({"legal_text": legal_text, "known_classes": json.dumps(
            relevant_conceptual_model, ensure_ascii=False), "class_name": class_name})
        class_relationships[class_name] = result["relationships"]

        relationships_list = []
        for prop in result["relationships"]:
            relationships_list.append(prop["name"])
        print(f"Relationships of {class_name}: {relationships_list}")

        # time.sleep(30)

    # %%
    class_relationships_definitions_file = f"{outputs_path}/class_relationships_definitions.json"
    with open(class_relationships_definitions_file, 'w', encoding="utf-8") as f:
        json.dump(class_relationships, f, ensure_ascii=False, indent=2)

    # %%
    for c in conceptual_model["classes"]:
        class_name = c["name"]
        print(f"{class_name}")
        print(f" - vztahy: {sources_of_class}")
        if (class_name not in class_relationships):
            continue
        for class_relationship in class_relationships[class_name]:
            class_relationship_name = class_relationship["name"]
            print(f"    {class_relationship_name}")
            class_relationship_definition = class_relationship.get(
                "definition", "")
            print(f"     - definice: {class_relationship_definition}")
            class_relationship_explanation = class_relationship.get(
                "explanation", "")
            print(f"     - vysvětlení: {class_relationship_explanation}")
            class_relationship_source = class_relationship.get("source", "")
            print(f"     - zdroj: {class_relationship_source}")
            class_relationship_target = class_relationship.get("target", "")
            print(f"     - cíl: {class_relationship_target}")
