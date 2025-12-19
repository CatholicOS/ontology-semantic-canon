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

python query_runner.py           # Interactive menu (standard queries)
python query_runner.py 01        # Run specific query (e.g., 01-list-all-classes.rq)
python query_runner.py --list    # List available queries
python query_runner.py --query "SELECT ?s WHERE { ?s a <http://www.w3.org/2002/07/owl#Class> } LIMIT 10"

# Semantic queries (optimized for rdflib, uses queries/rdflib/)
python query_runner.py --semantic           # Interactive menu with semantic queries
python query_runner.py --semantic 01        # Run semantic query 01-church-hierarchy.rq
python query_runner.py --semantic --list    # List semantic queries
```

### Apache Jena CLI (arq) - Recommended for complex queries

```bash
# Use queries/jena/ for full-featured semantic queries with property paths
arq --data=sources/ontology-semantic-canon.ttl --query=queries/jena/01-church-hierarchy.rq
arq --data=sources/ontology-semantic-canon.ttl --query=queries/jena/03-sacraments.rq --results=CSV

# Standard queries also work
arq --data=sources/ontology-semantic-canon.owl --query=queries/01-list-all-classes.rq
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

## Repository Structure

```
sources/                    # Ontology files (OWL, TTL, OWX, OMN, OFN formats)
queries/                    # Standard SPARQL query files (.rq) - use regex patterns
queries/jena/               # Full-featured semantic queries for Apache Jena (arq)
queries/rdflib/             # Simplified semantic queries for Python/rdflib
config/                     # Configuration files (query-categories.yaml)
scripts/                    # Utility scripts (pattern_generator.py)
examples/python/            # Python query runner using rdflib
examples/java/              # Java query runner using Apache Jena
```

## Query Engine Differences

| Feature | queries/jena/ | queries/rdflib/ |
|---------|---------------|-----------------|
| Engine | Apache Jena (arq) | Python rdflib |
| Property paths | `rdfs:subClassOf*` | UNION patterns (3 levels) |
| DISTINCT | Yes | No |
| ORDER BY | Yes | No |
| Multiple OPTIONALs | Yes | Limited |
| Stability | Reliable | May segfault on Python 3.12 |

Use `queries/jena/` with `arq` for full hierarchy traversal and complex queries. Use `queries/rdflib/` with the Python query runner for stable execution.

## Key Technical Details

- **Ontology size**: 120,000+ triples
- **Python caching**: The Python runner creates a `.pickle` cache file for faster subsequent loads. Delete it to force re-parsing.
- **Python 3.12 stability**: Known segfault issues with rdflib 7.x on Python 3.12 for complex queries. The rdflib queries use simplified patterns to avoid this.
- **Java requirements**: Java 17+ (Java 21 LTS recommended), Maven 3.6+
- **Default ontology format**: OWL/XML (`.owl`) for Python, Turtle (`.ttl`) for Java/Jena

## Ontology Namespace

The primary namespace is `https://ontology.catholicos.catholic/` (prefix: `osc:`).
