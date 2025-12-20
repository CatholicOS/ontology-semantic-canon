#!/usr/bin/env python3
"""
Pattern Generator for Catholic Semantic Canon Ontology

Generates regex patterns and VALUES clauses from the ontology class hierarchy.
This enables external systems that don't speak SPARQL to use ontology-derived
patterns for text matching.

Usage:
    python pattern_generator.py                          # Use defaults
    python pattern_generator.py --config config.yaml     # Custom config
    python pattern_generator.py --output patterns.json   # Custom output
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None
    print("Warning: PyYAML not installed. Install with: pip install pyyaml")

try:
    from rdflib import Graph, Namespace, URIRef
    from rdflib.namespace import RDF, RDFS, OWL, SKOS
except ImportError:
    print("Error: rdflib is not installed.")
    print("Install with: pip install rdflib")
    sys.exit(1)


# Paths relative to this script
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
SOURCES_DIR = PROJECT_ROOT / "sources"
CONFIG_DIR = PROJECT_ROOT / "config"
GENERATED_DIR = PROJECT_ROOT / "generated"

DEFAULT_ONTOLOGY = SOURCES_DIR / "ontology-semantic-canon.owl"
DEFAULT_CONFIG = CONFIG_DIR / "query-categories.yaml"
DEFAULT_OUTPUT = GENERATED_DIR / "patterns.json"

# Ontology namespace
OSC = Namespace("https://ontology.catholicos.catholic/")


def load_ontology(ontology_path: Path) -> Graph:
    """Load the ontology into an RDF graph."""
    print(f"Loading ontology from {ontology_path.name}...")

    # Try pickle cache first
    cache_path = ontology_path.with_suffix(".pickle")
    if cache_path.exists():
        try:
            import pickle
            with open(cache_path, "rb") as f:
                g = pickle.load(f)
            print(f"Loaded {len(g)} triples from cache.")
            return g
        except (pickle.UnpicklingError, EOFError, AttributeError, ModuleNotFoundError, OSError) as e:
            print(f"Cache load failed ({e}), parsing ontology...")

    g = Graph()
    suffix = ontology_path.suffix.lower()
    format_map = {
        ".ttl": "turtle",
        ".owl": "xml",
        ".owx": "xml",
        ".rdf": "xml",
        ".n3": "n3",
        ".nt": "nt",
    }
    rdf_format = format_map.get(suffix, "turtle")
    g.parse(str(ontology_path), format=rdf_format)
    print(f"Loaded {len(g)} triples.")

    # Save to cache for faster subsequent loads
    try:
        import pickle
        print(f"Saving to cache {cache_path.name}...")
        with open(cache_path, "wb") as f:
            pickle.dump(g, f)
        print("Cache saved successfully.")
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

    return g


def load_config(config_path: Path) -> dict:
    """Load the category configuration from YAML."""
    if not yaml:
        print("Error: PyYAML required to load config. Using built-in defaults.")
        return get_default_config()

    if not config_path.exists():
        print(f"Config not found: {config_path}. Using built-in defaults.")
        return get_default_config()

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Validate structure
    if not isinstance(config, dict):
        print("Warning: Invalid config structure, using defaults.")
        return get_default_config()
    if "categories" not in config or not isinstance(config["categories"], dict):
        print("Warning: Config missing 'categories', using defaults.")
        return get_default_config()

    return config


def get_default_config() -> dict:
    """Return built-in default configuration."""
    return {
        "namespace": "https://ontology.catholicos.catholic/",
        "categories": {
            "church_hierarchy": {
                "label": "Church Hierarchy",
                "root_classes": [{"id": "RChKPk9K152BirrIYgAREsY", "label": "Clergy"}]
            },
            "consecrated_life": {
                "label": "Consecrated Life",
                "root_classes": [{"id": "RDUOYPsMTjLKT8XTp6oHH2o", "label": "Consecrated Persons"}]
            },
            "sacraments": {
                "label": "Sacraments",
                "root_classes": [{"id": "RB91Ir5bSOsoHyaGccORDpQ", "label": "Sacraments"}]
            },
            "liturgy": {
                "label": "Liturgy",
                "root_classes": [{"id": "RDiYA0x2kAubW5cDdOR4oZV", "label": "Liturgy"}]
            },
            "canon_law": {
                "label": "Canon Law",
                "root_classes": [{"id": "RDCWfUYXx114d8AdyJQmbzH", "label": "Canon Law System"}]
            },
        }
    }


def get_subclass_labels(graph: Graph, root_uri: URIRef) -> set:
    """
    Get all labels for classes that are subclasses of the given root class.
    Uses UNION patterns to emulate rdfs:subClassOf* (avoids rdflib segfaults).

    Security note: root_uri is interpolated into the SPARQL query string.
    Only pass URIRef objects from trusted sources (e.g., config files).
    """
    # Validate URI format to prevent injection
    uri_str = str(root_uri)
    if not uri_str.startswith(("http://", "https://")) or any(c in uri_str for c in ['>', '<', '"', "'"]):
        raise ValueError(f"Invalid URI format: {uri_str}")

    # Use UNION patterns instead of rdfs:subClassOf* to avoid Python 3.12 segfaults
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?label
    WHERE {
      {
        # Level 0: root class itself
        BIND(<%s> AS ?class)
      }
      UNION
      {
        # Level 1: direct children
        ?class rdfs:subClassOf <%s> .
      }
      UNION
      {
        # Level 2: grandchildren
        ?parent rdfs:subClassOf <%s> .
        ?class rdfs:subClassOf ?parent .
      }
      UNION
      {
        # Level 3: great-grandchildren
        ?grandparent rdfs:subClassOf <%s> .
        ?parent rdfs:subClassOf ?grandparent .
        ?class rdfs:subClassOf ?parent .
      }
      ?class a owl:Class .
      {
        ?class rdfs:label ?label .
      }
      UNION
      {
        ?class skos:altLabel ?label .
      }
      UNION
      {
        ?class skos:prefLabel ?label .
      }
    }
    """ % (uri_str, uri_str, uri_str, uri_str)

    labels = set()
    try:
        for row in graph.query(query):
            if row.label:
                label_str = str(row.label)
                # Clean up the label
                label_str = label_str.strip()
                if label_str and len(label_str) > 1:
                    labels.add(label_str)
    except (TypeError, ValueError, AttributeError, KeyError) as e:
        print(f"  Warning: Query failed for {root_uri}: {e}")

    return labels


