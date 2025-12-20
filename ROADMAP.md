# Implementation Roadmap: Catholic Semantic Canon Ontology

Based on colleague feedback and analysis, this roadmap outlines prioritized improvements for the ontology-semantic-canon project.

---

## Phase 0: Critical Query Architecture Fix (Immediate Priority)

### The Core Problem: Hardcoded Regex vs. Living Ontology

The current SPARQL queries use hardcoded regex patterns that create **semantic blindness** and **maintenance burden**:

```sparql
# Current approach (fragile)
FILTER(REGEX(STR(?label), "Religious|Order|Monk|Friar|Sister|Brother", "i"))
```

**Problems with this approach:**

| Issue              | Example                                                              |
| ------------------ | -------------------------------------------------------------------- |
| Semantic blindness | "Brother" matches sibling AND monastic — regex can't disambiguate    |
| Maintenance burden | Add `Oblate` to ontology → must manually update every relevant query |
| Brittleness        | Typo in regex breaks silently; ontology validates                    |
| No inheritance     | Regex doesn't know `Franciscan` is a subclass of `ReligiousOrder`    |

---

### 0.1 Refactor Queries to Use Property Paths (Best Solution)

**Implementation**: Replace regex pattern matching with `rdfs:subClassOf*` property paths that leverage the ontology's semantic structure.

**Before** (fragile regex):

```sparql
SELECT ?entity ?label WHERE {
  ?entity rdfs:label ?label .
  FILTER(REGEX(STR(?label), "Religious|Order|Monk|Friar|Sister|Brother", "i"))
}
```

**After** (semantic query):

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX osc: <https://ontology.catholicos.catholic/>

SELECT ?entity ?label ?parentClass WHERE {
  # Use ontology structure — automatically includes new subclasses
  ?entity rdfs:subClassOf* osc:ConsecratedLife .
  ?entity rdfs:label ?label .

  # Show the class hierarchy for context
  OPTIONAL {
    ?entity rdfs:subClassOf ?parentClass .
    FILTER(?parentClass != owl:Thing)
  }
}
ORDER BY ?parentClass ?label
```

**Benefits**:

- Uses the ontology's inheritance hierarchy — add `Oblate` under `ConsecratedLife`, queries automatically include it
- Disambiguates — `Brother` as monastic has a different class URI than `Brother` as sibling
- Self-maintains — the ontology IS the query vocabulary

**Queries to Refactor**:

- [ ] `03-find-church-hierarchy-roles.rq` → Use `osc:ClericalRole` hierarchy
- [ ] `04-find-sacrament-concepts.rq` → Use `osc:Sacrament` hierarchy
- [ ] `06-find-religious-orders.rq` → Use `osc:ConsecratedLife` hierarchy
- [ ] `07-find-juridical-structures.rq` → Use `osc:JuridicalEntity` hierarchy
- [ ] `08-authority-properties.rq` → Use `osc:AuthorityConcept` hierarchy
- [ ] `13-find-liturgical-concepts.rq` → Use `osc:LiturgicalConcept` hierarchy
- [ ] `14-find-canon-law-documents.rq` → Use `osc:CanonLawDocument` hierarchy

---

### 0.2 Add Query Category Annotation Properties

**Problem**: Not all concepts fit neatly into a single hierarchy. Some may need explicit tagging for query categorization.

**Implementation**: Add custom annotation property in WebProtege:

```turtle
osc:queryCategory a owl:AnnotationProperty ;
    rdfs:label "query category"@en ;
    skos:definition "Explicit category tag for query grouping."@en .

# Usage example
osc:Franciscan a owl:Class ;
    rdfs:subClassOf osc:MendicantOrder ;
    osc:queryCategory "religious_life" ;
    osc:queryCategory "mendicant" .
```

**Query pattern**:

```sparql
SELECT ?entity ?label WHERE {
  ?entity osc:queryCategory "religious_life" ;
          rdfs:label ?label .
}
```

**WebProtege Tasks**:

- [ ] Create `osc:queryCategory` annotation property
- [ ] Define standard category values (religious_life, sacraments, hierarchy, juridical, liturgical)
- [ ] Apply categories to relevant classes

---

### 0.3 Add SKOS Annotations for Disambiguation

**Problem**: Terms like "Brother" can mean multiple things. The ontology needs explicit disambiguation.

**Implementation**: Use SKOS vocabulary consistently:

```turtle
osc:MonasticBrother a owl:Class ;
    rdfs:label "Brother"@en ;
    skos:altLabel "Frater"@la ;
    skos:altLabel "Religious Brother"@en ;
    skos:scopeNote "A male member of a religious institute who is not ordained. Distinguished from 'brother' as familial sibling."@en ;
    skos:definition "A male religious who has taken vows in a religious institute."@en .
