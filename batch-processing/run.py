import sys
import re
from attributeExtraction import attributeExtraction
from classCategorization import classCategorization
from classExtraction import classExtraction
from classMerging import classMerging
from legalTextPreparation import prepareLegalText
from owlExport import modelToOntology
from relationshipExtraction import relationshipExtraction


def main():
    input = sys.argv[1]
    if not re.search("[0-9]+\/[0-9]+\/[0-9]{4}-[0-9]{2}-[0-9]{2}", input):
        raise Exception(
            "Malformed law identification. \nExample input: 449/2001/2024-01-01")
    law = input.split("/")
    legal_act_number = law[0]
    legal_act_year = law[1]
    legal_act_valid_from_date = law[2]
    legal_act_url = f"https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/{legal_act_year}/{legal_act_number}/{legal_act_valid_from_date}"
    prepareLegalText(legal_act_number, legal_act_year,
                     legal_act_valid_from_date, legal_act_url)
    classExtraction(legal_act_number, legal_act_year,
                    legal_act_valid_from_date, legal_act_url)
    classMerging(legal_act_number, legal_act_year,
                 legal_act_valid_from_date, legal_act_url)
    classCategorization(legal_act_number, legal_act_year,
                        legal_act_valid_from_date, legal_act_url)
    attributeExtraction(legal_act_number, legal_act_year,
                        legal_act_valid_from_date, legal_act_url)
    relationshipExtraction(legal_act_number, legal_act_year,
                           legal_act_valid_from_date, legal_act_url)
    modelToOntology(legal_act_year, legal_act_number,
                    legal_act_valid_from_date)


if __name__ == "__main__":
    main()
