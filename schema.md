1. Úvod
Cílem této otevřené formální normy (OFN) je specifikovat strukturu pro výměnu slovníků pro popis dat. Nejedná se tedy o metodiku pro tvorbu slovníků samotných. Cílovou skupinou jsou techničtí pracovníci implementující publikaci či konzumaci slovníků, nikoliv tvůrci slovníků. Specifikace popisuje 3 úrovně komplexity slovníku a několik rozšíření.

Předpokladem pro alespoň základní aplikaci této OFN je znalost minimálně Pravidel pro tvorbu IRI, syntaxe JSON [JSON] a validace pomocí JSON Schema [JSON-SCHEMA-2020-12]. Pro hlubší porozumění je však také potřebná znalost problematiky propojených dat, konkrétně specifikací RDF [RDF11-CONCEPTS], RDF Turtle 1.1 [TURTLE], JSON-LD 1.1 [JSON-LD11], SKOS [SKOS-REFERENCE], RDF Schema [RDF11-SCHEMA], OWL2 [OWL2-RDF-BASED-SEMANTICS] a znalost metodiky popisu dat [POPIS-DAT].

Obsah OFN postupně představíme na příkladech spolu s odkazy na schémata a kontexty. Detailní celková specifikace je pak v dalších částech dokumentu. Jednotlivé pohledy na Slovníky lze, případně i je třeba kombinovat. Pak musí být data validní vůči všem schématům z kombinovaných částí.

Slovník typu Tezaurus musí být validní vůči schématu pro Tezaurus, i vůči schématu pro Slovník. Slovník typu Konceptuální model musí být validní vůči schématůn pro Slovník, Tezaurus i Konceptuální model. U jednotlivých rozšíření, tj. § 1.4 Rozšířená specifikace typů, § 1.5 Anotace pro registr práv a povinností či § 1.6 Anotace pro § 23 vyhlášky 360/2023 Sb. je třeba rozhodnout, zda jimi rozšířit § 1.2 Tezaurus či § 1.3 Konceptuální model, a zajistit validitu vůči těmto schématům. Rozšíření lze i kombinovat mezi sebou, a opět je třeba zajistit validitu vůči všem příslušným schématům.

1.1 Slovník
Nejprve je třeba popsat samotný slovník. Je třeba pro něj zvolit vhodné a perzistentní IRI, nazvat ho a popsat ho.


Obrázek 1 Slovník
Příklad 1: Slovník v JSON-LD
JSON-LD, JSON-LD kontext, Validní vůči JSON Schéma

{
    "@context": "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld",
    "iri": "https://slovník.gov.cz/datový/turistické-cíle",
    "typ": ["Slovník"],
    "název": {
        "cs": "Slovník turistických cílů",
        "en": "Vocabulary of tourist points of interest"
    },
    "popis": {
        "cs": "Slovník turistických cílů slouží v rámci příkladu pro OFN Slovníky",
        "en": "Vocabulary of tourist points of interest serves as an example in the formal open standard for vocabularies"
    },
    "vytvořeno": {
        "typ": "Časový okamžik",
        "datum": "2024-01-01"
    },
    "aktualizováno": {
        "typ": "Časový okamžik",
        "datum_a_čas": "2024-01-15T04:53:21+02:00"
    }
}
Příklad 2: Slovník v RDF Turtle
RDF Turtle

@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix slovníky: <https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix čas: <https://slovník.gov.cz/generický/čas/pojem/> .

<https://slovník.gov.cz/datový/turistické-cíle> a slovníky:slovník;
  dcterms:description "Slovník turistických cílů slouží v rámci příkladu pro OFN Slovníky"@cs,
    "Vocabulary of tourist points of interest serves as an example in the formal open standard for vocabularies"@en;
  skos:prefLabel "Slovník turistických cílů"@cs,
    "Vocabulary of tourist points of interest"@en;
  slovníky:okamžik-poslední-změny [
    a čas:časový-okamžik;
    čas:datum-a-čas "2024-01-15T04:53:21+02:00"^^xsd:dateTimeStamp
  ];
  slovníky:okamžik-vytvoření [
    a čas:časový-okamžik;
    čas:datum "2024-01-01"^^xsd:date
  ] .
1.2 Tezaurus
Nejjednodušším typem slovníku je tezaurus obsahující pojmy, které se v datech vyskytují. O každém pojmu je třeba uvést alespoň jeho identifikátor a název, volitelně pak popis, definici, definující a související ustanovení nebo jiné nelegislativní zdroje, či nadřazené a ekvivalentní pojmy.


Obrázek 2 Tezaurus
Příklad 3: Tezaurus v JSON-LD
JSON-LD, JSON-LD kontext, Validní vůči JSON Schéma Tezauru a JSON Schéma Slovníku

{
    "@context": "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld",
    "iri": "https://slovník.gov.cz/datový/turistické-cíle",
    "typ": [
        "Slovník",
        "Tezaurus"
    ],
    "název": {
        "cs": "Slovník turistických cílů",
        "en": "Vocabulary of tourist points of interest"
    },
    "popis": {
        "cs": "Slovník turistických cílů slouží v rámci příkladu pro OFN Slovníky",
        "en": "Vocabulary of tourist points of interest serves as an example in the formal open standard for vocabularies"
    },
    "vytvořeno": {
        "typ": "Časový okamžik",
        "datum": "2024-01-01"
    },
    "aktualizováno": {
        "typ": "Časový okamžik",
        "datum_a_čas": "2024-01-15T04:53:21+02:00"
    },
    "pojmy": [
        {
            "iri": "https://slovník.gov.cz/datový/turistické-cíle/pojem/turistický-cíl",
            "typ": [
                "Pojem",
                "Koncept"
            ],
            "název": {
                "cs": "Turistický cíl",
                "en": "Tourist point of interest"
            },
            "alternativní-název": {
                "cs": [
                    "Zajímavost",
                    "Turistická zajímavost"
                ],
                "en": [
                    "Attraction",
                    "Tourist attraction"
                ]
            },
            "definice": {
                "cs": "Samostatný turistický cíl.",
                "en": "Tourist point of interest"
            },
            "související-ustanovení-právního-předpisu": [
                "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/1992/114/2024-01-01/dokument/norma/cast_1/par_3/odst_1/pism_q"
            ],
            "nadřazený-pojem": [
                "https://slovník.gov.cz/generický/veřejná-místa/pojem/veřejné-místo"
            ],
            "ekvivalentní-pojem": [
                "https://schema.org/TouristAttraction"
            ]
        },
        {
            "iri": "https://slovník.gov.cz/datový/turistické-cíle/pojem/typ-turistického-cíle",
            "typ": [
                "Pojem",
                "Koncept"
            ],
            "název": {
                "cs": "Typ turistického cíle",
                "en": "Type of the tourist point of interest"
            },
            "definující-nelegislativní-zdroj": [
                {
                    "typ": "Digitální objekt",
                    "url": "https://data.dia.gov.cz/soubory/číselníky/typy-turistických-cílů.jsonld"
                }
            ],
            "související-nelegislativní-zdroj": [
                {
                    "typ": "Digitální objekt",
                    "název": {
                        "cs": "Seznam typů turistických cílů od KČT"
                    },
                    "popis": {
                        "cs": "Dokument k dispozici na podatelně KČT, proto nemá URL"
                    }
                }
            ],
            "definice": {
                "cs": "Typ turistického cíle (např. přírodní nebo kulturní) reprezentovaný jako položka číselníku typů turistických cílů."
            }
        },
        {
            "iri": "https://slovník.gov.cz/datový/turistické-cíle/pojem/má-typ-turistického-cíle",
            "typ": [
                "Pojem",
                "Koncept"
            ],
            "název": {
                "cs": "má typ turistického cíle",
                "en": "has type of tourist point of interest"
            },
            "popis": {
                "cs": "vazba propojuje turistický cíl a jeho typ"
            },
            "definice": {
                "cs": "Určuje, zda se jedná o přírodní nebo kulturní turistický cíl."
            }
        },
        {
            "iri": "https://slovník.gov.cz/datový/turistické-cíle/pojem/kouření-povoleno",
            "typ": [
                "Pojem",
                "Koncept"
            ],
            "název": {
                "cs": "kouření povoleno",
                "en": "smoking allowed"
            },
            "definice": {
                "cs": "Určuje, zda je možné v turistickém cíli kouření tabákových výrobků."
            }
        }
    ]
}
Příklad 4: Tezaurus v RDF Turtle
RDF Turtle

@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix schema: <http://schema.org/> .
@prefix schemas: <https://schema.org/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix slovníky: <https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix čas: <https://slovník.gov.cz/generický/čas/pojem/> .

<https://slovník.gov.cz/datový/turistické-cíle> a slovníky:slovník,
    skos:ConceptScheme;
  dcterms:description "Slovník turistických cílů slouží v rámci příkladu pro OFN Slovníky"@cs,
    "Vocabulary of tourist points of interest serves as an example in the formal open standard for vocabularies"@en;
  skos:prefLabel "Slovník turistických cílů"@cs,
    "Vocabulary of tourist points of interest"@en;
  slovníky:okamžik-poslední-změny [
    a čas:časový-okamžik;
    čas:datum-a-čas "2024-01-15T04:53:21+02:00"^^xsd:dateTimeStamp
  ];
  slovníky:okamžik-vytvoření [
    a čas:časový-okamžik;
    čas:datum "2024-01-01"^^xsd:date
  ] .
  
<https://slovník.gov.cz/datový/turistické-cíle/pojem/kouření-povoleno> a slovníky:pojem,
    skos:Concept;
  skos:definition "Určuje, zda je možné v turistickém cíli kouření tabákových výrobků."@cs;
  skos:inScheme <https://slovník.gov.cz/datový/turistické-cíle>;
  skos:prefLabel "kouření povoleno"@cs,
    "smoking allowed"@en .

<https://slovník.gov.cz/datový/turistické-cíle/pojem/má-typ-turistického-cíle> a slovníky:pojem,
    skos:Concept;
  dcterms:description "vazba propojuje turistický cíl a jeho typ"@cs;
  skos:definition "Určuje, zda se jedná o přírodní nebo kulturní turistický cíl."@cs;
  skos:inScheme <https://slovník.gov.cz/datový/turistické-cíle>;
  skos:prefLabel "má typ turistického cíle"@cs,
    "has type of tourist point of interest"@en .

<https://slovník.gov.cz/datový/turistické-cíle/pojem/turistický-cíl> a slovníky:pojem,
    skos:Concept;
  skos:altLabel "Zajímavost"@cs,
    "Turistická zajímavost"@cs,
    "Attraction"@en,
    "Tourist attraction"@en;
  skos:broader <https://slovník.gov.cz/generický/veřejná-místa/pojem/veřejné-místo>;
  skos:definition "Samostatný turistický cíl."@cs,
    "Tourist point of interest"@en;
  skos:exactMatch schemas:TouristAttraction;
  skos:inScheme <https://slovník.gov.cz/datový/turistické-cíle>;
  skos:prefLabel "Turistický cíl"@cs,
    "Tourist point of interest"@en;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/1992/114/2024-01-01/dokument/norma/cast_1/par_3/odst_1/pism_q> .

<https://slovník.gov.cz/datový/turistické-cíle/pojem/typ-turistického-cíle> a slovníky:pojem,
    skos:Concept;
  skos:definition "Typ turistického cíle (např. přírodní nebo kulturní) reprezentovaný jako položka číselníku typů turistických cílů."@cs;
  skos:inScheme <https://slovník.gov.cz/datový/turistické-cíle>;
  skos:prefLabel "Typ turistického cíle"@cs,
    "Type of the tourist point of interest"@en;
  slovníky:definující-nelegislativní-zdroj [
    a <https://slovník.gov.cz/generický/digitální-objekty/pojem/digitální-objekt>;
    schema:url "https://data.dia.gov.cz/soubory/číselníky/typy-turistických-cílů.jsonld"^^xsd:anyURI
  ];
  slovníky:související-nelegislativní-zdroj [
    a <https://slovník.gov.cz/generický/digitální-objekty/pojem/digitální-objekt>;
    dcterms:title "Seznam typů turistických cílů od KČT"@cs;
    dcterms:description "Dokument k dispozici na podatelně KČT, proto nemá URL"@cs
  ] .
1.3 Konceptuální model
Na této úrovni rozlišujeme pojmy, které reprezentují

třídy reprezentující typy subjektů a objektů práva,
vztahy mezi dvěma subjekty či objekty práva,
vlastnosti subjektů a objektů práva.

Obrázek 3 Konceptuální model
Příkladem je slovník s IRI https://slovník.gov.cz/datový/turistické-cíle obsahující pojmy. Dále každému pojmu přiděluje jeho typ z hlediska modelu, tj. zda se jedná o třídu, vztah či vlastnost. V závislosti na typu pojmu je pak daný pojem dále popsán. U vztahu má typ turistického cíle je ukázáno použití nadřazeného vztahu.

Příklad 5: Konceptuální model v JSON-LD
JSON-LD, JSON-LD kontext, Validní vůči JSON Schéma Konceptuálního modelu, JSON Schéma Tezauru a JSON Schéma Slovníku

{
  "@context": "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld",
  "iri": "https://slovník.gov.cz/datový/turistické-cíle",
  "typ": ["Slovník", "Tezaurus", "Konceptuální model"],
  "název": {
      "cs": "Slovník turistických cílů",
      "en": "Vocabulary of tourist points of interest"
  },
  "popis": {
      "cs": "Slovník turistických cílů slouží v rámci příkladu pro OFN Slovníky",
      "en": "Vocabulary of tourist points of interest serves as an example in the formal open standard for vocabularies"
  },
  "pojmy": [
      {
          "iri": "https://slovník.gov.cz/datový/turistické-cíle/pojem/turistický-cíl",
          "typ": ["Koncept", "Pojem", "Třída"],
          "název": {
              "cs": "Turistický cíl",
              "en": "Tourist point of interest"
          },
          "definice": {
              "cs": "Samostatný turistický cíl.",
              "en": "Tourist point of interest"
          },
          "související-ustanovení-právního-předpisu": [
              "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/1992/114/2024-01-01/dokument/norma/cast_1/par_3/odst_1/pism_q"
          ],
          "nadřazená-třída": [
              "https://slovník.gov.cz/generický/veřejná-místa/pojem/veřejné-místo",
              "https://slovník.gov.cz/veřejný-sektor/pojem/objekt-práva"
          ]
      },
      {
          "iri": "https://slovník.gov.cz/datový/turistické-cíle/pojem/typ-turistického-cíle",
          "typ": ["Koncept", "Pojem", "Třída"],
          "název": {
              "cs": "Typ turistického cíle",
              "en": "Type of the tourist point of interest"
          },
          "definice": {
              "cs": "Typ turistického cíle (např. přírodní nebo kulturní) reprezentovaný jako položka číselníku typů turistických cílů."
          },
          "instance-definovány-číselníkem": {
              "iri": "https://data.mvcr.gov.cz/zdroj/číselníky/typy-turistických-cílů",
              "typ": "Číselník",
              "datová-sada-v-nkod": "https://data.gov.cz/zdroj/datové-sady/17651921/ff931872553062c9890157ce8615af03"
          }
      },
      {
          "iri": "https://slovník.gov.cz/datový/turistické-cíle/pojem/má-typ-turistického-cíle",
          "typ": ["Koncept", "Pojem", "Vztah"],
          "název": {
              "cs": "má typ turistického cíle",
              "en": "has type of tourist point of interest"
          },
          "definice": {
              "cs": "Určuje, zda se jedná o přírodní nebo kulturní turistický cíl."
          },
          "definiční-obor": "https://slovník.gov.cz/datový/turistické-cíle/pojem/turistický-cíl",
          "obor-hodnot": "https://slovník.gov.cz/datový/turistické-cíle/pojem/typ-turistického-cíle",
          "nadřazený-vztah": [
              "https://slovník.gov.cz/datový/číselníky/pojem/má-přiřazenu-položku-číselníku"
          ]
      },
      {
          "iri": "https://slovník.gov.cz/datový/turistické-cíle/pojem/kouření-povoleno",
          "typ": ["Koncept", "Pojem", "Vlastnost"],
          "název": {
              "cs": "kouření povoleno",
              "en": "smoking allowed"
          },
          "definice": {
              "cs": "Určuje, zda je možné v turistickém cíli kouření tabákových výrobků."
          },
          "definiční-obor": "https://slovník.gov.cz/datový/turistické-cíle/pojem/turistický-cíl",
          "obor-hodnot": "xsd:boolean"
      }
  ]
}
Příklad 6: Konceptuální model v RDF Turtle
RDF Turtle