```

**Annotation Properties to Use**:

| Property          | Purpose                                |
| ----------------- | -------------------------------------- |
| `rdfs:label`      | Primary display name                   |
| `skos:altLabel`   | Synonyms, alternate names, Latin terms |
| `skos:prefLabel`  | Preferred label when multiple exist    |
| `skos:scopeNote`  | Disambiguation context                 |
| `skos:definition` | Formal definition                      |
| `skos:example`    | Usage examples                         |

**WebProtege Tasks**:

- [ ] Audit classes with ambiguous labels (Brother, Order, Mass, etc.)
- [ ] Add `skos:scopeNote` for disambiguation
- [ ] Add `skos:altLabel` for synonyms and Latin equivalents

---

### 0.4 Use VALUES Clause for Fixed Lists

**Implementation**: When you need a fixed list of types, use `VALUES` instead of regex:

**Before** (regex):

```sparql
FILTER(REGEX(STR(?label), "Pope|Cardinal|Archbishop|Bishop", "i"))
```

**After** (VALUES clause):

```sparql
VALUES ?targetType {
  osc:Pope
  osc:Cardinal
  osc:Archbishop
  osc:Bishop
}
?entity a ?targetType ;
        rdfs:label ?label .
```

**Benefits**:

- Faster than regex (indexed lookups vs. string scanning)
- Unambiguous (uses URIs, not string matching)
- Generatable from ontology queries

---

### 0.5 Build-Time Pattern Generation (For External Systems)

**Use Case**: External systems that don't speak SPARQL may still need regex patterns. Generate them from the ontology.

**Workflow**:

```text
Ontology (OWL/TTL)
    ↓ [SPARQL CONSTRUCT query]
Terms vocabulary (JSON/YAML)
    ↓ [Build script]
Generated regex patterns
    ↓
External systems use generated patterns
```

**Step 1**: Create vocabulary extraction query (`queries/extract-vocabulary.rq`):

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX osc: <https://ontology.catholicos.catholic/>

SELECT ?category ?label WHERE {
  ?entity osc:queryCategory ?category ;
          rdfs:label ?label .
}
UNION
{
  ?entity osc:queryCategory ?category ;
          skos:altLabel ?label .
}
ORDER BY ?category ?label
```

**Step 2**: Create pattern generator (`scripts/generate_patterns.py`):

```python
from rdflib import Graph
import json
import re
from collections import defaultdict

def generate_patterns(ontology_path, output_path):
    g = Graph()
    g.parse(ontology_path)

    query = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX osc: <https://ontology.catholicos.catholic/>

    SELECT ?category ?label WHERE {
      { ?entity osc:queryCategory ?category ; rdfs:label ?label }
      UNION
      { ?entity osc:queryCategory ?category ; skos:altLabel ?label }
    }
    """

    categories = defaultdict(set)
    for row in g.query(query):
        categories[str(row.category)].add(str(row.label))

    patterns = {
        cat: "|".join(re.escape(term) for term in sorted(terms))
        for cat, terms in categories.items()
    }

    with open(output_path, "w") as f:
        json.dump(patterns, f, indent=2)

    return patterns

if __name__ == "__main__":
    generate_patterns(
        "sources/ontology-semantic-canon.ttl",
        "generated/query-patterns.json"
    )
```

**Step 3**: Add to CI/CD to regenerate on ontology changes.

---

### Recommended Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    WebProtégé (Source of Truth)             │
│                                                             │
│  Classes with:                                              │
│  - rdfs:label (display name)                                │
│  - skos:altLabel (synonyms: "Brother", "Frater")            │
│  - skos:scopeNote (disambiguation: "monastic, not sibling") │
│  - osc:queryCategory (explicit query groupings)             │
└──────────────────────────┬──────────────────────────────────┘
                           │ Export
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              ontology-semantic-canon.owl / .ttl             │
└──────────────────────────┬──────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
┌───────────────────────┐    ┌────────────────────────────────┐
│  Semantic Queries     │    │  Generated Pattern Files       │
│  (property paths)     │    │  (for external systems)        │
│                       │    │                                │
│  ?x rdfs:subClassOf*  │    │  religious_life.json           │
│     osc:ConsecratedLife│   │  sacraments.json               │
│                       │    │  hierarchy.json                │
└───────────────────────┘    └────────────────────────────────┘
```

---

## Phase 1: Ontology Structure Improvements (High Priority)

### 1.1 Define Explicit Class Hierarchy for Scripture Structure

**Problem**: The current ontology lacks explicit `hasPart` relations between books, chapters, and verses, making hierarchical navigation difficult.

**Implementation**:

- Add `hasPart` / `isPartOf` object properties with proper inverses
- Define class hierarchy: `Bible → Testament → Book → Chapter → Verse`
- Use SKOS or DCTerms vocabulary for part-whole relationships

**Example Triples to Add**:

```turtle
@prefix osc: <https://ontology.catholicos.catholic/> .
@prefix dcterms: <http://purl.org/dc/terms/> .

