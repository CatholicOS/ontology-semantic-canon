#!/usr/bin/env python3
"""
Catholic Semantic Canon - SPARQL Query Runner

This script loads the ontology and runs SPARQL queries from the queries/ folder.

Usage:
    python query_runner.py                     # Interactive menu
    python query_runner.py 01                  # Run query 01-list-all-classes.rq
    python query_runner.py --list              # List available queries
    python query_runner.py --query "SELECT ..."  # Run inline SPARQL
    python query_runner.py --semantic          # Use semantic queries (property paths)
    python query_runner.py --semantic 01       # Run semantic query 01
    python query_runner.py --semantic --list   # List semantic queries
"""

import argparse
import pickle
import sys
from pathlib import Path

try:
    from rdflib import Graph
except ImportError:
    print("Error: rdflib is not installed.")
    print("Install it with: pip install -r requirements.txt")
    sys.exit(1)


# Paths relative to this script
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
SOURCES_DIR = PROJECT_ROOT / "sources"
QUERIES_DIR = PROJECT_ROOT / "queries"
RDFLIB_QUERIES_DIR = QUERIES_DIR / "rdflib"

# Default ontology file (OWL/XML format with pickle caching for stability)
DEFAULT_ONTOLOGY = SOURCES_DIR / "ontology-semantic-canon.owl"


def load_ontology(ontology_path: Path = DEFAULT_ONTOLOGY) -> Graph:
    """Load the ontology into an RDF graph, using pickle cache if available."""
    cache_path = ontology_path.with_suffix(".pickle")

    # Try to load from cache first
    if cache_path.exists():
        try:
            print(f"Loading from cache {cache_path.name}...")
            with open(cache_path, "rb") as f:
                g = pickle.load(f)
            print(f"Loaded {len(g)} triples from cache.")
            return g
        except Exception as e:
            print(f"Cache load failed ({e}), parsing ontology...")

    print(f"Loading ontology from {ontology_path.name}...")
    g = Graph()

    # Determine format from extension
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
        print(f"Saving to cache {cache_path.name}...")
        with open(cache_path, "wb") as f:
            pickle.dump(g, f)
        print("Cache saved successfully.")
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

    return g


def list_queries(semantic: bool = False) -> list[Path]:
    """List all available query files.

    Args:
        semantic: If True, list queries from the rdflib/ subdirectory
                  which use semantic patterns optimized for rdflib/Python.
    """
    query_dir = RDFLIB_QUERIES_DIR if semantic else QUERIES_DIR

    if not query_dir.exists():
        print(f"Error: Queries directory not found: {query_dir}")
        return []

    queries = sorted(query_dir.glob("*.rq"))
    return queries


def run_query(graph: Graph, query_text: str) -> None:
    """Execute a SPARQL query and print results."""
    try:
        results = graph.query(query_text)

        # Check if it's a CONSTRUCT query (returns a graph)
        if hasattr(results, 'graph') and results.graph is not None:
            print("\n--- CONSTRUCT Results (Turtle format) ---\n")
            print(results.graph.serialize(format="turtle"))
        else:
            # SELECT query results
            # Defensive check for results.vars (rdflib bug workaround)
            if results.vars and hasattr(results.vars, '__iter__'):
                try:
                    # Print header
                    header = " | ".join(str(var) for var in results.vars)
                    print(f"\n{header}")
                    print("-" * len(header))
                except TypeError:
                    # results.vars is not iterable due to rdflib bug
                    print("\n(Unable to display header due to rdflib bug)")

            count = 0
            for row in results:
                values = []
                for val in row:
                    if val is None:
                        values.append("")
                    else:
                        # Shorten URIs for readability
                        val_str = str(val)
                        if isinstance(val_str, str) and val_str.startswith("http"):
                            val_str = val_str.split("/")[-1].split("#")[-1]
                        values.append(str(val_str))
                print(" | ".join(values))
                count += 1

            print(f"\n({count} results)")

    except Exception as e:
        print(f"Query error: {e}")
        print("(This may be an intermittent rdflib/Python 3.12 bug - try running the query again)")