@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix l111-2009: <https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix slovníky: <https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/> .
@prefix vsgov: <https://slovník.gov.cz/veřejný-sektor/pojem/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://slovník.gov.cz/datový/turistické-cíle> a slovníky:slovník,
    skos:ConceptScheme,
    owl:Ontology;
  dcterms:description "Slovník turistických cílů slouží v rámci příkladu pro OFN Slovníky"@cs,
    "Vocabulary of tourist points of interest serves as an example in the formal open standard for vocabularies"@en;
  skos:prefLabel "Slovník turistických cílů"@cs,
    "Vocabulary of tourist points of interest"@en .
    
<https://slovník.gov.cz/datový/turistické-cíle/pojem/kouření-povoleno> a skos:Concept,
    slovníky:pojem,
    owl:DatatypeProperty;
  rdfs:domain <https://slovník.gov.cz/datový/turistické-cíle/pojem/turistický-cíl>;
  rdfs:range xsd:boolean;
  skos:definition "Určuje, zda je možné v turistickém cíli kouření tabákových výrobků."@cs;
  skos:inScheme <https://slovník.gov.cz/datový/turistické-cíle>;
  skos:prefLabel "kouření povoleno"@cs,
    "smoking allowed"@en .

<https://slovník.gov.cz/datový/turistické-cíle/pojem/má-typ-turistického-cíle> a skos:Concept,
    slovníky:pojem,
    owl:ObjectProperty;
  rdfs:domain <https://slovník.gov.cz/datový/turistické-cíle/pojem/turistický-cíl>;
  rdfs:range <https://slovník.gov.cz/datový/turistické-cíle/pojem/typ-turistického-cíle>;
  rdfs:subPropertyOf <https://slovník.gov.cz/datový/číselníky/pojem/má-přiřazenu-položku-číselníku>;
  skos:definition "Určuje, zda se jedná o přírodní nebo kulturní turistický cíl."@cs;
  skos:inScheme <https://slovník.gov.cz/datový/turistické-cíle>;
  skos:prefLabel "má typ turistického cíle"@cs,
    "has type of tourist point of interest"@en .

<https://data.mvcr.gov.cz/zdroj/číselníky/typy-turistických-cílů> a l111-2009:číselník;
  l111-2009:má-v-nkod-zastřešující-datovou-sadu <https://data.gov.cz/zdroj/datové-sady/17651921/ff931872553062c9890157ce8615af03> .

<https://slovník.gov.cz/datový/turistické-cíle/pojem/typ-turistického-cíle> a skos:Concept,
    slovníky:pojem,
    owl:Class;
  skos:definition "Typ turistického cíle (např. přírodní nebo kulturní) reprezentovaný jako položka číselníku typů turistických cílů."@cs;
  skos:inScheme <https://slovník.gov.cz/datový/turistické-cíle>;
  skos:prefLabel "Typ turistického cíle"@cs,
    "Type of the tourist point of interest"@en;
  slovníky:má-instance-definované-číselníkem <https://data.mvcr.gov.cz/zdroj/číselníky/typy-turistických-cílů> .

<https://slovník.gov.cz/datový/turistické-cíle/pojem/turistický-cíl> a skos:Concept,
    slovníky:pojem,
    owl:Class;
  rdfs:subClassOf <https://slovník.gov.cz/generický/veřejná-místa/pojem/veřejné-místo>,
    vsgov:objekt-práva;
  skos:definition "Samostatný turistický cíl."@cs,
    "Tourist point of interest"@en;
  skos:inScheme <https://slovník.gov.cz/datový/turistické-cíle>;
  skos:prefLabel "Turistický cíl"@cs,
    "Tourist point of interest"@en;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/1992/114/2024-01-01/dokument/norma/cast_1/par_3/odst_1/pism_q> .
1.4 Rozšířená specifikace typů
Na této úrovni rozlišujeme Typ subjektu práva a Typ objektu práva. Případné budoucí verze mohou toto rozlišení dále prohlubovat přidáváním dalších typů. Toto rozšíření lze aplikovat jak na Tezaurus, tak na Konceptuální model.


Obrázek 4 Rozšířená specifikace typů
Příkladem je slovník Slovník zákona č. 56/2001 Sb. o podmínkách provozu vozidel na pozemních komunikacích a o změně zákona č. 168/1999 Sb., o pojištění odpovědnosti za škodu způsobenou provozem vozidla a o změně některých souvisejících zákonů (zákon o pojištění odpovědnosti z provozu vozidla), ve znění zákona č. 307/1999 Sb. s IRI https://slovník.gov.cz/legislativní/sbírka/56/2001. Tak jako v základním modelu obsahuje pojmy a jejich typy z hlediska modelu, tj. zda se jedná o třídu, vztah či vlastnost a v závislosti na typu pojmu je pak daný pojem dále popsán. Navíc však u tříd specifikujeme, zda se jedná o Typ subjektu práva nebo Typ objektu práva.

Poznámka
JSON schéma kontroluje každý prvek na přítomnost všech rozšiřujících prvků z této kapitoly, je tedy určeno ke kontrole té podmnožiny pojmů ve slovníku, které toto rozšíření používají v celém jeho rozsahu. Všechny pojmy ve slovníku ale toto rozšíření používat nemusí.

Příklad 7: Rozšíření v JSON-LD
JSON-LD, JSON-LD kontext, Validní vůči JSON Schéma rozšíření, JSON Schéma Konceptuálního modelu, JSON Schéma Tezauru a JSON Schéma Slovníku

{
    "@context": "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld",
    "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001",
    "typ": ["Slovník", "Tezaurus", "Konceptuální model"],
    "název": {
        "cs": "Slovník zákona č. 56/2001 Sb. o podmínkách provozu vozidel na pozemních komunikacích a o změně zákona č. 168/1999 Sb., o pojištění odpovědnosti za škodu způsobenou provozem vozidla a o změně některých souvisejících zákonů (zákon o pojištění odpovědnosti z provozu vozidla), ve znění zákona č. 307/1999 Sb."
    },
    "popis": {
        "cs": "Slovník slouží v rámci příkladu pro OFN Slovníky"
    },
    "pojmy": [
        {
            "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo",
            "typ": ["Koncept", "Pojem", "Třída", "Typ objektu práva"],
            "název": {
                "cs": "Silniční vozidlo",
                "en": "Road vehicle"
            },
            "definice": {
                "cs": "Silniční vozidlo je motorové nebo nemotorové vozidlo, které je vyrobené za účelem provozu na pozemních komunikacích pro přepravu osob, zvířat nebo věcí."
            },
            "definující-ustanovení-právního-předpisu": [
                "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2026-01-01/dokument/norma/cast_1/par_2/odst_1"
            ],
            "související-ustanovení-právního-předpisu": [
                "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2004/277"
            ],
            "nadřazená-třída": [
                "https://slovník.gov.cz/legislativní/sbírka/361/2000/pojem/vozidlo"
            ]
        },
        {
            "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla",
            "typ": ["Koncept", "Pojem", "Třída", "Typ subjektu práva"],
            "název": {
                "cs": "Vlastník vozidla",
                "en": "Vehicle owner"
            },
            "definice": {
                "cs": "Vlastník vozidla"
            },
            "související-ustanovení-právního-předpisu": [
                "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a"
            ]
        },
        {
            "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/má-vlastníka-vozidla",
            "typ": ["Koncept", "Pojem", "Vztah"],
            "název": {
                "cs": "má vlastníka vozidla"
            },
            "definice": {
                "cs": "má vlastníka vozidla"
            },
            "související-ustanovení-právního-předpisu": [
                "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a"
            ],
            "definiční-obor": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo",
            "obor-hodnot": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla"
        },
        {
            "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastnictví-vozidla",
            "typ": ["Koncept", "Pojem", "Třída"],
            "název": {
                "cs": "Vlastnictví vozidla"
            },
            "definice": {
                "cs": "Vlastnictví vozidla"
            },
            "související-ustanovení-právního-předpisu": [
                "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_2/pism_a"
            ]
        },
        {
            "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/registrační-značka",
            "typ": ["Koncept", "Pojem", "Vlastnost"],
            "název": {
                "cs": "registrační značka"
            },
            "definice": {
                "cs": "Registrační značkou je státní poznávací značka přidělená silničnímu vozidlu. Registrační značka je tvořena kombinací velkých písmen latinské abecedy a arabských číslic."
            },
            "definiční-obor": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/tabulka-s-přidělenou-registrační-značkou",
            "obor-hodnot": "xsd:string"
        },
        {
            "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/havárie-silničního-vozidla",
            "typ": ["Koncept", "Pojem", "Třída", "Typ objektu práva"],
            "název": {
                "cs": "Havárie silničního vozidla"
            },
            "definice": {
                "cs": "Havárie silničního vozidla"
            }
        },
        {
            "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/zničené-silniční-vozidlo",
            "typ": ["Koncept", "Pojem", "Třída", "Typ objektu práva"],
            "název": {
                "cs": "Zničené silniční vozidlo"
            },
            "definice": {
                "cs": "Zničené silniční vozidlo"
            }
        }
    ]
}
Příklad 8: Rozšíření v RDF Turtle
RDF Turtle

@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix slovníky: <https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/> .
@prefix vsgov: <https://slovník.gov.cz/veřejný-sektor/pojem/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://slovník.gov.cz/legislativní/sbírka/56/2001> a slovníky:slovník,
    skos:ConceptScheme,
    owl:Ontology;
  dcterms:description "Slovník slouží v rámci příkladu pro OFN Slovníky"@cs;
  skos:prefLabel "Slovník zákona č. 56/2001 Sb. o podmínkách provozu vozidel na pozemních komunikacích a o změně zákona č. 168/1999 Sb., o pojištění odpovědnosti za škodu způsobenou provozem vozidla a o změně některých souvisejících zákonů (zákon o pojištění odpovědnosti z provozu vozidla), ve znění zákona č. 307/1999 Sb."@cs .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/havárie-silničního-vozidla> a skos:Concept,
    slovníky:pojem,
    owl:Class,
    vsgov:typ-objektu-práva;
  skos:definition "Havárie silničního vozidla"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Havárie silničního vozidla"@cs .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/má-vlastníka-vozidla> a skos:Concept,
    slovníky:pojem,
    owl:ObjectProperty;
  rdfs:domain <https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo>;
  rdfs:range <https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla>;
  skos:definition "má vlastníka vozidla"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "má vlastníka vozidla"@cs;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a> .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/registrační-značka> a skos:Concept,
    slovníky:pojem,
    owl:DatatypeProperty;
  rdfs:domain <https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/tabulka-s-přidělenou-registrační-značkou>;
  rdfs:range xsd:string;
  skos:definition "Registrační značkou je státní poznávací značka přidělená silničnímu vozidlu. Registrační značka je tvořena kombinací velkých písmen latinské abecedy a arabských číslic."@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "registrační značka"@cs .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastnictví-vozidla> a skos:Concept,
    slovníky:pojem,
    owl:Class;
  skos:definition "Vlastnictví vozidla"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Vlastnictví vozidla"@cs;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_2/pism_a> .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/zničené-silniční-vozidlo> a skos:Concept,
    slovníky:pojem,
    owl:Class,
    vsgov:typ-objektu-práva;
  skos:definition "Zničené silniční vozidlo"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Zničené silniční vozidlo"@cs .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo> a skos:Concept,
    slovníky:pojem,
    owl:Class,
    vsgov:typ-objektu-práva;
  rdfs:subClassOf <https://slovník.gov.cz/legislativní/sbírka/361/2000/pojem/vozidlo>;
  skos:definition "Silniční vozidlo je motorové nebo nemotorové vozidlo, které je vyrobené za účelem provozu na pozemních komunikacích pro přepravu osob, zvířat nebo věcí."@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Silniční vozidlo"@cs,
    "Road vehicle"@en;
  slovníky:definující-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2026-01-01/dokument/norma/cast_1/par_2/odst_1>;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2004/277> .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla> a skos:Concept,
    slovníky:pojem,
    owl:Class,
    vsgov:typ-subjektu-práva;
  skos:definition "Vlastník vozidla"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Vlastník vozidla"@cs,
    "Vehicle owner"@en;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a> .
1.5 Anotace pro registr práv a povinností
Pokud popisujeme subjekty a objekty práva pro jejich následnou reprezentaci v Registru práv a povinností (RPP), je třeba je popsat detailněji. Vyžaduje použití rozlišení na Typ subjektů práva a Typ objektů práva z Rozšířené specifikace typů.


Obrázek 5 Anotace pro registr práv a povinností
Poznámka
Pokud u vlastnosti či vztahu není uvedena (ne)veřejnost, interpretace je, že je stejná jako u třídy, jíž má vlastnost/vztah jako definiční obor.

Poznámka
JSON schéma kontroluje každý prvek na přítomnost všech rozšiřujících prvků z této kapitoly, je tedy určeno ke kontrole té podmnožiny pojmů ve slovníku, které toto rozšíření používají v celém jeho rozsahu. Všechny pojmy ve slovníku ale toto rozšíření používat nemusí.

Příklad 9: Anotace pro RPP v JSON-LD
JSON-LD, JSON-LD kontext, Validní vůči JSON Schéma anotace RPP, JSON Schéma rozšíření, JSON Schéma Konceptuálního modelu, JSON Schéma Tezauru, JSON Schéma Slovníku

{
  "@context": "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld",
  "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001",
  "typ": ["Slovník", "Tezaurus", "Konceptuální model"],
  "název": {
      "cs": "Slovník zákona č. 56/2001 Sb. o podmínkách provozu vozidel na pozemních komunikacích a o změně zákona č. 168/1999 Sb., o pojištění odpovědnosti za škodu způsobenou provozem vozidla a o změně některých souvisejících zákonů (zákon o pojištění odpovědnosti z provozu vozidla), ve znění zákona č. 307/1999 Sb."
  },
  "popis": {
      "cs": "Slovník slouží v rámci příkladu pro OFN Slovníky"
  },
  "pojmy": [
      {
          "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo",
          "typ": ["Koncept", "Pojem", "Třída", "Typ objektu práva"],
          "název": {
              "cs": "Silniční vozidlo",
              "en": "Road vehicle"
          },
          "definice": {
              "cs": "Silniční vozidlo je motorové nebo nemotorové vozidlo, které je vyrobené za účelem provozu na pozemních komunikacích pro přepravu osob, zvířat nebo věcí."
          },
          "související-ustanovení-právního-předpisu": [
              "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_1/par_2/odst_1"
          ],
          "nadřazená-třída": [
              "https://slovník.gov.cz/legislativní/sbírka/361/2000/pojem/vozidlo"
          ]
      },
      {
          "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla",
          "typ": ["Koncept", "Pojem", "Třída", "Typ subjektu práva"],
          "název": {
              "cs": "Vlastník vozidla",
              "en": "Vehicle owner"
          },
          "definice": {
              "cs": "Vlastník vozidla"
          },
          "související-ustanovení-právního-předpisu": [
              "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a"
          ],
          "je-sdílen-v-ppdf": true,
          "agendový-informační-systém": "https://rpp-opendata.egon.gov.cz/odrpp/zdroj/isvs/123456",
          "agenda": "https://rpp-opendata.egon.gov.cz/odrpp/zdroj/agenda/A1021"
      },
      {
          "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/má-vlastníka-vozidla",
          "typ": ["Koncept", "Pojem", "Vztah", "Neveřejný údaj"],
          "název": {
              "cs": "má vlastníka vozidla"
          },
          "definice": {
              "cs": "má vlastníka vozidla"
          },
          "související-ustanovení-právního-předpisu": [
              "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a"
          ],
          "definiční-obor": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo",
          "obor-hodnot": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla",
          "je-sdílen-v-ppdf": true,
          "ustanovení-dokládající-neveřejnost-údaje": [
              "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a"
          ]
      },
      {
          "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastnictví-vozidla",
          "typ": ["Koncept", "Pojem", "Třída", "Veřejný údaj"],
          "název": {
              "cs": "Vlastnictví vozidla"
          },
          "definice": {
              "cs": "Vlastnictví vozidla"
          },
          "související-ustanovení-právního-předpisu": [
              "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_2/pism_a"
          ]
      },
      {
          "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/registrační-značka",
          "typ": ["Koncept", "Pojem", "Vlastnost", "Veřejný údaj"],
          "název": {
              "cs": "registrační značka"
          },
          "definice": {
              "cs": "Registrační značkou je státní poznávací značka přidělená silničnímu vozidlu. Registrační značka je tvořena kombinací velkých písmen latinské abecedy a arabských číslic."
          },
          "definiční-obor": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/tabulka-s-přidělenou-registrační-značkou",
          "obor-hodnot": "xsd:string",
          "je-sdílen-v-ppdf": false
      },
      {
          "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/havárie-silničního-vozidla",
          "typ": ["Koncept", "Pojem", "Třída", "Typ objektu práva"],
          "název": {
              "cs": "Havárie silničního vozidla"
          },
          "definice": {
              "cs": "Havárie silničního vozidla"
          }
      },
      {
          "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/zničené-silniční-vozidlo",
          "typ": ["Koncept", "Pojem", "Třída", "Typ objektu práva"],
          "název": {
              "cs": "Zničené silniční vozidlo"
          },
          "definice": {
              "cs": "Zničené silniční vozidlo"
          }
      }
  ]
}
Příklad 10: Anotace pro RPP v RDF Turtle
RDF Turtle

