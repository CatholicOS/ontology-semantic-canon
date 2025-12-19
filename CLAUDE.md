# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The **Catholic Semantic Canon** is a formal OWL ontology modeling the Catholic Deposit of Faith - the hierarchical and relational structure of Sacred Scripture, Sacred Tradition, and the Magisterium. The ontology provides machine-readable semantic data (120,000+ triples) for theological concepts including church hierarchy, sacraments, religious orders, liturgy, and canon law.

**Source of Truth**: The ontology is maintained in WebProtege at https://webprotege.stanford.edu/#projects/75e2824f-d4e7-4a73-83be-1574345b9f28. Direct PRs to ontology files are generally not accepted.

## Running SPARQL Queries

### Python (rdflib)

```bash
cd examples/python
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python query_runner.py           # Interactive menu
python query_runner.py 01        # Run specific query (e.g., 01-list-all-classes.rq)
python query_runner.py --list    # List available queries
python query_runner.py --query "SELECT ?s WHERE { ?s a <http://www.w3.org/2002/07/owl#Class> } LIMIT 10"

# Semantic queries (use rdfs:subClassOf* property paths instead of regex)
python query_runner.py --semantic           # Interactive menu with semantic queries
python query_runner.py --semantic 01        # Run semantic query 01-church-hierarchy.rq
python query_runner.py --semantic --list    # List semantic queries
```

### Java (Apache Jena)

```bash
cd examples/java
mvn compile exec:java                    # Interactive menu
mvn compile exec:java -Dexec.args="01"   # Run specific query
mvn compile exec:java -Dexec.args="--list"

# Build executable JAR
mvn package
java -jar target/semantic-canon-query-runner-1.0.0.jar
```

### Apache Jena CLI (arq)

```bash
arq --data=sources/ontology-semantic-canon.owl --query=queries/01-list-all-classes.rq
arq --data=sources/ontology-semantic-canon.ttl --query=queries/03-find-church-hierarchy-roles.rq --results=CSV
```

## Repository Structure

```
sources/                    # Ontology files (OWL, TTL, OWX, OMN, OFN, NT formats)
queries/                    # Standard SPARQL query files (.rq) - use regex patterns
queries/semantic/           # Semantic queries using rdfs:subClassOf* property paths
config/                     # Configuration files (query-categories.yaml)
scripts/                    # Utility scripts (pattern_generator.py)
examples/python/            # Python query runner using rdflib
examples/java/              # Java query runner using Apache Jena
```

## Key Technical Details

- **Ontology size**: 120,000+ triples
- **Python caching**: The Python runner creates a `.pickle` cache file for faster subsequent loads. Delete it to force re-parsing.
- **Python 3.12 stability**: Known intermittent issues with rdflib 7.x on Python 3.12. The pickle cache mitigates this.
- **Java requirements**: Java 17+ (Java 21 LTS recommended), Maven 3.6+
- **Default ontology format**: OWL/XML (`.owl`) for Python, Turtle (`.ttl`) for Java

## Ontology Namespace

The primary namespace is `https://ontology.catholicos.catholic/` (prefix: `osc:`).

## Query Architecture Note

Current queries use regex pattern matching (fragile). The ROADMAP.md documents plans to refactor queries to use semantic property paths (`rdfs:subClassOf*`) which leverage the ontology's inheritance hierarchy. When writing new queries, prefer semantic patterns over regex where possible.
