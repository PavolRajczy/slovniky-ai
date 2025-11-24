# Semantic Modeling Assistant Specification

Semantic Modeling Assistant supports the following user stories.

## Create a new empty ontology

As a user I need to create a new empty ontology with its label and description so that I can work on it through one or more design projects later.

## Change an existing ontology

As a user I need to change the label or description of an existing ontology because whenever I do some work on the ontology I may find out that its label or description are not correct or sufficient and I need to change them easily.

## Create a new design project

As a user I need to create a new design project with a name, domain name, domain description so that I can do some work on a given existing ontology.

## Edit an existing design project

As a user I need to change an existing design project (its name, domain name or domain description) because whenever I do some work on the ontology I may find out that the names or description are not correct or sufficient and I need to change them easily.

## Load an existing design project

As a user I need to be able to choose from the list of existing design projects a design project so that it can be loaded and I can work on the ontology associated with this design project.

## Edit the knowledge base of the design project

As a user I need to be able to add and remove documents from the design project knowledge base, either legal or expert knowledge base, because I need to specify after the projec is created what is its knowledge base but also I can find new relevant documents later whenever I work on the project which can also lead to finding out that some documents are outdated and need to be removed from the knowledge base.

## Edit knowledge areas of the desing project

As a user I need to be able to manipulate with the knowledge areas of the design project manually, i.e. adding new areas, editing or removing exiting ones, because I appreciate that the assistant suggested domain areas but when I do not like them I need to change them manually - the assistant may be wrong sometimes.

## Reidentify knowledge areas of the design project

As a user I need to be able to ask the assistant to reidentify the knowledge areas of the design project considering my suggestion or requirement of how to change them (e.g., split a too big area to more, merge areas, change an area in some way, move a part of the are to some other area, etc - any instruction that I can specify as a free text command), because I appreciate that the assistant suggested domain areas but when I do not like them I need to ask the assistant to change them in some way that fits the needs and purposes of my design project.

## Suggest iterations for a domain area

As a user I need to choose a domain area from the domain of the design project and get suggestions of the next K iterations as a plan for further enhancements or updates the ontology based on the knowledge base so that I can get help from the assistant in planning the next work on the ontology within the project in the iterative manner, optionally with providing my text instruction of what the next iterations should focus on. This must be possible even when there already are some planned iterations - the assistant extends this plan with K new iterations.

## Edit iterations for a domain area

As a user I need to be able to manipulate with the planned iterations associated with the domain area manually, i.e. adding new iterations, editing or removing existing iterations, changing their order, because I appreciate that the assistant suggested a plan in the form of planned iterations but when I do not like them I need to change them manually - the assistant may be wrong sometimes.

## Plan tasks for an iteration

As a user I need to choose an iteration for a chosen domain area and get a suggestion of a plan of tasks to execute the iteration so that I can see concrete steps (in the form of individual tasks) of we need to change the ontology to fulfill the goal of the iteration.

## Edit tasks of an interation

As a user I need to be able to manipulate with the planned tasks for a given iteration manually, i.e. adding new tasks, editing or removing existing tasks, changing their order, because I appreciate that the assistant suggested a plan in the form of planned tasks but when I do not like them I need to change them manually - the assistant may be wrong sometimes.

## Execute an interation with planned tasks

As a user I need to be able to execute a given iteration that is planned and has at least one planned task, because I do not want to perform it manually but I need to control that the iteration executes correctly - for this I need to see the concrete materialization of the planned tasks into the sequence of ontology operations, and then apply them finally to the ontology after my approval.

## Edit materialized operations for an iteration

As a user, when I get the concrete materialization of the planned tasks in the form of sequence of ontology operations, I need to be able to reject any operation because I may find it wrong and not applicable into the ontology. I want to see the operations in a form that clearly distinguishes class, attribute and relationship operations visually. For now, I will check on my own if rejecting an operation needs also rejecting some follow-up operations but in the future development of the assistant I expect that there will be some automated test for this.

## See the ontology after executing the operations that materialize planned tasks of an iteration

As a user, after I approve executing the ontology edit operations that materialize the given planned tasks of a chosen iteration, I need to see the ontology with highlighted changes in the final ontology.

## See an existing ontology

As a user I need to see an existing ontology whenever I ask for even if this request is not related to executing the ontology edit operations materializing the given planned tasks of a chosen iteration so that I can see the current ontology whenever I want. In that case, I do not need to see the changes.

## Read knowledge base document

As a user I need to be able to choose a document in the knowledge base and read its content because I need to be able to check that the designed ontology corresponds to the content of the knowledge base documents semantically.

## See coverage of documents in knowledge base by ontology

As a user I need to see for the given knowledge base document its elements highlighted in a way that shows me for what elements we already have some ontology elements designed in the ontology and what are these elements, because I must be able to check what parts of the knowledge base are already reflected in the ontology and how.