@prefix a104: <https://slovník.gov.cz/agendový/104/pojem/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix l111-2009: <https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix slovníky: <https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/> .
@prefix vsgov: <https://slovník.gov.cz/veřejný-sektor/pojem/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<https://slovník.gov.cz/legislativní/sbírka/56/2001> a slovníky:slovník,
    skos:ConceptScheme,
    owl:Ontology;
  dcterms:description "Slovník slouží v rámci příkladu pro OFN Slovníky"@cs;
  skos:prefLabel "Slovník zákona č. 56/2001 Sb. o podmínkách provozu vozidel na pozemních komunikacích a o změně zákona č. 168/1999 Sb., o pojištění odpovědnosti za škodu způsobenou provozem vozidla a o změně některých souvisejících zákonů (zákon o pojištění odpovědnosti z provozu vozidla), ve znění zákona č. 307/1999 Sb."@cs .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/havárie-silničního-vozidla> a skos:Concept,
    slovníky:pojem,
    owl:Class,
    vsgov:typ-objektu-práva;
  skos:definition "Havárie silničního vozidla"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Havárie silničního vozidla"@cs .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/má-vlastníka-vozidla> a skos:Concept,
    slovníky:pojem,
    owl:ObjectProperty,
    l111-2009:neveřejný-údaj;
  rdfs:domain <https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo>;
  rdfs:range <https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla>;
  skos:definition "má vlastníka vozidla"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "má vlastníka vozidla"@cs;
  a104:je-sdílen-v-propojeném-datovém-fondu true;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a>;
  l111-2009:je-vymezen-ustanovením-stanovujícím-jeho-neveřejnost <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a> .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/registrační-značka> a skos:Concept,
    slovníky:pojem,
    owl:DatatypeProperty,
    l111-2009:veřejný-údaj;
  rdfs:domain <https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/tabulka-s-přidělenou-registrační-značkou>;
  rdfs:range xsd:string;
  skos:definition "Registrační značkou je státní poznávací značka přidělená silničnímu vozidlu. Registrační značka je tvořena kombinací velkých písmen latinské abecedy a arabských číslic."@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "registrační značka"@cs;
  a104:je-sdílen-v-propojeném-datovém-fondu false .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastnictví-vozidla> a skos:Concept,
    slovníky:pojem,
    owl:Class,
    l111-2009:veřejný-údaj;
  skos:definition "Vlastnictví vozidla"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Vlastnictví vozidla"@cs;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_2/pism_a> .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/zničené-silniční-vozidlo> a skos:Concept,
    slovníky:pojem,
    owl:Class,
    vsgov:typ-objektu-práva;
  skos:definition "Zničené silniční vozidlo"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Zničené silniční vozidlo"@cs .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo> a skos:Concept,
    slovníky:pojem,
    owl:Class,
    vsgov:typ-objektu-práva;
  rdfs:subClassOf <https://slovník.gov.cz/legislativní/sbírka/361/2000/pojem/vozidlo>;
  skos:definition "Silniční vozidlo je motorové nebo nemotorové vozidlo, které je vyrobené za účelem provozu na pozemních komunikacích pro přepravu osob, zvířat nebo věcí."@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Silniční vozidlo"@cs,
    "Road vehicle"@en;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_1/par_2/odst_1> .

<https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla> a skos:Concept,
    slovníky:pojem,
    owl:Class,
    vsgov:typ-subjektu-práva;
  skos:definition "Vlastník vozidla"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Vlastník vozidla"@cs,
    "Vehicle owner"@en;
  a104:je-sdílen-v-propojeném-datovém-fondu true;
  a104:sdružuje-údaje-vedené-nebo-vytvářené-v-rámci-agendy <https://rpp-opendata.egon.gov.cz/odrpp/zdroj/agenda/A1021>;
  a104:údaje-jsou-v-ais <https://rpp-opendata.egon.gov.cz/odrpp/zdroj/isvs/123456>;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a> .
1.6 Anotace pro § 23 vyhlášky 360/2023 Sb.
Pokud popisujeme údaje pro jejich kategorizaci dle § 23 vyhlášky 360/2023 Sb., je třeba je popsat detailněji.

Jednotlivé pojmy v datových slovnících budou mít přiřazeny kategorie dle § 23 vyhlášky č. 360/2023 Sb., o dlouhodobém řízení informačních systémů veřejné správy. Uplatněním všech tří způsobů kategorizace, tj. kategorií podle odst. 1 (způsob získání), odst. 2 (způsob sdílení) a odst. 3 (obsah) na úrovni pojmů v datovém slovníku bude definován předpokládaný či požadovaný stav dat, tj. „jak by to mělo být“ - „de iure“. Pojem tedy bude kategorizován jako údaj ze základních registrů (1a), pokud je ze základních registrů získatelný (zatím bez ohledu na to, zda je z nich reálně získáván). Analogicky bude pojem kategorizován jako údaj veřejně přístupný (2a), pokud není konkrétním legislativním ustanovením označen za neveřejný. Jako poskytovaný na žádost (2b) nebo zpřístupňovaný pro výkon jiné agendy přes ISSS (2c) bude pojem kategorizován, pokud existuje (je známý) požadavek na poskytnutí či zpřístupnění daného údaje nebo takový požadavek vyplývá z textu nějakého zákona.

Pojem může mít přiřazenu právě jednu kategorii podle odst. 1 (způsob získání) a odst. 3 (obsah), ale může mít přiřazenu více než jednu kategorii podle odst. 2 (způsob sdílení), tzn. může být zároveň např. veřejný (2a) a zpřístupňovaný pro výkon jiné agendy (2c).


Obrázek 6 Anotace pro § 23 vyhlášky 360/2023 Sb.
Poznámka
JSON schéma kontroluje každý prvek na přítomnost všech rozšiřujících prvků z této kapitoly, je tedy určeno ke kontrole té podmnožiny pojmů ve slovníku, které toto rozšíření používají v celém jeho rozsahu. Všechny pojmy ve slovníku ale toto rozšíření používat nemusí.

Příklad 11: Anotace pro § 23 vyhlášky 360/2023 Sb. v JSON-LD
JSON-LD, JSON-LD kontext, Validní vůči JSON Schéma anotace pro § 23 vyhlášky 360/2023 Sb., JSON Schéma rozšíření, JSON Schéma Tezauru, JSON Schéma Slovníku

{
    "@context": "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld",
    "iri": "https://slovník.gov.cz/legislativní/sbírka/56/2001",
    "typ": ["Slovník", "Tezaurus"],
    "název": {
        "cs": "Slovník agendy A1046: Agenda řidičů"
    },
    "popis": {
        "cs": "Slovník slouží v rámci příkladu kategorizace pojmů pro OFN Slovníky, § 23 vyhlášky 360/2023 Sb."
    },
    "pojmy": [
        {
            "iri": "https://slovník.gov.cz/legislativní/sbírka/361/2000/pojem/skupina-vozidel",
            "typ": ["Koncept", "Pojem", "Typ objektu práva"],
            "název": {
                "cs": "Skupina vozidel"
            },
            "definice": {
                "cs": "Skupina vozidel"
            },
            "způsob-získání-údaje": "způsoby-získání:vlastní",
            "způsoby-sdílení-údaje": [
                "způsoby-sdílení:veřejně-přístupné",
                "způsoby-sdílení:zpřístupňované-pro-výkon-agendy"
            ],
            "typ-obsahu-údaje": "typy-obsahu:evidenční"
        },
        {
            "iri": "https://slovník.gov.cz/legislativní/sbírka/361/2000/pojem/řidič-evidovaný-v-registru-řidičů",
            "typ": ["Koncept", "Pojem", "Typ subjektu práva"],
            "název": {
                "cs": "Řidič evidovaný v Centrálním registru řidičů"
            },
            "definice": {
                "cs": "Řidič evidovaný v Centrálním registru řidičů"
            },
            "související-ustanovení-právního-předpisu": [
                "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a"
            ],
            "je-sdílen-v-ppdf": true,
            "agendový-informační-systém": "https://rpp-opendata.egon.gov.cz/odrpp/zdroj/isvs/123456",
            "agenda": "https://rpp-opendata.egon.gov.cz/odrpp/zdroj/agenda/A1046",
            "způsob-získání-údaje": "způsoby-získání:vlastní",
            "způsoby-sdílení-údaje": [
                "způsoby-sdílení:zpřístupňované-pro-výkon-agendy"
            ],
            "typ-obsahu-údaje": "typy-obsahu:identifikační"
        }
    ]
}
Příklad 12: Anotace pro § 23 vyhlášky 360/2023 Sb. v RDF Turtle
@prefix a104: <https://slovník.gov.cz/agendový/104/pojem/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix slovníky: <https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/> .
@prefix typy-obsahu-údajů: <https://data.dia.gov.cz/zdroj/číselníky/typy-obsahu-údajů/položky/> .
@prefix vsgov: <https://slovník.gov.cz/veřejný-sektor/pojem/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix způsoby-sdílení-údajů: <https://data.dia.gov.cz/zdroj/číselníky/způsoby-sdílení-údajů/položky/> .
@prefix způsoby-získání-údajů: <https://data.dia.gov.cz/zdroj/číselníky/způsoby-získání-údajů/položky/> .

<https://slovník.gov.cz/legislativní/sbírka/56/2001> a slovníky:slovník,
    skos:ConceptScheme;
  dcterms:description "Slovník slouží v rámci příkladu kategorizace pojmů pro OFN Slovníky, § 23 vyhlášky 360/2023 Sb."@cs;
  skos:prefLabel "Slovník agendy A1046: Agenda řidičů"@cs .
  
<https://slovník.gov.cz/legislativní/sbírka/361/2000/pojem/skupina-vozidel> a skos:Concept,
    slovníky:pojem,
    vsgov:typ-objektu-práva;
  skos:definition "Skupina vozidel"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Skupina vozidel"@cs;
  slovníky:má-typ-obsahu-údaje typy-obsahu-údajů:evidenční;
  slovníky:má-způsob-sdílení-údaje způsoby-sdílení-údajů:veřejně-přístupné,
    způsoby-sdílení-údajů:zpřístupňované-pro-výkon-agendy;
  slovníky:má-způsob-získání-údaje způsoby-získání-údajů:vlastní .

<https://slovník.gov.cz/legislativní/sbírka/361/2000/pojem/řidič-evidovaný-v-registru-řidičů> a skos:Concept,
    slovníky:pojem,
    vsgov:typ-subjektu-práva;
  skos:definition "Řidič evidovaný v Centrálním registru řidičů"@cs;
  skos:inScheme <https://slovník.gov.cz/legislativní/sbírka/56/2001>;
  skos:prefLabel "Řidič evidovaný v Centrálním registru řidičů"@cs;
  a104:je-sdílen-v-propojeném-datovém-fondu true;
  a104:sdružuje-údaje-vedené-nebo-vytvářené-v-rámci-agendy <https://rpp-opendata.egon.gov.cz/odrpp/zdroj/agenda/A1046>;
  a104:údaje-jsou-v-ais <https://rpp-opendata.egon.gov.cz/odrpp/zdroj/isvs/123456>;
  slovníky:má-typ-obsahu-údaje typy-obsahu-údajů:identifikační;
  slovníky:má-způsob-sdílení-údaje způsoby-sdílení-údajů:zpřístupňované-pro-výkon-agendy;
  slovníky:má-způsob-získání-údaje způsoby-získání-údajů:vlastní;
  slovníky:související-ustanovení <https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2024-01-01/dokument/norma/cast_2/par_4/odst_1/pism_a> .
