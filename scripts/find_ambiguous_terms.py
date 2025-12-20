#!/usr/bin/env python3
"""
Scan the ontology for potentially ambiguous labels.

This script identifies terms where the same label appears on classes
in different hierarchies, which may require disambiguation queries.

Usage:
    python scripts/find_ambiguous_terms.py

Output:
    Lists labels that appear on multiple classes, grouped by label,
    showing the class URIs and their parent classes.
"""

import sys
from pathlib import Path
from collections import defaultdict

from rdflib import BNode, Graph, Namespace, RDF, RDFS, OWL
from rdflib.exceptions import ParserError
from rdflib.namespace import SKOS

# Ontology namespace
OSC = Namespace("https://ontology.catholicos.catholic/")

# Path to ontology file
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
ONTOLOGY_PATH = PROJECT_ROOT / "sources" / "ontology-semantic-canon.ttl"


def load_ontology():
    """Load the ontology from TTL file."""
    print(f"Loading ontology from: {ONTOLOGY_PATH}")
    g = Graph()
    g.parse(ONTOLOGY_PATH, format="turtle")
    print(f"Loaded {len(g)} triples")
    return g


def _process_label(g, class_uri, label_predicate, label_to_classes, is_alt=False):
    """Helper to process labels for a given predicate."""
    for label in g.objects(class_uri, label_predicate):
        label_str = str(label).lower().strip()

        # Get parent classes for context
        parents = []
        for parent in g.objects(class_uri, RDFS.subClassOf):
            if parent == OWL.Thing:
                continue
            for parent_label in g.objects(parent, RDFS.label):
                parents.append(str(parent_label))

        entry = {
            'uri': str(class_uri),
            'label': str(label),
            'parents': parents
        }
        if is_alt:
            entry['is_alt'] = True
        label_to_classes[label_str].append(entry)


def find_ambiguous_labels(g):
    """
    Find labels that appear on multiple classes.

    Returns a dict mapping label -> list of dicts with keys:
        'uri': class URI string
        'label': original label string
        'parents': list of parent label strings
        'is_alt': True if from skos:altLabel (optional)
    """
    # Collect all labels for each class
    label_to_classes = defaultdict(list)

    for class_uri in g.subjects(RDF.type, OWL.Class):
        # Skip blank nodes
        if isinstance(class_uri, BNode):
            continue
        # Only consider our ontology namespace
        if not str(class_uri).startswith(str(OSC)):
            continue

        # Get rdfs:label and skos:altLabel
        _process_label(g, class_uri, RDFS.label, label_to_classes)
        _process_label(g, class_uri, SKOS.altLabel, label_to_classes, is_alt=True)

    # Filter to only labels that appear on multiple classes
    ambiguous = {
        label: classes
        for label, classes in label_to_classes.items()
        if len(classes) > 1
    }

    return ambiguous


def print_ambiguous_terms(ambiguous):
    """Print ambiguous terms in a readable format."""
    if not ambiguous:
        print("\nNo ambiguous labels found.")
        return

    print(f"\n{'='*60}")
    print(f"AMBIGUOUS LABELS FOUND: {len(ambiguous)}")
    print(f"{'='*60}\n")

    for label, classes in sorted(ambiguous.items()):
        print(f'Label: "{label}" ({len(classes)} classes)')
        print("-" * 40)
        for cls in classes:
            uri_short = cls['uri'].replace(str(OSC), 'osc:')
            parent_str = ", ".join(cls['parents']) if cls['parents'] else "(no parent)"
            alt_marker = " [altLabel]" if cls.get('is_alt') else ""
            print(f"  • {uri_short}{alt_marker}")
            print(f"    Parent: {parent_str}")
        print()


def generate_values_clause(ambiguous):
    """Generate a VALUES clause for use in SPARQL queries."""
    if not ambiguous:
        return

    print(f"\n{'='*60}")
    print("VALUES CLAUSE FOR SPARQL QUERIES")
    print(f"{'='*60}\n")

    # Collect unique URIs
    uris = set()
    for classes in ambiguous.values():
        for cls in classes:
            uris.add(cls['uri'])

    print("VALUES ?class {")
    for uri in sorted(uris):
        uri_short = uri.replace(str(OSC), 'osc:')
        print(f"  {uri_short}")
    print("}")


def main():
    """Main entry point."""
    try:
        g = load_ontology()
    except FileNotFoundError:
        print(f"Error: Ontology file not found at {ONTOLOGY_PATH}")
        print("Make sure you have the TTL file in the sources/ directory.")
        sys.exit(1)
    except (ParserError, OSError) as e:
        print(f"Error loading ontology: {e}")
        sys.exit(1)

    print("\nScanning for ambiguous labels...")
    ambiguous = find_ambiguous_labels(g)

    print_ambiguous_terms(ambiguous)
    generate_values_clause(ambiguous)

    if ambiguous:
        print("\nNote: Review these terms to determine if they need")
        print("disambiguation in queries/rdflib/07-disambiguation.rq")


if __name__ == "__main__":
    main()