osc:hasPart a owl:ObjectProperty ;
    rdfs:label "has part"@en ;
    owl:inverseOf osc:isPartOf ;
    rdfs:domain osc:ScriptureUnit ;
    rdfs:range osc:ScriptureUnit .

osc:Bible rdfs:subClassOf osc:ScriptureCollection .
osc:Testament rdfs:subClassOf osc:ScriptureUnit .
osc:Book rdfs:subClassOf osc:ScriptureUnit .
osc:Chapter rdfs:subClassOf osc:ScriptureUnit .
osc:Verse rdfs:subClassOf osc:ScriptureUnit .
```

**WebProtege Tasks**:

- [ ] Create `ScriptureUnit` superclass
- [ ] Create `Bible`, `Testament`, `Book`, `Chapter`, `Verse` classes
- [ ] Add `hasPart` and `isPartOf` object properties
- [ ] Set domain/range constraints

---

### 1.2 Add Missing Numeric Properties

**Problem**: No properties exist for book/chapter/verse numbering, preventing queries like "find verse 3:16 of John."

**Implementation**:

- Add datatype properties: `hasBookNumber`, `hasChapterNumber`, `hasVerseNumber`
- Define range as `xsd:integer` or `xsd:positiveInteger`

**Example**:

```turtle
osc:hasBookNumber a owl:DatatypeProperty ;
    rdfs:label "has book number"@en ;
    rdfs:domain osc:Book ;
    rdfs:range xsd:positiveInteger .

osc:hasChapterNumber a owl:DatatypeProperty ;
    rdfs:label "has chapter number"@en ;
    rdfs:domain osc:Chapter ;
    rdfs:range xsd:positiveInteger .

osc:hasVerseNumber a owl:DatatypeProperty ;
    rdfs:label "has verse number"@en ;
    rdfs:domain osc:Verse ;
    rdfs:range xsd:positiveInteger .
```

---

### 1.3 Adopt Standard Bibliographic Vocabularies

**Problem**: Custom properties may limit interoperability with existing linked data resources.

**Recommended Standards**:

| Vocabulary      | Use Case                                | URI                                |
| --------------- | --------------------------------------- | ---------------------------------- |
| **FRBR**        | Work/Expression/Manifestation hierarchy | `http://purl.org/vocab/frbr/core#` |
| **FaBiO**       | Bibliographic ontology                  | `http://purl.org/spar/fabio/`      |
| **Dublin Core** | Basic metadata                          | `http://purl.org/dc/terms/`        |
| **BIBO**        | Bibliography ontology                   | `http://purl.org/ontology/bibo/`   |

**Implementation**:

- Map existing classes to FRBR concepts (Bible as Work, translations as Expressions)
- Use FaBiO for document types (Book, Chapter)
- Leverage `dcterms:isPartOf` for containment

---

### 1.4 Add Domain/Range Constraints

**Problem**: Some object properties lack explicit domain/range declarations, reducing reasoning capabilities.

**Tasks**:

- [ ] Audit all object properties in WebProtege
- [ ] Add missing `rdfs:domain` declarations
- [ ] Add missing `rdfs:range` declarations
- [ ] Document constraint rationale

