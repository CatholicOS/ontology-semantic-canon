# Catholic Semantic Canon

This repository contains a formal ontology designed to model the hierarchical and relational structure of the Catholic **Deposit of Faith**.
It maps the interdependence of Sacred Scripture, Sacred Tradition, and the Magisterium, providing a semantic framework for how these sources are transmitted and interpreted.

### 📖 Overview

The **Catholic Semantic Canon** moves beyond a static bibliography.
It provides a machine-readable logic for the "Living Tradition", capturing not just what the sources are,
but how they relate to one another in terms of authority, chronology, and theological weight.

### 🛠 Core Objectives

- **Hierarchical Mapping**: Defining the relationship between primary revelation and secondary authoritative commentary.
- **Interdependence**: Modeling how the Church’s Magisterium interprets Scripture and how Tradition sustains both.
- **Contextual Use**: Tracking the development of doctrine and the application of sources within liturgical and canonical contexts.
- **Semantic Interoperability**: Enabling theological data to be queried using standardized formats (such as OWL or RDF).

### 🗂 Key Components

| Component | Description |
| :--- | :--- |
| **Sacred Scripture** | The written Word of God, categorized by canon, genre, and testament. |
| **Sacred Tradition** | The oral and lived transmission of faith, including Patristics and Liturgy. |
| **The Magisterium** | The teaching authority (Papal Encyclicals, Conciliar Documents) and their levels of certainty. |
| **Relational Logic** | Predicates that define "Interpretation," "Clarification," and "Succession." |

### 🚀 Getting Started

The primary "source of truth" for this ontology is hosted on **WebProtégé**. To ensure data integrity and collaborative consistency, all structural edits and maintenance are managed through that platform.

* **Access the Model:** [Catholic OS Ontolgoy on WebProtégé](https://webprotege.stanford.edu/#projects/75e2824f-d4e7-4a73-83be-1574345b9f28)
* **Contributions:** Contributors should request access via the WebProtégé link above. All edits to classes and relationships should be made directly in the instance.
* **Issue Tracking:** Please use the **GitHub Issues** tab to propose major structural changes or discuss ontological definitions.
* **Versioning:** Versioning and exports are handled by the maintainers via WebProtégé. Direct Pull Requests to the ontology files in this repo will generally not be accepted.

### 🔍 Running SPARQL Queries

The `queries/` folder contains sample SPARQL queries for exploring the ontology. These queries can be run using various tools:

#### Using Apache Jena (Command Line)

Install [Apache Jena](https://jena.apache.org/) and use the `arq` command:

```bash
# Run a query against the OWL file
arq --data=sources/ontology-semantic-canon.owl --query=queries/01-list-all-classes.rq

# Run against the Turtle file
arq --data=sources/ontology-semantic-canon.ttl --query=queries/03-find-church-hierarchy-roles.rq
```

#### Using rdflib (Python)

```python
from rdflib import Graph

# Load the ontology
g = Graph()
g.parse("sources/ontology-semantic-canon.owl", format="xml")

# Run a query
with open("queries/01-list-all-classes.rq") as f:
    query = f.read()

for row in g.query(query):
    print(row)
```

#### Using a Triple Store

For larger-scale querying, load the ontology into a triple store:

- **Apache Jena Fuseki**: Upload the OWL/TTL file and use the built-in SPARQL endpoint
- **GraphDB**: Import the ontology and query via the Workbench UI
- **Blazegraph**: Load data and query through the web interface

#### Using Protégé

1. Open the ontology in [Protégé](https://protege.stanford.edu/)
2. Go to **Window → Tabs → SPARQL Query**
3. Paste any query from the `queries/` folder and execute

#### Available Queries

| Query | Description |
| :--- | :--- |
| `01-list-all-classes.rq` | List all classes with labels and definitions |
| `02-list-object-properties.rq` | List object properties with domains/ranges |
| `03-find-church-hierarchy-roles.rq` | Find Pope, Cardinal, Bishop, Priest roles |
| `04-find-sacrament-concepts.rq` | Find sacrament-related concepts |
| `05-class-hierarchy.rq` | Display subclass relationships |
| `06-find-religious-orders.rq` | Find religious orders and institutes |
| `07-find-juridical-structures.rq` | Find Diocese, Parish, Holy See, etc. |
| `08-authority-properties.rq` | Find authority/jurisdiction concepts |
| `09-provenance-relationships.rq` | Track document origins and versions |
| `10-legal-actions.rq` | Find FOLIO legal action properties |
| `11-search-by-keyword.rq` | Template for full-text keyword search |
| `12-ontology-statistics.rq` | Get counts of classes/properties |
| `13-find-liturgical-concepts.rq` | Find Mass, Liturgy, Rite concepts |
| `14-find-canon-law-documents.rq` | Find Canon, Decree, Encyclical types |
| `15-construct-label-graph.rq` | CONSTRUCT query for vocabulary extraction |