2. Hlavní profily tříd
2.1 Konceptuální model
IRI profilovaných tříd	skos:ConceptScheme
owl:Ontology
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/slovník
IRI	https://ofn.gov.cz/slovníky#KonceptuálníModel
Název	Konceptuální model
Definice	Na této úrovni rozlišujeme pojmy, které reprezentují - třídy reprezentující typy subjektů a objektů práva, - vztahy mezi dvěma subjekty či objekty práva, - vlastnosti subjektů a objektů práva.
Hierarchie	
profiluje třídu Concept Scheme (@en) (skos:ConceptScheme)
Definice: A set of concepts, optionally including statements about semantic relationships between those concepts.
profiluje třídu Ontology (@en) (owl:Ontology)
Definice: The class of ontologies.
specializuje třídu Resource (@en) (rdfs:Resource)
Definice: The class resource, everything.
profiluje třídu Slovník (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/slovník)
Definice: Slovník je seskupení pojmů popisující vybranou věcnou oblast.
specializuje profil Tezaurus (https://ofn.gov.cz/slovníky#Tezaurus)
Definice: Tezaurus je nejjednodušším typem slovníku.
profiluje třídu Concept Scheme (@en) (skos:ConceptScheme)
Definice: A set of concepts, optionally including statements about semantic relationships between those concepts.
profiluje třídu Slovník (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/slovník)
Definice: Slovník je seskupení pojmů popisující vybranou věcnou oblast.
specializuje profil Slovník (https://ofn.gov.cz/slovníky#Slovník)
profiluje třídu Slovník (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/slovník)
Definice: Slovník je seskupení pojmů popisující vybranou věcnou oblast.
2.2 Pojem
IRI profilovaných tříd	skos:Concept
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem
IRI	https://ofn.gov.cz/slovníky#Pojem
Název	Pojem
Definice	Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
Hierarchie	
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
Zpětné asociace

z domény § 2.2 Pojem → § 2.2.5 ekvivalentní pojem
z domény § 2.2 Pojem → § 2.2.11 nadřazený pojem
2.2.1 alternativní název
IRI profilovaných vztahů	skos:altLabel
IRI	https://ofn.gov.cz/slovníky#Pojem.alternativníNázev
Název	alternativní název
Definice	Alternativní název pojmu. Musí být jiný, než hlavní název.
Definiční obor	Pojem [0..*]
Obor hodnot	rdf:langString [0..*]
Hierarchie	
profiluje vlastnost alternative label (@en) (skos:altLabel)
Definice: skos:prefLabel, skos:altLabel and skos:hiddenLabel are pairwise disjoint properties.
specializuje vlastnost label (@en) (rdfs:label)
Definice: A human-readable name for the subject.
2.2.2 definice
IRI profilovaných vztahů	skos:definition
IRI	https://ofn.gov.cz/slovníky#Pojem.definice
Název	definice
Definice	Definice pojmu. Je unikátní v rámci definic pojmů ve slovníku.
Definiční obor	Pojem [0..*]
Obor hodnot	Text [0..1]
Hierarchie	
profiluje vlastnost definition (@en) (skos:definition)
Definice: A statement or formal explanation of the meaning of a concept.
specializuje vlastnost note (@en) (skos:note)
Definice: A general note, for any purpose.
2.2.3 definující nelegislativní zdroj
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/definující-nelegislativní-zdroj
IRI	https://ofn.gov.cz/slovníky#Pojem.definujícíNelegislativníZdroj
Název	definující nelegislativní zdroj
Definice	Nelegislativní zdroj, ve kterém je pojem definován.
Definiční obor	Pojem
Obor hodnot	Digitální objekt [0..*]
Hierarchie	
profiluje vlastnost definující nelegislativní zdroj (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/definující-nelegislativní-zdroj)
Definice: Nelegislativní zdroj, ve kterém je pojem definován.
2.2.4 definující ustanovení
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/definující-ustanovení
IRI	https://ofn.gov.cz/slovníky#Pojem.definujícíUstanovení
Název	definující ustanovení
Definice	Ustanovení právního předpisu, ve kterém je pojem definován.
Definiční obor	Pojem
Obor hodnot	Ustanovení [0..*]
Hierarchie	
profiluje vlastnost definující ustanovení (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/definující-ustanovení)
Definice: Ustanovení právního předpisu, ve kterém je pojem definován.
2.2.5 ekvivalentní pojem
IRI profilovaných vztahů	skos:exactMatch
IRI	https://ofn.gov.cz/slovníky#Pojem.ekvivalentníPojem
Název	ekvivalentní pojem
Definice	Významově ekvivalentní pojem. Typicky se jedná o pojem z jiného slovníku, který však má stejný význam.
Definiční obor	Pojem
Obor hodnot	Pojem [0..*]
Hierarchie	
profiluje vlastnost has exact match (@en) (skos:exactMatch)
Definice: skos:exactMatch is disjoint with each of the properties skos:broadMatch and skos:relatedMatch.
specializuje vlastnost has close match (@en) (skos:closeMatch)
Definice: skos:closeMatch is used to link two concepts that are sufficiently similar that they can be used interchangeably in some information retrieval applications. In order to avoid the possibility of "compound errors" when combining mappings across more than two concept schemes, skos:closeMatch is not declared to be a transitive property.
specializuje vlastnost is in mapping relation with (@en) (skos:mappingRelation)
Definice: These concept mapping relations mirror semantic relations, and the data model defined below is similar (with the exception of skos:exactMatch) to the data model defined for semantic relations. A distinct vocabulary is provided for concept mapping relations, to provide a convenient way to differentiate links within a concept scheme from links between concept schemes. However, this pattern of usage is not a formal requirement of the SKOS data model, and relies on informal definitions of best practice.
specializuje vlastnost is in semantic relation with (@en) (skos:semanticRelation)
Definice: Links a concept to a concept related by meaning.
2.2.6 je sdílen v propojeném datovém fondu
IRI profilovaných vztahů	https://slovník.gov.cz/agendový/104/pojem/je-sdílen-v-propojeném-datovém-fondu
IRI	https://ofn.gov.cz/slovníky#Pojem.jeSdílenVPropojenémDatovémFondu
Název	je sdílen v propojeném datovém fondu
Definiční obor	Pojem
Obor hodnot	xsd:boolean [0..1]
Hierarchie	
profiluje vlastnost Je sdílen v propojeném datovém fondu (https://slovník.gov.cz/agendový/104/pojem/je-sdílen-v-propojeném-datovém-fondu)
2.2.7 je v tezauru
IRI profilovaných vztahů	skos:inScheme
IRI	https://ofn.gov.cz/slovníky#Pojem.jeVTezauru
Název	je v tezauru
Definice	Vazba propojující pojem a tezaurus, ve kterém je pojem definován.
Definiční obor	Pojem
Obor hodnot	Tezaurus [1..1]
Hierarchie	
profiluje vlastnost is in scheme (@en) (skos:inScheme)
Definice: Relates a resource (for example a concept) to a concept scheme in which it is included.
2.2.8 má typ obsahu údaje
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-typ-obsahu-údaje
IRI	https://ofn.gov.cz/slovníky#Pojem.máTypObsahuÚdaje
Název	má typ obsahu údaje
Definice	Orgán veřejné správy strukturuje data vedená v informačním systému podle jejich obsahu na údaje: a) identifikační: údaje, které, které samostatně nebo ve skupině identifikují konkrétní subjekt práva b) evidenční: údaje, které neidentifikují konkrétní subjekt práva, ale váží se k subjektu nebo objektu práva v rámci agendy a evidence, která se v ní vede c) statistické: údaje, které seskupují a formou anonymizace či pseudonymizace zamezují vazbě konkrétní subjekt práva
Definiční obor	Pojem
Obor hodnot	Typ obsahu údaje [0..1]
Hierarchie	
profiluje vlastnost má typ obsahu údaje (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-typ-obsahu-údaje)
Definice: Orgán veřejné správy strukturuje data vedená v informačním systému podle jejich obsahu na údaje: a) identifikační: údaje, které, které samostatně nebo ve skupině identifikují konkrétní subjekt práva b) evidenční: údaje, které neidentifikují konkrétní subjekt práva, ale váží se k subjektu nebo objektu práva v rámci agendy a evidence, která se v ní vede c) statistické: údaje, které seskupují a formou anonymizace či pseudonymizace zamezují vazbě konkrétní subjekt práva
2.2.9 má způsob sdílení údaje
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-sdílení-údaje
IRI	https://ofn.gov.cz/slovníky#Pojem.máZpůsobSdíleníÚdaje
Název	má způsob sdílení údaje
Definice	Orgán veřejné správy strukturuje data vedená v informačním systému podle způsobu jejich sdílení na údaje: a) veřejně přístupné: údaje publikované veřejně ve formě otevřených dat či jakkoliv jinak b) poskytované na žádost: údaje poskytované na žádost subjektu práva nebo na základě zákona o svobodném přístupu k informacím c) zpřístupňované pro výkon agendy: údaje sdílené jiným agendám, které mají oprávněný zájem je využívat pro výkon své působnosti d) nesdílené: údaje, které nejsou sdílené žádným z předchozích způsobů
Definiční obor	Pojem
Obor hodnot	Způsob sdílení údaje [0..*]
Hierarchie	
profiluje vlastnost má způsob sdílení údaje (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-sdílení-údaje)
Definice: Orgán veřejné správy strukturuje data vedená v informačním systému podle způsobu jejich sdílení na údaje: a) veřejně přístupné: údaje publikované veřejně ve formě otevřených dat či jakkoliv jinak b) poskytované na žádost: údaje poskytované na žádost subjektu práva nebo na základě zákona o svobodném přístupu k informacím c) zpřístupňované pro výkon agendy: údaje sdílené jiným agendám, které mají oprávněný zájem je využívat pro výkon své působnosti d) nesdílené: údaje, které nejsou sdílené žádným z předchozích způsobů
2.2.10 má způsob získání údaje
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-získání-údaje
IRI	https://ofn.gov.cz/slovníky#Pojem.máZpůsobZískáníÚdaje
Název	má způsob získání údaje
Definice	Orgán veřejné správy strukturuje data vedená v informačním systému na údaje následujících kategorií: a) základních registrů: údaje čerpané pro výkon agendy ze základních registrů b) jiných agend: údaje získávané pro výkon agendy od jiných úřadů c) vlastní: údaje vznikající při výkonu agendy, které mají evidenční charakter, tedy vztahují se k objektu nebo subjektu práva za účelem výkonu veřejné správy d) provozní: údaje vznikající při výkonu agendy, které nemají evidenční charakter a nevznikají za účelem výkonu veřejné správy
Definiční obor	Pojem
Obor hodnot	Způsob získání údaje [0..1]
Hierarchie	
profiluje vlastnost má způsob získání údaje (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-způsob-získání-údaje)
Definice: Orgán veřejné správy strukturuje data vedená v informačním systému na údaje následujících kategorií: a) základních registrů: údaje čerpané pro výkon agendy ze základních registrů b) jiných agend: údaje získávané pro výkon agendy od jiných úřadů c) vlastní: údaje vznikající při výkonu agendy, které mají evidenční charakter, tedy vztahují se k objektu nebo subjektu práva za účelem výkonu veřejné správy d) provozní: údaje vznikající při výkonu agendy, které nemají evidenční charakter a nevznikají za účelem výkonu veřejné správy
2.2.11 nadřazený pojem
IRI profilovaných vztahů	skos:broader
IRI	https://ofn.gov.cz/slovníky#Pojem.nadřazenýPojem
Název	nadřazený pojem
Definice	Významově širší pojem. Může se jednat o specializaci, instanciaci, partonomii, apod.
Definiční obor	Pojem
Obor hodnot	Pojem [0..*]
Hierarchie	
profiluje vlastnost has broader (@en) (skos:broader)
Definice: Broader concepts are typically rendered as parents in a concept hierarchy (tree).
specializuje vlastnost has broader transitive (@en) (skos:broaderTransitive)
Definice: skos:broaderTransitive is a transitive superproperty of skos:broader.
specializuje vlastnost is in semantic relation with (@en) (skos:semanticRelation)
Definice: Links a concept to a concept related by meaning.
2.2.12 název
IRI profilovaných vztahů	skos:prefLabel
IRI	https://ofn.gov.cz/slovníky#Pojem.název
Název	název
Definice	Název pojmu. Je unikátní v rámci názvů pojmů ve slovníku.
Definiční obor	Pojem [0..*]
Obor hodnot	Text [1..1]
Hierarchie	
profiluje vlastnost preferred label (@en) (skos:prefLabel)
Definice: skos:prefLabel, skos:altLabel and skos:hiddenLabel are pairwise disjoint properties.
specializuje vlastnost label (@en) (rdfs:label)
Definice: A human-readable name for the subject.
2.2.13 popis
IRI profilovaných vztahů	dcterms:description
IRI	https://ofn.gov.cz/slovníky#Pojem.popis
Název	popis
Definice	
Definiční obor	Pojem [0..*]
Obor hodnot	Text [0..1]
Hierarchie	
profiluje vlastnost Description (@en) (dcterms:description)
Definice: An account of the resource.
Popis použití v profilu	Popis pojmu.
2.2.14 související nelegislativní zdroj
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/související-nelegislativní-zdroj
IRI	https://ofn.gov.cz/slovníky#Pojem.souvisejícíNelegislativníZdroj
Název	související nelegislativní zdroj
Definice	Nelegislativní zdroj, který s daným pojmem souvisí.
Definiční obor	Pojem
Obor hodnot	Digitální objekt [0..*]
Hierarchie	
profiluje vlastnost související nelegislativní zdroj (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/související-nelegislativní-zdroj)
Definice: Nelegislativní zdroj, který s daným pojmem souvisí.
2.2.15 související ustanovení
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/související-ustanovení
IRI	https://ofn.gov.cz/slovníky#Pojem.souvisejícíUstanovení
Název	související ustanovení
Definice	Ustanovení právního předpisu, které s daným pojmem souvisí.
Definiční obor	Pojem
Obor hodnot	Ustanovení [0..*]
Hierarchie	
profiluje vlastnost související ustanovení (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/související-ustanovení)
Definice: Ustanovení právního předpisu, které s daným pojmem souvisí.
2.3 Slovník
IRI profilovaných tříd	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/slovník
IRI	https://ofn.gov.cz/slovníky#Slovník
Název	Slovník
Definice	Slovník je seskupení pojmů popisující vybranou věcnou oblast.
Hierarchie	
profiluje třídu Slovník (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/slovník)
Definice: Slovník je seskupení pojmů popisující vybranou věcnou oblast.
2.3.1 název
IRI profilovaných vztahů	skos:prefLabel
IRI	https://ofn.gov.cz/slovníky#Slovník.název
Název	název
Definice	skos:prefLabel, skos:altLabel and skos:hiddenLabel are pairwise disjoint properties. (@en)
Definiční obor	Slovník [0..*]
Obor hodnot	Text [1..1]
Hierarchie	
profiluje vlastnost preferred label (@en) (skos:prefLabel)
Definice: skos:prefLabel, skos:altLabel and skos:hiddenLabel are pairwise disjoint properties.
specializuje vlastnost label (@en) (rdfs:label)
Definice: A human-readable name for the subject.
2.3.2 okamžik poslední změny
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/okamžik-poslední-změny
IRI	https://ofn.gov.cz/slovníky#Slovník.okamžikPosledníZměny
Název	okamžik poslední změny
Definiční obor	Slovník
Obor hodnot	Časový okamžik [0..1]
Hierarchie	
profiluje vlastnost okamžik poslední změny (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/okamžik-poslední-změny)
2.3.3 okamžik vytvoření
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/okamžik-vytvoření
IRI	https://ofn.gov.cz/slovníky#Slovník.okamžikVytvoření
Název	okamžik vytvoření
Definiční obor	Slovník
Obor hodnot	Časový okamžik [0..1]
Hierarchie	
profiluje vlastnost okamžik vytvoření (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/okamžik-vytvoření)
2.3.4 popis
IRI profilovaných vztahů	dcterms:description
IRI	https://ofn.gov.cz/slovníky#Slovník.popis
Název	popis
Definice	An account of the resource. (@en)
Definiční obor	Slovník [0..*]
Obor hodnot	Text [0..1]
Hierarchie	
profiluje vlastnost Description (@en) (dcterms:description)
Definice: An account of the resource.
2.4 Tezaurus
IRI profilovaných tříd	skos:ConceptScheme
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/slovník
IRI	https://ofn.gov.cz/slovníky#Tezaurus
Název	Tezaurus
Definice	Tezaurus je nejjednodušším typem slovníku.
Hierarchie	
profiluje třídu Concept Scheme (@en) (skos:ConceptScheme)
Definice: A set of concepts, optionally including statements about semantic relationships between those concepts.
profiluje třídu Slovník (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/slovník)
Definice: Slovník je seskupení pojmů popisující vybranou věcnou oblast.
specializuje profil Slovník (https://ofn.gov.cz/slovníky#Slovník)
profiluje třídu Slovník (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/slovník)
Definice: Slovník je seskupení pojmů popisující vybranou věcnou oblast.
Zpětné asociace

z domény § 2.2 Pojem → § 2.2.7 je v tezauru
2.5 Třída
IRI profilovaných tříd	skos:Concept
owl:Class
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem
IRI	https://ofn.gov.cz/slovníky#Třída
Název	Třída
Definice	Pojem reprezentující typ subjektu nebo objektu práva. Třída pak může mít instance - konkrétní subjekty či objekty práva.
Hierarchie	
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Class (@en) (owl:Class)
Definice: The class of OWL classes.
specializuje třídu Class (@en) (rdfs:Class)
Definice: The class of classes.
specializuje třídu Resource (@en) (rdfs:Resource)
Definice: The class resource, everything.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
specializuje profil Pojem (https://ofn.gov.cz/slovníky#Pojem)
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
Zpětné asociace

z domény § 2.7 Vztah → § 2.7.1 definiční obor
z domény § 2.6 Vlastnost → § 2.6.1 definiční obor
z domény § 2.5 Třída → § 2.5.2 nadřazená třída
z domény § 2.7 Vztah → § 2.7.3 obor hodnot
2.5.1 má instance definované číselníkem
IRI profilovaných vztahů	https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-instance-definované-číselníkem
IRI	https://ofn.gov.cz/slovníky#Třída.máInstanceDefinovanéČíselníkem
Název	má instance definované číselníkem
Definice	Číselník, jehož položky jsou instancemi třídy.
Definiční obor	Třída
Obor hodnot	Číselník [0..1]
Hierarchie	
profiluje vlastnost má instance definované číselníkem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/má-instance-definované-číselníkem)
Definice: Číselník, jehož položky jsou instancemi třídy.
2.5.2 nadřazená třída
IRI profilovaných vztahů	rdfs:subClassOf
IRI	https://ofn.gov.cz/slovníky#Třída.nadřazenáTřída
Název	nadřazená třída
Definice	Významově širší třída. Platí, že každá instance třídy je také instancí nadřazené třídy. Tj. každá instance třídy Hrad je také instancí třídy Turistický cíl.
Definiční obor	Třída
Obor hodnot	Třída [0..*]
Hierarchie	
profiluje vlastnost subClassOf (@en) (rdfs:subClassOf)
Definice: The subject is a subclass of a class.
2.6 Vlastnost
IRI profilovaných tříd	skos:Concept
owl:DatatypeProperty
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem
IRI	https://ofn.gov.cz/slovníky#Vlastnost
Název	Vlastnost
Definice	Pojem reprezenutjící vlastnost, kterou může mít instance nějaké třídy.
Hierarchie	
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu DatatypeProperty (@en) (owl:DatatypeProperty)
Definice: The class of data properties.
specializuje třídu Property (@en) (rdf:Property)
Definice: The class of RDF properties.
specializuje třídu Resource (@en) (rdfs:Resource)
Definice: The class resource, everything.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
specializuje profil Pojem (https://ofn.gov.cz/slovníky#Pojem)
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
Zpětné asociace

z domény § 2.6 Vlastnost → § 2.6.2 nadřazená vlastnost
2.6.1 definiční obor
IRI profilovaných vztahů	rdfs:domain
IRI	https://ofn.gov.cz/slovníky#Vlastnost.definičníObor
Název	definiční obor
Definice	Definiční obor vlastnosti. Určuje třídu, jejíž instance mají danou vlastnost.
Definiční obor	Vlastnost
Obor hodnot	Třída [1..1]
Hierarchie	
profiluje vlastnost domain (@en) (rdfs:domain)
Definice: A domain of the subject property.
2.6.2 nadřazená vlastnost
IRI profilovaných vztahů	rdfs:subPropertyOf
IRI	https://ofn.gov.cz/slovníky#Vlastnost.nadřazenáVlastnost
Název	nadřazená vlastnost
Definice	Významově širší vlastnost. Pokud je vlastností přiřazena hodnota nějaké instanci třídy, pak je tato hodnota té samé instanci přiřazena i nadřazenou vlastností. Tj. každý název hradu lze zároveň inteprentovat jako název turistického cíle.
Definiční obor	Vlastnost
Obor hodnot	Vlastnost [0..*]
Hierarchie	
profiluje vlastnost subPropertyOf (@en) (rdfs:subPropertyOf)
Definice: The subject is a subproperty of a property.
2.6.3 obor hodnot
IRI profilovaných vztahů	rdfs:range
IRI	https://ofn.gov.cz/slovníky#Vlastnost.oborHodnot
Název	obor hodnot
Definice	Obor hodnot vlastnosti. Určuje datový typ specifikující, jakých hodnot může nabývat nějaká vlastnost.
Definiční obor	Vlastnost
Obor hodnot	Datový typ [1..1]
Hierarchie	
profiluje vlastnost range (@en) (rdfs:range)
Definice: A range of the subject property.
2.7 Vztah
IRI profilovaných tříd	skos:Concept
owl:ObjectProperty
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem
IRI	https://ofn.gov.cz/slovníky#Vztah
Název	Vztah
Definice	Pojem reprezentující vztah, kterým mohou být propojeny instance dvou tříd, nebo dvě instance stejné třídy.
Hierarchie	
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu ObjectProperty (@en) (owl:ObjectProperty)
Definice: The class of object properties.
specializuje třídu Property (@en) (rdf:Property)
Definice: The class of RDF properties.
specializuje třídu Resource (@en) (rdfs:Resource)
Definice: The class resource, everything.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
specializuje profil Pojem (https://ofn.gov.cz/slovníky#Pojem)
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
Zpětné asociace

z domény § 2.7 Vztah → § 2.7.2 nadřazený vztah
2.7.1 definiční obor
IRI profilovaných vztahů	rdfs:domain
IRI	https://ofn.gov.cz/slovníky#Vztah.definičníObor
Název	definiční obor
Definice	Definiční obor vztahu. Určuje třídu, jejímž instancím mohou být tímto vztahem přiřazovány instance jiné třídy - oboru hodnot.
Definiční obor	Vztah
Obor hodnot	Třída [1..1]
Hierarchie	
profiluje vlastnost domain (@en) (rdfs:domain)
Definice: A domain of the subject property.
2.7.2 nadřazený vztah
IRI profilovaných vztahů	rdfs:subPropertyOf
IRI	https://ofn.gov.cz/slovníky#Vztah.nadřazenýVztah
Název	nadřazený vztah
Definice	Významově širší vztah. Pokud jsou dvě instance tříd propojeny vztahem, pak jsou propojeny i nadřazeným vztahem. Tj. pokud hradu přiřadíme správce pomocí vztahu správce hradu, pak je tento správce hradu přiřazen i nadřazeným vztahem správce turistického cíle.
Definiční obor	Vztah
Obor hodnot	Vztah [0..*]
Hierarchie	
profiluje vlastnost subPropertyOf (@en) (rdfs:subPropertyOf)
Definice: The subject is a subproperty of a property.
2.7.3 obor hodnot
IRI profilovaných vztahů	rdfs:range
IRI	https://ofn.gov.cz/slovníky#Vztah.oborHodnot
Název	obor hodnot
Definice	Obor hodnot vztahu. Určuje třídu, jejíž instance mohou být tímto vztahem přiřazovány instancím jiné třídy - definičního oboru.
Definiční obor	Vztah
Obor hodnot	Třída [1..1]
Hierarchie	
profiluje vlastnost range (@en) (rdfs:range)
Definice: A range of the subject property.
3. Podpůrné profily třídy
3.1 Agenda
IRI profilovaných tříd	https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/agenda
IRI	https://ofn.gov.cz/slovníky#Agenda
Název	Agenda
Definice	Ucelená oblast působnosti orgánu veřejné moci nebo ucelená oblast působení soukromoprávního uživatele údajů.
Hierarchie	
profiluje třídu Agenda (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/agenda)
Definice: Ucelená oblast působnosti orgánu veřejné moci nebo ucelená oblast působení soukromoprávního uživatele údajů.
specializuje třídu Objekt práva (https://slovník.gov.cz/veřejný-sektor/pojem/objekt-práva)
Definice: Objekt práva je příčinou vstupu subjektu do právního vztahu.
Popis použití v profilu	Hodnoty jsou identifikátory agend z datové sady Agendy. [AGENDY]
Zpětné asociace

z domény § 3.9 Typ objektu práva → § 3.9.1 sdružuje údaje vedené nebo vytvářené v rámci agendy
z domény § 3.11 Typ subjektu práva → § 3.11.1 sdružuje údaje vedené nebo vytvářené v rámci agendy
3.2 Agendový informační systém
IRI profilovaných tříd	https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/agendový-informační-systém
IRI	https://ofn.gov.cz/slovníky#AgendovýInformačníSystém
Název	Agendový informační systém
Definice	Agendovým informačním systémem se rozumí informační systém veřejné správy, který slouží k výkonu agendy, využívání elektronických formulářů nebo elektronické identifikaci.
Hierarchie	
profiluje třídu Agendový informační systém (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/agendový-informační-systém)
Definice: Agendovým informačním systémem se rozumí informační systém veřejné správy, který slouží k výkonu agendy, využívání elektronických formulářů nebo elektronické identifikaci.
specializuje třídu Informační systém veřejné správy (https://slovník.gov.cz/legislativní/sbírka/365/2000/pojem/informační-systém-veřejné-správy)
Definice: Informačním systémem veřejné správy funkční celek nebo jeho část zabezpečující cílevědomou a systematickou informační činnost pro účely výkonu veřejné správy nebo plnění jiných funkcí státu anebo dalších veřejnoprávních korporací. Každý informační systém veřejné správy zahrnuje data, která jsou uspořádána tak, aby bylo možné jejich zpracování a zpřístupnění, provozní údaje a dále technické a programové prostředky, případně jiné nástroje umožňující výkon informačních činností
Popis použití v profilu	Hodnoty jsou identifikátory AIS z datové sady Agendy. [ISVS]
Zpětné asociace

z domény § 3.9 Typ objektu práva → § 3.9.2 údaje jsou v AIS
z domény § 3.11 Typ subjektu práva → § 3.11.2 údaje jsou v AIS
3.3 Časový okamžik
IRI profilovaných tříd	https://slovník.gov.cz/generický/čas/pojem/časový-okamžik
IRI	https://ofn.gov.cz/slovníky#ČasovýOkamžik
Název	Časový okamžik
Definice	Pro reprezentaci časových okamžiků lze použít datum, čas a nebo kombinací data a času. Pokud je jasné, který datový typ je v daném místě vhodný, použije se konkrétní datový typ, tedy datum, čas či datum a čas. Často ale při tvorbě OFN není předem známo, jaká úroveň detailu bude pro určení okamžiku k dispozici. Aby se zabránilo různým reprezentacím této situace v různých OFN, je specifikována třída Časový okamžik.
Hierarchie	
profiluje třídu Časový okamžik (https://slovník.gov.cz/generický/čas/pojem/časový-okamžik)
Definice: Pro reprezentaci časových okamžiků lze použít datum, čas a nebo kombinací data a času. Pokud je jasné, který datový typ je v daném místě vhodný, použije se konkrétní datový typ, tedy datum, čas či datum a čas. Často ale při tvorbě OFN není předem známo, jaká úroveň detailu bude pro určení okamžiku k dispozici. Aby se zabránilo různým reprezentacím této situace v různých OFN, je specifikována třída Časový okamžik.
Zpětné asociace

z domény § 2.3 Slovník → § 2.3.2 okamžik poslední změny
z domény § 2.3 Slovník → § 2.3.3 okamžik vytvoření
3.3.1 datum
IRI profilovaných vztahů	https://slovník.gov.cz/generický/čas/pojem/datum
IRI	https://ofn.gov.cz/slovníky#ČasovýOkamžik.datum
Název	datum
Definice	Datum okamžiku.
Definiční obor	Časový okamžik [0..*]
Obor hodnot	xsd:date [0..1]
Hierarchie	
profiluje vlastnost datum (https://slovník.gov.cz/generický/čas/pojem/datum)
Definice: Datum okamžiku.
3.3.2 datum a čas
IRI profilovaných vztahů	https://slovník.gov.cz/generický/čas/pojem/datum-a-čas
IRI	https://ofn.gov.cz/slovníky#ČasovýOkamžik.datumAČas
Název	datum a čas
Definice	Datum a čas začátku okamžiku.
Definiční obor	Časový okamžik [0..*]
Obor hodnot	xsd:dateTimeStamp [0..1]
Hierarchie	
profiluje vlastnost datum a čas (https://slovník.gov.cz/generický/čas/pojem/datum-a-čas)
Definice: Datum a čas začátku okamžiku.
3.3.3 je nespecifikovaný
IRI profilovaných vztahů	https://slovník.gov.cz/generický/čas/pojem/je-nespecifikovaný
IRI	https://ofn.gov.cz/slovníky#ČasovýOkamžik.jeNespecifikovaný
Název	je nespecifikovaný
Definice	Nespecifikovaný časový okamžik, u kterého se ví, že jeho hodnota je neznámá. Jedná se o pro interoperabilitu výrazně lepší variantu, než si neznámou hodnotou uměle stanovit na 3333-03-03 či 9999-09-09 apod. nebo hodnotu vynechat.
Definiční obor	Časový okamžik [0..*]
Obor hodnot	xsd:boolean [0..1]
Hierarchie	
profiluje vlastnost je nespecifikovaný (https://slovník.gov.cz/generický/čas/pojem/je-nespecifikovaný)
Definice: Nespecifikovaný časový okamžik, u kterého se ví, že jeho hodnota je neznámá. Jedná se o pro interoperabilitu výrazně lepší variantu, než si neznámou hodnotou uměle stanovit na 3333-03-03 či 9999-09-09 apod. nebo hodnotu vynechat.
3.4 Číselník
IRI profilovaných tříd	https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/číselník
IRI	https://ofn.gov.cz/slovníky#Číselník
Název	Číselník
Definice	Číselník. Jeho identifikátorem (IRI) je IRI číselníku dle OFN Číselníky.
Hierarchie	
profiluje třídu Číselník (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/číselník)
Zpětné asociace

z domény § 2.5 Třída → § 2.5.1 má instance definované číselníkem
3.4.1 má v NKOD zastřešující datovou sadu
IRI profilovaných vztahů	https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/má-v-nkod-zastřešující-datovou-sadu
IRI	https://ofn.gov.cz/slovníky#Číselník.máVNkodZastřešujícíDatovouSadu
Název	má v NKOD zastřešující datovou sadu
Definiční obor	Číselník [0..1]
Obor hodnot	Datová sada v NKOD [1..1]
Hierarchie	
profiluje vlastnost má v NKOD zastřešující datovou sadu (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/má-v-nkod-zastřešující-datovou-sadu)
3.5 Datová sada v NKOD
IRI profilovaných tříd	https://slovník.gov.cz/veřejný-sektor/pojem/datová-sada
IRI	https://ofn.gov.cz/slovníky#DatováSadaNKOD
Název	Datová sada v NKOD
Definice	Zastřešující datová sada v NKOD reprezentující číselník. Je to datová série, jejímiž prvky jsou datové sady reprezentující jednotlivé verze číselníku.
Hierarchie	
profiluje třídu Datová sada (https://slovník.gov.cz/veřejný-sektor/pojem/datová-sada)
Definice: Datová sada označuje množinu souvisejících dat.
Popis použití v profilu	Hodnotou jsou identifikátory datových sad z Národního katalogu otevřených dat. [NKOD]
Zpětné asociace

z domény § 3.4 Číselník → § 3.4.1 má v NKOD zastřešující datovou sadu
3.6 Datový typ
IRI profilovaných tříd	rdfs:Datatype
IRI	https://ofn.gov.cz/slovníky#DatovýTyp
Název	Datový typ
Definice	Datový typ specifikující, jakých hodnot může nabývat nějaká vlastnost. Jejich přehled spolu s užitím v jednotlivých datových formátech je v OFN Základní datové typy. Datové typy jsou identifikovány jejich IRI.
Hierarchie	
profiluje třídu Datatype (@en) (rdfs:Datatype)
Definice: The class of RDF datatypes.
specializuje třídu Class (@en) (rdfs:Class)
Definice: The class of classes.
specializuje třídu Resource (@en) (rdfs:Resource)
Definice: The class resource, everything.
Zpětné asociace

z domény § 2.6 Vlastnost → § 2.6.3 obor hodnot
3.7 Digitální objekt
IRI profilovaných tříd	https://slovník.gov.cz/generický/digitální-objekty/pojem/digitální-objekt
IRI	https://ofn.gov.cz/slovníky#digitální-objekt
Název	Digitální objekt
Definice	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Hierarchie	
profiluje třídu Digitální objekt (https://slovník.gov.cz/generický/digitální-objekty/pojem/digitální-objekt)
Definice: Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
specializuje třídu Věc (https://slovník.gov.cz/generický/věci/pojem/věc)
Zpětné asociace

z domény § 2.2 Pojem → § 2.2.3 definující nelegislativní zdroj
z domény § 2.2 Pojem → § 2.2.14 související nelegislativní zdroj
3.7.1 název
IRI profilovaných vztahů	dcterms:title
IRI	https://ofn.gov.cz/slovníky#DigitálníObjekt.název
Název	název
Definice	Název digitálního objektu
Definiční obor	Digitální objekt [0..*]
Obor hodnot	Text [0..1]
Hierarchie	
profiluje vlastnost Title (@en) (dcterms:title)
Definice: A name given to the resource.
3.7.2 popis
IRI profilovaných vztahů	dcterms:description
IRI	https://ofn.gov.cz/slovníky#DigitálníObjekt.popis
Název	popis
Definice	Popis digitálního objektu.
Definiční obor	Digitální objekt [0..*]
Obor hodnot	Text [0..1]
Hierarchie	
profiluje vlastnost Description (@en) (dcterms:description)
Definice: An account of the resource.
3.7.3 URL ke stažení
IRI profilovaných vztahů	http://schema.org/url
IRI	https://ofn.gov.cz/slovníky#DigitálníObjekt.urlKeStažení
Název	URL ke stažení
Definice	URL, ze kterého může být stažen digitální objekt
Definiční obor	Digitální objekt [0..*]
Obor hodnot	xsd:anyURI [0..1]
Hierarchie	
profiluje vlastnost url (@en) (http://schema.org/url)
Definice: URL of the item.
3.8 Neveřejný údaj
IRI profilovaných tříd	https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/neveřejný-údaj
skos:Concept
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem
IRI	https://ofn.gov.cz/slovníky#NeveřejnýÚdaj
Název	Neveřejný údaj
Hierarchie	
profiluje třídu Neveřejný údaj (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/neveřejný-údaj)
specializuje třídu Údaj (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/údaj)
Definice: Údaj vedený v základních registrech nebo v jiných agendových informačních systémech zpřístupněný prostřednictvím informačního systému základních registrů nebo referenčních rozhraní pro výkon agend. Nejedná se o specifikaci hodnoty konkrétního objektu či subjektu údajů, ale o specifikaci na úrovni typu údaje vedeného o objektu či subjektu údajů.
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
specializuje profil Pojem (https://ofn.gov.cz/slovníky#Pojem)
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
3.8.1 je vymezen ustanovením stanovujícím jeho neveřejnost
IRI profilovaných vztahů	https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/je-vymezen-ustanovením-stanovujícím-jeho-neveřejnost
IRI	https://ofn.gov.cz/slovníky#NeveřejnýÚdaj.jeVymezenUstanovenímStanovujícímJehoNeveřejnost
Název	je vymezen ustanovením stanovujícím jeho neveřejnost
Definice	U neveřejného údaje je třeba odkázat na ustanovení, ze kterého jeho neveřejnost vyplývá.
Definiční obor	Neveřejný údaj
Obor hodnot	Ustanovení [1..*]
Hierarchie	
profiluje vlastnost je vymezen ustanovením stanovujícím jeho neveřejnost (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/je-vymezen-ustanovením-stanovujícím-jeho-neveřejnost)
3.9 Typ objektu práva
IRI profilovaných tříd	skos:Concept
https://slovník.gov.cz/veřejný-sektor/pojem/typ-objektu-práva
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem
IRI	https://ofn.gov.cz/slovníky#TypObjektuPráva
Název	Typ objektu práva
Definice	Typ jehož instance jsou podtřídami Objektu práva.
Hierarchie	
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Typ objektu práva (https://slovník.gov.cz/veřejný-sektor/pojem/typ-objektu-práva)
Definice: Typ jehož instance jsou podtřídami Objektu práva.
specializuje třídu Typ objektu (https://slovník.gov.cz/základní/pojem/typ-objektu)
Definice: Typ objektu (typ[objekt]) popisuje kategorii která může být objektu přiřazena. Příklady instancí: konkrétní typ letadla (Airbus 380), objekt/subjekt RPP (např. malé plavidlo),
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
specializuje profil Pojem (https://ofn.gov.cz/slovníky#Pojem)
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
3.9.1 sdružuje údaje vedené nebo vytvářené v rámci agendy
IRI profilovaných vztahů	https://slovník.gov.cz/agendový/104/pojem/sdružuje-údaje-vedené-nebo-vytvářené-v-rámci-agendy
IRI	https://ofn.gov.cz/slovníky#TypObjektuPráva.sdružujeÚdajeVedenéNeboVytvářenéVRámciAgendy
Název	sdružuje údaje vedené nebo vytvářené v rámci agendy
Definice	Přiřazuje subjektu nebo objektu údajů agendu v níž jsou údaje sdružené v subjektu nebo objektu údajů vedeny nebo vytvářeny. Subjekt nebo objekt údajů je veden nebo vytvářen v právě jedné agendě. V jedné agendě může být vedeno nebo vytvářeno více různých subjektů nebo objektů údajů.
Definiční obor	Typ objektu práva
Obor hodnot	Agenda [0..1]
Hierarchie	
profiluje vlastnost Sdružuje údaje vedené nebo vytvářené v rámci agendy (https://slovník.gov.cz/agendový/104/pojem/sdružuje-údaje-vedené-nebo-vytvářené-v-rámci-agendy)
Definice: Přiřazuje subjektu nebo objektu údajů agendu v níž jsou údaje sdružené v subjektu nebo objektu údajů vedeny nebo vytvářeny. Subjekt nebo objekt údajů je veden nebo vytvářen v právě jedné agendě. V jedné agendě může být vedeno nebo vytvářeno více různých subjektů nebo objektů údajů.
3.9.2 údaje jsou v AIS
IRI profilovaných vztahů	https://slovník.gov.cz/agendový/104/pojem/údaje-jsou-v-ais
IRI	https://ofn.gov.cz/slovníky#TypObjektuPráva.údajeJsouVAis
Název	údaje jsou v AIS
Definiční obor	Typ objektu práva
Obor hodnot	Agendový informační systém [0..1]
Hierarchie	
profiluje vlastnost údaje jsou v AIS (https://slovník.gov.cz/agendový/104/pojem/údaje-jsou-v-ais)
3.10 Typ obsahu údaje
IRI profilovaných tříd	https://slovník.gov.cz/legislativní/sbírka/360/2023/pojem/typ-obsahu-údaje
IRI	https://ofn.gov.cz/slovníky#TypObsahuÚdaje
Název	Typ obsahu údaje
Definice	Orgán veřejné správy strukturuje data vedená v informačním systému podle jejich obsahu na údaje: a) identifikační: údaje, které, které samostatně nebo ve skupině identifikují konkrétní subjekt práva b) evidenční: údaje, které neidentifikují konkrétní subjekt práva, ale váží se k subjektu nebo objektu práva v rámci agendy a evidence, která se v ní vede c) statistické: údaje, které seskupují a formou anonymizace či pseudonymizace zamezují vazbě konkrétní subjekt práva
Hierarchie	
profiluje třídu Typ obsahu údaje (https://slovník.gov.cz/legislativní/sbírka/360/2023/pojem/typ-obsahu-údaje)
Definice: Orgán veřejné správy strukturuje data vedená v informačním systému podle jejich obsahu na údaje: a) identifikační: údaje, které, které samostatně nebo ve skupině identifikují konkrétní subjekt práva b) evidenční: údaje, které neidentifikují konkrétní subjekt práva, ale váží se k subjektu nebo objektu práva v rámci agendy a evidence, která se v ní vede c) statistické: údaje, které seskupují a formou anonymizace či pseudonymizace zamezují vazbě konkrétní subjekt práva
specializuje třídu Položka číselníku (https://slovník.gov.cz/datový/číselníky/pojem/položka-číselníku)
Definice: Položka číselníku reprezentuje jednu přípustnou hodnotu datového prvku z množiny všech přípustných hodnot, které jsou kódovány číselníkem, do kterého položka patří.
Popis použití v profilu	Hodnoty z Číselníku typů obsahu údajů v ISVS dle § 23, odst. 3, vyhlášky č. 360/2023 Sb. [P23-O3-360-2023]
Zpětné asociace

z domény § 2.2 Pojem → § 2.2.8 má typ obsahu údaje
3.11 Typ subjektu práva
IRI profilovaných tříd	skos:Concept
https://slovník.gov.cz/veřejný-sektor/pojem/typ-subjektu-práva
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem
IRI	https://ofn.gov.cz/slovníky#TypSubjektuPráva
Název	Typ subjektu práva
Definice	Typ jehož instance jsou podtřídami Subjektu práva.
Hierarchie	
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Typ subjektu práva (https://slovník.gov.cz/veřejný-sektor/pojem/typ-subjektu-práva)
Definice: Typ jehož instance jsou podtřídami Subjektu práva.
specializuje třídu Typ objektu (https://slovník.gov.cz/základní/pojem/typ-objektu)
Definice: Typ objektu (typ[objekt]) popisuje kategorii která může být objektu přiřazena. Příklady instancí: konkrétní typ letadla (Airbus 380), objekt/subjekt RPP (např. malé plavidlo),
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
specializuje profil Pojem (https://ofn.gov.cz/slovníky#Pojem)
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
3.11.1 sdružuje údaje vedené nebo vytvářené v rámci agendy
IRI profilovaných vztahů	https://slovník.gov.cz/agendový/104/pojem/sdružuje-údaje-vedené-nebo-vytvářené-v-rámci-agendy
IRI	https://ofn.gov.cz/slovníky#TypSubjektuPráva.sdružujeÚdajeVedenéNeboVytvářenéVRámciAgendy
Název	sdružuje údaje vedené nebo vytvářené v rámci agendy
Definice	Přiřazuje subjektu nebo objektu údajů agendu v níž jsou údaje sdružené v subjektu nebo objektu údajů vedeny nebo vytvářeny. Subjekt nebo objekt údajů je veden nebo vytvářen v právě jedné agendě. V jedné agendě může být vedeno nebo vytvářeno více různých subjektů nebo objektů údajů.
Definiční obor	Typ subjektu práva
Obor hodnot	Agenda [0..1]
Hierarchie	
profiluje vlastnost Sdružuje údaje vedené nebo vytvářené v rámci agendy (https://slovník.gov.cz/agendový/104/pojem/sdružuje-údaje-vedené-nebo-vytvářené-v-rámci-agendy)
Definice: Přiřazuje subjektu nebo objektu údajů agendu v níž jsou údaje sdružené v subjektu nebo objektu údajů vedeny nebo vytvářeny. Subjekt nebo objekt údajů je veden nebo vytvářen v právě jedné agendě. V jedné agendě může být vedeno nebo vytvářeno více různých subjektů nebo objektů údajů.
3.11.2 údaje jsou v AIS
IRI profilovaných vztahů	https://slovník.gov.cz/agendový/104/pojem/údaje-jsou-v-ais
IRI	https://ofn.gov.cz/slovníky#TypSubjektuPráva.údajeJsouVAis
Název	údaje jsou v AIS
Definiční obor	Typ subjektu práva
Obor hodnot	Agendový informační systém [0..1]
Hierarchie	
profiluje vlastnost údaje jsou v AIS (https://slovník.gov.cz/agendový/104/pojem/údaje-jsou-v-ais)
3.12 Ustanovení
IRI profilovaných tříd	https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/ustanovení-právního-předpisu
http://data.europa.eu/eli/ontology#LegalResource
IRI	https://ofn.gov.cz/slovníky#Ustanovení
Název	Ustanovení
Definice	Ustanovení právního předpisu je identifikovatelná součást právního předpisu, např. jeho paragraf, odstavec nebo písmeno.
Hierarchie	
profiluje třídu Ustanovení právního předpisu (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/ustanovení-právního-předpisu)
Definice: Ustanovení právního předpisu je identifikovatelná součást právního předpisu, např. jeho paragraf, odstavec nebo písmeno.
profiluje třídu Legal Resource (@en) (http://data.europa.eu/eli/ontology#LegalResource)
Definice: A work in a legislative corpus. This applies to acts that have been legally enacted (whether or not they are still in force). For example, the abstract concept of the legal resource; e.g. "act 3 of 2005" (adapted from Akoma Ntoso) A legal resource can represent a legal act or any component of a legal act, like an article. Legal resources can be linked together using properties defined in the model. Note that ELI ontology accommodates different point of view on what should be considered a new legal resource, or a new legal expression of the same resource. Typically, a consolidated version can be viewed, in the context of ELI, either as separate legal resource (linked to original version and previous consolidated version using corresponding ELI relations), or as a different legal expression of the same legal resource.
specializuje třídu Work (@en) (http://data.europa.eu/eli/ontology#Work)
Definice: Any distinct intellectual creation (i.e., the intellectual content), in the context of ELI. The substance of Work is ideas.
specializuje třídu beze jména (http://iflastandards.info/ns/fr/frbr/frbroo/F1_Work)
Zpětné asociace

z domény § 2.2 Pojem → § 2.2.4 definující ustanovení
z domény § 3.8 Neveřejný údaj → § 3.8.1 je vymezen ustanovením stanovujícím jeho neveřejnost
z domény § 2.2 Pojem → § 2.2.15 související ustanovení
3.13 Veřejný údaj
IRI profilovaných tříd	https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/veřejný-údaj
skos:Concept
https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem
IRI	https://ofn.gov.cz/slovníky#VeřejnýÚdaj
Název	Veřejný údaj
Hierarchie	
profiluje třídu Veřejný údaj (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/veřejný-údaj)
specializuje třídu Údaj (https://slovník.gov.cz/legislativní/sbírka/111/2009/pojem/údaj)
Definice: Údaj vedený v základních registrech nebo v jiných agendových informačních systémech zpřístupněný prostřednictvím informačního systému základních registrů nebo referenčních rozhraní pro výkon agend. Nejedná se o specifikaci hodnoty konkrétního objektu či subjektu údajů, ale o specifikaci na úrovni typu údaje vedeného o objektu či subjektu údajů.
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
specializuje profil Pojem (https://ofn.gov.cz/slovníky#Pojem)
profiluje třídu Concept (@en) (skos:Concept)
Definice: An idea or notion; a unit of thought.
profiluje třídu Pojem (https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/pojem)
Definice: Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
3.14 Způsob sdílení údaje
IRI profilovaných tříd	https://slovník.gov.cz/legislativní/sbírka/360/2023/pojem/způsob-sdílení-údaje
IRI	https://ofn.gov.cz/slovníky#ZpůsobSdíleníÚdaje
Název	Způsob sdílení údaje
Definice	Orgán veřejné správy strukturuje data vedená v informačním systému podle způsobu jejich sdílení na údaje: a) veřejně přístupné: údaje publikované veřejně ve formě otevřených dat či jakkoliv jinak b) poskytované na žádost: údaje poskytované na žádost subjektu práva nebo na základě zákona o svobodném přístupu k informacím c) zpřístupňované pro výkon agendy: údaje sdílené jiným agendám, které mají oprávněný zájem je využívat pro výkon své působnosti d) nesdílené: údaje, které nejsou sdílené žádným z předchozích způsobů
Hierarchie	
profiluje třídu Způsob sdílení údaje (https://slovník.gov.cz/legislativní/sbírka/360/2023/pojem/způsob-sdílení-údaje)
Definice: Orgán veřejné správy strukturuje data vedená v informačním systému podle způsobu jejich sdílení na údaje: a) veřejně přístupné: údaje publikované veřejně ve formě otevřených dat či jakkoliv jinak b) poskytované na žádost: údaje poskytované na žádost subjektu práva nebo na základě zákona o svobodném přístupu k informacím c) zpřístupňované pro výkon agendy: údaje sdílené jiným agendám, které mají oprávněný zájem je využívat pro výkon své působnosti d) nesdílené: údaje, které nejsou sdílené žádným z předchozích způsobů
specializuje třídu Položka číselníku (https://slovník.gov.cz/datový/číselníky/pojem/položka-číselníku)
Definice: Položka číselníku reprezentuje jednu přípustnou hodnotu datového prvku z množiny všech přípustných hodnot, které jsou kódovány číselníkem, do kterého položka patří.
Popis použití v profilu	Hodnoty z Číselníku způsobů sdílení údajů v ISVS dle § 23, odst. 2, vyhlášky č. 360/2023 Sb. [P23-O2-360-2023]
Zpětné asociace

z domény § 2.2 Pojem → § 2.2.9 má způsob sdílení údaje
3.15 Způsob získání údaje
IRI profilovaných tříd	https://slovník.gov.cz/legislativní/sbírka/360/2023/pojem/způsob-získání-údaje
IRI	https://ofn.gov.cz/slovníky#ZpůsobZískáníÚdaje
Název	Způsob získání údaje
Definice	Orgán veřejné správy strukturuje data vedená v informačním systému na údaje následujících kategorií: a) základních registrů: údaje čerpané pro výkon agendy ze základních registrů b) jiných agend: údaje získávané pro výkon agendy od jiných úřadů c) vlastní: údaje vznikající při výkonu agendy, které mají evidenční charakter, tedy vztahují se k objektu nebo subjektu práva za účelem výkonu veřejné správy d) provozní: údaje vznikající při výkonu agendy, které nemají evidenční charakter a nevznikají za účelem výkonu veřejné správy
Hierarchie	
profiluje třídu Způsob získání údaje (https://slovník.gov.cz/legislativní/sbírka/360/2023/pojem/způsob-získání-údaje)
Definice: Orgán veřejné správy strukturuje data vedená v informačním systému na údaje následujících kategorií: a) základních registrů: údaje čerpané pro výkon agendy ze základních registrů b) jiných agend: údaje získávané pro výkon agendy od jiných úřadů c) vlastní: údaje vznikající při výkonu agendy, které mají evidenční charakter, tedy vztahují se k objektu nebo subjektu práva za účelem výkonu veřejné správy d) provozní: údaje vznikající při výkonu agendy, které nemají evidenční charakter a nevznikají za účelem výkonu veřejné správy
specializuje třídu Položka číselníku (https://slovník.gov.cz/datový/číselníky/pojem/položka-číselníku)
Definice: Položka číselníku reprezentuje jednu přípustnou hodnotu datového prvku z množiny všech přípustných hodnot, které jsou kódovány číselníkem, do kterého položka patří.
Popis použití v profilu	Hodnoty z Číselníku způsobů získání údajů v ISVS dle § 23, odst. 1, vyhlášky č. 360/2023 Sb. [P23-O1-360-2023]
Zpětné asociace

z domény § 2.2 Pojem → § 2.2.10 má způsob získání údaje
4. Vlastnosti
4.1 Je sdílen v propojeném datovém fondu
IRI	https://slovník.gov.cz/agendový/104/pojem/je-sdílen-v-propojeném-datovém-fondu
Název	Je sdílen v propojeném datovém fondu
Definiční obor	
Obor hodnot	xsd:boolean
5. Specifikace struktury pro Slovník
Slovník je seskupení pojmů popisující vybranou věcnou oblast.

5.1 JSON struktura pro Slovník
IRI
https://ofn.gov.cz/slovníky/2026-02-26/slovník/schéma.json
Definováno v
../slovník/schéma.json
Verze použitého jazyka
2020-12 (metaschema IRI: https://json-schema.org/draft/2020-12/schema)
Kořen
Kořenem JSON schématu je § 5.1.1 Objekt Slovník
5.1.1 Objekt Slovník
Popis	Slovník je seskupení pojmů popisující vybranou věcnou oblast.
Interpretace	Slovník
objekt s vlastnostmi (properties):
@context: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
pole hodnot {0..*} typu řetězec (formát: iri) a musí obsahovat: "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Slovník"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Slovník"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
vytvořeno: (okamžik vytvoření) nepovinná položka typu § 5.1.2 Objekt Časový okamžik
aktualizováno: (okamžik poslední změny) nepovinná položka typu § 5.1.2 Objekt Časový okamžik
5.1.2 Objekt Časový okamžik
Popis	Pro reprezentaci časových okamžiků lze použít datum, čas a nebo kombinací data a času. Pokud je jasné, který datový typ je v daném místě vhodný, použije se konkrétní datový typ, tedy datum, čas či datum a čas. Často ale při tvorbě OFN není předem známo, jaká úroveň detailu bude pro určení okamžiku k dispozici. Aby se zabránilo různým reprezentacím této situace v různých OFN, je specifikována třída Časový okamžik.
Interpretace	Časový okamžik
objekt s vlastnostmi (properties):
iri: nepovinná položka typu řetězec (formát: iri)
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Časový okamžik"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Časový okamžik"
je_nespecifikovaný: (je nespecifikovaný) nepovinná položka typu boolean (ano/ne)
datum_a_čas: (datum a čas) nepovinná položka typu řetězec (formát: date-time)
datum: (datum) nepovinná položka typu řetězec (formát: date)
5.1.3 Objekt Časový okamžik
Popis	Pro reprezentaci časových okamžiků lze použít datum, čas a nebo kombinací data a času. Pokud je jasné, který datový typ je v daném místě vhodný, použije se konkrétní datový typ, tedy datum, čas či datum a čas. Často ale při tvorbě OFN není předem známo, jaká úroveň detailu bude pro určení okamžiku k dispozici. Aby se zabránilo různým reprezentacím této situace v různých OFN, je specifikována třída Časový okamžik.
Interpretace	Časový okamžik
objekt s vlastnostmi (properties):
iri: nepovinná položka typu řetězec (formát: iri)
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Časový okamžik"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Časový okamžik"
je_nespecifikovaný: (je nespecifikovaný) nepovinná položka typu boolean (ano/ne)
datum_a_čas: (datum a čas) nepovinná položka typu řetězec (formát: date-time)
datum: (datum) nepovinná položka typu řetězec (formát: date)
6. Specifikace struktury pro Tezaurus
Datová struktura pro Tezaurus. Tezaurus je nejjednodušším typem slovníku.

6.1 JSON struktura pro Tezaurus
IRI
https://ofn.gov.cz/slovníky/2026-02-26/tezaurus/schéma.json
Definováno v
../tezaurus/schéma.json
Verze použitého jazyka
2020-12 (metaschema IRI: https://json-schema.org/draft/2020-12/schema)
Kořen
Kořenem JSON schématu je § 6.1.1 Objekt Tezaurus
6.1.1 Objekt Tezaurus
Popis	Tezaurus je nejjednodušším typem slovníku.
Interpretace	Tezaurus
objekt s vlastnostmi (properties):
@context: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
pole hodnot {0..*} typu řetězec (formát: iri) a musí obsahovat: "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Tezaurus", "Slovník"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
vytvořeno: (okamžik vytvoření) nepovinná položka typu § 6.1.5 Objekt Časový okamžik
aktualizováno: (okamžik poslední změny) nepovinná položka typu § 6.1.5 Objekt Časový okamžik
pojmy: (§ 2.2.7 je v tezauru) nepovinná položka typu pole hodnot {0..*} typu § 6.1.2 Objekt Pojem
6.1.2 Objekt Pojem
Popis	Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
Interpretace	Pojem
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
alternativní-název: (alternativní název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu pole hodnot {0..*} typu řetězec
en: nepovinná položka typu pole hodnot {0..*} typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definice: (definice) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definující-ustanovení-právního-předpisu: (definující ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
související-ustanovení-právního-předpisu: (související ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
definující-nelegislativní-zdroj: (definující nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 6.1.3 Objekt Digitální objekt
související-nelegislativní-zdroj: (související nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 6.1.3 Objekt Digitální objekt
ekvivalentní-pojem: (ekvivalentní pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
nadřazený-pojem: (nadřazený pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
6.1.3 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
6.1.4 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
6.1.5 Objekt Časový okamžik
Popis	Pro reprezentaci časových okamžiků lze použít datum, čas a nebo kombinací data a času. Pokud je jasné, který datový typ je v daném místě vhodný, použije se konkrétní datový typ, tedy datum, čas či datum a čas. Často ale při tvorbě OFN není předem známo, jaká úroveň detailu bude pro určení okamžiku k dispozici. Aby se zabránilo různým reprezentacím této situace v různých OFN, je specifikována třída Časový okamžik.
Interpretace	Časový okamžik
objekt s vlastnostmi (properties):
iri: nepovinná položka typu řetězec (formát: iri)
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Časový okamžik"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Časový okamžik"
je_nespecifikovaný: (je nespecifikovaný) nepovinná položka typu boolean (ano/ne)
datum_a_čas: (datum a čas) nepovinná položka typu řetězec (formát: date-time)
datum: (datum) nepovinná položka typu řetězec (formát: date)
6.1.6 Objekt Časový okamžik
Popis	Pro reprezentaci časových okamžiků lze použít datum, čas a nebo kombinací data a času. Pokud je jasné, který datový typ je v daném místě vhodný, použije se konkrétní datový typ, tedy datum, čas či datum a čas. Často ale při tvorbě OFN není předem známo, jaká úroveň detailu bude pro určení okamžiku k dispozici. Aby se zabránilo různým reprezentacím této situace v různých OFN, je specifikována třída Časový okamžik.
Interpretace	Časový okamžik
objekt s vlastnostmi (properties):
iri: nepovinná položka typu řetězec (formát: iri)
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Časový okamžik"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Časový okamžik"
je_nespecifikovaný: (je nespecifikovaný) nepovinná položka typu boolean (ano/ne)
datum_a_čas: (datum a čas) nepovinná položka typu řetězec (formát: date-time)
datum: (datum) nepovinná položka typu řetězec (formát: date)
7. Specifikace struktury pro Konceptuální model
Datová struktura pro Konceptuální model. Na této úrovni rozlišujeme pojmy, které reprezentují - třídy reprezentující typy subjektů a objektů práva, - vztahy mezi dvěma subjekty či objekty práva, - vlastnosti subjektů a objektů práva.

7.1 JSON struktura pro Konceptuální model
IRI
https://ofn.gov.cz/slovníky/2026-02-26/konceptuální-model/schéma.json
Definováno v
../konceptuální-model/schéma.json
Verze použitého jazyka
2020-12 (metaschema IRI: https://json-schema.org/draft/2020-12/schema)
Kořen
Kořenem JSON schématu je § 7.1.1 Objekt Konceptuální model
7.1.1 Objekt Konceptuální model
Popis	Na této úrovni rozlišujeme pojmy, které reprezentují - třídy reprezentující typy subjektů a objektů práva, - vztahy mezi dvěma subjekty či objekty práva, - vlastnosti subjektů a objektů práva.
Interpretace	Konceptuální model
objekt s vlastnostmi (properties):
@context: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
pole hodnot {0..*} typu řetězec (formát: iri) a musí obsahovat: "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Tezaurus", "Konceptuální model", "Slovník"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
pojmy: (§ 2.2.7 je v tezauru) nepovinná položka typu pole hodnot {0..*} typu alespoň jedno z následujících (anyOf):
§ 7.1.4 Objekt Třída
§ 7.1.3 Objekt Vztah
§ 7.1.2 Objekt Vlastnost
7.1.2 Objekt Vlastnost
Popis	Pojem reprezenutjící vlastnost, kterou může mít instance nějaké třídy.
Interpretace	Vlastnost
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Vlastnost", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
obor-hodnot: (obor hodnot) povinná položka typu řetězec (formát: iri)
definiční-obor: (definiční obor) povinná položka typu řetězec (formát: iri)
nadřazená-vlastnost: (nadřazená vlastnost) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
7.1.3 Objekt Vztah
Popis	Pojem reprezentující vztah, kterým mohou být propojeny instance dvou tříd, nebo dvě instance stejné třídy.
Interpretace	Vztah
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Vztah", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
obor-hodnot: (obor hodnot) povinná položka typu řetězec (formát: iri)
definiční-obor: (definiční obor) povinná položka typu řetězec (formát: iri)
nadřazený-vztah: (nadřazený vztah) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
7.1.4 Objekt Třída
Popis	Pojem reprezentující typ subjektu nebo objektu práva. Třída pak může mít instance - konkrétní subjekty či objekty práva.
Interpretace	Třída
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Třída", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
nadřazená-třída: (nadřazená třída) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
instance-definovány-číselníkem: (má instance definované číselníkem) nepovinná položka typu § 7.1.5 Objekt Číselník
7.1.5 Objekt Číselník
Popis	Číselník. Jeho identifikátorem (IRI) je IRI číselníku dle OFN Číselníky.
Interpretace	Číselník
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Číselník"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Číselník"
datová-sada-v-nkod: (má v NKOD zastřešující datovou sadu) povinná položka typu řetězec (formát: iri) (dle regulárního výrazu: ^https://data\.gov\.cz/zdroj/datové-sady/.*$)
8. Specifikace struktury pro Anotace pro registr práv a povinností
Datová struktura pro Tezaurus s anotacemi pro registr práv a povinností.

8.1 JSON struktura pro Anotace pro registr práv a povinností
IRI
https://ofn.gov.cz/slovníky/2026-02-26/rpp/schéma.json
Definováno v
../rpp/schéma.json
Verze použitého jazyka
2020-12 (metaschema IRI: https://json-schema.org/draft/2020-12/schema)
Kořen
Kořenem JSON schématu je § 8.1.1 Objekt Tezaurus
8.1.1 Objekt Tezaurus
Popis	Tezaurus je nejjednodušším typem slovníku.
Interpretace	Tezaurus
objekt s vlastnostmi (properties):
@context: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
pole hodnot {0..*} typu řetězec (formát: iri) a musí obsahovat: "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Tezaurus", "Slovník"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
pojmy: (§ 2.2.7 je v tezauru) nepovinná položka typu pole hodnot {0..*} typu alespoň jedno z následujících (anyOf):
§ 8.1.5 Objekt Veřejný údaj
§ 8.1.4 Objekt Neveřejný údaj
§ 8.1.3 Objekt Typ objektu práva
§ 8.1.2 Objekt Typ subjektu práva
8.1.2 Objekt Typ subjektu práva
Popis	Typ jehož instance jsou podtřídami Subjektu práva.
Interpretace	Typ subjektu práva
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Typ subjektu práva", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
agendový-informační-systém: (údaje jsou v AIS) nepovinná položka typu řetězec (formát: iri)
agenda: (sdružuje údaje vedené nebo vytvářené v rámci agendy) nepovinná položka typu řetězec (formát: iri)
8.1.3 Objekt Typ objektu práva
Popis	Typ jehož instance jsou podtřídami Objektu práva.
Interpretace	Typ objektu práva
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Typ objektu práva", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
agendový-informační-systém: (údaje jsou v AIS) nepovinná položka typu řetězec (formát: iri)
agenda: (sdružuje údaje vedené nebo vytvářené v rámci agendy) nepovinná položka typu řetězec (formát: iri)
8.1.4 Objekt Neveřejný údaj
Interpretace	Neveřejný údaj
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Neveřejný údaj", "Koncept", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
ustanovení-dokládající-neveřejnost-údaje: (je vymezen ustanovením stanovujícím jeho neveřejnost) povinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
8.1.5 Objekt Veřejný údaj
Interpretace	Veřejný údaj
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Veřejný údaj", "Koncept", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
9. Specifikace struktury pro Rozšířená specifikace typů
Datová struktura pro Tezaurus s Rozšířenou specifikací typů. Tezaurus je nejjednodušším typem slovníku.

9.1 JSON struktura pro Rozšířená specifikace typů
IRI
https://ofn.gov.cz/slovníky/2026-02-26/rozšířené-typy/schéma.json
Definováno v
../rozšířené-typy/schéma.json
Verze použitého jazyka
2020-12 (metaschema IRI: https://json-schema.org/draft/2020-12/schema)
Kořen
Kořenem JSON schématu je § 9.1.1 Objekt Tezaurus
9.1.1 Objekt Tezaurus
Popis	Tezaurus je nejjednodušším typem slovníku.
Interpretace	Tezaurus
objekt s vlastnostmi (properties):
@context: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
pole hodnot {0..*} typu řetězec (formát: iri) a musí obsahovat: "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Tezaurus", "Slovník"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
pojmy: (§ 2.2.7 je v tezauru) nepovinná položka typu pole hodnot {0..*} typu alespoň jedno z následujících (anyOf):
§ 9.1.4 Objekt Typ objektu práva
§ 9.1.3 Objekt Typ subjektu práva
§ 9.1.2 Objekt Pojem
9.1.2 Objekt Pojem
Popis	Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
Interpretace	Pojem
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
9.1.3 Objekt Typ subjektu práva
Popis	Typ jehož instance jsou podtřídami Subjektu práva.
Interpretace	Typ subjektu práva
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Typ subjektu práva", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
9.1.4 Objekt Typ objektu práva
Popis	Typ jehož instance jsou podtřídami Objektu práva.
Interpretace	Typ objektu práva
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Typ objektu práva", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
10. Specifikace struktury pro Anotace pro § 23 vyhlášky 360/2023 Sb.
Anotace pro § 23 vyhlášky 360/2023 Sb.

10.1 JSON struktura pro Anotace pro § 23 vyhlášky 360/2023 Sb.
IRI
https://ofn.gov.cz/slovníky/2026-02-26/360-2023/schéma.json
Definováno v
../360-2023/schéma.json
Verze použitého jazyka
2020-12 (metaschema IRI: https://json-schema.org/draft/2020-12/schema)
Kořen
Kořenem JSON schématu je § 10.1.1 Objekt Tezaurus
10.1.1 Objekt Tezaurus
Popis	Tezaurus je nejjednodušším typem slovníku.
Interpretace	Tezaurus
objekt s vlastnostmi (properties):
@context: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
pole hodnot {0..*} typu řetězec (formát: iri) a musí obsahovat: "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Tezaurus", "Slovník"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
pojmy: (§ 2.2.7 je v tezauru) nepovinná položka typu pole hodnot {0..*} typu § 10.1.2 Objekt Pojem
10.1.2 Objekt Pojem
Popis	Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
Interpretace	Pojem
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
způsob-získání-údaje: (má způsob získání údaje) povinná položka typu řetězec (dle regulárního výrazu: ^způsoby-získání:[^/]+$)
typ-obsahu-údaje: (má typ obsahu údaje) povinná položka typu řetězec (dle regulárního výrazu: ^typy-obsahu:[^/]+$)
způsoby-sdílení-údaje: (má způsob sdílení údaje) povinná položka typu pole hodnot {0..*} typu řetězec (dle regulárního výrazu: ^způsoby-sdílení:[^/]+$)
11. Specifikace struktury pro Slovníky celkem
Tato datová struktura slouží pro generování společného JSON-LD kontextu

11.1 JSON struktura pro Slovníky celkem
IRI
https://ofn.gov.cz/slovníky/2026-02-26/kompletní/schéma.json
Definováno v
../kompletní/schéma.json
Verze použitého jazyka
2020-12 (metaschema IRI: https://json-schema.org/draft/2020-12/schema)
Kořen
Kořenem JSON schématu je § 11.1.1 Objekt Konceptuální model
11.1.1 Objekt Konceptuální model
Popis	Na této úrovni rozlišujeme pojmy, které reprezentují - třídy reprezentující typy subjektů a objektů práva, - vztahy mezi dvěma subjekty či objekty práva, - vlastnosti subjektů a objektů práva.
Interpretace	Konceptuální model
objekt s vlastnostmi (properties):
@context: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
pole hodnot {0..*} typu řetězec (formát: iri) a musí obsahovat: "https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld"
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Tezaurus", "Konceptuální model", "Slovník"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
vytvořeno: (okamžik vytvoření) nepovinná položka typu § 11.1.27 Objekt Časový okamžik
aktualizováno: (okamžik poslední změny) nepovinná položka typu § 11.1.27 Objekt Časový okamžik
pojmy: (§ 2.2.7 je v tezauru) nepovinná položka typu pole hodnot {0..*} typu alespoň jedno z následujících (anyOf):
§ 11.1.24 Objekt Pojem
§ 11.1.21 Objekt Typ objektu práva
§ 11.1.18 Objekt Typ subjektu práva
§ 11.1.15 Objekt Neveřejný údaj
§ 11.1.12 Objekt Veřejný údaj
§ 11.1.9 Objekt Vlastnost
§ 11.1.6 Objekt Vztah
§ 11.1.2 Objekt Třída
11.1.2 Objekt Třída
Popis	Pojem reprezentující typ subjektu nebo objektu práva. Třída pak může mít instance - konkrétní subjekty či objekty práva.
Interpretace	Třída
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Třída", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
alternativní-název: (alternativní název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu pole hodnot {0..*} typu řetězec
en: nepovinná položka typu pole hodnot {0..*} typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definice: (definice) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definující-ustanovení-právního-předpisu: (definující ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
související-ustanovení-právního-předpisu: (související ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
definující-nelegislativní-zdroj: (definující nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
související-nelegislativní-zdroj: (související nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
ekvivalentní-pojem: (ekvivalentní pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
nadřazený-pojem: (nadřazený pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
způsob-získání-údaje: (má způsob získání údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^způsoby-získání:[^/]+$)
typ-obsahu-údaje: (má typ obsahu údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^typy-obsahu:[^/]+$)
způsoby-sdílení-údaje: (má způsob sdílení údaje) nepovinná položka typu pole hodnot {0..*} typu řetězec (dle regulárního výrazu: ^způsoby-sdílení:[^/]+$)
nadřazená-třída: (nadřazená třída) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
instance-definovány-číselníkem: (má instance definované číselníkem) nepovinná položka typu § 11.1.3 Objekt Číselník
11.1.3 Objekt Číselník
Popis	Číselník. Jeho identifikátorem (IRI) je IRI číselníku dle OFN Číselníky.
Interpretace	Číselník
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Číselník"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Číselník"
datová-sada-v-nkod: (má v NKOD zastřešující datovou sadu) povinná položka typu řetězec (formát: iri) (dle regulárního výrazu: ^https://data\.gov\.cz/zdroj/datové-sady/.*$)
11.1.4 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.5 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.6 Objekt Vztah
Popis	Pojem reprezentující vztah, kterým mohou být propojeny instance dvou tříd, nebo dvě instance stejné třídy.
Interpretace	Vztah
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Vztah", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
alternativní-název: (alternativní název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu pole hodnot {0..*} typu řetězec
en: nepovinná položka typu pole hodnot {0..*} typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definice: (definice) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definující-ustanovení-právního-předpisu: (definující ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
související-ustanovení-právního-předpisu: (související ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
definující-nelegislativní-zdroj: (definující nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
související-nelegislativní-zdroj: (související nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
ekvivalentní-pojem: (ekvivalentní pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
nadřazený-pojem: (nadřazený pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
způsob-získání-údaje: (má způsob získání údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^způsoby-získání:[^/]+$)
typ-obsahu-údaje: (má typ obsahu údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^typy-obsahu:[^/]+$)
způsoby-sdílení-údaje: (má způsob sdílení údaje) nepovinná položka typu pole hodnot {0..*} typu řetězec (dle regulárního výrazu: ^způsoby-sdílení:[^/]+$)
obor-hodnot: (obor hodnot) povinná položka typu řetězec (formát: iri)
definiční-obor: (definiční obor) povinná položka typu řetězec (formát: iri)
nadřazený-vztah: (nadřazený vztah) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
11.1.7 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.8 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.9 Objekt Vlastnost
Popis	Pojem reprezenutjící vlastnost, kterou může mít instance nějaké třídy.
Interpretace	Vlastnost
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Vlastnost", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
alternativní-název: (alternativní název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu pole hodnot {0..*} typu řetězec
en: nepovinná položka typu pole hodnot {0..*} typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definice: (definice) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definující-ustanovení-právního-předpisu: (definující ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
související-ustanovení-právního-předpisu: (související ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
definující-nelegislativní-zdroj: (definující nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
související-nelegislativní-zdroj: (související nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
ekvivalentní-pojem: (ekvivalentní pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
nadřazený-pojem: (nadřazený pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
způsob-získání-údaje: (má způsob získání údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^způsoby-získání:[^/]+$)
typ-obsahu-údaje: (má typ obsahu údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^typy-obsahu:[^/]+$)
způsoby-sdílení-údaje: (má způsob sdílení údaje) nepovinná položka typu pole hodnot {0..*} typu řetězec (dle regulárního výrazu: ^způsoby-sdílení:[^/]+$)
obor-hodnot: (obor hodnot) povinná položka typu řetězec (formát: iri)
definiční-obor: (definiční obor) povinná položka typu řetězec (formát: iri)
nadřazená-vlastnost: (nadřazená vlastnost) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
11.1.10 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.11 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.12 Objekt Veřejný údaj
Interpretace	Veřejný údaj
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Veřejný údaj", "Koncept", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
alternativní-název: (alternativní název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu pole hodnot {0..*} typu řetězec
en: nepovinná položka typu pole hodnot {0..*} typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definice: (definice) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definující-ustanovení-právního-předpisu: (definující ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
související-ustanovení-právního-předpisu: (související ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
definující-nelegislativní-zdroj: (definující nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
související-nelegislativní-zdroj: (související nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
ekvivalentní-pojem: (ekvivalentní pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
nadřazený-pojem: (nadřazený pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
způsob-získání-údaje: (má způsob získání údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^způsoby-získání:[^/]+$)
typ-obsahu-údaje: (má typ obsahu údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^typy-obsahu:[^/]+$)
způsoby-sdílení-údaje: (má způsob sdílení údaje) nepovinná položka typu pole hodnot {0..*} typu řetězec (dle regulárního výrazu: ^způsoby-sdílení:[^/]+$)
11.1.13 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.14 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.15 Objekt Neveřejný údaj
Interpretace	Neveřejný údaj
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Neveřejný údaj", "Koncept", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
alternativní-název: (alternativní název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu pole hodnot {0..*} typu řetězec
en: nepovinná položka typu pole hodnot {0..*} typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definice: (definice) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definující-ustanovení-právního-předpisu: (definující ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
související-ustanovení-právního-předpisu: (související ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
definující-nelegislativní-zdroj: (definující nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
související-nelegislativní-zdroj: (související nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
ekvivalentní-pojem: (ekvivalentní pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
nadřazený-pojem: (nadřazený pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
způsob-získání-údaje: (má způsob získání údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^způsoby-získání:[^/]+$)
typ-obsahu-údaje: (má typ obsahu údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^typy-obsahu:[^/]+$)
způsoby-sdílení-údaje: (má způsob sdílení údaje) nepovinná položka typu pole hodnot {0..*} typu řetězec (dle regulárního výrazu: ^způsoby-sdílení:[^/]+$)
ustanovení-dokládající-neveřejnost-údaje: (je vymezen ustanovením stanovujícím jeho neveřejnost) povinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
11.1.16 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.17 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.18 Objekt Typ subjektu práva
Popis	Typ jehož instance jsou podtřídami Subjektu práva.
Interpretace	Typ subjektu práva
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Typ subjektu práva", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
alternativní-název: (alternativní název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu pole hodnot {0..*} typu řetězec
en: nepovinná položka typu pole hodnot {0..*} typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definice: (definice) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definující-ustanovení-právního-předpisu: (definující ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
související-ustanovení-právního-předpisu: (související ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
definující-nelegislativní-zdroj: (definující nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
související-nelegislativní-zdroj: (související nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
ekvivalentní-pojem: (ekvivalentní pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
nadřazený-pojem: (nadřazený pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
způsob-získání-údaje: (má způsob získání údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^způsoby-získání:[^/]+$)
typ-obsahu-údaje: (má typ obsahu údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^typy-obsahu:[^/]+$)
způsoby-sdílení-údaje: (má způsob sdílení údaje) nepovinná položka typu pole hodnot {0..*} typu řetězec (dle regulárního výrazu: ^způsoby-sdílení:[^/]+$)
agenda: (sdružuje údaje vedené nebo vytvářené v rámci agendy) nepovinná položka typu řetězec (formát: iri)
agendový-informační-systém: (údaje jsou v AIS) nepovinná položka typu řetězec (formát: iri)
11.1.19 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.20 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.21 Objekt Typ objektu práva
Popis	Typ jehož instance jsou podtřídami Objektu práva.
Interpretace	Typ objektu práva
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Typ objektu práva", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
alternativní-název: (alternativní název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu pole hodnot {0..*} typu řetězec
en: nepovinná položka typu pole hodnot {0..*} typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definice: (definice) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definující-ustanovení-právního-předpisu: (definující ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
související-ustanovení-právního-předpisu: (související ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
definující-nelegislativní-zdroj: (definující nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
související-nelegislativní-zdroj: (související nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
ekvivalentní-pojem: (ekvivalentní pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
nadřazený-pojem: (nadřazený pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
způsob-získání-údaje: (má způsob získání údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^způsoby-získání:[^/]+$)
typ-obsahu-údaje: (má typ obsahu údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^typy-obsahu:[^/]+$)
způsoby-sdílení-údaje: (má způsob sdílení údaje) nepovinná položka typu pole hodnot {0..*} typu řetězec (dle regulárního výrazu: ^způsoby-sdílení:[^/]+$)
agenda: (sdružuje údaje vedené nebo vytvářené v rámci agendy) nepovinná položka typu řetězec (formát: iri)
agendový-informační-systém: (údaje jsou v AIS) nepovinná položka typu řetězec (formát: iri)
11.1.22 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.23 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.24 Objekt Pojem
Popis	Pojem, který reprezentuje typ subjektu práva, typ objektu práva, vlastnost nebo vztah.
Interpretace	Pojem
objekt s vlastnostmi (properties):
iri: povinná položka typu řetězec (formát: iri)
typ: povinná položka typu pole hodnot {0..*} typu řetězec a musí obsahovat: "Koncept", "Pojem"
název: (název) povinná položka typu objekt s vlastnostmi (properties):
cs: povinná položka typu řetězec
en: nepovinná položka typu řetězec
alternativní-název: (alternativní název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu pole hodnot {0..*} typu řetězec
en: nepovinná položka typu pole hodnot {0..*} typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definice: (definice) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
definující-ustanovení-právního-předpisu: (definující ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
související-ustanovení-právního-předpisu: (související ustanovení) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
definující-nelegislativní-zdroj: (definující nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
související-nelegislativní-zdroj: (související nelegislativní zdroj) nepovinná položka typu pole hodnot {0..*} typu § 11.1.4 Objekt Digitální objekt
ekvivalentní-pojem: (ekvivalentní pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
nadřazený-pojem: (nadřazený pojem) nepovinná položka typu pole hodnot {0..*} typu řetězec (formát: iri)
je-sdílen-v-ppdf: (je sdílen v propojeném datovém fondu) nepovinná položka typu boolean (ano/ne)
způsob-získání-údaje: (má způsob získání údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^způsoby-získání:[^/]+$)
typ-obsahu-údaje: (má typ obsahu údaje) nepovinná položka typu řetězec (dle regulárního výrazu: ^typy-obsahu:[^/]+$)
způsoby-sdílení-údaje: (má způsob sdílení údaje) nepovinná položka typu pole hodnot {0..*} typu řetězec (dle regulárního výrazu: ^způsoby-sdílení:[^/]+$)
11.1.25 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.26 Objekt Digitální objekt
Popis	Digitální objekt je objekt existující pouze v digitálním světě (např. databáze nebo datová sada) příp. se jedná o plně digitalizovaný objekt reálného světa (např. dokument, obrázek nebo kniha).
Interpretace	Digitální objekt
objekt s vlastnostmi (properties):
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Digitální objekt"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Digitální objekt"
název: (název) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
popis: (popis) nepovinná položka typu objekt s vlastnostmi (properties):
cs: nepovinná položka typu řetězec
en: nepovinná položka typu řetězec
url: (URL ke stažení) nepovinná položka typu řetězec (formát: iri)
11.1.27 Objekt Časový okamžik
Popis	Pro reprezentaci časových okamžiků lze použít datum, čas a nebo kombinací data a času. Pokud je jasné, který datový typ je v daném místě vhodný, použije se konkrétní datový typ, tedy datum, čas či datum a čas. Často ale při tvorbě OFN není předem známo, jaká úroveň detailu bude pro určení okamžiku k dispozici. Aby se zabránilo různým reprezentacím této situace v různých OFN, je specifikována třída Časový okamžik.
Interpretace	Časový okamžik
objekt s vlastnostmi (properties):
iri: nepovinná položka typu řetězec (formát: iri)
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Časový okamžik"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Časový okamžik"
je_nespecifikovaný: (je nespecifikovaný) nepovinná položka typu boolean (ano/ne)
datum_a_čas: (datum a čas) nepovinná položka typu řetězec (formát: date-time)
datum: (datum) nepovinná položka typu řetězec (formát: date)
11.1.28 Objekt Časový okamžik
Popis	Pro reprezentaci časových okamžiků lze použít datum, čas a nebo kombinací data a času. Pokud je jasné, který datový typ je v daném místě vhodný, použije se konkrétní datový typ, tedy datum, čas či datum a čas. Často ale při tvorbě OFN není předem známo, jaká úroveň detailu bude pro určení okamžiku k dispozici. Aby se zabránilo různým reprezentacím této situace v různých OFN, je specifikována třída Časový okamžik.
Interpretace	Časový okamžik
objekt s vlastnostmi (properties):
iri: nepovinná položka typu řetězec (formát: iri)
typ: povinná položka typu právě jedno z následujících (oneOf):
konstantní hodnota "Časový okamžik"
pole hodnot {0..*} typu řetězec a musí obsahovat: "Časový okamžik"
je_nespecifikovaný: (je nespecifikovaný) nepovinná položka typu boolean (ano/ne)
datum_a_čas: (datum a čas) nepovinná položka typu řetězec (formát: date-time)
datum: (datum) nepovinná položka typu řetězec (formát: date)
12. Předpřipravená metadata
Tato sekce obsahuje odkaz na vzorový metadatový záznam datové sady použitelný pro registraci datové sady do Národního katalogu otevřených dat. Registrace pomocí tohoto předpřipraveného záznamu umožní vyhledávat podobné datové sady publikované dle této otevřené formální normy.

13. Použité prefixy
Prefix	Namespace IRI
skos	http://www.w3.org/2004/02/skos/core#
owl	http://www.w3.org/2002/07/owl#
rdfs	http://www.w3.org/2000/01/rdf-schema#
rdf	http://www.w3.org/1999/02/22-rdf-syntax-ns#
xsd	http://www.w3.org/2001/XMLSchema#
dcterms	http://purl.org/dc/terms/
14. Přílohy
Součástí této specifikace jsou následující přílohy.

Příloha	Odkaz
Slovník	../model.owl.ttl
Aplikační profil	../dsv.ttl
JSON schéma	../slovník/schéma.json
JSON schéma	../tezaurus/schéma.json
JSON schéma	../konceptuální-model/schéma.json
JSON schéma	../rpp/schéma.json
JSON schéma	../rozšířené-typy/schéma.json
JSON schéma	../360-2023/schéma.json
JSON schéma	../kompletní/schéma.json
JSON-LD kontext	../kompletní/kontext.jsonld
Dokumentace	#
15. Poděkování
Na tvorbě této OFN se podíleli: Alice Binderová, Jakub Klímek, Petr Křemen, Martin Nečaský

A. Reference
A.1 Normativní reference
[AGENDY]
Agendy. Digitální a informační agentura. URL: https://data.gov.cz/datová-sada?iri=https%3A%2F%2Fdata.gov.cz%2Fzdroj%2Fdatové-sady%2F17651921%2F936a5ef628dc4df2318e1964f633c5ed
[ISVS]
Informační systémy veřejné správy. Digitální a informační agentura. URL: https://data.gov.cz/datová-sada?iri=https%3A%2F%2Fdata.gov.cz%2Fzdroj%2Fdatové-sady%2F17651921%2F6f8561e8f13e79e817b9854dcfbc4144
[JSON]
The JavaScript Object Notation (JSON) Data Interchange Format. T. Bray, Ed.. IETF. December 2017. Internet Standard. URL: https://www.rfc-editor.org/info/rfc8259/
[JSON-LD11]
JSON-LD 1.1. Gregg Kellogg; Pierre-Antoine Champin; Dave Longley. W3C. 16 July 2020. W3C Recommendation. URL: https://www.w3.org/TR/json-ld11/
[JSON-SCHEMA-2020-12]
JSON Schema: A Media Type for Describing JSON Documents. Draft 2020-12. Austin Wright; Henry Andrews; Ben Hutton; Greg Dennis. Internet Engineering Task Force (IETF). 10 June 2022. Internet-Draft. URL: https://datatracker.ietf.org/doc/html/draft-bhutton-json-schema-01
[NKOD]
Kompletní metadata - Národní katalog otevřených dat. Digitální a informační agentura. URL: https://data.gov.cz/datová-sada?iri=https%3A%2F%2Fdata.gov.cz%2Fzdroj%2Fdatové-sady%2F17651921%2F1845c4349bf1ecdb0aeb0872db0ed881
[OWL2-RDF-BASED-SEMANTICS]
OWL 2 Web Ontology Language RDF-Based Semantics (Second Edition). Michael Schneider. W3C. 11 December 2012. W3C Recommendation. URL: https://www.w3.org/TR/owl2-rdf-based-semantics/
[P23-O1-360-2023]
Číselník způsobů získání údajů v ISVS dle § 23, odst. 1, vyhlášky č. 360/2023 Sb.. Digitální a informační agentura. URL: https://data.gov.cz/datová-sada?iri=https%3A%2F%2Fdata.gov.cz%2Fzdroj%2Fdatové-sady%2F17651921%2F4b36c259ff070d700fae8864e50cb5e3
[P23-O2-360-2023]
Číselník způsobů sdílení údajů v ISVS dle § 23, odst. 2, vyhlášky č. 360/2023 Sb.. Digitální a informační agentura. URL: https://data.gov.cz/datová-sada?iri=https%3A%2F%2Fdata.gov.cz%2Fzdroj%2Fdatové-sady%2F17651921%2Ff675197b7cd720b5ff19b0d0f939f6cc
[P23-O3-360-2023]
Číselník typů obsahu údajů v ISVS dle § 23, odst. 3, vyhlášky č. 360/2023 Sb.. Digitální a informační agentura. URL: https://data.gov.cz/datová-sada?iri=https%3A%2F%2Fdata.gov.cz%2Fzdroj%2Fdatové-sady%2F17651921%2F44f48b721921b0b1ea6b42fcd9f865f6
[POPIS-DAT]
Metodika popisu dat. Digitální a informační agentura. URL: https://data.gov.cz/popis-dat/
[RDF11-CONCEPTS]
RDF 1.1 Concepts and Abstract Syntax. Richard Cyganiak; David Wood; Markus Lanthaler. W3C. 25 February 2014. W3C Recommendation. URL: https://www.w3.org/TR/rdf11-concepts/
[RDF11-SCHEMA]
RDF Schema 1.1. Dan Brickley; Ramanathan Guha. W3C. 25 February 2014. W3C Recommendation. URL: https://www.w3.org/TR/rdf-schema/
[SKOS-REFERENCE]
SKOS Simple Knowledge Organization System Reference. Alistair Miles; Sean Bechhofer. W3C. 18 August 2009. W3C Recommendation. URL: https://www.w3.org/TR/skos-reference/
[TURTLE]
RDF 1.1 Turtle. Eric Prud'hommeaux; Gavin Carothers. W3C. 25 February 2014. W3C Recommendation. URL: https://www.w3.org/TR/turtle/