**Query to Find Missing Constraints**:

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?property WHERE {
  ?property a owl:ObjectProperty .
  FILTER NOT EXISTS { ?property rdfs:domain ?d }
}
```

---

### 1.5 Add Inverse Properties

**Problem**: Navigation in both directions (parent→child and child→parent) requires inverse properties.

**Implementation**:

- Add `owl:inverseOf` declarations for all hierarchical relationships
- Ensure symmetrical property definitions

**Key Inverse Pairs**:

| Property     | Inverse       |
| ------------ | ------------- |
| `hasPart`    | `isPartOf`    |
| `hasChapter` | `chapterOf`   |
| `hasVerse`   | `verseOf`     |
| `contains`   | `containedIn` |
| `cites`      | `citedBy`     |

---

## Phase 2: Bible Canon Modeling (Medium Priority)

### 2.1 Define Canon Individuals

**Problem**: Different Christian traditions use different biblical canons. The ontology should model this.

**Implementation**:

- Create `BibleCanon` class
- Add individuals for major canons
- Link books to their respective canons

**Example**:

```turtle
osc:BibleCanon a owl:Class ;
    rdfs:label "Bible Canon"@en ;
    skos:definition "A specific collection of books considered authoritative scripture."@en .

osc:CatholicCanon a osc:BibleCanon ;
    rdfs:label "Catholic Canon"@en ;
    skos:definition "The 73-book canon recognized by the Catholic Church."@en .

osc:ProtestantCanon a osc:BibleCanon ;
    rdfs:label "Protestant Canon"@en ;
    skos:definition "The 66-book canon recognized by most Protestant denominations."@en .

osc:OrthodoxCanon a osc:BibleCanon ;
    rdfs:label "Orthodox Canon"@en ;
    skos:definition "The extended canon recognized by Eastern Orthodox churches."@en .

osc:EthiopianCanon a osc:BibleCanon ;
    rdfs:label "Ethiopian Canon"@en ;
    skos:definition "The 81-book canon of the Ethiopian Orthodox Tewahedo Church."@en .
```

---

### 2.2 Model Canon Membership

**Implementation**:

- Add `includedInCanon` object property
- Link book individuals to canon individuals
- Model deuterocanonical/apocryphal distinctions

**Example**:

```turtle
osc:includedInCanon a owl:ObjectProperty ;
    rdfs:label "included in canon"@en ;
    rdfs:domain osc:Book ;
    rdfs:range osc:BibleCanon .

osc:BookOfTobit a osc:Book ;
    rdfs:label "Tobit"@en ;
    osc:includedInCanon osc:CatholicCanon, osc:OrthodoxCanon ;
    osc:hasCanonStatus osc:Deuterocanonical .
```

---

### 2.3 Define Canon Status Classes

**Implementation**:

```turtle
osc:CanonStatus a owl:Class ;
    rdfs:label "Canon Status"@en .

osc:Protocanonical a osc:CanonStatus ;
    rdfs:label "Protocanonical"@en ;
    skos:definition "Books accepted by all major Christian traditions."@en .

osc:Deuterocanonical a osc:CanonStatus ;
    rdfs:label "Deuterocanonical"@en ;
    skos:definition "Books in the Catholic/Orthodox canons but not Protestant."@en .

osc:Apocryphal a osc:CanonStatus ;
    rdfs:label "Apocryphal"@en ;
    skos:definition "Books considered non-canonical but historically significant."@en .
```

---

## Phase 3: Query and Tooling Improvements (Medium Priority)

### 3.1 Create Reusable Query Templates

**Location**: `queries/templates/`

**Templates to Create**:

1. `template-find-by-hierarchy.rq` - Navigate part-whole relationships
2. `template-find-by-reference.rq` - Look up Book:Chapter:Verse
3. `template-canon-comparison.rq` - Compare books across canons
4. `template-cross-reference.rq` - Find citation relationships
5. `template-search-definitions.rq` - Full-text search with ranking

**Example Template** (`template-find-by-reference.rq`):

```sparql
# Template: Find Scripture by Reference
# Parameters: $BOOK, $CHAPTER, $VERSE

PREFIX osc: <https://ontology.catholicos.catholic/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?verse ?text WHERE {
  ?book rdfs:label "$BOOK"@en .
  ?chapter osc:isPartOf ?book ;
           osc:hasChapterNumber $CHAPTER .
  ?verse osc:isPartOf ?chapter ;
         osc:hasVerseNumber $VERSE ;
         osc:hasText ?text .
}
```

---

### 3.2 Standardize Query Prefixes

**Problem**: Queries inconsistently define prefixes, leading to errors and maintenance burden.

**Solution**: Create `queries/common-prefixes.rq` include file:

```sparql
# Common Prefixes for Catholic Semantic Canon
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX folio: <http://purl.obolibrary.org/obo/>
PREFIX osc: <https://ontology.catholicos.catholic/>
```

**Update Query Runners**:

- Python: Auto-inject common prefixes
- Java: Auto-inject common prefixes

---

### 3.3 Add Query Validation

**Implementation**:

- Add SPARQL syntax validation to query runners
- Create test harness for all queries
- Add expected result counts for regression testing

**Python Enhancement** (`examples/python/query_validator.py`):

```python
def validate_query(query_file):
    """Validate SPARQL syntax before execution."""
    from rdflib.plugins.sparql import prepareQuery
    with open(query_file) as f:
        query_text = f.read()
    try:
        prepareQuery(query_text)
        return True, None
    except Exception as e:
        return False, str(e)