def get_subclass_uris(graph: Graph, root_uri: URIRef) -> list:
    """
    Get all URIs for classes that are subclasses of the given root class.
    Uses UNION patterns to emulate rdfs:subClassOf* (avoids rdflib segfaults).

    Security note: root_uri is interpolated into the SPARQL query string.
    Only pass URIRef objects from trusted sources (e.g., config files).
    """
    # Validate URI format to prevent injection
    uri_str = str(root_uri)
    if not uri_str.startswith(("http://", "https://")) or any(c in uri_str for c in ['>', '<', '"', "'"]):
        raise ValueError(f"Invalid URI format: {uri_str}")

    # Use UNION patterns instead of rdfs:subClassOf* to avoid Python 3.12 segfaults
    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    SELECT ?class
    WHERE {
      {
        # Level 0: root class itself
        BIND(<%s> AS ?class)
      }
      UNION
      {
        # Level 1: direct children
        ?class rdfs:subClassOf <%s> .
      }
      UNION
      {
        # Level 2: grandchildren
        ?parent rdfs:subClassOf <%s> .
        ?class rdfs:subClassOf ?parent .
      }
      UNION
      {
        # Level 3: great-grandchildren
        ?grandparent rdfs:subClassOf <%s> .
        ?parent rdfs:subClassOf ?grandparent .
        ?class rdfs:subClassOf ?parent .
      }
      ?class a owl:Class .
    }
    """ % (uri_str, uri_str, uri_str, uri_str)

    uris = set()
    try:
        for row in graph.query(query):
            if row["class"]:
                uris.add(str(row["class"]))
    except (TypeError, ValueError, AttributeError, KeyError) as e:
        print(f"  Warning: Query failed for {root_uri}: {e}")

    return list(uris)


def generate_regex_pattern(labels: set) -> str:
    """Generate a regex pattern from a set of labels."""
    if not labels:
        return ""

    # Escape special regex characters and join with |
    escaped = [re.escape(label) for label in sorted(labels)]
    # Add word boundaries for whole-word matching
    pattern = "|".join(escaped)
    return rf"\b(?:{pattern})\b"


def generate_values_clause(uris: list) -> str:
    """Generate a SPARQL VALUES clause from a list of URIs."""
    if not uris:
        return "VALUES ?targetClass { }"

    formatted = " ".join(f"<{uri}>" for uri in sorted(uris))
    return f"VALUES ?targetClass {{ {formatted} }}"


def generate_patterns(ontology_path: Path, config: dict) -> dict:
    """Generate patterns for all categories defined in the config."""
    graph = load_ontology(ontology_path)
    namespace = config.get("namespace", "https://ontology.catholicos.catholic/")

    patterns = {
        "metadata": {
            "namespace": namespace,
            "ontology_file": str(ontology_path.name),
            "generated_by": "pattern_generator.py",
        },
        "categories": {}
    }

    categories = config.get("categories", {})

    for cat_name, cat_config in categories.items():
        print(f"\nProcessing category: {cat_name}")
        cat_labels = set()
        cat_uris = []

        root_classes = cat_config.get("root_classes", [])
        for root in root_classes:
            root_id = root.get("id", "")
            root_label = root.get("label", "")
            root_uri = URIRef(f"{namespace}{root_id}")

            print(f"  Root class: {root_label} ({root_id})")

            # Get labels from subclasses
            labels = get_subclass_labels(graph, root_uri)
            cat_labels.update(labels)
            print(f"    Found {len(labels)} labels")

            # Get URIs from subclasses
            uris = get_subclass_uris(graph, root_uri)
            cat_uris.extend(uris)
            print(f"    Found {len(uris)} classes")

        # Generate patterns
        patterns["categories"][cat_name] = {
            "label": cat_config.get("label", cat_name),
            "description": cat_config.get("description", ""),
            "labels": sorted(cat_labels),
            "label_count": len(cat_labels),
            "regex": generate_regex_pattern(cat_labels),
            "class_uris": sorted(set(cat_uris)),
            "class_count": len(set(cat_uris)),
            "values_clause": generate_values_clause(list(set(cat_uris))),
        }

    return patterns


def main():
    parser = argparse.ArgumentParser(
        description="Generate patterns from the Catholic Semantic Canon ontology"
    )
    parser.add_argument(
        "--ontology", "-o",
        type=Path,
        default=DEFAULT_ONTOLOGY,
        help=f"Path to ontology file (default: {DEFAULT_ONTOLOGY.name})"
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to category config (default: {DEFAULT_CONFIG.name})"
    )
    parser.add_argument(
        "--output", "-O",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path for generated patterns (default: {DEFAULT_OUTPUT.name})"
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.ontology.exists():
        print(f"Error: Ontology file not found: {args.ontology}")
        sys.exit(1)

    # Load config
    config = load_config(args.config)

    # Generate patterns
    patterns = generate_patterns(args.ontology, config)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(args.output, "w") as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)

    print(f"\nPatterns written to: {args.output}")

    # Summary
    print("\n=== Summary ===")
    for cat_name, cat_data in patterns["categories"].items():
        print(f"  {cat_name}: {cat_data['label_count']} labels, {cat_data['class_count']} classes")


if __name__ == "__main__":
    main()
