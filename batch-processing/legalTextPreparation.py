import os
import re
import rdflib


def prepareLegalText(legal_act_number: str, legal_act_year: str, legal_act_valid_from_date: str, legal_act_url: str):

    # %%
    g = rdflib.Graph()

    query_string = f"""
        PREFIX esel: <https://slovník.gov.cz/datový/sbírka/pojem/>

        SELECT ?fragment ?citace ?hierarchie ?poradi ?obsah
        WHERE {{
        SERVICE <https://opendata.eselpoint.cz/sparql> {{
            <{legal_act_url}> esel:má-fragment-znění ?fragment .

            ?fragment esel:citace-označení-fragmentu-znění-právního-aktu ?citace ;
            esel:hierarchie-fragmentu-znění-právního-aktu ?hierarchie ;
            esel:pořadí-fragmentu-znění-právního-aktu ?poradi ;
            esel:obsahuje-fragment/esel:text-fragmentu ?obsah .
        }}
        }}
        ORDER BY ?poradi
        """
    result = g.query(query_string)

    # %%

    act_paragraphs = {}

    for row in result:
        citace = str(row.citace)
        match = re.match(r"§ (\d+[a-z]*)( .*|$)", citace)
        if match:
            paragraph_number = match.group(1)
            if paragraph_number in act_paragraphs:
                act_paragraphs[paragraph_number] += "\n" + str(row.obsah)
            else:
                act_paragraphs[paragraph_number] = str(row.obsah)

    # %%

    legal_texts_path = f"{os.getcwd()}\\texts\\{legal_act_year}-{legal_act_number}\\"
    legal_texts_path_date = f"{os.getcwd()}\\texts\\{legal_act_year}-{legal_act_number}\\{legal_act_valid_from_date}\\"

    if not os.path.exists(legal_texts_path):
        os.mkdir(legal_texts_path)
    if not os.path.exists(legal_texts_path_date):
        os.mkdir(legal_texts_path_date)

    # %%
    for paragraph in act_paragraphs:
        paragraph_text_path = f"{legal_texts_path_date}p{paragraph}.txt"
        with open(paragraph_text_path, 'w', encoding="utf-8") as f:
            f.write(act_paragraphs[paragraph])
    print(f"Extracted {len(act_paragraphs)} paragraphs.")