```

---

## Phase 4: Testing and Quality Assurance (Medium Priority)

### 4.1 Create Test Suite

**Location**: `tests/`

**Test Categories**:

1. **Ontology Validation Tests**
   - OWL consistency checking
   - Domain/range constraint validation
   - Inverse property symmetry

2. **Query Tests**
   - Syntax validation for all `.rq` files
   - Expected result count assertions
   - Performance benchmarks

3. **Integration Tests**
   - Python query runner tests
   - Java query runner tests
   - Cross-language result consistency

**Example Test Structure**:

```text
tests/
├── ontology/
│   ├── test_consistency.py
│   ├── test_constraints.py
│   └── test_hierarchy.py
├── queries/
│   ├── test_query_syntax.py
│   ├── test_query_results.py
│   └── expected_results.json
└── integration/
    ├── test_python_runner.py
    └── test_java_runner.sh
```

---

### 4.2 Add CI/CD Pipeline

**Implementation** (`.github/workflows/validate.yml`):

```yaml
name: Validate Ontology

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate RDF Syntax
        run: |
          pip install rdflib
          python -c "from rdflib import Graph; g = Graph(); g.parse('sources/ontology-semantic-canon.ttl')"

      - name: Run Query Tests
        run: |
          pip install -r examples/python/requirements.txt
          python -m pytest tests/queries/

      - name: Validate with Apache Jena
        run: |
          riot --validate sources/ontology-semantic-canon.ttl
```

---

## Phase 5: Documentation Improvements (Lower Priority)

### 5.1 Ontology Design Documentation

**Create**: `docs/design-decisions.md`

**Content**:

- Rationale for FOLIO base ontology choice
- Namespace design decisions
- Class hierarchy philosophy
- Property naming conventions
- Versioning strategy

---

### 5.2 Vocabulary Documentation

**Create**: `docs/vocabulary.md`

**Content**:

- Complete class reference with definitions
- Property reference with domains/ranges
- Usage examples for each major class
- Cross-references to external vocabularies

---

### 5.3 API/Query Documentation

**Create**: `docs/querying.md`

**Content**:

- Query patterns for common use cases
- Performance optimization tips
- Reasoning/inference examples
- Named graph usage

---

## Phase 6: Future Enhancements (Long-term)

### 6.1 SPARQL Endpoint Deployment

- Deploy Apache Jena Fuseki as public endpoint
- Add authentication for write operations
- Implement rate limiting

### 6.2 Linked Data Integration

- Link to DBpedia/Wikidata entities
- Add `owl:sameAs` relationships
- Implement content negotiation

### 6.3 OWL Reasoning Examples

- Add reasoning examples with Pellet/HermiT
- Demonstrate inferred relationships
- Create inference query patterns

### 6.4 Multi-language Support

- Add labels in Latin, Greek, Hebrew
- Support liturgical language queries
- Add translation relationships

---

## Implementation Priority Matrix

| Phase                              | Priority     | Effort | Impact        | Dependencies  |
| ---------------------------------- | ------------ | ------ | ------------- | ------------- |
| **0.1 Property Path Queries**      | **Critical** | Medium | **Very High** | None          |
| **0.2 Query Category Annotations** | **Critical** | Low    | High          | None          |
| **0.3 SKOS Disambiguation**        | **Critical** | Medium | High          | None          |
| **0.4 VALUES Clause Patterns**     | **Critical** | Low    | Medium        | 0.1           |
| **0.5 Pattern Generation**         | High         | Medium | Medium        | 0.2, 0.3      |
| 1.1 Class Hierarchy                | High         | Medium | High          | 0.x           |
| 1.2 Numeric Properties             | High         | Low    | High          | 1.1           |
| 1.3 Standard Vocabularies          | High         | Medium | High          | None          |
| 1.4 Domain/Range                   | High         | Medium | Medium        | 1.1           |
| 1.5 Inverse Properties             | High         | Low    | Medium        | 1.1           |
| 2.1 Canon Individuals              | Medium       | Low    | High          | 1.1           |
| 2.2 Canon Membership               | Medium       | Medium | High          | 2.1           |
| 2.3 Canon Status                   | Medium       | Low    | Medium        | 2.1           |
| 3.1 Query Templates                | Medium       | Medium | Medium        | 0.x, 1.x      |
| 3.2 Standard Prefixes              | Medium       | Low    | Medium        | None          |
| 3.3 Query Validation               | Medium       | Medium | Medium        | None          |
| 4.1 Test Suite                     | Medium       | High   | High          | 0.x, 1.x, 3.x |
| 4.2 CI/CD Pipeline                 | Medium       | Medium | High          | 4.1           |
| 5.x Documentation                  | Lower        | Medium | Medium        | 1.x, 2.x      |
| 6.x Future                         | Long-term    | High   | High          | All           |

---

## Reference Implementations

A colleague has developed concrete implementations for both solutions. These should be integrated into the repository:

### Directory Structure to Add

```text
ontology-semantic-canon/
├── config/
│   └── query-categories.yaml    # Category→class mappings
├── scripts/
│   ├── pattern_generator.py     # Extract patterns from OWL
│   ├── query_templater.py       # Populate templates
│   └── vocabulary_extractor.py  # Full vocabulary export
├── queries/
│   ├── semantic/                # Solution 1: Semantic queries
│   │   ├── 01-religious-orders.rq
│   │   ├── 02-church-hierarchy.rq
│   │   ├── 03-sacraments.rq
│   │   ├── 04-juridical-structures.rq
│   │   ├── 05-liturgical-concepts.rq
│   │   ├── 06-canon-law-documents.rq
│   │   └── 07-disambiguation.rq
│   ├── templates/               # Query templates with {{placeholders}}
│   └── generated/               # Auto-generated from templates
├── generated/
│   ├── patterns.json            # Generated regex patterns
│   └── vocabulary.json          # Complete term export
└── .github/workflows/
    └── regenerate-patterns.yml  # Auto-regeneration on ontology change
