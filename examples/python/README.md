# Python SPARQL Query Runner

A Python tool for running SPARQL queries against the Catholic Semantic Canon ontology using [rdflib](https://rdflib.readthedocs.io/).

## Requirements

- Python 3.10 or higher
- Dependencies: `rdflib`, `lxml`

## Setup

### Option 1: Using `python -m venv` (Standard Library)

```bash
cd examples/python

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using `uv` (Faster Alternative)

[uv](https://github.com/astral-sh/uv) is a fast Python package manager written in Rust.

```bash
cd examples/python

# Create virtual environment and install dependencies in one step
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
uv pip install -r requirements.txt

# Or run directly without explicit activation
uv run python query_runner.py
```

## Usage

### Interactive Mode

```bash
python query_runner.py
```

This displays a menu of available queries. Select a number to run that query, or enter `c` to type a custom SPARQL query.

### Run a Specific Query

```bash
# Run query by number prefix
python query_runner.py 01           # Runs 01-list-all-classes.rq
python query_runner.py 03           # Runs 03-find-church-hierarchy-roles.rq

# Run inline SPARQL
python query_runner.py --query "SELECT ?s WHERE { ?s a <http://www.w3.org/2002/07/owl#Class> } LIMIT 10"
```

### List Available Queries

```bash
python query_runner.py --list
```

### Use a Different Ontology File

```bash
python query_runner.py --ontology ../../sources/ontology-semantic-canon.ttl
```

## Available Queries

| Query                               | Description                                  |
| :---------------------------------- | :------------------------------------------- |
| `01-list-all-classes.rq`            | List all classes with labels and definitions |
| `02-list-object-properties.rq`      | List object properties with domains/ranges   |
| `03-find-church-hierarchy-roles.rq` | Find Pope, Cardinal, Bishop, Priest roles    |
| `04-find-sacrament-concepts.rq`     | Find sacrament-related concepts              |
| `05-class-hierarchy.rq`             | Display subclass relationships               |
| `06-find-religious-orders.rq`       | Find religious orders and institutes         |
| `07-find-juridical-structures.rq`   | Find Diocese, Parish, Holy See, etc.         |
| `08-authority-properties.rq`        | Find authority/jurisdiction concepts         |
| `09-provenance-relationships.rq`    | Track document origins and versions          |
| `10-legal-actions.rq`               | Find FOLIO legal action properties           |
| `11-search-by-keyword.rq`           | Template for full-text keyword search        |
| `12-ontology-statistics.rq`         | Get counts of classes/properties             |
| `13-find-liturgical-concepts.rq`    | Find Mass, Liturgy, Rite concepts            |
| `14-find-canon-law-documents.rq`    | Find Canon, Decree, Encyclical types         |
| `15-construct-label-graph.rq`       | CONSTRUCT query for vocabulary extraction    |

### Semantic Queries

Additional semantic queries optimized for rdflib are available in `queries/rdflib/`. These use UNION patterns instead of property paths (`rdfs:subClassOf*`) for better compatibility with rdflib/Python 3.12.

```bash
# Run semantic queries
python query_runner.py --semantic          # Interactive menu
python query_runner.py --semantic 01       # Run semantic query 01
python query_runner.py --semantic --list   # List semantic queries
```

| Query                   | Description                                        |
| :---------------------- | :------------------------------------------------- |
| `01-church-hierarchy.rq` | Clergy classes (Pope, Cardinal, Bishop, etc.)      |
| `02-consecrated-life.rq` | Religious orders (Religious Brother/Sister, etc.)  |
| `03-sacraments.rq`       | Sacrament classes (Initiation, Healing, etc.)      |
| `04-liturgy.rq`          | Liturgy classes (Mass, Rite, Divine Office, etc.)  |
| `05-canon-law.rq`        | Religious law systems including Canon Law          |
| `06-religious-events.rq` | Comprehensive religious events hierarchy           |
| `07-disambiguation.rq`   | Disambiguate terms with parent class context       |
| `08-hierarchy-tree.rq`   | Class hierarchy tree (2 levels deep)               |

## Performance: Pickle Caching

The ontology contains 120,000+ triples and takes several seconds to parse. To improve startup time, the query runner automatically caches the parsed graph:

1. **First run**: Parses the OWL file and saves to `ontology-semantic-canon.pickle`
2. **Subsequent runs**: Loads from the pickle cache (~2 seconds)

The cache is stored alongside the ontology file in `sources/`. If you update the ontology, delete the `.pickle` file to regenerate it.

## Known Issues

### Python 3.12 + rdflib Compatibility

There are known stability issues with rdflib 7.x on Python 3.12 that can cause intermittent crashes when parsing large RDF files.
The pickle caching mechanism helps mitigate this by reducing the number of parse operations.

If you encounter crashes:

- Re-run the command (usually succeeds on retry)
- Ensure `lxml` is installed (`pip install lxml`)
- Consider using Python 3.11 for maximum stability

### Complex SPARQL Queries

Some complex SPARQL patterns (multiple OPTIONAL clauses with OR in FILTER) may cause issues. If a query crashes, try simplifying it by:

- Reducing the number of OPTIONAL clauses
- Using UNION instead of OR in FILTER
- Removing ORDER BY clauses

## Programmatic Usage

```python
from rdflib import Graph

# Load the ontology
g = Graph()
g.parse("../../sources/ontology-semantic-canon.owl", format="xml")
print(f"Loaded {len(g)} triples")

# Run a query
query = """
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?class ?label
WHERE {
  ?class a owl:Class .
  ?class rdfs:label ?label .
  FILTER(REGEX(?label, "Bishop", "i"))
}
LIMIT 10
"""

for row in g.query(query):
    print(f"{row.label}")
```

## Troubleshooting

### "No module named 'rdflib'"

Make sure you've activated the virtual environment and installed dependencies:

```bash
source venv/bin/activate  # or `.venv/bin/activate` if using uv
pip install -r requirements.txt
```

### "Ontology file not found"

Run the script from the `examples/python` directory, or specify the ontology path:

```bash
python query_runner.py --ontology /path/to/ontology-semantic-canon.owl
```

### Slow startup

Delete the pickle cache to regenerate it:

```bash
rm ../../sources/ontology-semantic-canon.pickle
python query_runner.py  # Will regenerate cache
```