def run_query_file(graph: Graph, query_path: Path) -> None:
    """Load and execute a query from a file."""
    print(f"\n=== Running: {query_path.name} ===\n")

    with open(query_path, "r") as f:
        query_text = f.read()

    run_query(graph, query_text)


def interactive_menu(graph: Graph, semantic: bool = False) -> None:
    """Show an interactive menu to select and run queries.

    Args:
        semantic: If True, show semantic queries from queries/rdflib/
                  instead of regex-based queries from queries/.
    """
    queries = list_queries(semantic=semantic)

    if not queries:
        return

    query_type = "Semantic" if semantic else "Standard"

    while True:
        print("\n" + "=" * 60)
        print(f"Available {query_type} SPARQL Queries:")
        if semantic:
            print("(Optimized for rdflib - use queries/jena/ with arq for full features)")
        print("=" * 60)

        for i, q in enumerate(queries, 1):
            # Extract description from filename
            name = q.stem
            print(f"  {i:2}. {name}")

        print("\n  q. Quit")
        print("  c. Custom SPARQL query")
        print(f"  s. Switch to {'standard' if semantic else 'semantic'} queries")
        print("=" * 60)

        choice = input("\nSelect a query number (or 'q' to quit): ").strip().lower()

        if choice == 'q':
            print("Goodbye!")
            break
        elif choice == 'c':
            print("\nEnter your SPARQL query (end with an empty line):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            if lines:
                run_query(graph, "\n".join(lines))
        elif choice == 's':
            # Switch query type and refresh the menu
            semantic = not semantic
            queries = list_queries(semantic=semantic)
            query_type = "Semantic" if semantic else "Standard"
            print(f"\nSwitched to {query_type.lower()} queries.")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(queries):
                    run_query_file(graph, queries[idx])
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Please enter a number.")


def main():
    parser = argparse.ArgumentParser(
        description="Run SPARQL queries against the Catholic Semantic Canon ontology"
    )
    parser.add_argument(
        "query_number",
        nargs="?",
        help="Query number to run (e.g., '01' for 01-list-all-classes.rq)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available queries"
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        help="Run an inline SPARQL query"
    )
    parser.add_argument(
        "--ontology", "-o",
        type=Path,
        default=DEFAULT_ONTOLOGY,
        help=f"Path to ontology file (default: {DEFAULT_ONTOLOGY.name})"
    )
    parser.add_argument(
        "--semantic", "-s",
        action="store_true",
        help="Use semantic queries (UNION patterns to emulate subClassOf*, avoids rdflib segfaults)"
    )

    args = parser.parse_args()

    # List queries mode
    if args.list:
        queries = list_queries(semantic=args.semantic)
        query_type = "semantic" if args.semantic else "standard"
        print(f"\nAvailable {query_type} queries:")
        for q in queries:
            print(f"  {q.name}")
        if not args.semantic:
            print("\n  (Use --semantic to list semantic queries)")
        return

    # Load ontology
    if not args.ontology.exists():
        print(f"Error: Ontology file not found: {args.ontology}")
        print("Make sure you're running from the examples/python directory")
        print("or provide the path with --ontology")
        sys.exit(1)

    graph = load_ontology(args.ontology)

    # Run inline query
    if args.query:
        run_query(graph, args.query)
        return

    # Run specific query by number
    if args.query_number:
        queries = list_queries(semantic=args.semantic)
        matching = [q for q in queries if q.name.startswith(args.query_number)]
        if matching:
            run_query_file(graph, matching[0])
        else:
            query_type = "semantic" if args.semantic else "standard"
            print(f"No {query_type} query found matching '{args.query_number}'")
            print("Use --list to see available queries")
        return

    # Interactive mode
    interactive_menu(graph, semantic=args.semantic)


if __name__ == "__main__":
    main()