```

### Semantic Queries (Solution 1)

| Query                        | Purpose                                     |
| ---------------------------- | ------------------------------------------- |
| `01-religious-orders.rq`     | Religious institutes via `rdfs:subClassOf*` |
| `02-church-hierarchy.rq`     | Clerical offices and ranks                  |
| `03-sacraments.rq`           | All seven sacraments                        |
| `04-juridical-structures.rq` | Dioceses, parishes, curia                   |
| `05-liturgical-concepts.rq`  | Mass, rites, seasons                        |
| `06-canon-law-documents.rq`  | Encyclicals, canons, decrees                |
| `07-disambiguation.rq`       | Resolves "Brother" (monastic vs. sibling)   |

### Pattern Generation Workflow (Solution 2)

```bash
# 1. Generate patterns from ontology
python scripts/pattern_generator.py \
    --ontology sources/ontology-semantic-canon.ttl \
    --config config/query-categories.yaml \
    --output generated/patterns.json

# 2. Populate query templates
python scripts/query_templater.py \
    --patterns generated/patterns.json \
    --templates queries/templates/ \
    --output queries/generated/
```

---

## Getting Started

1. **Integrate reference implementations**: Add the `scripts/`, `config/`, and `queries/semantic/` directories
2. **Point to real ontology**: Update paths in `config/query-categories.yaml`
3. **Adjust namespaces**: Ensure scripts use `https://ontology.catholicos.catholic/`
4. **Start with Phase 0**: Fix the query architecture
   - Define root classes for each query category (e.g., `osc:ConsecratedLife`, `osc:ClericalRole`)
   - Add `osc:queryCategory` annotation property in WebProtege
   - Add `skos:altLabel` and `skos:scopeNote` to ambiguous terms
5. **Test semantic queries**: Run the new semantic queries against the ontology
6. **Then Phase 1.1**: Define the Scripture hierarchy in WebProtege
7. **Add numeric properties (1.2)** immediately after hierarchy
8. **Document decisions** as you go
9. **Create tests** for each new feature before moving on

All ontology changes should be made through WebProtege, then exported to the repository.

---

## Contributing

1. Discuss proposed changes via GitHub Issues first
2. Make structural changes in WebProtege
3. Export updated ontology files
4. Update queries and documentation
5. Run test suite before submitting PR
6. Update this roadmap as items are completed

---

_Last updated: December 2024_
